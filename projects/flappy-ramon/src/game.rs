//! Direct, hand-authored Rust port of the Flappy Madruga event logic.
//!
//! This is not a the source editor importer. The source project, layouts and event
//! sheets were inspected and translated directly. The update order below
//! follows the original Event Sheet group order:
//! Start -> Movement -> Collisions -> Scoring -> Background -> Obstacle.

use crate::geometry::{
    polygons_intersect, rectangle_polygon, transform_polygon, BOTTOM_PIPE_CHAVES,
    MADRUGA_DEFAULT, MADRUGA_FLYING, PIPE_DEFAULT, TOP_PIPE_CHAVES,
};
use impossible_runtime::{
    validate_source_program, DeterministicRng, SourceEventHandler, SourceFrameClock,
    SourceGroup, WaitQueue,
};

pub const VIEW_WIDTH: f32 = 400.0;
pub const VIEW_HEIGHT: f32 = 500.0;

const BIRD_START: [f32; 2] = [69.332_04, 240.193_33];
const BIRD_SIZE: [f32; 2] = [73.076_92, 56.447_76];
const BIRD_HOTSPOT: [f32; 2] = [0.513158, 0.524590];
const BIRD_JUMP_STRENGTH: f32 = 500.0;
const PLATFORM_GRAVITY: f32 = 1500.0;
const PLATFORM_MAX_FALL_SPEED: f32 = 1000.0;

const PIPE_SIZE: [f32; 2] = [70.0, 604.0];
const PIPE_HOTSPOT: [f32; 2] = [0.5, 0.5];

const GROUND_COLLISION: (f32, f32, f32, f32) = (0.0, 453.0, 1107.0, 19.0);
const BACKGROUND_WRAP_X: f32 = -560.0;
const GROUND_WRAP_X: f32 = -410.0;
const PIPE_DESTROY_X: f32 = -50.0;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Layout {
    Start,
    Continuous,
    Chaves,
}

impl Layout {
    pub fn from_cli_argument(value: &str) -> Option<Self> {
        match value.to_ascii_lowercase().as_str() {
            "start" => Some(Self::Start),
            "continuous" => Some(Self::Continuous),
            "chaves" => Some(Self::Chaves),
            _ => None,
        }
    }

    pub fn source_name(self) -> &'static str {
        match self {
            Self::Start => "Start",
            Self::Continuous => "Continuous",
            Self::Chaves => "Chaves",
        }
    }

    /// The original project contains no layout after Chaves. Returning no
    /// successor is deliberate: the source action has no known fourth target.
    pub fn next_in_source_order(self) -> Option<Self> {
        match self {
            Self::Start => Some(Self::Continuous),
            Self::Continuous => Some(Self::Chaves),
            Self::Chaves => None,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BirdAnimation {
    Default,
    Flying,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PipeSkin {
    Default,
    Chaves,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CollisionKind {
    Ground,
    TopPipe,
    BottomPipe,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Effect {
    StopAllAudio,
    PlayMusic,
    StopMusic,
    PlayBeat,
    PlayQueda,
    SaveHighScore(u32),
    RequestGooglePlaySignIn,
    NextLayoutUnavailable,
}

#[derive(Clone, Copy, Debug, Default)]
pub struct InputFrame {
    /// Click on the Start layout's Play_Continuous button.
    pub start_button_pressed: bool,
    /// Touch-start or the Space key.
    pub flap_pressed: bool,
    /// Click on the retry button or press Return after Queda becomes true.
    pub restart_pressed: bool,
    /// Start layout's Return key path.
    pub return_pressed: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum WaitEvent {
    BirdAnimationDefault,
    TopPipeGameOver,
    RetryVisible,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum RestartTask {
    RestartCurrentLayout,
}

#[derive(Clone, Debug)]
pub struct Bird {
    /// the source editor world position is the sprite hotspot, not its visual center.
    pub position: [f32; 2],
    pub velocity_y: f32,
    pub angle_degrees: f32,
    pub queda: bool,
    pub animation: BirdAnimation,
}

impl Bird {
    fn new() -> Self {
        Self {
            position: BIRD_START,
            velocity_y: -BIRD_JUMP_STRENGTH,
            angle_degrees: 320.0,
            queda: false,
            animation: BirdAnimation::Default,
        }
    }

    pub fn visual_center(&self) -> [f32; 2] {
        [
            self.position[0] + (0.5 - BIRD_HOTSPOT[0]) * BIRD_SIZE[0],
            self.position[1] + (0.5 - BIRD_HOTSPOT[1]) * BIRD_SIZE[1],
        ]
    }

    pub fn collision_polygon(&self) -> Vec<[f32; 2]> {
        let points: &[[f32; 2]] = match self.animation {
            BirdAnimation::Default => &MADRUGA_DEFAULT,
            BirdAnimation::Flying => &MADRUGA_FLYING,
        };

        transform_polygon(
            points,
            self.position,
            BIRD_SIZE,
            BIRD_HOTSPOT,
            self.angle_degrees,
        )
    }
}

#[derive(Clone, Debug)]
pub struct Pipe {
    pub id: u64,
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
    pub animation_frame: usize,
    animation_clock: f32,
}

impl Pipe {
    fn new(id: u64, x: f32, y: f32) -> Self {
        Self {
            id,
            x,
            y,
            width: PIPE_SIZE[0],
            height: PIPE_SIZE[1],
            animation_frame: 0,
            animation_clock: 0.0,
        }
    }

    pub fn collision_polygon(&self, skin: PipeSkin, top: bool) -> Vec<[f32; 2]> {
        let points: Vec<[f32; 2]> = match skin {
            PipeSkin::Default => PIPE_DEFAULT.to_vec(),
            PipeSkin::Chaves if top => TOP_PIPE_CHAVES[self.animation_frame % 4].to_vec(),
            PipeSkin::Chaves => BOTTOM_PIPE_CHAVES[self.animation_frame % 4].to_vec(),
        };

        transform_polygon(
            &points,
            [self.x, self.y],
            [self.width, self.height],
            PIPE_HOTSPOT,
            0.0,
        )
    }
}

#[derive(Clone, Debug)]
pub struct PipePair {
    pub top: Pipe,
    pub bottom: Pipe,
    pub top_alive: bool,
    pub bottom_alive: bool,
    pub scored: bool,
}

impl PipePair {
    fn spawned(id: u64, top_y: f32) -> Self {
        Self {
            top: Pipe::new(id, 440.0, top_y),
            bottom: Pipe::new(id + 1, 440.0, top_y + 750.0),
            top_alive: true,
            bottom_alive: true,
            scored: false,
        }
    }
}

#[derive(Clone, Debug)]
pub struct Game {
    pub layout: Layout,
    pub bird: Bird,
    pub pipes: Vec<PipePair>,
    pub score: u32,
    pub high_score: u32,
    pub required_score: u32,
    pub scroll_speed: f32,
    pub seconds_per_obstacle: f32,
    pub layout_name: String,
    pub tiled_background_x: f32,
    pub tiled_background2_x: f32,
    pub pipe_skin: PipeSkin,
    pub retry_visible: bool,
    pub retry_enabled: bool,
    pub high_score_visible: bool,
    pub high_score_text: String,
    pub score_text_on_top: bool,
    pub music_requested: bool,
    pub migration_warnings: Vec<String>,
    effects: Vec<Effect>,
    spawn_elapsed: f32,
    waits: WaitQueue<WaitEvent>,
    restart_waits: WaitQueue<RestartTask>,
    progression_fired: bool,
    next_entity_id: u64,
    rng: DeterministicRng,
    android_build: bool,
}

impl Game {
    pub fn new(layout: Layout, high_score: u32, seed: u64) -> Self {
        let mut game = Self {
            layout,
            bird: Bird::new(),
            pipes: Vec::new(),
            score: 0,
            high_score,
            required_score: 0,
            scroll_speed: 0.0,
            seconds_per_obstacle: 0.0,
            layout_name: layout.source_name().to_string(),
            tiled_background_x: 0.0,
            tiled_background2_x: 0.0,
            pipe_skin: PipeSkin::Default,
            retry_visible: false,
            retry_enabled: false,
            high_score_visible: false,
            high_score_text: "Highscore: 0".to_string(),
            score_text_on_top: true,
            music_requested: false,
            migration_warnings: Vec::new(),
            effects: Vec::new(),
            spawn_elapsed: 0.0,
            waits: WaitQueue::default(),
            restart_waits: WaitQueue::default(),
            progression_fired: false,
            next_entity_id: 100,
            rng: DeterministicRng::seeded(seed),
            android_build: cfg!(target_os = "android"),
        };

        validate_source_program(crate::source::SOURCE_EVENTS)
            .expect("generated Flappy source-event bindings must be valid");
        assert_eq!(
            crate::source::SOURCE_EVENT_COUNT,
            crate::source::SOURCE_EVENTS.len(),
            "generated Flappy source-event count must match its binding table"
        );

        match layout {
            Layout::Start => {
                if game.has_source_handler(SourceEventHandler::StopAllAudioOnStart) {
                    game.effects.push(Effect::StopAllAudio);
                }
            }
            Layout::Continuous | Layout::Chaves => game.enter_layout(layout),
        }

        game
    }

    fn has_source_handler(&self, handler: SourceEventHandler) -> bool {
        crate::source::SOURCE_EVENTS.iter().any(|event| event.handler == handler)
    }

    pub fn drain_effects(&mut self) -> Vec<Effect> {
        std::mem::take(&mut self.effects)
    }

    /// A platform adapter may call this after a Google Play sign-in callback.
    pub fn on_google_play_signed_in(&mut self) {
        if self.layout == Layout::Start
            && self.has_source_handler(SourceEventHandler::GooglePlaySignedIn)
        {
            self.enter_layout(Layout::Continuous);
        }
    }

    /// Explicit offline fallback when Google Play is not available for a target.
    pub fn on_google_play_unavailable(&mut self) {
        if self.layout == Layout::Start
            && self.has_source_handler(SourceEventHandler::GooglePlaySignInRequest)
        {
            self.migration_warnings.push(
                "Google Play sign-in is not configured for this target; continuing offline."
                    .to_string(),
            );
            self.enter_layout(Layout::Continuous);
        }
    }

    fn enter_layout(&mut self, layout: Layout) {
        self.layout = layout;
        self.layout_name = layout.source_name().to_string();

        if layout == Layout::Start {
            if self.has_source_handler(SourceEventHandler::StopAllAudioOnStart) {
                self.effects.push(Effect::StopAllAudio);
            }
            return;
        }

        // Chaves.xml sets Required_Score=10 and applies the Chaves
        // animation to the editor-time TopPipe/BottomPipe instances.
        // Common in-game is included before this event and queues those
        // editor-time instances for destruction. the source editor applies Destroy
        // after event processing, so the animation action is accounted for,
        // but the later timer-created instances start with Default animation.
        if layout == Layout::Chaves
            && self.has_source_handler(SourceEventHandler::ChavesLayoutStart)
        {
            self.required_score = 10;
        } else {
            self.required_score = 0;
        }
        self.pipe_skin = PipeSkin::Default;

        if self.has_source_handler(SourceEventHandler::CommonLayoutStart) {
            self.common_game_layout_start();
        }
    }

    /// Direct translation of source event SID 2246972820014324:
    /// Common in-game -> On start of layout.
    fn common_game_layout_start(&mut self) {
        self.bird = Bird::new();
        self.score = 0;
        self.layout_name = self.layout.source_name().to_string();
        self.scroll_speed = 300.0;
        self.seconds_per_obstacle = 1.0;
        self.tiled_background_x = 0.0;
        self.tiled_background2_x = 0.0;
        self.spawn_elapsed = 0.0;
        // The source layouts contain editor-time pipe instances at x=447/450,
        // but Common in-game destroys both at layout start. The first visible
        // pair is created by the one-second obstacle timer below.
        self.pipes.clear();

        self.retry_visible = false;
        self.retry_enabled = false;
        self.high_score_visible = false;
        self.high_score_text = format!("Highscore: {}", self.high_score);
        self.score_text_on_top = true;
        self.music_requested = true;
        self.waits.clear();
        self.restart_waits.clear();
        self.progression_fired = false;

        // Source action order sets the initial jump before movement begins.
        self.bird.velocity_y = -BIRD_JUMP_STRENGTH;
        self.bird.angle_degrees = 320.0;

        // Nested Trigger once while true Music event follows layout start.
        if self.has_source_handler(SourceEventHandler::StartMusicOnce) {
            self.effects.push(Effect::PlayMusic);
        }
    }

    pub fn update(&mut self, input: InputFrame, source_dt: f32) {
        let frame_delta = SourceFrameClock::default().sample(source_dt);
        let elapsed_dt = frame_delta.elapsed_seconds;
        let simulation_dt = frame_delta.simulation_seconds;

        if self.layout == Layout::Start {
            self.update_start(input);
            return;
        }

        // Existing Wait continuations advance before new ones are scheduled.
        // A Wait created by this frame's input starts counting next frame.
        self.update_wait_continuations(elapsed_dt);

        // The compiled source-event table defines which event groups exist and
        // their execution order. Each group delegates to its typed Rust handler.
        for group in crate::source::SOURCE_UPDATE_ORDER.iter().copied() {
            if !self.has_source_group(group) {
                continue;
            }
            match group {
                SourceGroup::Start | SourceGroup::CommonInLevels => {}
                SourceGroup::Movement => {
                    self.update_movement(input, simulation_dt, elapsed_dt);
                }
                SourceGroup::Collisions => self.check_collisions(),
                SourceGroup::Scoring => self.score_pipes(),
                SourceGroup::Background => self.update_background_and_pipes(simulation_dt),
                SourceGroup::Obstacle => self.update_obstacle_timer(elapsed_dt),
                SourceGroup::Restart => self.update_restart(input, elapsed_dt),
            }
        }

        // Common-in-levels is a shared include used only by the Chaves layout.
        if self.layout == Layout::Chaves
            && crate::source::SOURCE_CHAVES_ORDER.contains(&SourceGroup::CommonInLevels)
            && self.has_source_group(SourceGroup::CommonInLevels)
        {
            self.update_level_progression();
        }
    }

    fn has_source_group(&self, group: SourceGroup) -> bool {
        crate::source::SOURCE_EVENTS
            .iter()
            .any(|event| event.group == Some(group))
    }

    fn update_movement(
        &mut self,
        input: InputFrame,
        simulation_dt: f32,
        elapsed_dt: f32,
    ) {
        // Touch-start OR Space, then NOT Madruga.Queda.
        if input.flap_pressed
            && !self.bird.queda
            && self.has_source_handler(SourceEventHandler::FlapInputOr)
            && self.has_source_handler(SourceEventHandler::FlapWhenAlive)
        {
            self.bird.velocity_y = -BIRD_JUMP_STRENGTH;
            self.bird.angle_degrees = 320.0;
            self.bird.animation = BirdAnimation::Flying;
            self.waits
                .schedule(0.5, WaitEvent::BirdAnimationDefault)
                .expect("the source Wait duration is valid");
        }

        // Every tick AND NOT Madruga.Queda.
        if !self.bird.queda && self.has_source_handler(SourceEventHandler::RotateBird) {
            self.bird.angle_degrees =
                (self.bird.angle_degrees + 60.0 * simulation_dt) % 360.0;
        }

        // Platform behavior: gravity=1500, max-fall-speed=1000.
        self.update_platform_behavior(simulation_dt);
        self.update_pipe_animations(elapsed_dt);
    }

    fn update_start(&mut self, input: InputFrame) {
        if !(input.start_button_pressed || input.return_pressed)
            || !self.has_source_handler(SourceEventHandler::StartButtonOrReturn)
        {
            return;
        }

        // Start events.xml: Android requests Google Play sign-in and waits for
        // On signed in. Other targets follow the source Else child to Continuous.
        if self.android_build {
            if self.has_source_handler(SourceEventHandler::GooglePlaySignInRequest) {
                self.effects.push(Effect::RequestGooglePlaySignIn);
            }
        } else if self.has_source_handler(SourceEventHandler::StartNonAndroidElse) {
            self.enter_layout(Layout::Continuous);
        }
    }

    fn update_wait_continuations(&mut self, elapsed_dt: f32) {
        // The scheduler advances only waits that existed before this dispatch.
        // Multiple waits remain independent and complete in their original order.
        for continuation in self.waits.advance(elapsed_dt) {
            match continuation {
                WaitEvent::BirdAnimationDefault => {
                    self.bird.animation = BirdAnimation::Default;
                }
                WaitEvent::TopPipeGameOver => {
                    self.effects.push(Effect::PlayQueda);
                    self.finish_game_over(CollisionKind::TopPipe);
                }
                WaitEvent::RetryVisible => {
                    self.retry_visible = true;
                    self.retry_enabled = true;
                }
            }
        }
    }

    fn update_platform_behavior(&mut self, dt: f32) {
        if dt <= 0.0 {
            return;
        }

        self.bird.velocity_y =
            (self.bird.velocity_y + PLATFORM_GRAVITY * dt).min(PLATFORM_MAX_FALL_SPEED);
        self.bird.position[1] += self.bird.velocity_y * dt;

        // Solid behavior resolution for TiledBackground2. The source event
        // sheet receives the collision after the Platform behavior meets it.
        let bird_polygon = self.bird.collision_polygon();
        let ground = rectangle_polygon(
            GROUND_COLLISION.0,
            GROUND_COLLISION.1,
            GROUND_COLLISION.2,
            GROUND_COLLISION.3,
        );

        if polygons_intersect(&bird_polygon, &ground) && self.bird.velocity_y >= 0.0 {
            let bottom = bird_polygon
                .iter()
                .map(|point| point[1])
                .fold(f32::NEG_INFINITY, f32::max);

            self.bird.position[1] -= (bottom - GROUND_COLLISION.1).max(0.0);
            self.bird.velocity_y = 0.0;
        }
    }

    fn update_pipe_animations(&mut self, dt: f32) {
        if self.pipe_skin != PipeSkin::Chaves || dt <= 0.0 {
            return;
        }

        // Chaves pipe animations have four frames at speed=4.
        for pair in &mut self.pipes {
            for (alive, pipe) in [
                (pair.top_alive, &mut pair.top),
                (pair.bottom_alive, &mut pair.bottom),
            ] {
                if !alive {
                    continue;
                }
                pipe.animation_clock += dt;
                while pipe.animation_clock >= 0.25 {
                    pipe.animation_clock -= 0.25;
                    pipe.animation_frame = (pipe.animation_frame + 1) % 4;
                }
            }
        }
    }

    fn check_collisions(&mut self) {
        if !self.has_source_handler(SourceEventHandler::CollisionGuard) {
            return;
        }
        let bird_polygon = self.bird.collision_polygon();
        let ground = rectangle_polygon(
            GROUND_COLLISION.0,
            GROUND_COLLISION.1,
            GROUND_COLLISION.2,
            GROUND_COLLISION.3,
        );

        // Collision child order in the original event sheet:
        // TiledBackground2, TopPipe, BottomPipe.
        if self.has_source_handler(SourceEventHandler::GroundCollision)
            && polygons_intersect(&bird_polygon, &ground)
        {
            self.handle_collision(CollisionKind::Ground);
            return;
        }

        if self.has_source_handler(SourceEventHandler::TopPipeCollision)
            && self.pipes.iter().any(|pair| {
            pair.top_alive
                && polygons_intersect(
                    &bird_polygon,
                    &pair.top.collision_polygon(self.pipe_skin, true),
                )
        }) {
            self.handle_collision(CollisionKind::TopPipe);
            return;
        }

        if self.has_source_handler(SourceEventHandler::BottomPipeCollision)
            && self.pipes.iter().any(|pair| {
            pair.bottom_alive
                && polygons_intersect(
                    &bird_polygon,
                    &pair.bottom.collision_polygon(self.pipe_skin, false),
                )
        }) {
            self.handle_collision(CollisionKind::BottomPipe);
        }

        // Source event SID 9569398275688901 ("Is outside layout") has no
        // actions, so leaving the layout intentionally has no extra effect.
    }

    fn handle_collision(&mut self, kind: CollisionKind) {
        // Parent event SID 7365620846625415 runs only while Queda is false.
        if self.bird.queda || !self.has_source_handler(SourceEventHandler::CollisionGuard) {
            return;
        }

        let collision_handler = match kind {
            CollisionKind::Ground => SourceEventHandler::GroundCollision,
            CollisionKind::TopPipe => SourceEventHandler::TopPipeCollision,
            CollisionKind::BottomPipe => SourceEventHandler::BottomPipeCollision,
        };
        if !self.has_source_handler(collision_handler) {
            return;
        }

        self.bird.queda = true;
        self.scroll_speed = 0.0;
        self.seconds_per_obstacle = 0.0;

        // Common actions shared by all three collision children.
        self.effects.push(Effect::PlayBeat);
        self.effects.push(Effect::StopMusic);
        self.music_requested = false;

        match kind {
            CollisionKind::TopPipe => {
                // TopPipe collision waits 0.5s before Queda audio and retry UI.
                self.waits
                    .schedule(0.5, WaitEvent::TopPipeGameOver)
                    .expect("the source Wait duration is valid");
                self.waits
                    .schedule(0.5, WaitEvent::RetryVisible)
                    .expect("the source Wait duration is valid");
            }
            CollisionKind::Ground | CollisionKind::BottomPipe => {
                self.retry_visible = true;
                self.retry_enabled = true;
                self.finish_game_over(kind);
            }
        }
    }

    fn finish_game_over(&mut self, kind: CollisionKind) {
        // Nested collision subevents update high score only on Continuous.
        if self.layout_name == "Continuous" {
            let save_handler = match kind {
                CollisionKind::Ground => SourceEventHandler::SaveHighScoreAfterGround,
                CollisionKind::TopPipe => SourceEventHandler::SaveHighScoreAfterTopPipe,
                CollisionKind::BottomPipe => SourceEventHandler::SaveHighScoreAfterBottomPipe,
            };
            let display_handler = match kind {
                CollisionKind::Ground => SourceEventHandler::ShowHighScoreAfterGround,
                CollisionKind::TopPipe => SourceEventHandler::ShowHighScoreAfterTopPipe,
                CollisionKind::BottomPipe => SourceEventHandler::ShowHighScoreAfterBottomPipe,
            };

            if self.has_source_handler(save_handler) && self.score > self.high_score {
                self.high_score = self.score;
                self.effects.push(Effect::SaveHighScore(self.high_score));
            }

            if self.has_source_handler(display_handler) {
                self.high_score_text = format!("Highscore: {}", self.high_score);
                self.high_score_visible = true;
            }
        }
    }

    fn score_pipes(&mut self) {
        if !self.has_source_handler(SourceEventHandler::ScorePipeOnce) {
            return;
        }
        for pair in &mut self.pipes {
            if pair.bottom_alive
                && pair.bottom.x <= self.bird.position[0]
                && !pair.scored
            {
                self.score += 1;
                pair.scored = true;
            }
        }
    }

    fn update_background_and_pipes(&mut self, dt: f32) {
        // Background wrap checks precede the Every tick movement event.
        if self.has_source_handler(SourceEventHandler::WrapBackground)
            && self.tiled_background_x <= BACKGROUND_WRAP_X
        {
            self.tiled_background_x = 0.0;
        }

        if self.has_source_handler(SourceEventHandler::WrapGround)
            && self.tiled_background2_x <= GROUND_WRAP_X
        {
            self.tiled_background2_x = 0.0;
        }

        if dt > 0.0 && self.has_source_handler(SourceEventHandler::MoveBackgroundAndPipes) {
            let movement = self.scroll_speed * dt;
            for pair in &mut self.pipes {
                if pair.bottom_alive {
                    pair.bottom.x -= movement;
                }
                if pair.top_alive {
                    pair.top.x -= movement;
                }
            }

            self.tiled_background2_x -= movement;
            self.tiled_background_x -= movement;
        }

        // the source editor destroys TopPipe and BottomPipe independently.
        for pair in &mut self.pipes {
            if self.has_source_handler(SourceEventHandler::DestroyTopPipe)
                && pair.top_alive && pair.top.x < PIPE_DESTROY_X
            {
                pair.top_alive = false;
            }
            if self.has_source_handler(SourceEventHandler::DestroyBottomPipe)
                && pair.bottom_alive && pair.bottom.x < PIPE_DESTROY_X
            {
                pair.bottom_alive = false;
            }
        }
        self.pipes.retain(|pair| pair.top_alive || pair.bottom_alive);
    }

    fn update_obstacle_timer(&mut self, dt: f32) {
        if !self.has_source_handler(SourceEventHandler::SpawnObstacleTimer)
            || self.seconds_per_obstacle <= 0.0 || dt <= 0.0 {
            return;
        }

        self.spawn_elapsed += dt;

        while self.spawn_elapsed >= self.seconds_per_obstacle {
            self.spawn_elapsed -= self.seconds_per_obstacle;

            // the source editor expression random(-70, -250), represented as a
            // uniformly sampled Y in [-250, -70]. BottomPipe.Y = TopPipe.Y+750.
            let top_y = self.random_range(-250.0, -70.0);
            let pair = PipePair::spawned(self.next_entity_id, top_y);
            self.next_entity_id += 2;
            self.pipes.push(pair);

            // Source actions also move ScoreText to the top and clear Scored.
            self.score_text_on_top = true;
        }
    }

    fn update_restart(&mut self, input: InputFrame, dt: f32) {
        // Source event SID 9708342499359544: button click OR Return.
        // Child SID 3112928811038152 schedules a 0.1-second Wait at the end
        // of this event group, so its clock advances at the same phase.
        for task in self.restart_waits.advance(dt) {
            match task {
                RestartTask::RestartCurrentLayout => {
                    let layout = self.layout;
                    self.enter_layout(layout);
                    return;
                }
            }
        }

        if input.restart_pressed
            && self.bird.queda
            && self.restart_waits.is_empty()
            && self.has_source_handler(SourceEventHandler::RetryButtonOrReturn)
            && self.has_source_handler(SourceEventHandler::RestartAfterWait)
        {
            self.restart_waits
                .schedule(0.1, RestartTask::RestartCurrentLayout)
                .expect("the source restart Wait duration is valid");
        }
    }

    fn update_level_progression(&mut self) {
        // Common in-levels is included only by Chaves.xml. Its comparison is
        // Score == Required_Score, and the action requests the next layout.
        if !self.has_source_handler(SourceEventHandler::ChavesLevelProgression)
            || self.layout != Layout::Chaves
            || self.progression_fired
            || self.score != self.required_score
        {
            return;
        }

        self.progression_fired = true;

        if let Some(next) = self.layout.next_in_source_order() {
            self.enter_layout(next);
        } else {
            // The checked-in project contains only Start, Continuous and
            // Chaves. There is no fourth layout to receive this source action.
            self.effects.push(Effect::NextLayoutUnavailable);
        }
    }

    fn random_range(&mut self, min: f32, max: f32) -> f32 {
        self.rng.range_f32(min, max)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn playing_game() -> Game {
        Game::new(Layout::Continuous, 0, 0x1234_5678)
    }

    #[test]
    fn continuous_layout_initializes_source_variables_and_objects() {
        let game = playing_game();

        assert_eq!(game.layout_name, "Continuous");
        assert_eq!(game.score, 0);
        assert_eq!(game.scroll_speed, 300.0);
        assert_eq!(game.seconds_per_obstacle, 1.0);
        assert_eq!(game.bird.velocity_y, -500.0);
        assert_eq!(game.bird.angle_degrees, 320.0);
        assert!(game.pipes.is_empty());
        assert!(!game.retry_visible);
    }

    #[test]
    fn chaves_layout_applies_required_score_and_pipe_skin() {
        let game = Game::new(Layout::Chaves, 0, 7);

        assert_eq!(game.required_score, 10);
        assert_eq!(game.pipe_skin, PipeSkin::Default);
        assert_eq!(game.layout_name, "Chaves");
    }

    #[test]
    fn start_layout_routes_to_continuous_on_return() {
        let mut game = Game::new(Layout::Start, 0, 7);
        game.update(
            InputFrame {
                return_pressed: true,
                ..InputFrame::default()
            },
            1.0 / 60.0,
        );

        assert_eq!(game.layout, Layout::Continuous);
        assert_eq!(game.scroll_speed, 300.0);
    }

    #[test]
    fn flap_is_ignored_after_queda() {
        let mut game = playing_game();
        game.bird.queda = true;
        game.bird.velocity_y = 123.0;

        game.update(
            InputFrame {
                flap_pressed: true,
                ..InputFrame::default()
            },
            1.0 / 60.0,
        );

        assert_eq!(game.bird.velocity_y, 123.0 + PLATFORM_GRAVITY / 60.0);
        assert_ne!(game.bird.animation, BirdAnimation::Flying);
    }

    #[test]
    fn flap_sets_platform_vertical_velocity_and_waits_for_default_animation() {
        let mut game = playing_game();

        game.update(
            InputFrame {
                flap_pressed: true,
                ..InputFrame::default()
            },
            0.0,
        );

        assert_eq!(game.bird.velocity_y, -500.0);
        assert_eq!(game.bird.angle_degrees, 320.0);
        assert_eq!(game.bird.animation, BirdAnimation::Flying);

        game.update(InputFrame::default(), 0.51);

        assert_eq!(game.bird.animation, BirdAnimation::Default);
    }

    #[test]
    fn source_dt_moves_pipes_and_backgrounds() {
        let mut game = playing_game();
        game.pipes.push(PipePair::spawned(1, -150.0));
        let initial_x = game.pipes[0].top.x;

        game.update(InputFrame::default(), 1.0 / 60.0);

        assert!((game.pipes[0].top.x - (initial_x - 5.0)).abs() < 0.001);
        assert!((game.tiled_background_x - (-5.0)).abs() < 0.001);
        assert!((game.tiled_background2_x - (-5.0)).abs() < 0.001);
    }

    #[test]
    fn pipe_instances_are_destroyed_independently_at_the_source_threshold() {
        let mut game = playing_game();
        let mut pair = PipePair::spawned(1, -150.0);
        pair.top.x = PIPE_DESTROY_X - 0.01;
        pair.bottom.x = PIPE_DESTROY_X + 2.0;
        game.pipes.push(pair);

        game.update_background_and_pipes(0.0);

        assert_eq!(game.pipes.len(), 1);
        assert!(!game.pipes[0].top_alive);
        assert!(game.pipes[0].bottom_alive);

        game.pipes[0].bottom.x = PIPE_DESTROY_X - 0.01;
        game.update_background_and_pipes(0.0);

        assert!(game.pipes.is_empty());
    }

    #[test]
    fn simulation_dt_is_capped_at_construct_default_maximum() {
        let mut game = playing_game();
        game.pipes.push(PipePair::spawned(1, -150.0));
        let initial_x = game.pipes[0].top.x;

        game.update(InputFrame::default(), 0.5);

        // the source editor's default maximum delta is 1/30 second: 300 px/s * 1/30.
        assert!((game.pipes[0].top.x - (initial_x - 10.0)).abs() < 0.001);
    }

    #[test]
    fn obstacle_timer_spawns_a_pair_after_one_second() {
        let mut game = playing_game();

        // Isolate the Every-X-seconds event from gravity/collision updates.
        game.update_obstacle_timer(0.99);
        assert!(game.pipes.is_empty());

        game.update_obstacle_timer(0.02);
        assert_eq!(game.pipes.len(), 1);

        let spawned = &game.pipes[0];
        assert_eq!(spawned.top.x, 440.0);
        assert_eq!(spawned.bottom.x, 440.0);
        assert!((spawned.bottom.y - spawned.top.y - 750.0).abs() < 0.001);
        assert!(spawned.top_alive);
        assert!(spawned.bottom_alive);
        assert!(!spawned.scored);
    }

    #[test]
    fn a_bottom_pipe_scores_only_once() {
        let mut game = playing_game();
        game.pipes.push(PipePair::spawned(1, -150.0));
        game.pipes[0].bottom.x = game.bird.position[0] - 1.0;

        game.score_pipes();
        game.score_pipes();

        assert_eq!(game.score, 1);
        assert!(game.pipes[0].scored);
    }

    #[test]
    fn ground_collision_stops_scrolling_and_enables_retry() {
        let mut game = playing_game();
        game.handle_collision(CollisionKind::Ground);

        assert!(game.bird.queda);
        assert_eq!(game.scroll_speed, 0.0);
        assert_eq!(game.seconds_per_obstacle, 0.0);
        assert!(game.retry_visible);
        assert!(game.retry_enabled);

        let effects = game.drain_effects();
        assert!(effects.contains(&Effect::PlayBeat));
        assert!(effects.contains(&Effect::StopMusic));
    }

    #[test]
    fn top_pipe_collision_waits_before_queda_audio_and_retry_ui() {
        let mut game = playing_game();
        game.handle_collision(CollisionKind::TopPipe);

        assert!(!game.retry_visible);
        assert!(!game.retry_enabled);
        assert!(game.waits.contains(&WaitEvent::TopPipeGameOver));
        assert!(game.waits.contains(&WaitEvent::RetryVisible));

        game.update_wait_continuations(0.51);

        assert!(game.retry_visible);
        assert!(game.retry_enabled);
        assert!(game.drain_effects().contains(&Effect::PlayQueda));
    }

    #[test]
    fn continuous_game_over_updates_high_score() {
        let mut game = playing_game();
        game.score = 4;
        game.handle_collision(CollisionKind::BottomPipe);

        assert_eq!(game.high_score, 4);
        assert!(game.high_score_visible);
        assert_eq!(game.high_score_text, "Highscore: 4");
        assert!(game.drain_effects().contains(&Effect::SaveHighScore(4)));
    }

    #[test]
    fn chaves_score_threshold_has_no_unlisted_successor() {
        let mut game = Game::new(Layout::Chaves, 0, 7);
        game.score = 10;
        game.update_level_progression();

        assert_eq!(game.layout, Layout::Chaves);
        assert!(game.progression_fired);
        assert!(game.drain_effects().contains(&Effect::NextLayoutUnavailable));
    }

    #[test]
    fn restart_wait_reinitializes_current_layout() {
        let mut game = playing_game();
        game.bird.queda = true;
        game.score = 7;
        game.retry_visible = true;

        game.update(
            InputFrame {
                restart_pressed: true,
                ..InputFrame::default()
            },
            0.05,
        );
        assert_eq!(game.score, 7);

        game.update(InputFrame::default(), 0.11);

        assert_eq!(game.score, 0);
        assert!(!game.bird.queda);
        assert!(!game.retry_visible);
        assert_eq!(game.layout, Layout::Continuous);
    }
}

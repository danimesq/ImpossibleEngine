//! Illustrative typed Rust output for the source-derived Flappy Madruga slice.
//! Source: danimesq/Flappy-Ramon, legacy visual-editor event sheets.
//! This is a reference output, not output from an implemented IGC compiler.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PipeAnimation {
    Default,
    Chaves,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct AnimationSelection {
    pub animation: PipeAnimation,
    pub from_frame: u32,
}

#[derive(Clone, Debug)]
pub struct FlappyMadrugaState {
    pub required_score: i32,
    pub score: i32,
    pub scroll_speed: f32,
    pub seconds_per_obstacle: f32,
    pub madruga_queda: bool,
    pub top_pipe_x: f32,
    pub bottom_pipe_x: f32,
    pub tiled_background_x: f32,
    pub tiled_background2_x: f32,
    pub top_pipe_animation: AnimationSelection,
    pub bottom_pipe_animation: AnimationSelection,
}

impl Default for FlappyMadrugaState {
    fn default() -> Self {
        let default_animation = AnimationSelection {
            animation: PipeAnimation::Default,
            from_frame: 0,
        };

        Self {
            required_score: 0,
            score: 0,
            scroll_speed: 150.0,
            seconds_per_obstacle: 1.0,
            madruga_queda: false,
            top_pipe_x: 0.0,
            bottom_pipe_x: 0.0,
            tiled_background_x: 0.0,
            tiled_background2_x: 0.0,
            top_pipe_animation: default_animation,
            bottom_pipe_animation: default_animation,
        }
    }
}

/// Source event SID 9305905589121505 in Event sheets/Chaves.xml.
pub fn on_chaves_layout_start(state: &mut FlappyMadrugaState) {
    state.required_score = 10;
    state.top_pipe_animation = AnimationSelection {
        animation: PipeAnimation::Chaves,
        from_frame: 1,
    };
    state.bottom_pipe_animation = AnimationSelection {
        animation: PipeAnimation::Chaves,
        from_frame: 1,
    };
}

/// Source event SID 2246972820014324 in Event sheets/Common in-game.xml.
pub fn on_common_game_layout_start(state: &mut FlappyMadrugaState) {
    state.madruga_queda = false;
    state.score = 0;
    state.scroll_speed = 300.0;
    state.seconds_per_obstacle = 1.0;
    state.tiled_background2_x = 0.0;
    state.tiled_background_x = 0.0;
}

/// Source event SID 1385689931601852 in Event sheets/Common in-game.xml.
///
/// the source editor's dt is kept explicit. The importer must verify the source
/// scheduler and delta semantics before claiming runtime equivalence.
pub fn every_source_tick(state: &mut FlappyMadrugaState, source_dt_seconds: f32) {
    if !source_dt_seconds.is_finite() || source_dt_seconds < 0.0 {
        return;
    }

    // Preserve the source action order and the exact X - speed * dt formula.
    state.bottom_pipe_x -= state.scroll_speed * source_dt_seconds;
    state.top_pipe_x -= state.scroll_speed * source_dt_seconds;
    state.tiled_background2_x -= state.scroll_speed * source_dt_seconds;
    state.tiled_background_x -= state.scroll_speed * source_dt_seconds;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn chaves_layout_start_selects_the_chaves_pipe_animations() {
        let mut state = FlappyMadrugaState::default();

        on_chaves_layout_start(&mut state);

        assert_eq!(state.required_score, 10);
        assert_eq!(state.top_pipe_animation.animation, PipeAnimation::Chaves);
        assert_eq!(state.top_pipe_animation.from_frame, 1);
        assert_eq!(state.bottom_pipe_animation.animation, PipeAnimation::Chaves);
        assert_eq!(state.bottom_pipe_animation.from_frame, 1);
    }

    #[test]
    fn common_layout_start_resets_the_source_variables() {
        let mut state = FlappyMadrugaState {
            score: 42,
            scroll_speed: 12.0,
            madruga_queda: true,
            ..FlappyMadrugaState::default()
        };

        on_common_game_layout_start(&mut state);

        assert_eq!(state.score, 0);
        assert_eq!(state.scroll_speed, 300.0);
        assert_eq!(state.seconds_per_obstacle, 1.0);
        assert!(!state.madruga_queda);
        assert_eq!(state.tiled_background2_x, 0.0);
        assert_eq!(state.tiled_background_x, 0.0);
    }

    #[test]
    fn source_tick_scrolls_every_source_object_using_dt() {
        let mut state = FlappyMadrugaState {
            scroll_speed: 300.0,
            top_pipe_x: 440.0,
            bottom_pipe_x: 440.0,
            tiled_background_x: 0.0,
            tiled_background2_x: 10.0,
            ..FlappyMadrugaState::default()
        };

        every_source_tick(&mut state, 0.5);

        assert_eq!(state.top_pipe_x, 290.0);
        assert_eq!(state.bottom_pipe_x, 290.0);
        assert_eq!(state.tiled_background_x, -150.0);
        assert_eq!(state.tiled_background2_x, -140.0);
    }

    #[test]
    fn invalid_delta_is_ignored() {
        let mut state = FlappyMadrugaState {
            top_pipe_x: 10.0,
            ..FlappyMadrugaState::default()
        };

        every_source_tick(&mut state, f32::NAN);

        assert_eq!(state.top_pipe_x, 10.0);
    }
}

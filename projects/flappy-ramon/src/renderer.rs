//! Temporary vector renderer used while the original media assets are pending.
//! All positions are rendered in the original 400x500 Construct layout space.

use flappy_madruga::game::{BirdAnimation, Game, Layout, PipeSkin, VIEW_HEIGHT, VIEW_WIDTH};
use macroquad::prelude::*;

struct Viewport {
    scale: f32,
    offset_x: f32,
    offset_y: f32,
}

impl Viewport {
    fn new() -> Self {
        let scale = (screen_width() / VIEW_WIDTH).min(screen_height() / VIEW_HEIGHT);
        Self {
            scale,
            offset_x: (screen_width() - VIEW_WIDTH * scale) * 0.5,
            offset_y: (screen_height() - VIEW_HEIGHT * scale) * 0.5,
        }
    }

    fn point(&self, x: f32, y: f32) -> (f32, f32) {
        (
            self.offset_x + x * self.scale,
            self.offset_y + y * self.scale,
        )
    }

    fn rect(&self, x: f32, y: f32, width: f32, height: f32, color: Color) {
        let (sx, sy) = self.point(x, y);
        draw_rectangle(sx, sy, width * self.scale, height * self.scale, color);
    }

    fn circle(&self, x: f32, y: f32, radius: f32, color: Color) {
        let (sx, sy) = self.point(x, y);
        draw_circle(sx, sy, radius * self.scale, color);
    }

    fn text(&self, text: &str, x: f32, y: f32, size: f32, color: Color, font: Option<&Font>) {
        let (sx, sy) = self.point(x, y);
        draw_text_ex(
            text,
            sx,
            sy,
            TextParams {
                font,
                font_size: size.max(1.0) as u16,
                font_scale: self.scale,
                color,
                ..Default::default()
            },
        );
    }

    fn centered_text(
        &self,
        text: &str,
        center_x: f32,
        y: f32,
        size: f32,
        color: Color,
        font: Option<&Font>,
    ) {
        // PressStart2P is a monospaced bitmap-like font. This estimate keeps
        // labels centered while the original font file is still pending.
        let estimated_width = text.chars().count() as f32 * size * 0.61;
        self.text(text, center_x - estimated_width * 0.5, y, size, color, font);
    }
}

pub fn draw(game: &Game, font: Option<&Font>) {
    clear_background(Color::from_rgba(18, 27, 43, 255));
    let view = Viewport::new();

    // The original Construct project uses letterbox scaling at 400x500.
    view.rect(0.0, 0.0, VIEW_WIDTH, VIEW_HEIGHT, Color::from_rgba(126, 197, 224, 255));

    if game.layout == Layout::Start {
        draw_start_screen(&view, font);
        return;
    }

    draw_sky_and_background(&view, game);
    draw_pipes(&view, game);
    draw_ground(&view, game);
    draw_bird(&view, game);

    // ScoreText occupies the upper 398x70 region in the original layouts.
    view.centered_text(
        &game.score.to_string(),
        200.0,
        52.0,
        34.0,
        WHITE,
        font,
    );

    if game.high_score_visible && game.layout_name == "Continuous" {
        view.text(&game.high_score_text, 156.0, 197.0, 12.0, WHITE, font);
    }

    if game.retry_visible && game.retry_enabled {
        draw_retry_button(&view, font);
    }

    view.text(
        if game.layout == Layout::Chaves { "CHAVES" } else { "CONTINUOUS" },
        12.0,
        490.0,
        8.0,
        Color::from_rgba(255, 255, 255, 160),
        font,
    );

    view.centered_text(
        "ORIGINAL MEDIA PENDING",
        200.0,
        480.0,
        7.0,
        Color::from_rgba(255, 255, 255, 150),
        font,
    );
}

fn draw_start_screen(view: &Viewport, font: Option<&Font>) {
    // Source layout has a full-screen Splash sprite. This geometric scene is a
    // temporary renderer fallback, not a replacement for the original artwork.
    view.rect(0.0, 0.0, 400.0, 500.0, Color::from_rgba(101, 177, 207, 255));
    view.circle(330.0, 90.0, 58.0, Color::from_rgba(255, 225, 140, 255));
    view.rect(0.0, 360.0, 400.0, 140.0, Color::from_rgba(78, 142, 89, 255));

    view.centered_text(
        "FLAPPY MADRUGA",
        200.0,
        155.0,
        21.0,
        Color::from_rgba(255, 255, 255, 255),
        font,
    );
    view.centered_text(
        "THE ORIGINAL GAME, NOW NATIVE RUST",
        200.0,
        190.0,
        7.0,
        Color::from_rgba(255, 255, 255, 230),
        font,
    );

    // Original Play_Continuous instance: x=13, y=255, w=162, h=32.
    view.rect(13.0, 255.0, 162.0, 32.0, Color::from_rgba(47, 74, 98, 255));
    view.rect(15.0, 257.0, 158.0, 28.0, Color::from_rgba(251, 210, 91, 255));
    view.text("CONTINUOUS PLAY", 22.0, 278.0, 8.0, Color::from_rgba(45, 51, 62, 255), font);

    view.centered_text(
        "MEDIA PLACEHOLDERS ACTIVE",
        200.0,
        440.0,
        8.0,
        Color::from_rgba(255, 255, 255, 220),
        font,
    );
    view.centered_text(
        "ENTER OR TAP CONTINUOUS PLAY",
        200.0,
        458.0,
        7.0,
        Color::from_rgba(255, 255, 255, 210),
        font,
    );
}

fn draw_sky_and_background(view: &Viewport, game: &Game) {
    view.rect(0.0, 0.0, 400.0, 500.0, Color::from_rgba(126, 197, 224, 255));

    // Low-detail placeholder scenery until the original background images
    // and tiled textures are populated.
    for (x, y, radius) in [
        (65.0, 105.0, 19.0),
        (270.0, 140.0, 25.0),
        (190.0, 70.0, 13.0),
    ] {
        view.circle(x, y, radius, Color::from_rgba(221, 239, 236, 180));
    }

    let bg_x = game.tiled_background_x;
    for offset in [0.0, 560.0, 1120.0] {
        view.rect(
            bg_x + offset,
            472.0,
            560.0,
            28.0,
            Color::from_rgba(71, 133, 75, 255),
        );
    }
}

fn draw_pipes(view: &Viewport, game: &Game) {
    for pair in &game.pipes {
        draw_pipe(view, pair.top.x, pair.top.y, true, game.pipe_skin);
        draw_pipe(view, pair.bottom.x, pair.bottom.y, false, game.pipe_skin);
    }
}

fn draw_pipe(view: &Viewport, x: f32, y: f32, top: bool, skin: PipeSkin) {
    let (body, rim, outline) = match skin {
        PipeSkin::Default => (
            Color::from_rgba(74, 161, 96, 255),
            Color::from_rgba(130, 207, 117, 255),
            Color::from_rgba(35, 97, 65, 255),
        ),
        PipeSkin::Chaves => (
            Color::from_rgba(170, 118, 57, 255),
            Color::from_rgba(218, 174, 93, 255),
            Color::from_rgba(98, 69, 44, 255),
        ),
    };

    // The source object is 70x604 with a centered hotspot. These flat shapes
    // are explicitly temporary; frame art and exact collision shapes remain
    // recorded in the source-derived metadata.
    view.rect(x - 32.0, y - 302.0, 64.0, 604.0, outline);
    view.rect(x - 28.0, y - 299.0, 56.0, 598.0, body);

    let rim_y = if top { y + 270.0 } else { y - 302.0 };
    view.rect(x - 38.0, rim_y, 76.0, 32.0, outline);
    view.rect(x - 35.0, rim_y + 3.0, 70.0, 25.0, rim);
}

fn draw_ground(view: &Viewport, game: &Game) {
    // TiledBackground2 is the collision surface at y=453. TiledBackground is
    // the lower decorative strip at y=472; both move with SCROLLSPEED.
    view.rect(
        game.tiled_background2_x,
        453.0,
        1107.0,
        19.0,
        Color::from_rgba(205, 190, 130, 255),
    );
    view.rect(
        game.tiled_background_x,
        472.0,
        1118.0,
        28.0,
        Color::from_rgba(67, 133, 76, 255),
    );

    for x in (0..12).map(|index| index as f32 * 40.0) {
        view.rect(x, 454.0, 18.0, 3.0, Color::from_rgba(235, 225, 180, 200));
        view.rect(x + 12.0, 480.0, 16.0, 3.0, Color::from_rgba(104, 163, 91, 255));
    }
}

fn draw_bird(view: &Viewport, game: &Game) {
    let center = game.bird.visual_center();
    let (body, beak) = match game.bird.animation {
        BirdAnimation::Default => (
            Color::from_rgba(241, 184, 74, 255),
            Color::from_rgba(220, 110, 62, 255),
        ),
        BirdAnimation::Flying => (
            Color::from_rgba(255, 207, 91, 255),
            Color::from_rgba(224, 117, 56, 255),
        ),
    };

    let (sx, sy) = view.point(center[0], center[1]);
    draw_ellipse(
        sx,
        sy,
        34.0 * view.scale,
        25.0 * view.scale,
        game.bird.angle_degrees,
        body,
    );

    let angle = game.bird.angle_degrees.to_radians();
    let direction = [angle.cos(), angle.sin()];
    let beak_center = [
        center[0] + direction[0] * 28.0,
        center[1] + direction[1] * 28.0,
    ];
    let left = [
        beak_center[0] - direction[1] * 7.0,
        beak_center[1] + direction[0] * 7.0,
    ];
    let right = [
        beak_center[0] + direction[1] * 7.0,
        beak_center[1] - direction[0] * 7.0,
    ];
    let (bx, by) = view.point(beak_center[0], beak_center[1]);
    let (lx, ly) = view.point(left[0], left[1]);
    let (rx, ry) = view.point(right[0], right[1]);
    draw_triangle(vec2(bx, by), vec2(lx, ly), vec2(rx, ry), beak);

    let eye = [center[0] + direction[0] * 7.0, center[1] - direction[1] * 7.0];
    view.circle(eye[0], eye[1], 4.0, WHITE);
    view.circle(eye[0] + 1.0, eye[1], 1.7, BLACK);

    // A tiny hat silhouette acknowledges the source character while keeping
    // the missing source sprite visibly separate from the original artwork.
    view.rect(center[0] - 12.0, center[1] - 25.0, 23.0, 4.0, Color::from_rgba(72, 54, 43, 255));
    view.rect(center[0] - 7.0, center[1] - 34.0, 14.0, 10.0, Color::from_rgba(72, 54, 43, 255));
}

fn draw_retry_button(view: &Viewport, font: Option<&Font>) {
    // Original retry button instance: x=120, y=211, w=181, h=81.
    view.rect(120.0, 211.0, 181.0, 81.0, Color::from_rgba(38, 58, 73, 255));
    view.rect(124.0, 215.0, 173.0, 73.0, Color::from_rgba(248, 211, 100, 255));
    view.centered_text("TRY AGAIN!", 210.5, 260.0, 12.0, Color::from_rgba(43, 49, 57, 255), font);
}

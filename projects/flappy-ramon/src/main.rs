//! Macroquad host for the platform-neutral Flappy Madruga game core.

mod renderer;
mod services;

use flappy_madruga::game::{Game, InputFrame, Layout};
use macroquad::prelude::*;
use services::Services;

#[macroquad::main(window_conf)]
async fn main() {
    let mut services = Services::load().await;
    let high_score = services.load_high_score();
    let initial_layout = initial_layout_from_args();
    // Macroquad's monotonic clock is available in native and browser builds.
    let seed = ((get_time() * 1_000_000.0) as u64)
        .wrapping_add((screen_width() as u64) << 32)
        .max(1);

    let mut game = Game::new(initial_layout, high_score, seed);
    apply_pending_effects(&mut game, &mut services);

    loop {
        let mouse_pressed = is_mouse_button_pressed(MouseButton::Left);
        let enter_pressed = is_key_pressed(KeyCode::Enter);
        let space_pressed = is_key_pressed(KeyCode::Space);
        let touch_started = touches()
            .iter()
            .any(|touch| touch.phase == TouchPhase::Started);

        let logical_pointer = screen_to_game(mouse_position());
        let start_clicked = mouse_pressed
            && logical_pointer
                .map(|point| contains(point, (13.0, 255.0, 162.0, 32.0)))
                .unwrap_or(false);

        let retry_clicked = mouse_pressed
            && game.retry_visible
            && game.retry_enabled
            && logical_pointer
                .map(|point| contains(point, (120.0, 211.0, 181.0, 81.0)))
                .unwrap_or(false);

        let input = InputFrame {
            start_button_pressed: start_clicked,
            flap_pressed: space_pressed || mouse_pressed || touch_started,
            restart_pressed: enter_pressed || retry_clicked,
            return_pressed: enter_pressed,
        };

        // Construct's Every tick uses its source dt value. Do not replace this
        // with the renderer's fixed timestep or silently clamp it.
        let source_dt = get_frame_time();
        game.update(input, source_dt);
        apply_pending_effects(&mut game, &mut services);

        renderer::draw(&game, services.font.as_ref());

        next_frame().await;
    }
}

fn window_conf() -> Conf {
    Conf {
        window_title: "Flappy Madruga | Impossible".to_string(),
        window_width: 800,
        window_height: 1000,
        high_dpi: true,
        window_resizable: true,
        ..Default::default()
    }
}

fn initial_layout_from_args() -> Layout {
    #[cfg(not(target_arch = "wasm32"))]
    {
        if let Some(layout) = std::env::args()
            .skip(1)
            .find_map(|argument| argument.strip_prefix("--layout=").and_then(Layout::from_cli_argument))
        {
            return layout;
        }
    }

    // Browser output starts through the original Start layout.
    Layout::Start
}

fn screen_to_game(position: (f32, f32)) -> Option<[f32; 2]> {
    let scale = (screen_width() / 400.0).min(screen_height() / 500.0);
    if scale <= 0.0 {
        return None;
    }

    let offset_x = (screen_width() - 400.0 * scale) * 0.5;
    let offset_y = (screen_height() - 500.0 * scale) * 0.5;
    let x = (position.0 - offset_x) / scale;
    let y = (position.1 - offset_y) / scale;

    if (0.0..=400.0).contains(&x) && (0.0..=500.0).contains(&y) {
        Some([x, y])
    } else {
        None
    }
}

fn contains(point: [f32; 2], rect: (f32, f32, f32, f32)) -> bool {
    point[0] >= rect.0
        && point[1] >= rect.1
        && point[0] <= rect.0 + rect.2
        && point[1] <= rect.1 + rect.3
}

fn apply_pending_effects(game: &mut Game, services: &mut Services) {
    // Effects may enqueue a follow-up (Google Play fallback); keep processing
    // until the queue is empty so all state transitions remain synchronous.
    loop {
        let effects = game.drain_effects();
        if effects.is_empty() {
            break;
        }

        for effect in effects {
            if !services.apply_effect(effect) {
                game.on_google_play_unavailable();
            }
        }
    }
}

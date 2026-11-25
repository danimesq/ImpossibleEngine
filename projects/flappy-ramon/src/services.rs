//! Host-service adapters for audio, WebStorage and optional platform integrations.
//!
//! Missing media is a warning, not a crash: the project is deliberately
//! scaffolded with empty media folders until verified source assets are added.

use flappy_madruga::game::Effect;
use macroquad::audio::{
    load_sound, play_sound, play_sound_once, set_sound_volume, stop_sound, PlaySoundParams, Sound,
};
use macroquad::file::set_pc_assets_folder;
use macroquad::text::{load_ttf_font, Font};

#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen(
    inline_js = r#"
export function impossibleLoadHighScore() {
    try {
        return window.localStorage.getItem("flappy-madruga.highscore");
    } catch (_) {
        return null;
    }
}
export function impossibleSaveHighScore(value) {
    try {
        window.localStorage.setItem("flappy-madruga.highscore", value);
        return true;
    } catch (_) {
        return false;
    }
}
"#
)]
extern "C" {
    #[wasm_bindgen(js_name = impossibleLoadHighScore)]
    fn impossible_load_high_score() -> Option<String>;

    #[wasm_bindgen(js_name = impossibleSaveHighScore)]
    fn impossible_save_high_score(value: &str) -> bool;
}

#[derive(Default)]
pub struct Services {
    music: Option<Sound>,
    beat: Option<Sound>,
    queda: Option<Sound>,
    pub font: Option<Font>,
    pub warnings: Vec<String>,
    music_playing: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum IntegrationStatus {
    Available,
    NotConfigured,
    NotUsedBySourceEvents,
}

impl Services {
    pub async fn load() -> Self {
        set_pc_assets_folder("assets");

        let mut services = Self::default();

        services.music = load_first_sound(&[
            "audio/music/Music.ogg",
            "audio/music/Music.m4a",
        ])
        .await;

        services.beat = load_first_sound(&[
            "audio/sfx/beat/beat.ogg",
            "audio/sfx/beat/beat.m4a",
        ])
        .await;

        services.queda = load_first_sound(&[
            "audio/sfx/queda/Queda.ogg",
            "audio/sfx/queda/Queda.m4a",
        ])
        .await;

        services.font = match load_ttf_font("fonts/press-start-2p.ttf").await {
            Ok(font) => Some(font),
            Err(error) => {
                services.warnings.push(format!(
                    "PressStart2P.ttf is pending; Macroquad's default font will be used ({error})."
                ));
                None
            }
        };

        for warning in &services.warnings {
            eprintln!("[media] {warning}");
        }

        services
    }

    pub fn load_high_score(&self) -> u32 {
        #[cfg(target_arch = "wasm32")]
        {
            return impossible_load_high_score()
                .and_then(|value| value.parse::<u32>().ok())
                .unwrap_or(0);
        }

        #[cfg(not(target_arch = "wasm32"))]
        {
            std::fs::read_to_string("save/highscore.txt")
                .ok()
                .and_then(|value| value.trim().parse::<u32>().ok())
                .unwrap_or(0)
        }
    }

    pub fn save_high_score(&mut self, value: u32) {
        #[cfg(target_arch = "wasm32")]
        {
            if !impossible_save_high_score(&value.to_string()) {
                self.warnings.push(
                    "Browser localStorage rejected the high-score write.".to_string(),
                );
            }
        }

        #[cfg(not(target_arch = "wasm32"))]
        {
            let result = std::fs::create_dir_all("save")
                .and_then(|_| std::fs::write("save/highscore.txt", value.to_string()));

            if let Err(error) = result {
                self.warnings
                    .push(format!("Could not persist high score: {error}"));
            }
        }
    }

    pub fn apply_effect(&mut self, effect: Effect) -> bool {
        match effect {
            Effect::StopAllAudio => {
                if let Some(sound) = self.music.as_ref() {
                    stop_sound(sound);
                }
                self.music_playing = false;
            }
            Effect::PlayMusic => {
                if let Some(sound) = self.music.as_ref() {
                    play_sound(
                        sound,
                        PlaySoundParams {
                            looped: true,
                            // Construct's source volume is 0 dB, then adds a
                            // +40 dB effect. Macroquad exposes normalized
                            // output volume instead of a tagged gain DSP chain.
                            volume: 1.0,
                        },
                    );
                    set_sound_volume(sound, 1.0);
                    self.music_playing = true;
                }
            }
            Effect::StopMusic => {
                if let Some(sound) = self.music.as_ref() {
                    stop_sound(sound);
                }
                self.music_playing = false;
            }
            Effect::PlayBeat => {
                if let Some(sound) = self.beat.as_ref() {
                    play_sound_once(sound);
                }
            }
            Effect::PlayQueda => {
                if let Some(sound) = self.queda.as_ref() {
                    play_sound_once(sound);
                }
            }
            Effect::SaveHighScore(value) => self.save_high_score(value),
            Effect::RequestGooglePlaySignIn => {
                // No Google Play credentials/SDK adapter is included in this
                // first desktop/web port. The caller performs offline fallback.
                return false;
            }
            Effect::NextLayoutUnavailable => {
                self.warnings.push(
                    "Chaves reached Required_Score, but the source project has no fourth layout."
                        .to_string(),
                );
            }
        }

        true
    }

    /// The Construct project declares Google Play, but its sign-in integration
    /// needs an Android SDK client ID and credentials that are not in source.
    pub fn google_play_status(&self) -> IntegrationStatus {
        IntegrationStatus::NotConfigured
    }

    /// Facebook is declared as a Construct plugin but no Facebook event
    /// condition/action is present in the checked-in Event Sheets.
    pub fn facebook_status(&self) -> IntegrationStatus {
        IntegrationStatus::NotUsedBySourceEvents
    }

    /// Browser is declared by the source project but no Browser plugin
    /// action/condition is used by the inspected Event Sheets.
    pub fn browser_status(&self) -> IntegrationStatus {
        IntegrationStatus::NotUsedBySourceEvents
    }

    pub fn audio_ready(&self) -> bool {
        self.music.is_some() || self.beat.is_some() || self.queda.is_some()
    }

    pub fn music_playing(&self) -> bool {
        self.music_playing
    }
}

async fn load_first_sound(paths: &[&str]) -> Option<Sound> {
    for path in paths {
        if let Ok(sound) = load_sound(path).await {
            return Some(sound);
        }
    }

    eprintln!(
        "[media] Pending audio asset; tried: {}",
        paths.join(", ")
    );
    None
}

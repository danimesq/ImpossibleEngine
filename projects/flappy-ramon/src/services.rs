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

    /// The the source editor project uses WebStorage.localvalue("Highscore").
    /// quad-storage maps that key to Web Storage on WASM and local.data natively.
    pub fn load_high_score(&mut self) -> u32 {
        match quad_storage::STORAGE.lock() {
            Ok(storage) => storage
                .get("Highscore")
                .and_then(|value| value.parse::<u32>().ok())
                .unwrap_or(0),
            Err(error) => {
                self.warnings.push(format!("High-score storage lock failed: {error}"));
                0
            }
        }
    }

    pub fn save_high_score(&mut self, value: u32) {
        match quad_storage::STORAGE.lock() {
            Ok(mut storage) => storage.set("Highscore", &value.to_string()),
            Err(error) => self
                .warnings
                .push(format!("Could not lock high-score storage: {error}")),
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
                            // Source volume is zero dB, followed by a +40 dB
                            // gain effect. Macroquad exposes normalized volume,
                            // so full-scale output is the closest host mapping.
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
                // This build does not include the Android Google Play Games
                // SDK client or credentials. The caller performs offline fallback.
                return false;
            }
            Effect::NextLayoutUnavailable => {
                // the source editor's official behavior is a no-op when there is no
                // next layout. Keep a diagnostic without inventing a new scene.
                self.warnings.push(
                    "The Chaves score threshold was reached; source project has no next layout."
                        .to_string(),
                );
            }
        }

        true
    }

    /// Google Play is declared and used in the Start event sheet on Android,
    /// but the project does not contain client credentials or an SDK adapter.
    pub fn google_play_status(&self) -> IntegrationStatus {
        IntegrationStatus::NotConfigured
    }

    /// Facebook is declared as a the source editor plugin but no event-sheet operation
    /// uses it in this source project.
    pub fn facebook_status(&self) -> IntegrationStatus {
        IntegrationStatus::NotUsedBySourceEvents
    }

    /// Browser is declared as a the source editor plugin but no event-sheet operation
    /// uses it in this source project.
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

    eprintln!("[media] Pending audio asset; tried: {}", paths.join(", "));
    None
}

//! Platform-neutral execution primitives used by compiled Impossible projects.
//!
//! This crate deliberately has no windowing, renderer, audio-device or platform API.
//! It owns deterministic simulation timing, waits, RNG and compiled source bindings.

use std::collections::HashSet;

/// Source-editor event handlers that have concrete Rust-side implementations.
/// The generated Flappy binding table uses these typed identifiers, never source strings.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum SourceEventHandler {
    StopAllAudioOnStart,
    StartButtonOrReturn,
    GooglePlaySignInRequest,
    StartNonAndroidElse,
    GooglePlaySignedIn,
    CommonLayoutStart,
    StartMusicOnce,
    FlapInputOr,
    FlapWhenAlive,
    RotateBird,
    CollisionGuard,
    GroundCollision,
    SaveHighScoreAfterGround,
    ShowHighScoreAfterGround,
    TopPipeCollision,
    SaveHighScoreAfterTopPipe,
    ShowHighScoreAfterTopPipe,
    BottomPipeCollision,
    SaveHighScoreAfterBottomPipe,
    ShowHighScoreAfterBottomPipe,
    OutsideLayoutNoOp,
    ScorePipeOnce,
    WrapBackground,
    WrapGround,
    MoveBackgroundAndPipes,
    DestroyTopPipe,
    DestroyBottomPipe,
    SpawnObstacleTimer,
    RetryButtonOrReturn,
    RestartAfterWait,
    ChavesLevelProgression,
    ChavesLayoutStart,
}

/// Logical update groups retained from the imported source Event Sheets.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum SourceGroup {
    Start,
    Movement,
    Collisions,
    Scoring,
    Background,
    Obstacle,
    Restart,
    CommonInLevels,
}

/// Explicit coverage status. These statuses distinguish supported logic from
/// host work that can be supplied later without changing gameplay semantics.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SourceEventStatus {
    Mapped,
    HostAdapter,
    PolicyFallback,
    MediaPending,
    VectorUi,
    SourceNoOp,
    RngPolicy,
    InstanceLifetime,
    SemanticsPreserved,
}

/// One source event linked to a concrete runtime handler.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SourceEventBinding {
    pub sid: &'static str,
    pub name: &'static str,
    pub group: Option<SourceGroup>,
    pub parent_sid: Option<&'static str>,
    pub handler: SourceEventHandler,
    pub status: SourceEventStatus,
}

/// Validate the generated program before a project instance is created.
pub fn validate_source_program(events: &[SourceEventBinding]) -> Result<(), String> {
    let mut ids = HashSet::with_capacity(events.len());
    for event in events {
        if event.sid.is_empty() || event.name.is_empty() {
            return Err("source event IDs and names must not be empty".into());
        }
        if !ids.insert(event.sid) {
            return Err(format!("duplicate source event SID: {}", event.sid));
        }
    }

    for event in events {
        if let Some(parent) = event.parent_sid {
            if !ids.contains(parent) {
                return Err(format!(
                    "source event {} references missing parent {}",
                    event.sid, parent
                ));
            }
        }
    }
    Ok(())
}

/// Delta values for one host frame.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct FrameDelta {
    /// Uncapped wall-clock time, used by System timers and Wait continuations.
    pub elapsed_seconds: f32,
    /// Capped source simulation delta, used by per-tick movement and behaviors.
    pub simulation_seconds: f32,
}

/// Preserves the legacy editor's separation between elapsed time and capped dt.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct SourceFrameClock {
    max_delta_seconds: f32,
}

impl SourceFrameClock {
    pub const LEGACY_DEFAULT_MAX_DELTA: f32 = 1.0 / 30.0;

    pub fn new(max_delta_seconds: f32) -> Self {
        let maximum = if max_delta_seconds.is_finite() && max_delta_seconds > 0.0 {
            max_delta_seconds
        } else {
            Self::LEGACY_DEFAULT_MAX_DELTA
        };
        Self { max_delta_seconds: maximum }
    }

    pub fn sample(&self, host_delta_seconds: f32) -> FrameDelta {
        let elapsed = if host_delta_seconds.is_finite() && host_delta_seconds > 0.0 {
            host_delta_seconds
        } else {
            0.0
        };
        FrameDelta {
            elapsed_seconds: elapsed,
            simulation_seconds: elapsed.min(self.max_delta_seconds),
        }
    }

    pub fn max_delta_seconds(&self) -> f32 {
        self.max_delta_seconds
    }
}

impl Default for SourceFrameClock {
    fn default() -> Self {
        Self::new(Self::LEGACY_DEFAULT_MAX_DELTA)
    }
}

#[derive(Clone, Debug)]
struct PendingWait<T> {
    remaining_seconds: f32,
    sequence: u64,
    payload: T,
}

/// Ordered, independent Wait continuations.
///
/// Advancing a queue never runs work scheduled by the same event dispatch until
/// the next advance call. This matches the source game's event/action boundary.
#[derive(Clone, Debug)]
pub struct WaitQueue<T> {
    next_sequence: u64,
    pending: Vec<PendingWait<T>>,
}

impl<T> Default for WaitQueue<T> {
    fn default() -> Self {
        Self { next_sequence: 0, pending: Vec::new() }
    }
}

impl<T: PartialEq + Clone> WaitQueue<T> {
    pub fn schedule(&mut self, delay_seconds: f32, payload: T) -> Result<(), &'static str> {
        if !delay_seconds.is_finite() || delay_seconds <= 0.0 {
            return Err("wait duration must be finite and greater than zero");
        }
        let sequence = self.next_sequence;
        self.next_sequence = self.next_sequence.wrapping_add(1);
        self.pending.push(PendingWait { remaining_seconds: delay_seconds, sequence, payload });
        Ok(())
    }

    /// Advance existing waits and return completed payloads in scheduling order.
    pub fn advance(&mut self, elapsed_seconds: f32) -> Vec<T> {
        let elapsed = if elapsed_seconds.is_finite() && elapsed_seconds > 0.0 {
            elapsed_seconds
        } else {
            0.0
        };

        let mut completed = Vec::new();
        for wait in &mut self.pending {
            wait.remaining_seconds -= elapsed;
        }

        self.pending.retain(|wait| {
            if wait.remaining_seconds <= 0.0 {
                completed.push((wait.sequence, wait.payload.clone()));
                false
            } else {
                true
            }
        });
        completed.sort_by_key(|(sequence, _)| *sequence);
        completed.into_iter().map(|(_, payload)| payload).collect()
    }

    pub fn contains(&self, payload: &T) -> bool {
        self.pending.iter().any(|wait| &wait.payload == payload)
    }

    pub fn len(&self) -> usize {
        self.pending.len()
    }

    pub fn is_empty(&self) -> bool {
        self.pending.is_empty()
    }

    pub fn clear(&mut self) {
        self.pending.clear();
    }
}

/// Deterministic xorshift64 RNG used for reproducible source-project tests/builds.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DeterministicRng {
    state: u64,
}

impl DeterministicRng {
    pub const ZERO_SEED: u64 = 0x9e37_79b9_7f4a_7c15;

    pub fn seeded(seed: u64) -> Self {
        Self { state: if seed == 0 { Self::ZERO_SEED } else { seed } }
    }

    pub fn state(&self) -> u64 {
        self.state
    }

    pub fn next_u64(&mut self) -> u64 {
        let mut value = self.state;
        value ^= value << 13;
        value ^= value >> 7;
        value ^= value << 17;
        self.state = value;
        value
    }

    /// Return a [0, 1) value using the top 24 random bits, matching the previous Flappy port.
    pub fn unit_f32(&mut self) -> f32 {
        (self.next_u64() >> 40) as f32 / ((1u32 << 24) as f32)
    }

    pub fn range_f32(&mut self, min: f32, max: f32) -> f32 {
        min + (max - min) * self.unit_f32()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn simulation_delta_is_capped_but_elapsed_time_is_preserved() {
        let clock = SourceFrameClock::default();
        let frame = clock.sample(0.5);
        assert_eq!(frame.elapsed_seconds, 0.5);
        assert!((frame.simulation_seconds - 1.0 / 30.0).abs() < f32::EPSILON);
    }

    #[test]
    fn invalid_host_delta_is_zero() {
        let frame = SourceFrameClock::default().sample(f32::NAN);
        assert_eq!(frame.elapsed_seconds, 0.0);
        assert_eq!(frame.simulation_seconds, 0.0);
    }

    #[test]
    fn waits_run_in_order_and_only_after_their_delay() {
        let mut waits = WaitQueue::default();
        waits.schedule(0.5, "bird").unwrap();
        waits.schedule(0.1, "retry").unwrap();
        assert_eq!(waits.advance(0.05), Vec::<&str>::new());
        assert_eq!(waits.advance(0.1), vec!["retry"]);
        assert_eq!(waits.advance(0.4), vec!["bird"]);
        assert!(waits.is_empty());
    }

    #[test]
    fn a_wait_scheduled_after_a_dispatch_starts_on_the_next_advance() {
        let mut waits = WaitQueue::default();
        assert!(waits.advance(10.0).is_empty());
        waits.schedule(0.1, "continue").unwrap();
        assert!(waits.advance(0.0).is_empty());
        assert_eq!(waits.advance(0.1), vec!["continue"]);
    }

    #[test]
    fn deterministic_rng_is_repeatable_and_stays_in_bounds() {
        let mut left = DeterministicRng::seeded(7);
        let mut right = DeterministicRng::seeded(7);
        for _ in 0..100 {
            let a = left.range_f32(-250.0, -70.0);
            let b = right.range_f32(-250.0, -70.0);
            assert_eq!(a, b);
            assert!((-250.0..-70.0).contains(&a));
        }
    }

    #[test]
    fn source_program_rejects_duplicate_ids_and_dangling_parents() {
        let binding = SourceEventBinding {
            sid: "one", name: "event", group: None, parent_sid: None,
            handler: SourceEventHandler::OutsideLayoutNoOp,
            status: SourceEventStatus::SourceNoOp,
        };
        assert!(validate_source_program(&[binding, binding]).is_err());
        let child = SourceEventBinding { sid: "child", parent_sid: Some("missing"), ..binding };
        assert!(validate_source_program(&[child]).is_err());
    }
}

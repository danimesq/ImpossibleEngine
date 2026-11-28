//! Flappy Madruga gameplay compiled by ImpossibleEngine.
//!
//! This library has no renderer or host dependency. A target host drives the
//! state machine and consumes semantic effects through a separate adapter.

pub mod game;
pub mod geometry;

/// Generated, source-pinned Event Sheet bindings.
pub mod source {
    include!("generated/source_events.rs");
}

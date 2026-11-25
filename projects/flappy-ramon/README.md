# Flappy Madruga — first Impossible project

**Source:** [danimesq/Flappy-Ramon](https://github.com/danimesq/Flappy-Ramon)  
**Original project:** Flappy Madruga, Construct 2, version 0.6.1.6  
**Port status:** First native Rust implementation is in progress. The source project is mapped directly; a general-purpose Construct importer is not part of this round.

## Run

From this directory:

    cargo run

The default launch opens the original Start screen. You can also launch a gameplay layout directly for testing:

    cargo run -- --layout=continuous
    cargo run -- --layout=chaves

Run the platform-neutral gameplay and collision tests:

    cargo test

Build an optimized native executable:

    cargo build --release

## Controls

- Start: click Continuous Play or press Enter.
- Flap: touch anywhere in the game viewport, click, or press Space.
- Retry: click Try Again! or press Enter after a collision.

The viewport preserves the original 400 × 500 portrait layout using letterbox scaling.

## What is implemented in the first native slice

- Start, Continuous and Chaves layout states.
- Source layout-start variables and design-time pipe destruction.
- Platform-style vertical motion using the source gravity and max-fall-speed values.
- Bird angle and Flying/Default animation wait.
- TopPipe/BottomPipe timed spawning, source positions, gap offset and independent cleanup.
- Scoring once per BottomPipe instance.
- Ground, TopPipe and BottomPipe collision checks using source polygons.
- Background wrap and per-frame source-delta scrolling.
- Game-over transitions, source waits, retry visibility and layout restart.
- Continuous high-score update and persistent Highscore key.
- Music, beat and Queda audio effect adapters, pending the original sound files.
- Explicit policy for Google Play sign-in (offline fallback until an Android SDK client is configured).

The actual source-event-to-Rust map is in event-sheets/source-coverage.json. Layout, object, behavior, variable and animation source data is in source-model.json. These are manually transcribed source references, not output from a generic importer.

## Assets

All original media folders are placeholders until the verified files are supplied. The current renderer draws temporary vector artwork and logs missing audio/font files. It does not claim that this fallback artwork is the original game.

See asset-placeholders.json for the complete source-to-destination media list.

## Important compatibility notes

- The original Start/Continuous/Chaves layout order is preserved.
- Common in-game destroys the design-time TopPipe and BottomPipe instances at layout start. The first runtime pair is created after the one-second obstacle interval.
- Construct delta time is passed to the gameplay update once per rendered frame. It is not silently replaced with a fixed tick.
- Chaves is the last source layout. Construct's Go to next layout action does nothing when already on the last layout.
- The original project declares Facebook and Browser plugins but does not use either in its checked-in event sheets.
- Google Play is used on Android but the checked-in project does not provide an SDK client ID/credentials. The current port falls back to offline play and exposes a callback boundary for a future configured adapter.

## Validation status

The source model, event map, gameplay code and geometry tests are committed. The current execution environment did not have Cargo/rustc installed, so this PR cannot claim a successful local cargo test or native build. GitHub Actions now performs both as a PR check.

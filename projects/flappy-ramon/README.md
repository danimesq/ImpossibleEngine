# Flappy Madruga — first Impossible project

**Source:** [danimesq/Flappy-Ramon](https://github.com/danimesq/Flappy-Ramon)  
**Original project:** Flappy Madruga, legacy visual-editor, version 0.6.1.6  
**Port status:** A source-pinned ImpossibleEngine project can be opened, validated and compiled to a headless Rust gameplay library. This is a project-specific Construct 2 adapter, not a general-purpose legacy project importer.

## Open and compile with ImpossibleEngine

From the repository root:

    python -m impossible

Open `projects/flappy-ramon/Flappy-Madruga.ieproj` in the editor. The native project contains all five source Event Sheets, ten object types, three layouts and twenty placed instances, source provenance, and the pinned Construct 2 snapshots. The GTK workspace exposes the imported scenes in its Layouts page.

Validate the original source and project mapping:

    python -m impossible.compiler validate --project projects/flappy-ramon/Flappy-Madruga.ieproj --target logic

Compile the headless gameplay motor:

    python -m impossible.compiler compile --project projects/flappy-ramon/Flappy-Madruga.ieproj --target logic

The compiler validates every source Event Sheet against the pinned XML, generates the typed Rust source-event table, runs the Rust workspace tests, and builds the optimized `flappy-madruga` library. Graphics are deliberately not part of this target.

The editor can also open the project directly:

    impossible

## Optional legacy preview controls

The GTK editor and the headless compiler do not open a game window. For the existing Macroquad preview only (not the Foundation graphics host), run:

    cargo run -p flappy-madruga --features graphics -- --layout=continuous
    cargo run -p flappy-madruga --features graphics


- Start: click Continuous Play or press Enter.
- Flap: touch anywhere in the game viewport, click, or press Space.
- Retry: click Try Again! or press Enter after a collision.

The viewport preserves the original 400 × 500 portrait layout using letterbox scaling.

## Headless logic target

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

The source-event map is in event-sheets/source-coverage.json. The immutable original project, all five Event Sheets and all three layouts are pinned under source/legacy-construct2/ at revision aab10559cea2d1283eafa2a8792aaf877cbffcf5. The compiler compares the source XML, source model, coverage map and native .ieproj before generating the Rust binding table. This is an explicit adapter for this one project, not a generic Construct 2 importer.

## Graphics and assets

The default Impossible compile target is headless and does not depend on Macroquad or open a window. Rendering and presentation through RustMultiConsoleFoundation are deferred. The existing Macroquad display/audio host remains available only as an optional legacy preview via `cargo run -p flappy-madruga --features graphics`; it is not the Foundation graphics integration. The planned Foundation boundary is `foundation-runtime::RuntimeHost` with `Sdl3Host` for native SDL3 and `Canvas2dHost` for the current browser Canvas 2D host. The game will emit Foundation-neutral `DrawCommand`/`FrameOutput` and semantic `AudioRequest` values; no Foundation dependency is linked in this headless logic build.

Original media bytes are still pending. The logic build does not claim visual or audio asset completeness.

## Assets

All original media folders are placeholders until the verified files are supplied. The current renderer draws temporary vector artwork and logs missing audio/font files. It does not claim that this fallback artwork is the original game.

See asset-placeholders.json for the complete source-to-destination media list.

## Important compatibility notes

- The original Start/Continuous/Chaves layout order is preserved.
- Common in-game destroys the design-time TopPipe and BottomPipe instances at layout start. The first runtime pair is created after the one-second obstacle interval.
- the source editor's per-frame dt is preserved for movement, including the default 1/30-second maximum delta cap. System Every-X-seconds timers and Wait continuations use elapsed time independently rather than accumulating the capped movement dt.
- Chaves is the last source layout. the source editor's Go to next layout action does nothing when already on the last layout.
- The original project declares Facebook and Browser plugins but does not use either in its checked-in event sheets.
- Google Play is used on Android but the checked-in project does not provide an SDK client ID/credentials. The current port falls back to offline play and exposes a callback boundary for a future configured adapter.

## Validation status

The headless Impossible compiler has a dedicated GitHub Actions workflow that validates the pinned source, generates bindings, runs runtime/gameplay tests and builds the optimized logic library. The optional legacy preview has a separate graphics-enabled CI path.

The source differential test against a running original Construct 2 build, original media population (12 media groups), Google Play SDK setup, and Foundation renderer/audio-host integration remain acceptance items.

**Headless validation passed in CI:** 27 Python tests and 23 Rust tests passed; the source-pinned importer validated all 32 event SIDs and all 20 placed instances across the three layouts, and the optimized logic library compiled. The separate optional preview CI also built the Macroquad native desktop and WebAssembly targets. These checks prove source mapping consistency and compilation, not differential equivalence with a live Construct 2 build or visual/browser parity.

The Macroquad browser package still needs its matching JavaScript vendor files. Foundation browser presentation is a separate future integration.

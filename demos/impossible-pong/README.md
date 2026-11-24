# Impossible Pong

The first bundled demo game for Impossible Engine. Its purpose is both to be a
small playable game and to exercise the Event Sheet -> typed IR -> Rust/Bevy
export pipeline.

## Status

**Authoring sample / compiler contract in progress.** The project JSON is the
initial declarative gameplay specification. The Bevy adapter, validator,
intermediate representation and Rust exporter are being implemented in stages.
Do not treat this directory as a finished playable build yet.

## Reference study

The initial inspiration is
[Plonq/bevy-pong](https://github.com/Plonq/bevy-pong), a compact Bevy Pong
implementation. Its source targets Bevy 0.7.0, so it is a historical gameplay
reference, not a dependency or a source file to transplant unchanged into this
project. Impossible Pong will be implemented against the Bevy version pinned
by the ImpossibleEngine workspace.

The upstream repository declares MIT, but its checked-in license text still
contains the unfilled `<YEAR> <COPYRIGHT HOLDER>` template. We are therefore
not copying its source or assets into this monorepo. The game mechanics are
being reimplemented independently, with original Impossible Pong assets and
branding.

## Project data

- `project.json`: typed Event Sheet draft, stable IDs, input map and runtime
  profile.
- `../../docs/EVENT-SHEETS-AND-CODEGEN.md`: semantics and exporter contract.

## Intended first playable slice

- Player paddle controlled by keyboard.
- Opponent paddle with a simple deterministic tracking rule.
- Ball, walls, paddle bounce and goals.
- Score and round reset.
- Desktop Bevy target first; browser WASM target after the native vertical
  slice is validated.

Gameplay state should use fixed-point/integer values and a numbered simulation
tick. Bevy transforms are presentation state only. This is deliberate: a fixed
timestep helps consistency, but does not by itself guarantee deterministic
floating-point behavior across architectures.

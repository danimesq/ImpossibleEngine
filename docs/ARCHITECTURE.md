# Impossible Engine architecture notes

## Frontend

The first GUI prototype uses the CUBIC/UNIC Python GUI stack:

- GTK 3
- PyGObject
- GtkBuilder
- GTK CSS

The prototype reuses the technology family, not CUBIC's ISO-building internals.
The editor shell is replaceable and must not own project semantics.

## Project model

Project data is represented independently of GTK. Event Sheets, logical
objects, assets, platform profiles and sparse platform overrides are persisted
as JSON. A future Rust GUI can read and write this format without inheriting
the Python widget architecture.

Event Sheet data is a typed language contract, not arbitrary code strings.
The compiler frontend validates and lowers that data into an engine-neutral
intermediate representation before any backend-specific code is generated.
See EVENT-SHEETS-AND-CODEGEN.md.

## Runtime and output targets

Impossible may adapt existing game engines and runtimes instead of requiring a
new renderer or physics engine immediately. Engine integrations belong behind
adapters; project authoring data must not depend on one selected engine.

The first demo backend is Bevy. The adapter maps Impossible logical objects
and components to Bevy ECS entities/components, and lowers ordered gameplay
operations into explicit systems and system sets. The JSON and compiler IR
must not expose Bevy-specific type names or arbitrary Rust snippets.

The browser output target should use **Rust compiled directly to WebAssembly**,
initially investigating `wasm32-unknown-unknown` with `wasm-bindgen` and
`web-sys`. The browser host should expose rendering through Canvas 2D and/or
WebGL 2, selected behind an Impossible renderer adapter. WebGPU may be evaluated
as an optional future backend, not assumed as the baseline.

WASM runs the Rust game logic; it does not draw to a canvas by itself. Browser
APIs remain host APIs and are reached through bindings. The Emscripten toolchain
is not the planned default for this Rust-first web target. See WEB-WASM.md for
the initial investigation boundaries and caveats.

Native Rust and console targets are also backend/toolchain integrations. A
console profile in the editor is an authoring target definition, not a claim
that its SDK, licensing requirements, compiler or runtime adapter is already
available.

## Platform-aware content

Platform variants are part of the project model from the beginning:

- Logical assets have one stable ID and may map to distinct source files per
  target.
- Logical objects have common base properties plus sparse per-target overrides.
- The resolver prefers an exact platform variant, then a generic/base variant,
  then the default asset source.
- Event logic should remain shared unless a real gameplay rule differs by
  platform; visual and resource constraints should not force duplicated logic.

Examples include a 3D character using separate PC, PS1 and N64 meshes, and a 2D
character using distinct modern-mobile, GBA and GBC sprite sheets.

See PLATFORM-VARIANTS.md for the initial profile set and authoring direction.

## Long-term validation projects

The intended validation path is:

1. Port Street Chaves into Impossible while preserving the behavior and
   fidelity of its existing implementation.
2. Use the Point Blank Rust port as the more demanding end-to-end validation.

Impossible Pong is the first smaller vertical slice for validating the
Event Sheet language and Bevy backend before those larger projects.

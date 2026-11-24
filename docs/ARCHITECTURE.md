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

## Runtime and output targets

Impossible may adapt existing game engines and runtimes instead of requiring a
new renderer or physics engine immediately. Engine integrations belong behind
adapters; project authoring data must not depend on one selected engine.

The project's HTML5 output target is the **Emscripten-based path**. The exact
integration between generated Rust and that toolchain is a separate technical
spike: it must be demonstrated and documented rather than assumed from the
fact that both Rust and WebAssembly exist.

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

These are end goals, not capabilities delivered by the current GUI prototype.

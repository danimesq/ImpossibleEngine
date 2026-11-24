# Impossible Engine architecture notes

## Frontend

The first GUI prototype uses the CUBIC/UNIC Python GUI stack: GTK 3, PyGObject, GtkBuilder and GTK CSS. The prototype reuses the technology family, not CUBIC's ISO-building internals. The editor shell is replaceable and must not own project semantics.

## Project model

Project data is represented independently of GTK. Event Sheets, logical objects, assets, platform profiles and sparse platform overrides are persisted as JSON. Event Sheet operations are contributed by plugins and validated against a plugin registry before lowering to engine-neutral IR. Mandatory System provides generic game/flow/tick semantics; Input, Collision and Audio are built-in optional capabilities. See docs/PLUGINS.md and EVENT-SHEETS-AND-CODEGEN.md.

## Runtime and output targets

Impossible may adapt existing game engines and runtimes instead of requiring a new renderer or physics engine immediately. Engine integrations belong behind adapters; project data must not depend on one selected engine. First demo backend is Bevy, mapping logical objects to ECS and lowering operations into explicit systems. JSON/IR must not expose Bevy types or arbitrary Rust snippets.

Browser output is planned as Rust compiled directly to WASM, initially wasm32-unknown-unknown with wasm-bindgen/web-sys, hosted through Canvas 2D and/or WebGL 2. WebGPU is optional future exploration. WASM logic requires browser bindings to draw. Emscripten is not the planned default. Console profiles are authoring targets, not proof SDK/toolchain adapters exist.

## Platform-aware content

Logical assets may have platform variants. Objects have common properties and sparse overrides. Resolver prefers exact platform, then generic/base, then default. Gameplay logic stays shared unless a genuine platform gameplay difference exists. Profiles include PC/PS1/N64 for 3D and mobile/GBA/GBC for 2D. See PLATFORM-VARIANTS.md.

## Plugin architecture

Event operation definitions live in plugins, not compiler-core hardcoding. System is mandatory; Input, Collision and Audio are optional built-in capabilities; game-specific operations stay out of System. See docs/PLUGINS.md.

## Validation projects

Port Street Chaves preserving fidelity, then use Point Blank Rust as demanding validation. Impossible Pong is the first smaller slice for Event Sheets, plugin registration, deterministic simulation and Bevy.

# Impossible Engine architecture notes

## Frontend

The first GUI prototype uses the CUBIC/UNIC Python GUI stack: GTK 3, PyGObject, GtkBuilder and GTK CSS. The prototype reuses the technology family, not CUBIC's ISO-building internals. The editor shell is replaceable and must not own project semantics.

## Project model

Project data is represented independently of GTK. Event Sheets, logical objects, assets, platform profiles, clock profiles and sparse platform overrides are persisted as JSON. Event Sheet operations are contributed by plugins and validated against a plugin registry before lowering to engine-neutral IR. Mandatory System provides generic game/flow/temporal operations; Input, Collision and Audio are built-in optional capabilities.

Every project declares an explicitly versioned clock contract. The contract defines simulation tick cadence, game-time semantics, pause/time-scale/suspension policy, input-to-tick assignment, catch-up behavior and the ordered simulation schedule. Host, simulation, game and render clocks are distinct domains. Backend defaults must never silently replace project semantics.

See docs/PLUGINS.md, docs/EVENT-SHEETS-AND-CODEGEN.md and docs/CLOCKS-AND-FIDELITY.md.

## Runtime and output targets

Impossible may adapt existing game engines and runtimes instead of requiring a new renderer or physics engine immediately. Engine integrations belong behind adapters; project data must not depend on one selected engine. First demo backend is Bevy, mapping logical objects to ECS and lowering operations into explicit systems. JSON/IR must not expose Bevy types or arbitrary Rust snippets.

The clock contract and phase schedule are engine-neutral. Bevy is an execution adapter, not the authority on project timing. The headless runner is the canonical environment for deterministic simulation, replay and reference-trace comparison. Rendering and audio presentation must not mutate authoritative gameplay state.

Browser output is planned as Rust compiled directly to WASM, initially wasm32-unknown-unknown with wasm-bindgen/web-sys, hosted through Canvas 2D and/or WebGL 2. WebGPU is optional future exploration. WASM logic requires browser bindings to draw. Emscripten is not the planned default. Console profiles are authoring targets, not proof SDK/toolchain adapters exist.

## Platform-aware content

Logical assets may have platform variants. Objects have common properties and sparse overrides. Resolver prefers exact platform, then generic/base, then default. Gameplay logic stays shared unless a genuine platform gameplay difference exists. Profiles include PC/PS1/N64 for 3D and mobile/GBA/GBC for 2D. See PLATFORM-VARIANTS.md.

## Plugin architecture

Event operation definitions live in plugins, not compiler-core hardcoding. System is mandatory; Input, Collision and Audio are optional built-in capabilities; game-specific operations stay out of System. Plugins declare temporal domains, execution phases, deterministic constraints, RNG usage and structural-mutation effects where relevant. The runtime clock and phase scheduler remain core infrastructure; System exposes operations against that contract. See docs/PLUGINS.md.

## Fidelity and validation projects

Street Chaves is a first-class behavioral-fidelity target. Its Pascal reference and StreetChavesRust reconstruction are used to derive a source-backed clock profile, exact ordered phase schedule, deterministic input/replay contract and differential trace tests. Byte-identical executable reproduction is not required; observable gameplay behavior is.

Point Blank Rust is a later demanding validation project. Impossible Pong remains the smaller vertical slice for Event Sheets, plugin registration, deterministic simulation and Bevy.


## Construct project compatibility boundary

Alien-Parcor and Flappy Madruga are C2 reference projects used to derive the
ACE, object-plugin, behavior-plugin, selection and runtime compatibility model.
They are not manually imported into Impossible and their C2 project/XML formats
are not accepted by the production importer.

The intended migration path is:

`C2 project -> external C2-to-C3 project converter -> C3 project -> Impossible C3 importer -> typed IR -> Rust backend`

The importer accepts Construct 3 folder projects and `.c3p` archives only.
The C2-to-C3 converter is an external adapter and must be pinned by repository,
commit/version, license, supported input versions, output schema and command
interface before integration. Addon conversion is a separate workflow and must
not be confused with whole-project conversion.

Impossible imports C3 resources into its own normalized project model,
resolves plugins/behaviors/ACEs, type-checks expressions and selection effects,
then lowers into engine-neutral IR. Unknown or incompatible features produce
an explicit compatibility report; they are never silently dropped.

See [CONSTRUCT-REFERENCE-STUDY.md](CONSTRUCT-REFERENCE-STUDY.md) and
[CONSTRUCT-ACE-AND-IMPORT.md](CONSTRUCT-ACE-AND-IMPORT.md).

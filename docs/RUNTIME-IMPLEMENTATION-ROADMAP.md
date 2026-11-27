# 🌈 Runtime execution roadmap

**Status:** implementation backlog, 2026-11-27  
**Scope:** connect the built-in add-on catalogue to a real Rust compiler/runtime, turn behavior contracts into executable systems, define concrete host adapters, and track renderer-backed effects.

This document is an implementation plan, not a claim that the planned runtime already exists.

## 🌈 1. Current state: metadata exists, execution does not

The current `main` catalogue contains:

| Catalogue item | Count |
|---|---:|
| Plugins | 40 |
| Behaviors | 31 |
| Effects | 43 |
| Conditions | 204 |
| Actions | 282 |
| Expressions | 154 |
| **Total ACEs** | **640** |
| **Total add-ons** | **114** |

All 114 add-ons currently declare `implementation.status = specification_only` and `engine_runtime = false`.

The Python `impossible.addons` module validates the catalogue, IDs, parameter metadata, categories, dependencies and presentation contracts. It does not compile an Event Sheet or execute an ACE.

The existing Rust file under `examples/flappy-madruga/generated.rs` remains an illustrative fixture, not compiler output. A reusable `crates/impossible-runtime` now exists with the first shared primitives (clock, Wait queue, deterministic RNG and source-event binding validation), and the Flappy project-specific compiler generates its own source-event table. This is a real vertical slice, but not yet the full generic scheduler/IR/object model described by the proposal.

The typed Event Sheet v1 format and universal registry-ACE-to-IR compiler remain proposals in `EVENT-SHEETS-JSON-TO-RUST.md`. The Flappy compiler currently uses explicit SIDs and project-specific Rust handlers.

This distinction must stay visible in the README and release notes: an editor catalogue is not an executable engine.

## 🌈 1A. First project-specific vertical slice

The Flappy Madruga path now exists as a concrete, deliberately narrow
implementation on this branch:

- Native project container: `projects/flappy-ramon/Flappy-Madruga.ieproj`.
- Pinned original Construct 2 project, five Event Sheets and three layout XMLs:
  `projects/flappy-ramon/source/legacy-construct2/`.
- Three native layouts, twenty source-UID-preserving placed instances, ten
  object types and five Event Sheets, all checked against the pinned source.
- All 32 source event-block SIDs have explicit typed Rust handler bindings in
  `src/generated/source_events.rs`.
- `crates/impossible-runtime` provides reusable timing, elapsed-vs-simulation
  delta separation, ordered Wait continuations, deterministic RNG and source
  binding validation.
- `impossible.compiler` validates the source snapshot and native project,
  regenerates the Rust binding table, runs workspace tests and builds the
  headless gameplay library.
- The GTK editor has a Layouts page that displays the three scenes and their
  placed instances.

The headless CI has passed 27 Python tests and 23 Rust tests; the release logic
library has compiled. Separate optional preview checks also compile the legacy
Macroquad desktop and WebAssembly hosts.

This vertical slice is **specific to Flappy Madruga**, not a generic importer
or the universal 640-ACE compiler. The game logic is still a source-specific
Rust implementation linked to its 32 event SIDs; it does not yet lower
arbitrary registry ACEs into a generic typed Event Sheet IR. The original
media (12 groups), live source differential testing and Android Google Play
SDK remain pending.

### 🌈 Graphics integration boundary

Rendering is intentionally outside the headless logic target. The intended
adapter is the existing RustMultiConsoleFoundation `foundation-runtime`
contract:

- native host: `foundation_runtime::native_sdl::Sdl3Host`;
- browser host: `foundation_runtime::web::Canvas2dHost`;
- game-to-host boundary: `RuntimeHost`, `RuntimeConfig`,
  `FrameContext`, `InputSnapshot`, `FrameOutput`, `DrawCommand`,
  `TextureId` and semantic `AudioRequest` values.

The Foundation API currently provides SDL3 native drawing and Canvas 2D
browser output, not a WebGL/WebGPU effect renderer. ImpossibleEngine should
own the logical 400×500 scene, object transforms, source collision geometry
and draw-command generation; Foundation should own the native/browser window,
canvas, texture/device and presentation lifecycle. Do not link the existing
Macroquad preview as if it were the Foundation adapter.

## 🌈 2. What the Construct references teach us

### 🌈 C2-Clock-Addon

[Repository](https://github.com/Gamlr/C2-Clock-Addon)

A small, clean example of the minimum plugin shape:

- stable plugin identity and picker category;
- eight typed date/time expressions;
- separate editor declarations and runtime methods;
- a single-global object with no layout drawing.

It is useful as a first compiler/runtime fixture. The modern implementation should define timezone and calendar semantics explicitly rather than copying accidental legacy details.

### 🌈 airconsole-construct2

[Repository](https://github.com/Gamlr/airconsole-construct2)

This plugin declares 25 conditions, 20 actions and 26 expressions. Its useful patterns include:

- meaningful ACE categories such as Signalling, Messaging, Highscores, Persistent Data, Ads, Profile and Controller;
- asynchronous operations paired with completion/error triggers;
- callback data made available to expressions;
- explicit offline/capability state;
- device and player identity as separate concepts.

The AirConsole README says the plugin is not maintained by AirConsole itself. Treat it as a reference implementation, not as a current platform SDK or a dependency to embed.

The most important lesson is that an asynchronous action must enter the runtime scheduler again through a typed completion event. It must not block a frame or pretend that a request has completed synchronously.

### 🌈 construct-plugins

[Repository](https://github.com/Gamlr/construct-plugins)

The repository demonstrates a practical separation between:

- addon identity and version;
- ACE definitions;
- editor scripts and picker resources;
- localization and icons;
- Construct 2 and Construct 3 runtime implementations;
- distributable packages and example projects.

Its C3 examples use `addon.json`, `aces.json`, `lang/`, `icon.png` and separate runtime files. The Firebase example is also useful for typed success/error callbacks and typed result access.

ImpossibleEngine already has a unified catalogue with stable IDs and typed parameters. It should keep that stronger single source of truth while adding runtime bindings and localization resources, not copy two parallel C2/C3 manifests.

### 🌈 construct2_plugins_behaviors

[Repository](https://github.com/Gamlr/construct2_plugins_behaviors)

The archive contains 49 extension folders with editor/runtime pairs. They cover a much broader surface than movement alone: paths, pinning, drag-and-drop, audio, camera, microphone, video, image processing, SVG, QR codes, file access, UI and shader experiments.

Not all 49 folders are behaviors; the repository explicitly contains both plugins and behaviors. It is a feature-discovery catalogue, not a count of behavior implementations.

The shader example creates its own WebGL context/canvas. That is useful historical material for shader compilation, but it is not the architecture ImpossibleEngine should use. Effects must participate in the engine renderer's shared render graph.

Legacy Flash, PhoneGap, jQuery and obsolete browser APIs must not be carried forward as implicit dependencies.

## 🌈 3. ACEs need a real compiler binding

The registry's stable ACE ID must become the bridge between the editor, compiler and runtime.

The intended path is:

1. The editor emits a versioned Event Sheet that references namespaced ACE IDs, typed arguments and explicit object-selection references.
2. The compiler resolves each ID against the catalogue and validates its section, execution class, argument count, parameter types, enum values, return type, selection policy and declared state writes.
3. Resolution produces a typed IR operation. The operation stores the source event/ACE IDs for diagnostics and migration.
4. Target lowering selects a built-in implementation or a host-adapter capability.
5. Code generation emits normal Rust calls or statically dispatched operation identifiers. The game must not perform string-based ACE discovery or parse the registry on every frame.
6. The runtime executes the operation and reports typed results, triggers or diagnostics to the scheduler.

### 🌈 Current Event Sheet schema gap

The proposed `event-sheet-v1.schema.json` does not yet reference catalogue ACE IDs. It currently models only two trigger kinds (`on_layout_start` and `every_tick`), two condition forms (`compare` and `not`), a small expression grammar (`const`, `ref`, `sub`, `mul`) and three generic action kinds (`set`, `set_x`, `set_animation`).

That means the sample Event Sheet is a small source-derived DSL, not yet a representation of the 640 registry ACEs. The current fixture can demonstrate a compiler subset, but it cannot prove general ACE resolution.

The next format revision should represent registry operations by stable ACE ID plus typed arguments and explicit target/selection references. Existing v1 documents must remain readable through a deliberate v1-to-IR lowering adapter; do not silently change the meaning of v1 or pretend its generic action names cover the catalogue. Preserve source IDs and provide a diagnostic for every operation that cannot be mapped exactly.

The runtime binding should be explicit. An ACE that has no implementation must fail compilation with a useful diagnostic such as:

- unresolved ACE ID;
- known ACE, but no engine implementation;
- required adapter unavailable for this target;
- incompatible argument or return type;
- unsupported selection/lifecycle semantics.

Do not silently no-op, substitute an unrelated behavior, or mark an entire plugin executable because one ACE happens to work.

### 🌈 Execution classes

- **Trigger:** emitted by lifecycle, input, behavior or adapter events and delivered through the scheduler.
- **Predicate:** evaluates against the current event/selection context without hidden mutation or I/O.
- **Command:** performs an ordered state mutation or starts an explicitly asynchronous operation.
- **Pure expression:** returns a typed value and must not mutate state, block, or perform hidden I/O.

Conditions, actions and expressions must preserve source order and their documented semantics. Object picking, families, trigger context, nested events, loops, waits, timers, trigger-once state and deterministic random-number generation need explicit IR/runtime support. A name match is not proof of semantic compatibility with Construct.

## 🌈 4. Build the Rust execution core first

Create a reusable Rust engine/runtime crate (or a small set of crates grouped by ownership), independent from GTK and from any one game project.

The core should own:

- project/runtime lifecycle and scene/layout transitions;
- stable object and instance handles, object selection and picking context;
- event scheduler, trigger queue, condition evaluation and action ordering;
- timer, wait and continuation scheduling;
- simulation clock, delta-time provenance and fixed/variable-step policy;
- deterministic seeded random-number generation;
- typed runtime values and expression evaluation;
- behavior attachment/state storage and system update phases;
- diagnostic, trace and feature-capability reporting.

The core must not own a windowing toolkit, audio device, camera API, HTTP stack, WebSocket client or GPU context. Those belong behind host/runtime adapter interfaces.

The compiler and runtime should share typed operation definitions, but the runtime must not depend on GTK or on the Python editor. Python remains a replaceable authoring frontend.

## 🌈 5. Turn the 31 behaviors into executable systems

Do not create 31 isolated crates or 31 unrelated update loops. Implement shared subsystems, then attach behavior-specific configuration and per-instance state to them.

| Runtime subsystem | Behaviors covered |
|---|---|
| Movement and steering | Platform Movement, Eight Direction, Bullet Movement, Vehicle Dynamics, Oscillation, Seek, Pursuit & Evade, Arrive, Wander, Flocking |
| Physics and collision | Solid / Static Collider, Physics Body, Bounce, Platform Solid |
| Camera and world bounds | Scroll To / Camera Follow, Anchor to Viewport, Bound to Layout, Destroy Outside Layout, Wrap Around Layout |
| Animation and timing | Fade, Flash, Tween, Rotate To Target |
| Sensing and navigation | Turret, Line of Sight, Path Follower |
| Interaction and constraints | Drag & Drop, Pin / Follow Object, Orbit, Spring, Grid Movement |

Each behavior needs a stable attachment contract, validated properties, typed ACE bindings, owned per-instance state, update phase, emitted triggers and explicit dependencies on shared systems.

Start with small deterministic systems (Oscillation, Bullet, Eight Direction and camera/world bounds), then movement/collision and physics, then steering/navigation and interaction. Platform Movement must include grounded transitions, coyote time, jump buffering and input-edge semantics from its descriptor, rather than only moving an object vertically.

Behavior conformance tests must cover delta-time behavior, update order, enable/disable, object destruction, attachment lifecycle, collision and event emission. Reusable systems should be tested independently from the editor.

## 🌈 6. Concrete adapters for plugins and platform services

An adapter is an implementation boundary, not a promise that every target supports every API. Each host must report capabilities before compilation or launch.

| Capability family | Required contract |
|---|---|
| HTTP | Request identity, method, URI, headers/body, progress, cancellation, response and typed failures |
| WebSocket | Connect/close, send/receive, reconnect policy, message ordering and transport errors |
| Multiplayer | Sessions, rooms, peers, authority, input/state replication and interpolation; not just a WebSocket wrapper |
| Audio | Asset loading, playback, stop, seek, loop, gain, mute, playback rate and completion events |
| Video | Decode/playback state, seek, pause, frame presentation and platform-specific media errors |
| Camera / microphone | Permission lifecycle, device selection, stream state, capture, stop and resource cleanup |
| Storage / files | Namespaces, persistence guarantees, quotas, serialization, file selection and access errors |
| Browser / platform | URL/navigation, clipboard, lifecycle, safe-area, orientation and platform capabilities |
| Haptics / speech / social / advertising | Capability-gated requests, permissions/consent and asynchronous result events |

Use typed request handles and typed completion payloads. Cancellation, timeout, permission denial, unavailable service, network failure and unsupported target must be distinguishable.

Keep credentials and platform secrets out of the project catalogue and generated source. Adapters should own permissions, resource lifetimes, validation and platform-specific error mapping.

A target that lacks an adapter must receive a build-time or launch-time diagnostic. It must not get a fake implementation that reports success.

## 🌈 7. Effects: explicit future renderer work

The 43 effect descriptors are currently metadata only. They do not yet have GLSL/WGSL shader implementations or integration with a renderer.

Track this as a dedicated renderer milestone, not as a side effect of adding effect names to the picker.

Required work:

- define one shared effect/pass contract and property-to-uniform binding;
- implement the render graph, pass scheduling, intermediate render targets and resource lifetime;
- implement shader variants for WebGL 2 (GLSL ES) and WebGPU (WGSL);
- bind descriptor properties to typed uniforms and validate ranges/defaults;
- honor render stage, multipass cost, alpha policy, blend modes and bounding-box extension;
- implement background, depth and cross-sampling only where declared and supported;
- validate shader compilation and pipeline creation in CI for each backend;
- add image-based reference tests and tests for effect-stack ordering;
- emit an explicit unsupported-renderer diagnostic rather than silently dropping an effect.

Initial effect work should prioritize inexpensive single-pass effects (grayscale, tint, invert, color matrix, brightness/contrast and pixelate), then blur/bloom and other multipass effects, then sampling-dependent effects such as displacement, refraction and depth-aware lighting.

The renderer must own GPU contexts and pipelines. An effect must not create a private canvas or bypass the engine's render graph.

## 🌈 8. Implementation order and release gates

### Gate A — executable core

- Add a reusable Rust runtime crate and compile/test it independently.
- Define lifecycle, world/object handles, scheduler, typed values and capability interfaces.
- Keep the first runtime test host deterministic and headless.

### Gate B — first compiler vertical slice

- Parse and validate a typed Event Sheet document.
- Resolve ACE IDs to typed IR and report all unresolved operations.
- Generate Rust for a small supported set and compile the generated consumer.
- Start with clock/time expressions, basic object state operations, input triggers, Timer and a small behavior set.
- Prove source order, event traces, delta-time and trigger behavior with fixtures.

### Gate C — behavior systems

- Implement behavior subsystems in small, testable batches.
- Enable runtime support per behavior only after its ACEs, properties, lifecycle and conformance tests work together.

### Gate D — host adapters

- Add adapters independently for each supported host and capability family.
- Test both successful operations and all failure/permission/cancellation paths.
- Add multiplayer semantics above transport rather than conflating the two.

### Gate E — renderer and effects

- Integrate the render graph into each renderer backend.
- Port the effect catalogue in small shader-tested batches.
- Enable an effect only on renderers for which a valid shader/pipeline exists.

## 🌈 9. Definition of done

An ACE or add-on can be marked runtime-supported only when all applicable requirements are met:

1. Its stable ID resolves to a typed compiler/runtime binding.
2. Its parameter, return, selection, trigger and state-write semantics are enforced.
3. Its implementation is executable, not a descriptor or placeholder.
4. Every required adapter/capability exists for the selected target.
5. Lifecycle, error and asynchronous behavior are covered by automated tests.
6. The generated Rust consumer compiles and the runtime conformance fixture passes.
7. Documentation and target support status match the implementation.

Track support per ACE, behavior and target where necessary. Add-on-level status must not hide partially implemented features. Keep `specification_only` until the relevant release gate is actually met.

## 🌈 10. Reference and licensing policy

Use the four repositories above to study feature breadth, ACE presentation, parameter design, callback semantics, extension packaging and runtime separation. Do not copy source files, icons, bundled libraries or assets into ImpossibleEngine without reviewing the applicable repository and third-party licenses. Preserve provenance for any code that is intentionally reused.

The goal is a Rust-first engine with a rich visual authoring surface and explicit, portable execution contracts—not a JavaScript compatibility layer for old Construct addons.

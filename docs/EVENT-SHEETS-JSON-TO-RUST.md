# Typed Event Sheets: JSON to native Rust

**Status:** Architecture proposal and reference fixture, 2026-11-25.  
**Implementation status:** The editor currently persists project schema version 1 and text-based Event Sheet rows. The typed Event Sheet format, schema, importer, semantic IR, Rust generator and build integration below are proposals, not implemented compiler features.

## 1. The central decision

ImpossibleEngine can use JSON as a declarative gameplay authoring language and still ship a normally compiled Rust game.

The intended path is:

~~~text
Construct / native editor events
        |
        v
versioned source-preserving project JSON
        |
        v
schema validation + semantic validation
        |
        v
typed, engine-neutral Event Sheet IR
        |
        v
target/capability lowering
        |
        v
generated Rust source + native Rust modules
        |
        v
cargo check / tests / cargo build / rustc
        |
        v
native executable or another Rust target artifact
~~~

JSON is the authoring and interchange representation. It is **not required to be interpreted every frame**. The compiler reads it during import/build, resolves operations to typed IR nodes, and emits ordinary Rust code. The game executes compiled Rust functions.

The hard part is not converting JSON fields into Rust syntax. It is defining the original game's execution semantics precisely enough that the generated program behaves the same way.

## 2. This is grounded in a real Construct 2 project

The first migration fixture is not a made-up Flappy clone. The source project already exists at [danimesq/Flappy-Ramon](https://github.com/danimesq/Flappy-Ramon), and its project metadata identifies the game as **Flappy Madruga**.

The source project contains:

- Flappy Madruga.caproj, project version 0.6.1.6, saved with Construct version 21400.
- A 400 × 500 portrait game configured for the HTML5 exporter.
- Layouts: Start, Continuous and Chaves.
- Event sheets: Start events, Continuous events, Common in-game, Common in-levels and Chaves.
- The Chaves event sheet includes Common in-game and Common in-levels; Continuous events includes Common in-game.
- Plugins: Audio, Browser, Button, Facebook, Keyboard, Sprite, Text, Tiled Background, Touch, WebStorage and Google Play.
- Behaviors: Platform and Solid.
- The Madruga sprite has a Queda boolean instance variable and the Platform behavior.
- BottomPipe has a Scored boolean instance variable. Pipe sprites contain animation data and custom collision polygons.
- Global event-sheet variables include JumpStrength (500), SCROLLSPEED (150, later set to 300 at layout start), SECONDSPEROBSTACLE (1) and Score (0).

Useful primary-source files:

- [Flappy Madruga.caproj](https://github.com/danimesq/Flappy-Ramon/blob/master/Flappy%20Madruga.caproj)
- [Common in-game.xml](https://github.com/danimesq/Flappy-Ramon/blob/master/Event%20sheets/Common%20in-game.xml)
- [Chaves.xml event sheet](https://github.com/danimesq/Flappy-Ramon/blob/master/Event%20sheets/Chaves.xml)
- [Common in-levels.xml](https://github.com/danimesq/Flappy-Ramon/blob/master/Event%20sheets/Common%20in-levels.xml)
- [Chaves.xml layout](https://github.com/danimesq/Flappy-Ramon/blob/master/Layouts/Chaves.xml)

The importer must treat the actual project and its event XML as source evidence. It must not replace the original with a simplified demonstration.

## 3. Keep this separate from the existing project schema

The current ImpossibleEngine model has project schema_version 1 and stores Event Sheet conditions/actions as strings. That format must continue to load.

This proposal introduces a separately versioned typed Event Sheet document:

- Project container version: currently 1.
- Typed Event Sheet document: format is impossible.event-sheet, version is 1.
- Future project migration: an explicit migration/import step, not silent reinterpretation of old strings.
- Source import record: preserve original product/version, file paths, event/group IDs, source order, plugin/behavior names and versions, and raw source values where semantics have not yet been established.

The reference schema is schemas/event-sheet-v1.schema.json. The source-derived Flappy Madruga fixture is examples/flappy-madruga/event-sheet.json. The corresponding illustrative Rust output is examples/flappy-madruga/generated.rs.

## 4. Semantic contract

A compiler must not guess the meaning of an Event Sheet. Version 1 establishes these rules for the small reference subset:

1. **Stable source order:** events execute in source declaration/tree order within their dispatch phase.
2. **Condition order:** conditions are evaluated in declaration order and combined with logical AND unless the source event explicitly declares OR semantics.
3. **Action order:** actions execute sequentially in declaration order.
4. **Immediate writes:** an action's state changes are visible to later actions and later events in the same dispatch, unless the source runtime specifies deferred behavior.
5. **Delta-time provenance:** a source expression using Construct's dt must remain tied to the source runtime's per-tick delta semantics. Do not silently replace it with a fixed timestep or render-frame delta from another runtime.
6. **Input edges:** touch-start and key-pressed triggers are edge events. They must not repeat because the renderer runs more than once.
7. **Typed references:** every object, variable, behavior, animation and expression reference resolves against a symbol/type table. Unknown paths, incompatible types and unknown enum values are diagnostics.
8. **No string evaluation:** expressions are an allowlisted AST. Source expression text is parsed into that AST; it is never passed to eval, a shell, a template engine or arbitrary Rust source generation.
9. **Deterministic dispatch:** event queues, object selection, instance iteration, collision pairs and random-number generation need documented ordering. If equivalence cannot be guaranteed, the importer must report it.
10. **Explicit numeric policy:** each field has a declared type. A fixed or variable timestep alone does not guarantee bit-identical floating-point results across CPUs and compiler versions.

Nested events, event groups, includes, OR blocks, object picking, families, loops, waits, timers, trigger-once behavior, behavior-specific actions, random-number generation and plugin operations require explicit IR nodes and conformance tests before an importer may claim support.

## 5. What belongs where

| Concern | Owner |
| --- | --- |
| Event identity, source order, conditions, actions and project-authored constants | Typed Event Sheet JSON |
| Type checking, reference resolution, control flow and diagnostics | ImpossibleEngine compiler |
| Typed gameplay operations and generated state transitions | Generated Rust |
| Window, device polling, rendering, audio devices, files and platform APIs | Selected runtime/host adapter |
| Complex or unsupported game-specific systems | Native Rust modules behind documented interfaces |
| Platform availability and feature/capability reporting | Selected platform/Foundation adapter |
| Source XML, plugin IDs, raw enum values, provenance and unsupported constructs | Source-preserving import package |

A JSON action such as setting a sprite's X coordinate is not a request for JSON reflection at runtime. The compiler resolves the target to a typed Rust field/accessor. Runtime adapters provide normalized input, collision notifications, clocks and host services through a separate interface.

## 6. Real source behavior versus a safe first compiler slice

The source-derived fixture deliberately compiles only a bounded subset whose meaning can be read directly from the checked-in project:

- Chaves layout start: set Required_Score to 10 and select the Chaves animation for TopPipe and BottomPipe.
- Common in-game layout start: reset the Queda flag and Score, set SCROLLSPEED to 300 and SECONDSPEROBSTACLE to 1, and reset the two tiled-background X coordinates.
- Background group, every tick: move BottomPipe, TopPipe, TiledBackground2 and TiledBackground using their X coordinate minus SCROLLSPEED multiplied by Construct's dt.

The generated Rust reference mirrors these actions and keeps the source delta explicit. It does not invent a bird collision event or pretend the whole game has been ported.

The source project also contains additional behavior that must remain visible in the import report:

- Touch-start OR Space-key input, a Queda guard, Platform behavior Set vector Y, animation changes and a 0.5-second Wait.
- Collision handling against TiledBackground2, TopPipe and BottomPipe, including Queda, scroll/obstacle stop, audio and retry-button changes.
- Per-pipe score logic: compare BottomPipe.X against Madruga.X, check the Scored instance variable, increment Score and mark that pipe as scored.
- Background wrap thresholds, pipe destruction, obstacle creation every SECONDSPEROBSTACLE seconds, and random TopPipe Y placement.
- High-score persistence through WebStorage, font loading, audio playback, Facebook and Google Play integrations, and layout navigation/restart behavior.

These are not interchangeable with generic if statements. For example, the touch event is an OR-trigger with nested child conditions; the pipe scoring event uses per-instance picking and a one-time flag; obstacle creation uses a source-specific random expression and object-instance relationships; the game uses the Construct Platform behavior. Each requires explicit mappings and tests.

## 7. Compiler stages and diagnostics

### Parse and validate

- Parse UTF-8 JSON and validate the declared format/version.
- Reject duplicate or missing identifiers where uniqueness is required.
- Validate references to objects, variables, behaviors, assets and event sources.
- Produce diagnostics with document path, event ID, action/condition index and original source ID.

### Build the typed IR

The IR should be independent of GTK, Python widgets, Bevy ECS types, Foundation-specific types and any particular renderer.

Suggested node families:

- Trigger: layout start, input edge, per-frame tick, fixed tick, collision enter, timer, named event.
- Condition: comparison, all/any/not, object existence, instance-variable state, object picking and source-specific trigger predicates.
- Expression: typed constants, typed references, arithmetic, conversions, delta time, and approved functions such as a deterministic random source.
- Action: set/add, set instance variable, set transform, set animation, spawn/destroy, emit event, change layout, play/stop audio, wait, and call a registered behavior.
- Control flow: event group, subevent, branch, loop, wait/timer continuation and function call, added only with defined scheduling semantics.

Every node retains a source span/provenance record so diagnostics and editor selection can point back to the original event/action ID.

### Lower and generate

- Resolve abstract operations to typed state accessors, simulation systems and runtime contracts.
- Select native Rust, Rust/WebAssembly, specialized console lowering or a documented fallback.
- Generate readable Rust modules and a build manifest.
- Run formatting, cargo check, tests and the actual target build as separate gates.
- Preserve a source map from generated Rust back to event/group/action IDs.
- Cache generated artifacts by normalized IR hash, compiler version, target profile and dependency-lock state.

Successful source generation is not a successful game build. A compiler implementation must report each gate separately.

## 8. Static compilation and dynamic content

| Use case | Preferred path |
| --- | --- |
| Shipping gameplay authored in the editor | JSON → typed IR → generated Rust → native compilation |
| Frequently edited mod rules or user-created content | Validated JSON → bytecode/VM or constrained data-driven runtime |
| Complex, performance-sensitive or unusual game systems | Native Rust module behind a documented game interface |
| Browser output | Rust compiled to WebAssembly, with browser APIs behind the web host |
| Targets without a usable general-purpose Rust runtime | Specialized target lowering/toolchain with explicit capability checks |

A hybrid game is expected, not a failure. A project may compile most bounded Event Sheets to Rust and retain specialized native modules for the rest. The compiler must make that boundary visible.

## 9. Construct 2 / Construct 3 migration contract

The Construct importer must preserve the original event graph before attempting Rust generation. It should record, at minimum:

- source application/version and project identity;
- layout, layer, object, family and instance identifiers;
- event order, event groups, includes, conditions, actions and subevents;
- object-picking/selection context and the meaning of OR conditions;
- instance/global variables and expression trees;
- behavior/plugin identifiers plus their versions;
- timers, waits, loops, trigger semantics, time scaling, collision settings and delta-time usage;
- asset references, animation frames, origins, collision polygons and audio metadata;
- constructs unsupported, ambiguous or dependent on an unavailable plugin.

Use a versioned adapter per source format/version and a registry mapping source condition/action/behavior IDs to typed IR operations. Do not assume similarly named operations in Construct 2 and Construct 3 have identical semantics.

Every imported construct gets a migration status:

- **Exact mapping:** semantics and ordering are represented and covered by tests.
- **Mapped with constraints:** valid only under documented restrictions.
- **Native island:** retained as a handwritten/imported Rust module behind an interface.
- **Preserved but unsupported:** original data remains in the project; export is blocked or requires an explicit fallback.
- **Unknown:** importer emits a diagnostic and never silently drops the construct.

### First pilot: the existing Flappy Madruga project

The pilot starts with danimesq/Flappy-Ramon, not a newly invented game. First import the actual .caproj, layouts, event sheets, assets, plugin/behavior declarations and source IDs. Then create a coverage report before translating behavior.

A safe sequence:

1. Preserve the original project as an immutable source package and hash every source file/asset.
2. Parse project metadata, layouts, objects, variables, animations, collision polygons, event sheets, includes, groups and nested events.
3. Build a source event graph with exact IDs and declaration order.
4. Map initialization and simple coordinate updates as the first compiled vertical slice.
5. Add Touch/Keyboard OR triggers, Platform behavior and Wait continuations only after their semantics are implemented.
6. Add collision, object picking, one-time pipe scoring, spawn/destruction and random placement with deterministic regression fixtures.
7. Add audio, WebStorage, fonts, Google Play and Facebook behind explicit services or retain them as reported unsupported integrations.
8. Compare state traces and play scenarios against the original Construct build before expanding the supported subset.

Do not claim a full C2/C3 port because a game launches or looks similar. Timing, object picking, collision polygons, animation transitions, plugin behavior and event ordering are part of compatibility.

## 10. Delphi reverse engineering to native Rust

For a Delphi-origin game such as the Street Chaves lineage, keep a separate recovery pipeline. Delphi uses Object Pascal, but reconstructing Pascal from a compiled executable is reverse engineering, not lossless source conversion.

~~~text
Delphi source / executable / resources
    -> evidence inventory and provenance
    -> static + dynamic reverse engineering
    -> reconstructed, documented Object Pascal
    -> semantic recovery and regression fixtures
    -> typed Event Sheet IR where fully representable
       + native Rust modules for complex behavior
    -> native Rust build and differential tests
~~~

The recovered Pascal layer is an auditable intermediate and compatibility reference. Record the compiler/runtime dialect where known, recovered types, resource/form data, external dependencies, confidence levels and links from reconstructed routines to evidence. If only a binary survives, original comments, names, project structure and exact source statements cannot be assumed to be recoverable.

Distinguish:

- **Recovered evidence:** facts observed in binaries, resources, traces or surviving source.
- **Reconstruction:** a best-supported Pascal representation of those facts.
- **Semantic port:** Rust code intended to preserve verified behavior.
- **Unresolved behavior:** ambiguous code paths retained as TODOs/fixtures or isolated native modules, never silently guessed.

When the original executable can run, capture deterministic inputs and outputs as golden fixtures. When it cannot, document the weaker evidence and confidence level. Preserve assets and metadata separately from code recovery. Never execute untrusted recovered binaries as part of the compiler.

For StreetChavesRust, the goal is native Rust validated against recovered behavior. ImpossibleEngine must not depend on the StreetChavesRust Cargo package, and not every Pascal routine needs to become an Event Sheet. Bounded gameplay belongs in typed IR when semantics are complete; complex, source-specific or timing-sensitive systems can remain native Rust behind explicit interfaces.

## 11. Foundation integration

This proposal complements RUST-GAMING-ECLIPSE.md:

- ImpossibleEngine owns schemas, importers, semantic validation, typed IR, lowering and generated project composition.
- RustMultiConsoleFoundation owns reusable host/platform contracts and adapters.
- The generated game owns its game state and rules.
- Flappy Madruga and StreetChavesRust are independent migration/validation consumers.

Do not invent a Foundation crate path or add an unverified dependency. Generated code should target a documented, versioned public API only after a compiling consumer adapter exists for the selected target. A minimal mock contract is useful for compiler tests; it is not evidence of production platform support.

## 12. Suggested implementation milestones

1. **Specification:** schema, typed operation registry, execution ordering and diagnostics.
2. **Parser/validator:** parse the source-derived fixture, reject invalid types/references and produce stable diagnostics.
3. **Typed IR:** lower the fixture without importing GTK or platform code.
4. **Rust backend:** generate the reference-equivalent functions and compile them in CI.
5. **Conformance harness:** compare state snapshots from a source-compatible reference model and generated Rust.
6. **Construct importer:** parse the actual Flappy Madruga project and publish an honest per-feature coverage report.
7. **Pascal recovery adapter:** ingest reconstructed Pascal with provenance, then migrate bounded routines and native Rust islands.
8. **Runtime/Foundation integration:** only after the selected public host contract and target adapter compile independently.

## 13. Acceptance criteria for a real compiler PR

- Existing project schema version 1 and text Event Sheets remain readable.
- Typed Event Sheet JSON has an explicit version and strict schema.
- The compiler has no GTK dependency and does not evaluate arbitrary strings.
- Every supported operation has defined type and scheduling semantics.
- The Flappy Madruga fixture validates, lowers to typed IR and generates Rust.
- Generated Rust compiles and tests pass.
- Source IDs survive parsing, lowering and code generation for diagnostics.
- Unsupported importer features are preserved and reported, not dropped.
- Construct and Pascal importers use independent, testable adapters.
- Platform/runtime limitations are explicit, and no unverified Foundation API is assumed.

## Non-goals of this proposal

This document and its fixtures do not implement a Construct importer, Delphi decompiler, Pascal parser, typed compiler, Rust generator, runtime VM, renderer, physics engine or production platform adapter. They establish an explicit, testable design target for those future implementations.

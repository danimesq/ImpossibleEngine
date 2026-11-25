# Game import and migration strategy

**Status:** Architecture proposal, 2026-11-25.  
**Scope:** Source-preserving import paths for Construct 2/3 projects and Delphi/Object Pascal game recovery into ImpossibleEngine and native Rust.

## 1. Two source families, one destination model

ImpossibleEngine should support multiple source adapters that converge on the same versioned project model and typed Event Sheet IR:

- **Construct 2/3:** structured project container, layouts, object model, event graph and plugin/behavior ecosystem.
- **Delphi/Object Pascal:** surviving source or binary/resources, reverse-engineering evidence, reconstructed Pascal and semantic port.

These are not the same reverse-engineering problem. A Construct project may expose a structured event graph. A Delphi executable may require substantial static and dynamic analysis to reconstruct behavior. The shared destination does not justify pretending the source formats are equivalent.

## 2. Import architecture

~~~text
Original project / executable / assets
             |
             v
     immutable source package
             |
             v
       source-specific adapter
             |
             v
 loss-aware source representation
             |
             v
 semantic mapping registry
             |
             v
 versioned project model + typed Event Sheet IR
             |
       +-----+------------------+
       |                        |
       v                        v
 generated Rust           preserved native
 gameplay modules         Rust modules / assets
       |                        |
       +-----------+------------+
                   v
           Rust build pipeline
                   |
                   v
         differential validation
~~~

Every import stores source identity, source version, source-file hashes, provenance and a coverage report. A failed mapping must not destroy original project data.

## 3. Construct 2/3 adapter

The importer must be version-aware and preserve the original event graph before normalization. Plugins and behaviors are versioned semantic dependencies, not merely names displayed in an editor.

Compatibility surfaces include event/subevent order, event groups/includes, OR conditions, expressions, object picking, families, instance/global variables, layouts/layers, containers, behaviors, triggers, loops, waits, timers, time scale, delta-time semantics, collision shapes and animation state. The exact surface depends on the source project and installed plugins.

### Mapping registry

Each source operation should map through a registry entry containing:

- source product and version range;
- source plugin/behavior ID and version, when applicable;
- source operation/condition/action ID;
- expected input/output types;
- typed IR operation;
- ordering and object-selection effects;
- unsupported parameter combinations;
- conformance fixture and migration status.

A mapping is not exact simply because operation names look similar. Object picking and subevent scope can change which instances an action affects; timing and trigger behavior can change when an event fires.

### Actual pilot: Flappy Madruga

The first source project is danimesq/Flappy-Ramon, whose checked-in Construct 2 project file is named Flappy Madruga.caproj. It is a real source project, not a placeholder fixture. Its project metadata records version 0.6.1.6, Construct save version 21400, HTML5 export configuration and a 400 × 500 portrait layout.

The project has Start, Continuous and Chaves layouts, and five event sheets. The Chaves sheet includes Common in-game and Common in-levels; Continuous events includes Common in-game. The source declares Audio, Browser, Button, Facebook, Keyboard, Sprite, Text, Tiled Background, Touch, WebStorage and Google Play plugins, plus Platform and Solid behaviors.

Known gameplay structure includes:

- Madruga as a Sprite with the Platform behavior and a Queda boolean instance variable.
- BottomPipe with a Scored boolean instance variable.
- JumpStrength = 500, SCROLLSPEED = 150, SECONDSPEROBSTACLE = 1 and Score = 0 at source declaration; common layout initialization later sets SCROLLSPEED to 300 and Score to 0.
- The Chaves layout-start event sets Required_Score = 10 and changes TopPipe/BottomPipe to their Chaves animation.
- Touch-start OR Space-key input is guarded by Queda and sets Platform behavior vertical velocity to -JUMPSTRENGTH, angle to 320, and animation to Flying; a 0.5-second Wait then restores Default animation.
- Background and pipes scroll on every tick using SCROLLSPEED multiplied by Construct's dt.
- Pipe pairs are created every SECONDSPEROBSTACLE seconds, with randomized TopPipe Y and BottomPipe positioned relative to it.
- The first time each BottomPipe passes Madruga, Score increases and that pipe's Scored flag is set.
- Collisions with TiledBackground2, TopPipe and BottomPipe initiate fall/game-over behavior, stop scrolling and obstacle creation, play audio, and reveal/enable retry UI.
- The project also uses WebStorage for high-score data, custom font loading, audio, Google Play and Facebook integrations.

Source files to preserve and test against:

- [Project metadata](https://github.com/danimesq/Flappy-Ramon/blob/master/Flappy%20Madruga.caproj)
- [Common in-game events](https://github.com/danimesq/Flappy-Ramon/blob/master/Event%20sheets/Common%20in-game.xml)
- [Chaves events](https://github.com/danimesq/Flappy-Ramon/blob/master/Event%20sheets/Chaves.xml)
- [Common level progression](https://github.com/danimesq/Flappy-Ramon/blob/master/Event%20sheets/Common%20in-levels.xml)
- [Chaves layout instances and properties](https://github.com/danimesq/Flappy-Ramon/blob/master/Layouts/Chaves.xml)

The first implementation should parse and inventory all of these constructs before compiling a selected subset. The JSON/Rust example in examples/flappy-madruga represents a **bounded source-derived slice**, not a claim that the entire game has already been converted.

### Migration status

| Feature | First-pass policy |
| --- | --- |
| Project metadata, layout dimensions, global variables and object IDs | Preserve and type-check |
| Layout-start assignments and pipe animation selection | Map to typed IR and verify |
| Per-tick X movement using source delta time | Map only with explicit delta semantics |
| Touch/Keyboard OR event and nested Queda guard | Preserve tree; implement edge triggers before compiling |
| Platform behavior and its properties | Behavior adapter required; do not replace with guessed physics |
| Wait action and delayed animation continuation | Scheduler/continuation IR required |
| Collision events and collision polygons | Runtime behavior/collision conformance required |
| Per-instance pipe picking and Scored flag | Object-picking and per-instance IR required |
| Every-X-seconds spawn, random Y and linked pipe placement | Timer + deterministic RNG + instance relationship support required |
| WebStorage, Audio, font, Facebook and Google Play | Explicit host-service adapters or visible unsupported status |

A Construct 3 adapter is separate from the Construct 2 adapter. The importer must read the actual source version and use the matching parser/semantic registry.

## 4. Delphi -> reverse engineering -> Pascal -> native Rust

Use this route when original Delphi source is missing, incomplete or cannot be built in its original environment.

### A. Evidence inventory

Preserve read-only copies and hashes of available files: executable, libraries, debug artifacts, resources, forms, images, audio, configuration and save data. Record known compiler/runtime version, operating-system assumptions, dependencies and license/provenance information.

If source code survives, parse and inspect it directly first. Do not reverse engineer a binary unnecessarily.

### B. Static and dynamic analysis

Build an evidence corpus from executable structure, strings, symbols/RTTI when present, resources/forms, imported libraries, disassembly/decompiler output and observed runtime traces. Keep tool output separate from conclusions.

Run legacy software only in an isolated, disposable environment with no access to secrets or production systems. Record inputs, timing, outputs, file/network behavior and error cases. One successful playthrough is not complete behavioral coverage.

### C. Reconstruct Pascal

Reconstruct readable Object Pascal routines as a forensic intermediate:

- record the likely Delphi/Object Pascal dialect and compiler/runtime assumptions;
- separate confirmed facts from inferred names, types and control flow;
- preserve routine/resource identifiers and links to evidence;
- annotate confidence and unresolved branches;
- keep forms/resources and game data distinct from recovered logic.

Recovered Pascal is not automatically original source. A decompiler may recover control flow while losing names, comments, type intent, component structure and high-level abstractions. State exactly what is known.

### D. Port to native Rust

Partition each recovered routine into one of three destinations:

1. Typed Event Sheet IR when behavior fits the declared operations and scheduling semantics.
2. Native Rust modules when behavior is complex, timing-sensitive, performance-critical or not naturally declarative.
3. Preserved unsupported material with a diagnostic and migration task when evidence or semantics are insufficient.

Do not force every Pascal routine into visual events. The purpose of the IR is to make common gameplay authorable and portable, not to hide complexity behind an enormous generic action language.

### E. Differential validation

When the original executable remains runnable, capture deterministic scenarios and compare the original with the reconstructed/ported version. Useful checkpoints include game state, positions, velocities, collisions, score, timers, RNG state, animation transitions, audio/event requests and save data.

When the original cannot run, use surviving recordings, save files, assets, documentation and independent observations as weaker fixtures. Mark those comparisons partial rather than equivalent.

## 5. Porting policy

- Preserve original files and evidence; never overwrite the source package with normalized data.
- Keep importer adapters independent from GTK and from a specific runtime.
- Preserve unknown data and emit actionable diagnostics.
- Track mapping status and source provenance down to event/routine level.
- Compare behavior, not just appearance or source-line counts.
- Keep generated Rust readable and debuggable, with source maps to imported constructs.
- Keep game-specific modules outside generic compiler/runtime crates.
- Do not claim lossless migration without semantic coverage and differential tests.

## 6. First implementation sequence

1. Finalize typed Event Sheet schema and the source-derived Flappy Madruga JSON/Rust slice.
2. Build parser/validator/typed-IR vertical slice for that fixture.
3. Build Rust code generator and compile/test its output in CI.
4. Inventory the full Flappy Madruga C2 project and publish an import coverage report.
5. Add mappings one operation at a time, with differential fixtures.
6. Create a separate Delphi evidence/reconstruction workspace for StreetChaves.
7. Port recovered Pascal routines into typed IR or native Rust in independently testable slices.

The importer must never block unrelated editor work, and it must never make the engine depend on an original game project at runtime.

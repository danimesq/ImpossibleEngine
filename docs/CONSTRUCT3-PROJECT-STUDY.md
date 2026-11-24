# Construct 3 project study and built-in importer design

## 1. Decision and pipeline boundary

Impossible will not embed the Construct 2-to-Construct 3 converter in this
repository. The project-level C2-to-C3 converter will live in a separate
repository created and maintained for that purpose.

The migration path is:

```text
C2 project
  -> external C2-to-C3 project converter (separate repository)
  -> C3 project (.c3p archive or folder project)
  -> built-in Impossible C3 importer (this repository)
  -> normalized Impossible project
  -> typed Event Sheet AST
  -> engine-neutral IR
  -> deterministic Rust code generation
```

The C3-to-Impossible importer is a first-party, built-in Impossible component.
It is not an external CLI dependency, addon, service or separately maintained
converter repository. The external C2 converter stops at C3. The Impossible
importer starts at C3.

Alien-Parcor and Flappy Madruga remain C2 semantic reference material. They
inform ACE, behavior and runtime requirements, but are not fed to this C3
importer directly.

## 2. Two real Construct 3 folder projects

Both projects below are separate Construct 3 folder projects committed inside
the GitHub repository
[MrPrattASH/Game_Design_In_Construct_3](https://github.com/MrPrattASH/Game_Design_In_Construct_3).
They are pinned to the repository revision
[`0dfcecbeda166a10c9d621f655c21e51dcf89020`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/tree/0dfcecbeda166a10c9d621f655c21e51dcf89020)
so the study refers to inspectable source snapshots.

The repository describes itself as a collection of Construct 3 tutorial
projects and identifies the source material as tutorials from Construct.net.
The importer fixtures record structural and semantic expectations only. No
game art, music, fonts or other media from these projects is copied into
Impossible.

### Project A: Platform abstraction

Source folder:
[`LG1_Using_Construct3/module_2.0_basic_platformer/finished_construct_folder`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/tree/0dfcecbeda166a10c9d621f655c21e51dcf89020/LG1_Using_Construct3/module_2.0_basic_platformer/finished_construct_folder)

Main manifest:
[`project.c3proj`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/blob/0dfcecbeda166a10c9d621f655c21e51dcf89020/LG1_Using_Construct3/module_2.0_basic_platformer/finished_construct_folder/project.c3proj)

Event Sheet:
[`eventSheets/Event sheet 1.json`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/blob/0dfcecbeda166a10c9d621f655c21e51dcf89020/LG1_Using_Construct3/module_2.0_basic_platformer/finished_construct_folder/eventSheets/Event%20sheet%201.json)

Layout:
[`layouts/Layout 1.json`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/blob/0dfcecbeda166a10c9d621f655c21e51dcf89020/LG1_Using_Construct3/module_2.0_basic_platformer/finished_construct_folder/layouts/Layout%201.json)

Observed manifest facts:

- `projectFormatVersion = 1`, `savedWithRelease = 31702`, runtime `c3`.
- Project name: `Platform abstraction`.
- Project viewport: 854 × 480.
- One layout (`Layout 1`) measuring 4000 × 2048.
- Two layout layers: `Platforms` with 40 instances and `HUD` with 1.
- Nine object types and one Event Sheet.
- Object plugins: Tiled Background (`TiledBg`), Tilemap, Sprite, Keyboard and Text.
- Behaviors: Solid, Flash, Platform, Scroll To and Sine.

The event sheet contains one variable declaration, two groups, twelve comments
and nineteen event blocks. It uses System and object/behavior ACEs such as
`every-tick`, `on-key-pressed`, Platform state triggers, collision
conditions, `compare-y`, `else`, animation changes, object destruction,
Platform vector changes and variable updates.

The project deliberately separates the player collision body from the player
art:

- `PlayerBox` is a Sprite object type with Platform and Scroll To behaviors.
- `PlayerAnim` is a Sprite object type with the Flash behavior.
- An every-tick event positions `PlayerAnim` relative to `PlayerBox`.
- Platform behavior state triggers change the artwork animation.
- Collision logic uses `PlayerBox`, while the visible artwork can be animated
  and flashed independently.

This is a useful object-composition fixture. An importer must not merge these
two object types just because one is positioned over the other. It must preserve
the explicit event action that relates them.

Other useful cases:

- `Enemy` has a string instance variable named `Action` and a Platform
  behavior. Its direction changes after collision with an `EdgeMarker`.
- `Pickup` uses Sine behavior.
- The Tilemap instance has a Solid behavior and a large
  `ownData.tilemapData` payload containing its tile data.
- The Tilemap is not merely a Sprite with a texture. Its own data and behavior
  must remain typed and addressable.

The first semantic test set should cover behavior composition, instance
variables, Platform triggers, collision selection, else branches, source
event order, the artwork/hitbox split and non-image object-specific data.

### Project B: Driving template

Source folder:
[`Bonus_Learning_Material/module_1_Advanced_AI_Driving_Cars/finished_example_construct_folder`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/tree/0dfcecbeda166a10c9d621f655c21e51dcf89020/Bonus_Learning_Material/module_1_Advanced_AI_Driving_Cars/finished_example_construct_folder)

Main manifest:
[`project.c3proj`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/blob/0dfcecbeda166a10c9d621f655c21e51dcf89020/Bonus_Learning_Material/module_1_Advanced_AI_Driving_Cars/finished_example_construct_folder/project.c3proj)

Event Sheet:
[`eventSheets/Event sheet 1.json`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/blob/0dfcecbeda166a10c9d621f655c21e51dcf89020/Bonus_Learning_Material/module_1_Advanced_AI_Driving_Cars/finished_example_construct_folder/eventSheets/Event%20sheet%201.json)

Layout:
[`layouts/Layout 1.json`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/blob/0dfcecbeda166a10c9d621f655c21e51dcf89020/Bonus_Learning_Material/module_1_Advanced_AI_Driving_Cars/finished_example_construct_folder/layouts/Layout%201.json)

Timeline:
[`timelines/Car AI Path.json`](https://github.com/MrPrattASH/Game_Design_In_Construct_3/blob/0dfcecbeda166a10c9d621f655c21e51dcf89020/Bonus_Learning_Material/module_1_Advanced_AI_Driving_Cars/finished_example_construct_folder/timelines/Car%20AI%20Path.json)

Observed manifest facts:

- `projectFormatVersion = 1`, `savedWithRelease = 32703`, runtime `c3`.
- Project name: `Driving template`.
- Project viewport: 640 × 480.
- One layout (`Layout 1`) measuring 1500 × 1500.
- Four layers: `Game` (185 instances), `Cars` (3), `Checkpoints` (4)
  and `UI` (3), for 195 instances in total.
- Twelve object types, one Event Sheet and one Timeline.
- Object plugins: Keyboard, Sprite, Text, Tiled Background and Gamepad.
- Behaviors: Car, Pathfinding, Timer, Scroll To and Solid.

The Event Sheet contains four variable declarations, four groups, seventeen
comments and nineteen event blocks. Its conditions/actions include layout
start, animation-finished, timer, every-tick, collision, For Each,
instance-variable comparison, event-variable comparison, object picking by
comparison, Pathfinding completion, Gamepad axis comparisons, car-control
simulation and timer operations.

The object type definitions and layout instances demonstrate why object
definitions and object instances must be separate:

- `Car` is a Sprite object type with `Laps` and
  `RecentCheckpointCrossed` numeric instance variables. Its layout instance
  attaches Car and Scroll To behaviors with instance-specific properties.
- `AICar` is a Sprite object type with `RecentCheckPointCrossed`,
  `Laps` and `PathFoundState` numeric instance variables. It attaches
  Pathfinding, whose layout instance stores cell size, obstacle mode, speed,
  acceleration, rotation and diagonal-navigation settings.
- `CheckPoint` has a numeric `CheckPointNumber` and boolean
  `isFinishLine` and `PlayerCollided` instance variables.
- `UIText` attaches Timer.

The event sheet increments the player's lap count by iterating checkpoints
with a System `for-each` condition and testing the per-instance
`PlayerCollided` flag. It uses `pick-by-comparison` to select the next
checkpoint for the AI car. Those operations must alter and consume an explicit
selection context, not just evaluate as booleans.

#### Asynchronous Pathfinding

The AI car uses the Pathfinding behavior in three distinct steps:

1. `find-path` requests a route to the selected next checkpoint.
2. `on-path-found` is a behavior trigger raised when the route has been
   calculated.
3. `move-along-path` begins following the completed path.

The project tutorial explicitly notes that path generation happens
asynchronously and is not available immediately after the Find path action.
The importer/runtime therefore cannot translate this sequence into a
synchronous function call or assume the next action can consume the completed
path in the same call stack.

This is a high-value test for behavior-owned triggers, asynchronous operation
state, event scheduling, object selection and deterministic external-result
handling. The compatibility layer must decide how the completion result enters
the simulation timeline and how replay records it.

#### Timer, Gamepad and expressions

The project uses the Timer behavior on a Text object with `start-timer` and
`on-timer`, including a string tag. It also evaluates Gamepad analog axes and
uses them to issue Car behavior controls. Event parameters contain expressions
such as:

- `1.2 - Car.Car.Speed / 1000`
- `lerp(LayerScale("Game"), IntendedScale, 0.01)`
- `Car.Laps` and `AICar.Laps`
- `CheckPoint.CheckPointNumber`
- `AICar.RecentCheckPointCrossed+1`

These are not arbitrary text labels. The ACE parameter schema determines
whether a value is a literal, enum, object reference or expression. Expression
strings must be parsed and type-checked before lowering.

#### Timeline resource

The project declares a Timeline named `Car AI Path`. Its JSON contains an
instance track targeting the `AICar` instance (`worldInstance = 190`) and
property tracks for `offsetX` and `offsetY`, with keyframe data.

This proves that an importer limited to `project.c3proj`, layouts and Event
Sheets would still be incomplete for this project. Timeline resources and
their cross-references must be imported or explicitly reported as unsupported.

## 3. What the two projects teach us

| Import concern | Platform abstraction | Driving template |
|---|---|---|
| Object plugins | Sprite, Tilemap, Tiled Background, Keyboard, Text | Sprite, Tiled Background, Keyboard, Text, Gamepad |
| Behaviors | Platform, Solid, Flash, Sine, Scroll To | Car, Pathfinding, Timer, Solid, Scroll To |
| Layout | Two layers, 41 instances, large tilemap | Four layers, 195 instances, racing/checkpoint scene |
| Instance data | Enemy direction state | Car laps, checkpoint state and AI path state |
| Selection | Collision-based Enemy/Pickup selection | Collision, For Each and Pick by Comparison |
| Event tree | Groups, comments, blocks, nested collision branches | Groups, comments, blocks, nested loops and AI path logic |
| Temporal behavior | Every tick and Platform behavior triggers | Start/animation triggers, Timer and async Pathfinding |
| Rich resources | Tilemap `ownData`, Sprite animations | Timeline instance track and keyframes |
| Expressions | String concatenation, variable references and comparisons | Arithmetic, `lerp`, object/behavior properties and variable references |

The projects are complementary rather than exhaustive. They do not establish
complete Construct 3 compatibility, cover every plugin or represent every
project format release.

## 4. Construct 3 project package and file model

Construct documents describe two source forms:

- A **folder project**, with its files and subfolders directly on disk.
- A **single-file `.c3p` project**, which is a ZIP archive containing the
  project folder structure.

The root `project.c3proj` is JSON and acts as the main resource index and
stores project metadata. The importer must use this manifest to discover
resources. It must not infer the project by indiscriminately scanning every
JSON file in the folder.

The manifest organizes resource lists using `items` and `subfolders`.
Relevant resource classes include object types, families, layouts, Event
Sheets, timelines, flowcharts, 3D models, palettes, tilemap brushes, scripts,
sounds, music, video, fonts, icons and general project files. Preserve folder
hierarchy and resource order.

The main resource families observed in the source projects are:

| Resource | Location | Import purpose |
|---|---|---|
| Project manifest | `project.c3proj` | Project metadata and complete resource index |
| Object types | `objectTypes/*.json` | Plugin identity, variables, behaviors, effects and animations |
| Layouts | `layouts/*.json` | Layers, instances, transforms, instance state and own data |
| Event Sheets | `eventSheets/*.json` | Ordered event tree, variables, conditions, actions and children |
| Timelines | `timelines/*.json` | Tracks, instance references and keyframes |
| Images | `images/*` | Sprite frames and single-image object resources |
| Additional resources | Manifest-declared folders | Scripts, audio, fonts, icons, videos and data files |
| UI state | `uistate` and `*.uistate.json` | Construct editor UI state; not gameplay content |

The official Construct format guide states that unreferenced files are ignored
by Construct and that UI-state files do not affect project operation. Impossible
should therefore distinguish authoritative project resources from incidental
editor state.

### Manifest metadata to preserve

At minimum, record:

- `projectFormatVersion` (file-format version);
- `savedWithRelease` (Construct editor release/build);
- project name and `uniqueId`;
- runtime and worker mode;
- viewport dimensions and project properties;
- declared layouts, Event Sheets, object types and other resource trees;
- `usedAddons` with addon type, ID, name, author, version when present and
  bundled flag;
- `bundleAddons` and other packaging settings;
- the source file path and source checksum for every imported resource.

Do not conflate `projectFormatVersion` with `savedWithRelease`. The two
sample projects both have project format version 1, but were saved with
different Construct releases (31702 and 32703).

### Object type JSON

The two projects show object type records containing:

- `name`, `plugin-id`, `sid` and `isGlobal`;
- declared `instanceVariables` and their types;
- `behaviorTypes` and `effectTypes`;
- animation lists, animation speed/loop settings and frame metadata;
- per-frame dimensions, origin points, collision polygons and image
  references.

A behavior's presence in an object's `behaviorTypes` list is a different
fact from its instantiated settings on a layout instance. Keep the object
capability declaration and the instance's behavior properties as separate
data.

### Layout JSON

Layout records include dimensions, viewport origin, projection, an associated
Event Sheet, layer hierarchy and ordered instances. Layer and sub-layer order
must be preserved.

Instances identify their object type and UID, then carry data such as:

- per-instance properties;
- per-instance variables;
- attached behavior properties;
- world transform and visual data;
- object-specific `ownData` (such as Tilemap data).

The world transform observed in the samples includes X/Y, width/height,
origin X/Y, color, angle and Z elevation. Preserve the source representation
and units until the target adapter performs a tested conversion.

A UID identifies an individual placed instance. Do not replace all references
to an object type with one object-type-level action. The Driving template
demonstrates multiple `CheckPoint` instances with different values of
`CheckPointNumber` and `PlayerCollided`.

### Event Sheet JSON

An Event Sheet record contains its name, SID and an ordered `events` array.
The samples contain several event-node types:

- `variable`: typed event variables with initial values and flags;
- `comment`: editor-authored explanatory text;
- `group`: named, enabled containers with nested children;
- `block`: ordered conditions, actions and nested children.

Condition and action records identify an ACE with a string `id`, an
`objectClass`, optional `behaviorType`, a source SID and a `parameters`
object. Preserve the object/behavior distinction. A System ACE, an object
plugin ACE and a behavior ACE may have the same general shape but belong to
different providers.

Never flatten the event tree into a single list. Preserve node types, child
relationships, variable declarations, conditions/actions and authored order.
When encountering an unknown C3 event node, retain its raw source payload and
emit a compatibility diagnostic rather than silently discarding it.

### ACE and addon metadata

The Construct 3 Addon SDK defines plugin and behavior ACEs through
`aces.json`. It uses string IDs, and each ACE can specify parameters and
other metadata. The language file supplies presentation strings; runtime
JavaScript implements the actual behavior.

For importing, `aces.json` is useful as a **declarative schema source**:

- resolve the ACE ID;
- identify condition/action/expression kind;
- obtain ordered parameter definitions and types;
- determine whether the ACE belongs to a plugin or behavior;
- map it to a versioned Impossible operation descriptor.

The importer must not execute `plugin.js`, `behavior.js` or C3 runtime
JavaScript. An addon adapter in Impossible must provide the semantics in
trusted Rust/plugin code. Metadata can describe an operation; it cannot prove
that Impossible implements its runtime behavior.

Construct's own guidance also treats released ACE IDs as stable compatibility
identifiers: released ACEs should be deprecated rather than deleted. Impossible
must retain explicit source aliases and version constraints so existing
projects continue resolving to the intended operation.

## 5. Built-in C3-to-Impossible importer architecture

The importer belongs inside Impossible. It is a read-only project reader and
semantic translator, not a C3 editor and not a C3 project rewriter.

### Stage 1: source adapter

Expose one logical `C3Source` interface over:

- a folder project;
- a `.c3p` ZIP archive.

Both forms must yield the same normalized virtual file tree. The archive
adapter must validate ZIP entry paths, reject path traversal and unsafe entry
types, detect duplicate normalized paths, enforce archive-size/entry-count
limits and avoid executing any content. It should read files on demand rather
than extracting an untrusted archive wholesale.

### Stage 2: manifest and version gate

1. Locate root `project.c3proj`.
2. Parse and validate the JSON root.
3. Read `projectFormatVersion` and `savedWithRelease` independently.
4. Select a known, versioned reader profile.
5. Traverse `items` and `subfolders` in the manifest.
6. Resolve every referenced resource path with case-sensitive path handling.
7. Check for missing, duplicate or mismatched references.

Do not assume that a new Construct release keeps every field or resource
layout unchanged. A release outside the tested parser range must produce an
explicit compatibility result. Unknown fields should be retained in source
provenance where possible.

### Stage 3: resource graph

Load manifest-declared project resources and build a graph before lowering
anything:

- object type definitions;
- families and containers;
- layouts and layer trees;
- placed instances and instance-variable data;
- Event Sheets and nested events;
- timelines and instance/property tracks;
- assets and additional files;
- addon/plugin/behavior dependencies.

Resolve object type, layer, layout, Event Sheet, asset, behavior and timeline
references by stable source identity. Do not resolve only by display labels.

### Stage 4: addon and ACE resolution

Resolve every `usedAddons` entry against Impossible's versioned plugin
registry and source-alias table. Use the C3 addon identity and version as the
lookup key; the display name alone is not sufficient.

For each Event Sheet condition/action/expression:

1. Resolve `objectClass` to the object plugin or global plugin.
2. Resolve `behaviorType`, when present, to the attached behavior provider.
3. Resolve the ACE string `id` within that provider.
4. Validate parameter count, order, types and defaults against the ACE schema.
5. Parse expression-valued parameters using their declared parameter type.
6. Produce a typed Impossible operation node.

A missing addon or ACE is never replaced with a no-op. It creates a
`missing-dependency` or `unsupported` diagnostic and blocks a strict build
when it affects authoritative behavior.

### Stage 5: typed resource parsing

Convert C3 resources into Impossible's normalized project model:

- logical object definitions with plugin identity, variables, behaviors,
  effects and animations;
- layout definitions with layers, ordering and placed instances;
- stable instance IDs derived from preserved source provenance;
- image frames, origins and collision polygons;
- Tilemap data and other object-specific payloads;
- variables with explicit project/event/object/instance scope;
- Event Sheet node trees and includes/references;
- timeline tracks, keyframes and instance targets;
- assets and non-game/editor metadata kept in separate categories.

Preserve the exact source path, source SID, source UID, original name, addon
identity and source release on imported entities. Generated Impossible IDs
must be stable for the same source project and importer version. A normalized
source identity can be namespaced by the C3 project's `uniqueId` and the
resource's SID/UID, with collision detection and a deterministic fallback.

### Stage 6: semantic lowering

Lower C3 semantics only after all references and ACE definitions are resolved:

- event tree and group semantics;
- object selection and picked-instance context;
- instance-variable and event-variable scopes;
- condition groups, inversion, loops and child-event scope;
- behavior triggers and behavior state;
- timers and delayed continuations;
- asynchronous behavior events such as Pathfinding completion;
- object creation/destruction and visibility boundaries;
- expressions, random operations and clock-domain values;
- timeline evaluation and presentation state.

External asynchronous results must enter the runtime through a declared
deterministic boundary. For the Pathfinding sample, the runtime must represent
the route request and its later `on-path-found` trigger; it cannot pretend
that Find path synchronously returns a path in the same action call.

### Stage 7: compatibility report and normalized output

Every import produces:

1. a normalized Impossible project;
2. a source/provenance manifest;
3. a machine-readable compatibility report;
4. human-readable diagnostics with source file, event/object identity and
   actionable remediation.

Use the existing status vocabulary:

- `supported`: semantics mapped to an equivalent Impossible operation;
- `emulated`: preserved by a declared compatibility adapter;
- `partial`: only part of the source behavior is represented;
- `unsupported`: no semantic implementation exists;
- `missing-dependency`: a required plugin, behavior, addon or capability
  could not be resolved.

A strict mode must prevent export when unsupported authoritative behavior
remains. An explicitly lossy import may allow inspection, but losses remain
attached to the project and visible.

## 6. Security, correctness and fidelity rules

- Import is read-only. Never rewrite the source `.c3p` or folder project.
- Never execute JavaScript/TypeScript, addon code, event scripts or embedded
  commands during import.
- Do not trust project paths, archive names, asset paths or addon labels.
- Do not infer semantic identity from display names.
- Do not assume every string in ACE `parameters` is an expression; use the
  ACE parameter schema to distinguish expressions, literals and enums.
- Preserve numeric representations, coordinate systems and source units until
  a tested adapter converts them.
- Preserve array order, layer order, event order and selected-instance order.
- Preserve unknown node/resource payloads where practical; report unsupported
  behavior rather than dropping it.
- Ignore editor UI-state files because they are not runtime project content.
- Keep editor layout state and game semantics separate.
- Treat the Construct format as versioned and evolving, not as a stable public
  schema.

## 7. Conformance fixtures and implementation order

The first C3 fixture corpus should be built from the two source projects above.
The fixture index is `fixtures/construct3-reference/cases.json`. It contains
resource paths, release numbers and semantic assertions, not redistributed
game media.

Implementation sequence:

1. C3 source adapter for folders and `.c3p` ZIPs, plus archive safety tests.
2. Manifest parser and recursive resource-index walker.
3. Version gate and project provenance capture.
4. Object type, layout and instance parser.
5. Event Sheet tree and variable parser.
6. Addon/ACE resolver with typed parameter schemas.
7. Expression parser and selection context.
8. Behavior, trigger, timer and asynchronous continuation semantics.
9. Timeline, Tilemap and asset-reference adapters.
10. Compatibility report, deterministic normalized project and golden tests.
11. C3 corpus end-to-end imports, then compile/build tests through the normal
    Impossible pipeline.

Acceptance is not “the file opened”. Both sample projects must import with
their manifest references intact, expected layouts/layers/instances present,
object/behavior composition preserved, Event Sheet order and hierarchy
preserved, variables and selections correctly scoped, and no unsupported
operation silently dropped.

## 8. Format and source references

- [Construct's project format](https://www.construct.net/en/tutorials/constructs-project-format-3275)
  — folder/.c3p format, manifest-driven indexing, resources, images, layouts,
  event trees, SIDs, UIDs and UI-state files.
- [Construct 3 project structure](https://www.construct.net/en/make-games/manuals/construct-3/overview/project-structure)
  — layouts, layers, Event Sheets, instances and project resources.
- [Construct 3 Addon SDK](https://www.construct.net/en/make-games/manuals/addon-sdk)
  — plugin and behavior extension architecture.
- [Defining actions, conditions and expressions](https://www.construct.net/en/make-games/manuals/addon-sdk/guide/defining-aces)
  — ACE IDs and parameter schemas.
- [The .c3addon file](https://www.construct.net/en/make-games/manuals/addon-sdk/guide/c3addon-file)
  — addon archive and declarative ACE metadata.

Construct's own project-format guide explicitly says the format has no
published specification and can change with releases. These documents and
fixtures therefore define an observed, versioned compatibility target, not a
claim that the full private format has been formally specified.

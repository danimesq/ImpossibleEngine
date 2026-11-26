# ImpossibleEngine Project Format

## Purpose

ImpossibleEngine uses its own editable, source-first project format. The canonical project entry file is **`project.ieproj`**, a UTF-8 JSON document at the root of the project directory.

The `.ieproj` extension is the format's stable identity. `.iep` is not used as an alternative: the longer extension is explicit, recognizable and leaves room for related ImpossibleEngine project tooling without ambiguity.

A project is a directory/package, not a single JSON file. `project.ieproj` indexes the project and records its identity, schema version, entry points, resource catalogs and enabled capabilities. The files referenced by it contain the editable source data.

## Minimal project entry file

```json
{
  "format": "impossible-engine-project",
  "schema_version": 1,
  "project": {
    "id": "org.example.first-game",
    "name": "First Game",
    "engine_version": "0.1"
  },
  "entry_points": {
    "scenes": "scenes/index.json",
    "event_sheets": "event-sheets/index.json",
    "objects": "objects/index.json"
  },
  "resources": {
    "manifest": "assets/index.json"
  },
  "platforms": [
    "desktop",
    "web",
    "wasm"
  ],
  "features": {
    "three_dimensional": false,
    "timelines": false
  }
}
```

The example is a format contract, not a claim that every referenced editor subsystem is already implemented. A validator must report missing referenced files instead of silently inventing them.

## Package layout

A typical project can use this layout:

```text
MyGame/
  project.ieproj
  scenes/
    index.json
    main.scene.json
  event-sheets/
    index.json
    main.events.json
  objects/
    index.json
    player.object.json
  behaviors/
    movement.behavior.json
  assets/
    index.json
    images/
    audio/
    video/
    fonts/
    data/
  scripts/
  plugins/
  timelines/
  models/
```

This is a recommended organization, not a closed directory whitelist. Projects may add folders and resource types. The project index and sub-indexes define what belongs to the package.

## Core invariants

- **Versioned serialization:** every project declares `format` and `schema_version`. Migrations are explicit and version-aware.
- **Stable identity:** project, scene, Event Sheet, object, behavior, script and resource identifiers remain stable across save/load cycles.
- **Relative paths:** package references are relative to the project root, preserve filename case, and cannot escape the package with absolute paths or traversal segments.
- **Source preservation:** unknown fields and unrecognized files survive round trips. Reading a project must not erase data merely because the current editor does not understand it.
- **Deterministic writing:** serialization uses stable ordering where ordering is meaningful, consistent encoding and predictable formatting.
- **Provenance:** imported or generated nodes may record their origin, source path and transformation history without making provenance part of runtime semantics.
- **Feature declaration:** optional systems such as 3D, timelines, physics, networking or platform extensions are discoverable from project metadata and referenced resource definitions.

## Project model

The source model must represent, at minimum:

- Scenes, scene dimensions, layers, instances and scene-specific settings.
- Event Sheets, ordered event trees, conditions, actions, subevents, groups, includes, loops, triggers, waits and local scope.
- Object types, families, instances, instance/global variables and containers.
- Behaviors, effects, animation sets, image points, collision shapes and object properties.
- Scripts, plugins, extensions and custom editor metadata.
- Images, audio, video, fonts, icons, screenshots and arbitrary data files.
- Timelines, 3D models, materials, cameras, lights and other optional systems when enabled.

The source package remains authoritative for editing and round-trip serialization. Runtime IR and compiled artifacts are derived representations, not replacements for the editable project.

## Event Sheet semantics

Event Sheets are structured programs, not flat callback lists. Their model must preserve source order, conditions, actions, nested subevents, object selection, loop state, trigger context, wait/scheduling behavior and local variable scope.

ImpossibleEngine should preserve the serialized source tree first, then lower supported constructs into typed Event Sheet IR. Every lowering rule needs explicit semantics and conformance tests. Unsupported nodes remain preserved and produce diagnostics; they must never disappear or be replaced with guessed behavior.

## ImpossibleEngine architecture

1. **Package reader:** opens a project directory or supported archive without mutating it.
2. **Index parser:** validates `project.ieproj`, schema version and referenced sub-indexes.
3. **Version migrations:** upgrades older project schemas through explicit, testable transformations.
4. **Source model:** represents editable scenes, Event Sheets, objects, behaviors, scripts and resources while retaining unknown data.
5. **Semantic registry:** maps project operations and features to typed IR and runtime/compiler capabilities.
6. **Validator:** reports broken references, unsupported features, unsafe paths and semantic gaps.
7. **Editor model:** provides change tracking, undo/redo and stable object identity independently of the GUI toolkit.
8. **Project writer:** emits deterministic `project.ieproj` packages and validates round-trip preservation.

Parsing, editing, semantic conversion, compilation, runtime execution and publishing remain separate layers. Opening or saving a project must not require launching a particular runtime host.

## Publishing boundary

ImpossibleEngine owns the editable `.ieproj` project and the high-level export choices. When publishing for the browser, its publishing backend uses RustMultiConsoleFoundation's shared Web/WASM export API to declare the compiled module, JavaScript glue and explicit resource paths.

RustMultiConsoleFoundation owns the common `web-export.json` contract, package-path validation, browser resource loading and platform host. StreetChavesRust uses that same API and runtime contract as a game consumer. The editable project format and the published Web/WASM package are separate products with separate schemas.

## Validation strategy

Before declaring a project schema version stable, keep fixtures that exercise:

- multiple scenes, layers, object types and instances;
- nested Event Sheets, includes, groups, subevents and object selection;
- families, containers, behaviors and effect properties;
- global/instance variables, arrays, dictionaries and custom data;
- animations, image points, collision polygons and tiled backgrounds;
- scripts, plugins and extension metadata;
- mixed-case resource paths, nested folders and arbitrary files;
- audio, video, fonts, icons and screenshots;
- timelines, 3D models and platform-specific variants;
- migration from older `schema_version` values.

For every fixture, record source hashes, parsed feature inventory, validation diagnostics, unsupported nodes, round-trip differences and expected semantic behavior. A successful JSON parse alone is not evidence of project compatibility.

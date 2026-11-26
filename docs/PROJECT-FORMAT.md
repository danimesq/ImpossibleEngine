# ImpossibleEngine Project Format

## Purpose and file identity

ImpossibleEngine projects use a native, folder-based source format. The canonical entry file is **`project.ieproj`**, a UTF-8 JSON document at the root of the project directory.

`.ieproj` is the project-index extension. It is not a compiled game, runtime bundle or archive extension. The project itself is a directory containing the index plus the JSON and media files referenced by it.

The main file acts as an index of the project. It stores project-wide metadata and enumerates layouts, Event Sheets, object types, families, scripts, timelines, flowcharts, 3D models, palettes, tilemap brushes, add-ons and categorized root files. Each indexed resource is stored separately, in its appropriate package subfolder. A file that is not referenced by the index is not silently imported as project content.

## Canonical package layout

A project can be represented as:

```text
MyGame/
  project.ieproj
  objectTypes/
    Player.json
    Enemies/
      Slime.json
  families/
    Enemies.json
  layouts/
    Main.json
    Levels/
      Level01.json
  eventSheets/
    MainEvents.json
    Levels/
      Level01Events.json
  timelines/
  flowcharts/
  3dmodels/
  palettes/
  tilemapBrushes/
  images/
    player-idle-000.png
    player-idle-001.png
  scripts/
    main.js
    gameplay.ts
    Gameplay/
      boss.ts
  sounds/
  music/
  videos/
  fonts/
  icons/
  files/
    data/
    shaders/
  uistate/
```

Folders are created only when needed. The index's `items` and `subfolders` trees define the editor-visible hierarchy. Resource folders preserve that hierarchy. The `images/` directory is the exception: object images live directly in that folder, without further subfolders.

The `uistate/` directory and files ending in `.uistate.json` contain editor-window state, not game content. They may be ignored by source-control tooling and can be regenerated without changing runtime behavior.

## Main project index

The `project.ieproj` file is JSON. Its core shape uses a project-format version, project metadata, an add-on inventory and resource categories with an ordered `items` list and recursively nested `subfolders`:

```json
{
  "format": "impossible-engine-project",
  "projectFormatVersion": 1,
  "savedWithRelease": "0.1.0",
  "name": "First Game",
  "runtime": "impossible",
  "useWorker": "auto",
  "bundleAddons": false,
  "viewport": {
    "width": 400,
    "height": 300
  },
  "usedAddons": [
    {
      "type": "plugin",
      "id": "Sprite",
      "name": "Sprite",
      "author": "ImpossibleEngine",
      "bundled": true
    },
    {
      "type": "behavior",
      "id": "Platform",
      "name": "Platform",
      "author": "ImpossibleEngine",
      "bundled": true
    }
  ],
  "uniqueId": "iegame-7r2k9m4q",
  "objectTypes": {
    "items": ["Player", "Slime"],
    "subfolders": [
      {
        "name": "World",
        "items": ["Door", "Chest"],
        "subfolders": []
      }
    ]
  },
  "autosaveData": null,
  "containers": [],
  "families": {
    "items": ["Enemies"],
    "subfolders": []
  },
  "layouts": {
    "items": ["Title", "Game"],
    "subfolders": [
      {
        "name": "Levels",
        "items": ["Level01"],
        "subfolders": []
      }
    ]
  },
  "eventSheets": {
    "items": ["TitleEvents", "GameEvents"],
    "subfolders": []
  },
  "rootFileFolders": {
    "script": {
      "items": [
        {
          "name": "main.js",
          "type": "application/javascript",
          "sid": 123456789012345,
          "script-info": { "purpose": "none" }
        }
      ],
      "subfolders": []
    },
    "sound": { "items": [], "subfolders": [] },
    "music": { "items": [], "subfolders": [] },
    "video": { "items": [], "subfolders": [] },
    "font": { "items": [], "subfolders": [] },
    "icon": { "items": [], "subfolders": [] },
    "file": { "items": [], "subfolders": [] }
  },
  "timelines": { "items": [], "subfolders": [] },
  "flowcharts": { "items": [], "subfolders": [] },
  "3dmodels": { "items": [], "subfolders": [] },
  "palettes": { "items": [], "subfolders": [] },
  "tilemapBrushes": { "items": [], "subfolders": [] }
}
```

This is a format example, not a complete list of every optional top-level property. The reader must preserve recognized metadata and unknown properties. New features add versioned fields and resource categories without making older project files unreadable.

Each `items` list preserves editor order. A subfolder node has a `name`, its own `items` list and its own `subfolders` list. Entries in `rootFileFolders` carry file metadata such as filename, MIME type, serialization ID and category-specific metadata.

## Resource files

The main index identifies which resources belong to the project. The editor then reads each resource's own JSON document or media file.

- **Object types:** JSON metadata, properties, behaviors, effects, animations and references to image frames.
- **Families:** JSON definitions grouping object types and preserving member references.
- **Layouts:** JSON metadata plus a recursive layer tree. Layers preserve their properties and ordered object instances, including sub-layers.
- **Event Sheets:** JSON event trees, including nested subevents, groups, functions, custom actions, conditions, actions and inline script blocks.
- **Timelines:** JSON definitions for sequences of changes over time.
- **Flowcharts:** JSON node/connection graphs for conversation trees, state machines and related logic.
- **3D models:** project-side JSON resources for imported models, materials and related metadata. Source GLTF/GLB files may be retained as import provenance.
- **Palettes and tilemap brushes:** separate JSON resources that can be independently versioned in source control.
- **Images:** standalone source images referenced by object animation/frame metadata. Image files are stored directly under `images/`, normally with lowercase names. A single-image object uses its object name; animated frames use `object-animation-000.ext` naming with a zero-padded frame index. The referenced MIME type determines the extension.
- **Scripts:** JavaScript and TypeScript files stored under `scripts/`, with nested folders matching the project index.
- **Sounds, music, videos, fonts, icons and arbitrary files:** standalone files stored in `sounds/`, `music/`, `videos/`, `fonts/`, `icons/` and `files/`, respectively. Their metadata and folder hierarchy are indexed by `rootFileFolders`.

A loader must resolve paths from the index and each resource's references. It must not assume that every project contains every folder or that every object type has image data. Media files remain standalone source assets; browser-specific encoding or optimization belongs to the publishing pipeline rather than the editable project package.

## Identity and relationships

The format distinguishes project-resource identity from layout-instance identity:

- **Serialization IDs (`sid`):** stable identifiers for serialized resources and members whose identity must survive renames. New IDs should use 15 decimal digits to reduce collision risk during collaboration.
- **Instance UIDs (`uid`):** unique numeric identifiers for placed object instances. Every instance in the project must have a distinct UID; the value itself has no special semantic meaning. Six-digit random values are convenient for human inspection while still supporting safe collaboration at typical project scales.
- **Resource names and paths:** names are editor-facing labels, not identity. A rename must not silently change a resource SID or break references.
- **Ordering:** the order of items in the project index, layers, object instances and event trees is preserved whenever it affects editor presentation or runtime behavior.

IDs must be validated for uniqueness in their defined scope. Importers and writers must retain existing identifiers instead of regenerating them during routine save operations.

## Event Sheet execution model

Event Sheets are structured programs, not flat lists of callbacks. The serialized tree must preserve source order, event kinds, conditions, actions, nested subevents, groups, function declarations, custom actions, inline script, object picking, loop context, trigger context and local scope.

ImpossibleEngine first loads the source tree losslessly. It then lowers supported nodes into typed Event Sheet IR. Every lowering rule needs explicit execution semantics, parameter types, ordering rules, object-selection effects and conformance tests. Unsupported nodes remain preserved and produce diagnostics; they must never disappear or be replaced with guessed behavior.

## Serialization and round-trip rules

- **Versioned schema:** every project declares `format` and `projectFormatVersion`. Migrations are explicit, ordered and testable.
- **Index-first loading:** the index defines the project inventory. Unreferenced files are not silently imported into the project.
- **Loss-aware parsing:** unknown fields, resource categories and files survive round trips.
- **Path safety:** references are package-relative, preserve filename case and cannot escape the project directory through absolute paths, traversal segments or symbolic-link escapes.
- **Deterministic writing:** resource lists and JSON output use stable ordering where the schema makes ordering meaningful.
- **External asset editing:** media files remain standalone where practical. If image metadata dimensions disagree with the actual image file, the decoder reads the dimensions from the file.
- **Provenance:** imported or generated nodes may record origin, source path, hashes and transformation history without making provenance part of runtime semantics.

## ImpossibleEngine architecture

1. **Package reader:** opens a project directory or supported archive without mutating it.
2. **Index parser:** validates `project.ieproj`, project format version and all indexed resources.
3. **Resource readers:** parse layout, Event Sheet, object type, family, brush, script and optional system files.
4. **Version migrations:** upgrade older project schemas through explicit, testable transformations.
5. **Source model:** represents editable project data while retaining unknown fields and provenance.
6. **Semantic registry:** maps project operations and features to typed IR and runtime/compiler capabilities.
7. **Validator:** reports broken references, duplicate IDs, unsupported features, unsafe paths and semantic gaps.
8. **Editor model:** provides change tracking, undo/redo and stable object identity independently of the GUI toolkit.
9. **Project writer:** emits deterministic `project.ieproj` packages and validates round-trip preservation.

Parsing, editing, semantic conversion, compilation, runtime execution and publishing remain separate layers. Opening or saving a project must not require launching a particular runtime host.

## Publishing boundary

ImpossibleEngine owns the editable `.ieproj` project and high-level export choices. When publishing for the browser, its publishing backend uses RustMultiConsoleFoundation's shared Web/WASM export API to stage the compiled module, JavaScript glue, page shell and selected resources.

RustMultiConsoleFoundation owns the common `web-export.json` contract, package staging, path validation, browser resource loading and platform host. StreetChavesRust uses that same API and runtime contract as a game consumer. The editable project package and published Web/WASM package are separate products with separate schemas.

A Rust publishing backend can stage a browser build through Foundation:

```rust
use foundation_runtime::web_export::{
    WebAssetKind, WebExportAsset, WebExportBuilder,
};

WebExportBuilder::new(project.application_id(), project.name())
    .wasm_bundle_files(
        "target/web/game.js",
        "target/web/game_bg.wasm",
        "pkg/game.js",
        "pkg/game_bg.wasm",
    )
    .asset_file(
        WebExportAsset::new(
            "main_scene_atlas",
            "assets/images/main-scene.webp",
            WebAssetKind::Image,
        ),
        project.asset_source_path("main_scene_atlas")?,
    )
    .package_file("web-template/index.html", "index.html")
    .package_file("web-template/main.js", "main.js")
    .write_to("dist/web")?;
```

The exporter derives project identity, resource IDs and source paths from the editable project/build result. The WASM compilation step creates the generated module and JavaScript glue; Foundation copies those outputs and declared resources into the package and writes `web-export.json`. The current GTK/Python editor prototype is not yet wired to this Rust publishing backend; this documents the intended integration point rather than claiming the editor already exports packages.

## Validation strategy

Before declaring a project format version stable, keep fixtures that exercise:

- multiple layouts, nested folders, layers, object types and instances;
- recursive layer trees with mixed instance types and stable UIDs;
- nested Event Sheets, includes, groups, functions, custom actions and inline scripts;
- families, tilemap brushes, containers, behaviors and effect properties;
- global/instance variables, arrays, dictionaries and custom data;
- animations, image points, collision polygons, tiled backgrounds and source image edits;
- categorized root files, script metadata and nested arbitrary files;
- audio, video, fonts, icons and splash screens;
- timelines, flowcharts, 3D models, palettes and platform-specific variants;
- schema migration from older `projectFormatVersion` values.

For every fixture, record source hashes, parsed feature inventory, validation diagnostics, unsupported nodes, round-trip differences and expected semantic behavior. A successful JSON parse alone is not evidence of project compatibility.

# Construct 3 Project Format

## Scope

ImpossibleEngine owns the editable/source-project compatibility layer for Construct 3. This document describes the **Construct 3 project format**, not the published HTML5/Web export. Export packaging, browser URLs, media fetching and runtime loading belong to RustMultiConsoleFoundation.

Construct 3 projects are structured project packages. The primary project file is `project.c3proj`, a JSON document that indexes and describes the project. A project also contains structured data and resource files organized into folders. The project file is not the Web export manifest and must never be treated as one.

## Project package model

An importer should treat a C3 project as a package with:

- a `project.c3proj` entry document;
- project metadata and editor/version information;
- layouts and their object instances/layers;
- event sheets and their event trees;
- object types, families and their properties;
- behaviors, effects, animations and related object data;
- scripts and other code resources;
- project files such as images, audio, video, fonts and arbitrary files;
- optional feature-specific data such as timelines and 3D models.

The precise set of directories and serialized fields evolves across Construct releases and depends on which features a project uses. Do not hardcode a single folder tree as the complete schema. Discover references from the project index and preserve unrecognized entries.

## Serialization and source preservation

The importer should parse `project.c3proj` as JSON while retaining the original source package unchanged. Build a version-aware parser around explicit schema adapters rather than assuming that a current project file can be interpreted identically to every older project.

Preserve:
- original project-relative paths and filename case;
- stable source identifiers where present;
- object, layout, event-sheet and resource names;
- source ordering where it affects execution or editor presentation;
- unknown JSON properties and unknown resource files;
- original version metadata and a content hash for every source file.

The normalized ImpossibleEngine representation must retain provenance back to the original file, JSON pointer/property or resource path. A round-trip exporter must not silently discard fields it does not understand.

## Event Sheets and semantics

Event Sheets are not merely lists of callbacks. They represent ordered event structures with conditions, actions, nested subevents, groups, includes, local scope, object selection/picking, loops, triggers, waits and other execution semantics.

ImpossibleEngine should preserve the source tree first, then lower supported constructs into its typed Event Sheet IR. Every mapping needs source-version context, typed parameters, object-picking effects, ordering rules and conformance fixtures. Unknown conditions/actions remain preserved nodes with diagnostics; they must not vanish or be replaced with guessed behavior.

## Layouts, objects and resources

The project model must account for:
- layouts, layout dimensions, layers, layer properties and layout-specific settings;
- object types, families, instances, instance variables and global variables;
- transforms, visibility, z-order, containers, collision polygons and animation state;
- behaviors and their versioned properties;
- effects and rendering-related metadata;
- image/animation resources and their source references;
- audio, video, fonts, icons, screenshots and arbitrary project files;
- scripts, timelines, 3D models and other feature-specific resources when present.

The project importer records logical asset identity and source-relative location. It does not implement browser URL resolution or the published export's optimized media layout. Those are Foundation responsibilities.

## Proposed ImpossibleEngine architecture

1. **Package reader:** open a directory or supported archive without mutating it.
2. **Project index parser:** parse `project.c3proj`, identify project version and referenced resources.
3. **Version adapters:** translate version-specific serialized structures into a loss-aware source model.
4. **Source model:** represent layouts, event sheets, object types, families, behaviors, scripts and resources while retaining unknown data.
5. **Semantic registry:** map source operations and features to typed IR or native Rust implementations.
6. **Validator:** report missing references, unsupported features, invalid identifiers and semantic gaps.
7. **Project writer:** serialize ImpossibleEngine projects and, later, export compatible C3 project packages where the mapping is proven lossless.

Keep parsing, semantic conversion, editor UI and runtime execution as separate layers. Importing a project should not require launching the Construct editor or executing its runtime.

## Compatibility and validation strategy

Before claiming support for a Construct 3 version, maintain real fixture projects that exercise:

- multiple layouts, layers, object types and instances;
- nested event sheets, includes, groups and subevents;
- families, containers, behaviors and effects;
- global/instance variables, arrays/dictionaries and object picking;
- animations, image points, collision polygons and tiled backgrounds;
- scripts and project files with nested folders and mixed-case names;
- audio, video, fonts and arbitrary files;
- timelines and 3D features where supported by the target version;
- older project versions that require migration.

For every fixture, record the Construct version, source file hashes, parsed feature inventory, unsupported nodes, round-trip differences and expected semantic behavior. A successful JSON parse alone is not evidence of project compatibility.

## Explicit ownership boundary

| Concern | Owner |
| --- | --- |
| `project.c3proj` parsing and editable project structure | ImpossibleEngine |
| Layouts, Event Sheets, objects, behaviors, editor/project model | ImpossibleEngine |
| ImpossibleEngine native project serialization | ImpossibleEngine |
| Published Web/HTML5 export filesystem | RustMultiConsoleFoundation |
| Browser asset URL resolution and fetch/decode backends | RustMultiConsoleFoundation |
| Native/Web runtime asset loading used by games | RustMultiConsoleFoundation |
| StreetChaves gameplay and its asset manifest/catalog | StreetChavesRust |

## Official references

- [Construct 3 project format](https://www.construct.net/en/tutorials/constructs-project-format-3275)
- [Project structure](https://www.construct.net/en/make-games/manuals/construct-3/overview/project-structure)
- [Project files](https://www.construct.net/en/make-games/manuals/construct-3/project-primitives/files)
- [Event sheets](https://www.construct.net/en/make-games/manuals/construct-3/ Construct 3 event sheets) 

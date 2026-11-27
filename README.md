# Impossible Engine

A Rust-first visual game authoring environment built around Event Sheets,
platform-independent project data, and interchangeable runtime adapters.

## Current prototype
- GTK 3 + PyGObject + GtkBuilder desktop shell.
- Toolkit-independent Python project model and JSON project persistence.
- Event Sheets, Objects, Assets and Platform Variants authoring surfaces.
- Platform-specific asset sources and sparse object-property overrides.
- Built-in add-on registry with typed plugin ACEs, reusable behaviors, effect
  descriptors, picker categories and icon references.

The Event Sheet GUI remains a prototype. The built-in registry is still
specification-only as a general catalogue, but the Flappy Madruga project is
now a source-pinned vertical slice: Impossible can open its native `.ieproj`,
validate all five original Event Sheets, generate typed Rust source bindings,
run its headless gameplay tests, and build the logic library. This does not
claim that all catalogue ACEs or arbitrary Construct projects are executable.

## Add-on registry
The canonical built-in catalogue is `addons/builtin-v1.json`, validated by
`impossible.addons`. It is independent from GTK and describes add-on picker
identity, icon references, ACE categories, Conditions, Actions, Expressions,
typed parameters and runtime status. See [docs/ADDON-SYSTEM.md](docs/ADDON-SYSTEM.md).

All current add-ons are marked specification-only until runtime code,
platform adapters and conformance tests exist.

## Flappy Madruga: first compiled project

Open `projects/flappy-ramon/Flappy-Madruga.ieproj` in the editor.

Validate its pinned source and import map:

    python -m impossible.compiler validate --project projects/flappy-ramon/Flappy-Madruga.ieproj --target logic

Compile its headless Rust gameplay motor:

    python -m impossible.compiler compile --project projects/flappy-ramon/Flappy-Madruga.ieproj --target logic

The compiler checks the original source revision, all 32 source event IDs, source order, includes, groups, layouts and object inventory. It generates Rust source-event bindings, runs workspace tests and builds the optimized gameplay library. Renderer and presentation integration with RustMultiConsoleFoundation are deferred; the old Macroquad preview is an optional feature, not the engine's graphics backend.

## GUI stack
- GTK 3
- PyGObject
- GtkBuilder
- GTK CSS

The prototype intentionally does not use Qt/PySide6.

## Run
    python3 -m impossible

Or:
    python3 -m pip install -e .
    impossible

## Tests
    python3 -m unittest discover -s tests -v

## Architecture
The UI is replaceable. Project data, Event Sheets, assets, add-on metadata,
compiler models and platform-variant resolution are toolkit-independent.
Runtime adapters and RustMultiConsoleFoundation own concrete execution and
platform integration boundaries.

See [docs/README.md](docs/README.md) for the documentation index.

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

The Event Sheet GUI remains a prototype. The registry prepares the metadata
needed by future authoring dialogs, but does not claim runtime execution.

## Add-on registry
The canonical built-in catalogue is `addons/builtin-v1.json`, validated by
`impossible.addons`. It is independent from GTK and describes add-on picker
identity, icon references, ACE categories, Conditions, Actions, Expressions,
typed parameters and runtime status. See [docs/ADDON-SYSTEM.md](docs/ADDON-SYSTEM.md).

All current add-ons are marked specification-only until runtime code,
platform adapters and conformance tests exist.

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

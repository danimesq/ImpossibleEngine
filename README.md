# Impossible Engine

A Rust-first visual game authoring environment built around Event Sheets,
platform-independent project data, and interchangeable runtime adapters.

The first editor prototype uses **GTK 3 + PyGObject + GtkBuilder**, following
the same Python GUI technology family used by CUBIC/UNIC. It does not import
CUBIC's ISO-builder internals, and it does not introduce Qt/PySide6.

## Current prototype

- GTK desktop shell with Event Sheets, Objects, Assets and Platform Variants.
- Editable condition/action rows in Event Sheets.
- JSON project open/save.
- Platform-specific sources for logical assets.
- Sparse platform-specific object-property overrides.
- Toolkit-independent Python project model, suitable for a future Rust GUI or
  compiler frontend.

## Bundled demo games

- **[Impossible Pong](demos/impossible-pong/)**: the first bundled demo-game
  project and the initial vertical slice for typed Event Sheets, deterministic
  simulation and Rust/Bevy code generation. Its JSON gameplay specification is
  being developed before the runtime/exporter implementation.

## Event Sheets and code generation

Event Sheets are intended to be a typed declarative language, not arbitrary
text expressions. The compiler pipeline is JSON parsing, schema validation,
symbol resolution, type checking, lowering to an engine-neutral IR, and
deterministic Rust generation.

See [docs/EVENT-SHEETS-AND-CODEGEN.md](docs/EVENT-SHEETS-AND-CODEGEN.md) and
the [Impossible Pong project](demos/impossible-pong/project.json).

## Platform variants from day one

One logical object or asset can have different realizations per target:

- 3D game: modern PC mesh, PS1 mesh and Nintendo 64 mesh.
- 2D game: modern mobile sprite sheet, GBA sprite sheet and GBC sprite sheet.
- Browser game: Rust compiled to WebAssembly, hosted by browser APIs.

The current profiles are authoring presets. Actual console builds require
verified platform adapters, SDKs/toolchains and target-specific validation.

See docs/PLATFORM-VARIANTS.md, docs/ARCHITECTURE.md and docs/WEB-WASM.md.

## GUI stack

The editor follows the CUBIC/UNIC GUI stack:

- GTK 3
- PyGObject (gi)
- GtkBuilder for the main application shell
- GTK CSS for theming

It intentionally does not use PySide6 or Qt.

### Ubuntu / Debian packages

    sudo apt install python3 python3-gi gir1.2-gtk-3.0

## Run from a checkout

    python3 -m impossible

Or install the project in editable mode:

    python3 -m pip install -e .
    impossible

On Debian/Ubuntu, prefer the distribution's PyGObject package so the Python
binding matches the system GTK libraries.

## Tests

The model tests do not require a graphical session or PyGObject:

    python3 -m unittest discover -s tests -v

## Current limitations

This is an early GUI prototype, not a finished game runtime or compiler yet.
The existing editor still has text-based Event Sheet rows. The typed Event
Sheet schema and Impossible Pong JSON are the first compiler-contract draft;
validation, typed IR, Rust code generation, a runnable Bevy adapter, browser
WASM output and console toolchains remain future work.

## Architecture boundary

The UI is replaceable. Project data, Event Sheets, assets, object properties
and platform-variant resolution belong to toolkit-independent modules. GTK is
the first frontend, not the definition of the project format.

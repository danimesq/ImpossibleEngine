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

## Event Sheets and plugin architecture

Each Event Sheet is a first-class project resource that owns its ordered event
tree. Events own their conditions, actions and child events; trigger conditions
are part of the event's condition list, not a separate top-level field. The
language is typed and declarative, not arbitrary text expressions. The compiler
pipeline is JSON parsing, schema validation, symbol resolution, type checking,
lowering to an engine-neutral IR, and deterministic Rust generation.

See [docs/EVENT-SHEETS-AND-CODEGEN.md](docs/EVENT-SHEETS-AND-CODEGEN.md),
[docs/PLUGINS.md](docs/PLUGINS.md) and the
[Impossible Pong project](demos/impossible-pong/project.json).


## Construct compatibility direction

Alien-Parcor and Flappy Madruga are reference projects for Impossible's ACE,
object-plugin, behavior-plugin and runtime semantics. They are not manually
ported and are not direct C2 importer inputs.

The planned chain is **C2 project → external C2-to-C3 project converter
(separate repository) → C3 project → built-in Impossible C3 importer → typed
IR → Rust backend**. The C2 converter will be developed outside this
repository. The C3-to-Impossible importer is a first-party component shipped
inside Impossible and accepts C3 projects only. C2 addon conversion is a
separate concern.

See [the C2 reference-project study](docs/CONSTRUCT-REFERENCE-STUDY.md),
[the C3 project study and importer design](docs/CONSTRUCT3-PROJECT-STUDY.md)
and [the typed ACE / C3 import contract](docs/CONSTRUCT-ACE-AND-IMPORT.md).
Semantic fixtures live in [fixtures/construct-reference](fixtures/construct-reference/README.md)
and [fixtures/construct3-reference](fixtures/construct3-reference/README.md).

## Versioned clocks and behavioral fidelity

Every project must declare a versioned clock contract. Project timing is not a
global engine constant: simulation ticks, game timers, pause/time scale,
suspension, input sampling, catch-up and ordered update phases are explicit
project data with versioned semantics. Host, simulation, game and render clocks
remain separate.

Street Chaves is a first-class fidelity target. Impossible aims to reproduce
the Pascal reference's observable gameplay behavior, using StreetChavesRust and
reference traces as implementation and validation evidence. Byte-identical
executable reproduction is not required; timing, update order, collision and
hit resolution, state transitions, RNG consumption and other observable
behavior are.

See [docs/CLOCKS-AND-FIDELITY.md](docs/CLOCKS-AND-FIDELITY.md) for the full
clock contract, proposed profile shape, scheduling rules, Street Chaves
requirements and differential-validation plan.

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
Sheet schema, Impossible Pong JSON and clock/fidelity documents are design
contracts; clock parsing/runtime, typed IR, Rust code generation, a runnable
Bevy adapter, browser WASM output and console toolchains remain future work.

## Architecture boundary

The UI is replaceable. Project data, Event Sheets, assets, object properties,
clock profiles and platform-variant resolution belong to toolkit-independent
modules. GTK is the first frontend, not the definition of the project format.

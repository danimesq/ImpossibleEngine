# 🌈 ImpossibleEngine

A cross-platform visual authoring environment built around Event Sheets,
platform-independent project data and an extensible add-on catalogue.

## 🌈 Editor

The desktop prototype uses GTK 3, PyGObject and GtkBuilder. The Python project
model, JSON persistence, add-on registry and authoring operations are kept
independent from GTK so they can also be used in automation.

## 🌈 Add-on catalogue

The built-in catalogue lives at `addons/builtin-v1.json` and is validated by
`impossible.addons`. Plugins, behaviors and effects expose typed Conditions,
Actions and Expressions with stable IDs, categories and picker metadata.
Current catalogue entries are specifications, not claims of executable runtime
support.

Third-party packages can be dropped into
`add-ons/<vendor>/<package>/addon.json`. The metadata loader checks the
manifest and entrypoint paths without executing package code.

See [docs/ADDON-SYSTEM.md](docs/ADDON-SYSTEM.md) and
[docs/CLI.md](docs/CLI.md).

## 🌈 Headless CLI

Install the project and use the same project model without opening GTK:

```sh
python3 -m pip install -e .
impossible --help
impossible addons list --kind behavior --format json
impossible addons show plugin.sprite
impossible addons add plugin.sprite --project ./MyProject.ieproj
impossible addons list --project ./MyProject.ieproj --format json
impossible events list --project ./MyProject.ieproj
impossible resources list --project ./MyProject.ieproj --kind event-sheet
impossible project validate --project ./MyProject.ieproj --format json
```

Running `impossible` with no arguments still opens the graphical editor.
Machine-readable JSON output is available for scripts and AI agents with
`--format json`.

## 🌈 Tests

```sh
python3 -m compileall -q impossible tests
python3 -m unittest discover -s tests -v
```

## 🌈 Architecture

GUI and CLI share the toolkit-independent operations in
`impossible.operations`. Add-on selection is stored in the project `usedAddons`
field. The CLI does not introduce a second project model or a parallel add-on
registry.

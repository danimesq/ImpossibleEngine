# 🌈 ImpossibleEngine CLI

The `impossible` command is the headless, scriptable interface to the same
project model used by the GTK editor. It is intended for shell scripts, CI,
automation and AI coding agents.

No GTK or display server is imported for normal CLI commands.

## 🌈 Launch behavior

- `impossible` with no arguments opens the graphical editor, preserving the
  historical behavior.
- `impossible gui` explicitly opens the graphical editor.
- `impossible --help` prints CLI help.
- `python -m impossible` uses the same dispatcher.

## 🌈 Output formats

Commands that return collections or project reports support `--format table`
(the default) and `--format json`. JSON output is designed for pipelines and
agents. Errors are written to stderr and return a non-zero exit status.

## 🌈 Projects

Create, inspect and validate editable projects:

```sh
impossible project create --path ./MyProject.ieproj --name "My Project"
impossible project inspect --project ./MyProject.ieproj --format json
impossible project validate --project ./MyProject.ieproj --format json
impossible project set-platform --project ./MyProject.ieproj --platform web-wasm
```

Creation adds a default `Gameplay` Event Sheet. Pass `--no-default-sheet`
to create an empty project. Creation refuses to overwrite an existing path.

The CLI validator checks the editable project model, duplicate resource IDs
and basic layout/object/asset references. It does not claim to compile arbitrary
ACE descriptors or execute add-on code.

## 🌈 Add-ons

Browse the built-in metadata catalogue by kind, category or search text:

```sh
impossible addons list
impossible addons list --kind behavior
impossible addons list --kind effect --search blur --format json
impossible addons show plugin.sprite
impossible addons list --third-party-dir ./add-ons
```

Select or remove a catalogue entry in a project:

```sh
impossible addons add plugin.sprite --project ./MyProject.ieproj
impossible addons remove plugin.sprite --project ./MyProject.ieproj
```

Adding an entry records its stable ID, type, display name and author in the
project's canonical `usedAddons` field. Missing catalogue dependencies are
added first; removal is refused when another selected add-on depends on the
requested entry.

Third-party packages can be placed under `add-ons/<vendor>/<package>/addon.json`
or discovered from another directory with `--third-party-dir`. The registry
validates the manifest and checks every declared entrypoint path remains inside
the package directory. It reads metadata only and never executes package code.

**Important:** selecting an add-on records project metadata; it does not execute
or install its runtime. The current built-in catalogue entries are marked
`specification_only`, so selection does not make their Conditions, Actions or
Expressions executable.

## 🌈 Event Sheets

```sh
impossible events list --project ./MyProject.ieproj
impossible events add --project ./MyProject.ieproj --name "Player jumps"
impossible events condition add --project ./MyProject.ieproj --event-id event-1 --text "On jump"
impossible events action add --project ./MyProject.ieproj --event-id event-1 --text "Apply vertical impulse"
impossible events disable --project ./MyProject.ieproj --event-id event-1
impossible events enable --project ./MyProject.ieproj --event-id event-1
impossible events remove --project ./MyProject.ieproj --event-id event-1
```

Use `--sheet SHEET_ID` when the project contains multiple Event Sheets and an
event ID is not globally unique. If a project has no Event Sheet yet,
`events add` creates the same default `Gameplay` sheet used by the GUI.

Conditions and Actions are stored as authored expression strings. This command
surface does not claim to compile arbitrary ACE expressions.

## 🌈 Inspect resources and edit variants

```sh
impossible layouts list --project ./MyProject.ieproj
impossible objects list --project ./MyProject.ieproj
impossible assets list --project ./MyProject.ieproj
impossible platforms --format json

impossible assets set-variant --project ./MyProject.ieproj \
  --asset-id asset-hero-sprite --platform gba \
  --path assets/hero/hero-gba.png

impossible assets set-variant --project ./MyProject.ieproj \
  --asset-id asset-hero-sprite --platform gba --clear

impossible objects set-override --project ./MyProject.ieproj \
  --object-id object-hero-3d --platform ps1 \
  --values '{"scale": 0.8, "shadow": false}'
```

An empty object override removes the target-specific override. Asset variants
can be cleared to restore the project's fallback source resolution.

## 🌈 Shared implementation

The GUI and CLI call the toolkit-independent operations in
`impossible.operations` for Event Sheet edits, platform selection, asset
variants, object overrides and project add-on selection. Keep editing behavior
in that shared layer rather than implementing separate GUI and CLI semantics.

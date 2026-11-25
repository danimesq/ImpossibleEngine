# Flappy Madruga — first Impossible project

**Source:** [danimesq/Flappy-Ramon](https://github.com/danimesq/Flappy-Ramon)  
**Original project:** Flappy Madruga, Construct 2, version 0.6.1.6  
**Port status:** Scaffold and source-derived compiler slice only. The complete port is the objective of the current migration round; it is not yet complete.

This folder is the destination for the full native Impossible project. The original Construct project remains the source of truth until each source construct has been imported, mapped and verified.

## Project rules

1. Preserve the original source package read-only, with pinned revision and file hashes.
2. Import all layouts, objects, instances, event sheets, includes, groups, behaviors, plugins, variables, animations and collision data.
3. Preserve source SIDs and source-file paths in provenance metadata.
4. Map bounded gameplay to typed Event Sheet JSON and generate ordinary Rust code.
5. Keep complex or source-specific behavior in explicit native Rust modules, not an untyped JSON escape hatch.
6. Do not require Construct 2 at runtime.
7. Do not claim a complete port while any source construct is unexplained or silently omitted.
8. Keep media references portable and relative. Original Windows paths are evidence only.
9. The asset folders contain placeholders until the original media is supplied. Do not invent replacement artwork, sound or fonts.

## Workspace

- migration-manifest.json — pinned source identity, game profile and migration gates.
- asset-placeholders.json — source media inventory and destination paths.
- assets/ — empty category folders reserved for media.
- src/ — generated and handwritten Rust game code will live here in later implementation steps.
- event-sheets/ — complete imported typed Event Sheet documents will live here.

## Media placeholder categories

- sprites
- backgrounds
- animation-frames
- audio/sfx
- audio/music
- fonts
- ui
- icons

Each category README documents intended content and the pending state. Media population is a later task; the project should still be structurally importable and testable without pretending the final artwork is present.

## Complete-port checklist

- [ ] Inventory every source file and hash it.
- [ ] Import all three layouts and all five Event Sheets, including includes and nested subevents.
- [ ] Import every object type, instance, variable, layer, behavior and property.
- [ ] Reproduce Platform and Solid behavior semantics.
- [ ] Reproduce input, timing, wait, collision, spawning, random, scoring, progression and restart behavior.
- [ ] Map audio, font, persistence, browser, Facebook and Google Play operations to target-aware services.
- [ ] Map every media reference to a project-relative asset ID.
- [ ] Generate and compile the native Rust project.
- [ ] Pass differential behavior tests against the original game.
- [ ] Populate and verify all media placeholders before claiming visual/content completeness.

The small example under examples/flappy-madruga is a compiler fixture only. It does not replace this full project workspace.

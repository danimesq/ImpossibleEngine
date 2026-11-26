# Construct 3 Web Export Filesystem

## Scope

This document describes the **published Web/HTML5 export**, not the editable
Construct project folder, `.c3proj`/ `.c3p` format, or the editor's internal
asset database.

The goal is to make ImpossibleEngine capable of importing, inspecting,
packaging and eventually running games whose source of truth is an exported
web package. This is a compatibility target and architectural reference, not a
claim that ImpossibleEngine already imports Construct exports.

## What the exported package represents

A Construct 3 Web export is a deployable web application package. It contains
an HTML entry point, runtime JavaScript (and possibly worker-related scripts,
depending on export settings), and the resources required by the game. The
export is delivered as a ZIP or can be written directly to a folder.

The exact filenames and generated runtime layout are exporter-version and
settings dependent. Do not make the engine depend on undocumented generated
JavaScript names, hashed filenames, or one fixed sample export. Inspect real
exports from the supported Construct 3 versions and treat the HTML bootstrap
and runtime loader as an implementation detail unless a documented interface
exists.

## Resource filesystem behavior documented by Construct

### Project files and folders

Construct's modern **Folders** export mode is the recommended mode. It
preserves filename case and exports project files into subfolders matching
their organization in the Project Bar. The legacy **Flat** mode lowercases
filenames and places project files in the root export folder for backwards
compatibility.

This setting affects string-based references to project files. An importer
must therefore preserve path case and directory boundaries and must not
silently lowercase paths.

### Media

Construct exposes a media subfolder through its runtime asset manager. In an
export, `mediaFolder` identifies the media directory and is documented as
typically `media/`. Sound and music files are included there. The API also
provides `getMediaFileUrl(url)` to obtain a usable URL for an audio resource.

Construct distinguishes **Sounds** from **Music** semantically:
- Sounds are short effects and are loaded completely before playback.
- Music is intended for longer tracks and is streamed, allowing playback to
  begin without loading the entire track first.

The importer should preserve this distinction as metadata rather than flatten
all audio into one undifferentiated category.

### Images and optimization

The web publishing pipeline can deduplicate identical images and select
lossless and lossy output formats. Consequently, an exported image may not
retain its original authoring filename, source encoding, or one-file-per-
source-image relationship. Runtime resource identity must not be inferred
from a guessed filename convention.

### Additional project files

The runtime asset manager exposes a read-only `projectFileList` containing
project files from categories including Sounds, Music, Videos, Fonts, Icons &
Screenshots, and Files. The `getProjectFileUrl(url)` method resolves a
project-file reference to a URL that can be fetched directly; the returned URL
may differ from the input, for example by using a `blob:` URL when direct
fetching is unsupported.

The documented asset manager also exposes asynchronous `fetchText`,
`fetchJson`, `fetchBlob`, and `fetchArrayBuffer` helpers. These are
important compatibility clues: consumers should ask the runtime's resolver
for a fetchable resource instead of assuming every logical resource name is
already a browser URL.

## Export options that affect package handling

- **Deduplicate images** can remove duplicate image payloads.
- **Lossless format** and **Lossy format** control image optimization.
- **Offline support** is enabled by default for web exports and allows the
  exported game to continue working offline after its first load.
- Export can be downloaded as a ZIP or written directly to a disk folder.

ImpossibleEngine should record export settings when they are available, but
must not assume offline support or a particular image encoding is enabled.

## Proposed ImpossibleEngine import model

Use a layered import pipeline:

1. **Package scanner**: enumerate the actual export tree, preserve relative
   paths and case, identify the HTML entry point, scripts, media and ancillary
   files, and compute file sizes and hashes.
2. **Export profile detector**: record the declared/importer-selected
   Construct generation and export mode (Folders or legacy Flat) without
   pretending that a heuristic is definitive.
3. **Logical resource catalog**: assign stable engine IDs to imported
   resources while retaining the original relative path, original filename,
   category, MIME type, size, hash and provenance.
4. **Runtime URL resolver**: map logical resources to actual package URLs or
   runtime-provided URLs. Never turn native filesystem paths into web URLs by
   string concatenation.
5. **Backend loader**: decode images, audio and data using target-specific
   implementations. Keep browser URL resolution separate from native file
   access.
6. **Compatibility adapter**: where needed, interpret Construct runtime
   metadata or documented asset-manager interfaces without coupling the
   engine's core asset catalog to minified Construct runtime internals.

A resource record should be able to preserve at least:

- stable ImpossibleEngine resource ID;
- original relative path and case;
- category (image, sound, music, video, font, icon, data, other);
- MIME type and detected encoding;
- source/export provenance and content hash;
- loading policy (eager, lazy, streamed);
- optional alternate encodings and fallback candidates;
- package-relative location, distinct from any resolved runtime URL.

## Importer invariants

- Never confuse the editable project filesystem with the published export.
- Never assume `images/` and `media/` are the only directories.
- Never assume all audio is stored or loaded the same way.
- Never lowercase or normalize away meaningful path case.
- Never derive asset identity from optimized filenames.
- Never assume a browser URL can be constructed from a native path.
- Never assume the exported package is a single static folder: optional
  offline support, worker scripts and exporter changes may add files.
- Preserve unknown files so round-tripping or later compatibility work does
  not silently discard user content.

## Validation plan before claiming full Construct compatibility

Use actual Web/HTML5 exports from multiple Construct 3 versions and settings.
At minimum, capture:
- a minimal game with one sprite, one sound and one music track;
- a game with nested project-file folders and mixed-case filenames;
- an export with image deduplication and lossy/lossless optimization;
- exports with offline support enabled and disabled;
- a project containing video, fonts and arbitrary data files;
- both ZIP and direct-to-folder export output.

Record the complete file tree, representative file signatures/MIME types,
runtime requests and network paths. This empirical fixture set is required
before implementing a parser for undocumented generated runtime metadata.

## Official references

- [Publishing projects](https://www.construct.net/en/make-games/manuals/construct-3/overview/publishing-projects)
- [Importing Construct 2 projects](https://www.construct.net/en/make-games/manuals/construct-3/tips-and-guides/importing-c2-projects) — documents the modern Folders export and legacy Flat mode distinction.
- [AssetManager script interface](https://www.construct.net/en/make-games/manuals/construct-3/scripting/scripting-reference/interfaces/iassetmanager)
- [Project files](https://www.construct.net/en/make-games/manuals/construct-3/project-primitives/files)
- [Project structure](https://www.construct.net/en/make-games/manuals/construct-3/overview/project-structure)
- [Windows wrapper options](https://www.construct.net/en/make-games/manuals/construct-3/interface/dialogs/windows-wrapper-options) — documents `assets.dat` bundling for the Windows wrapper, not the ordinary Web export.

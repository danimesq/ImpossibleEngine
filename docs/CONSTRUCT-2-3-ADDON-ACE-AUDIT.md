# 🌈 Construct 2 / Construct 3 Add-on and ACE Audit

**Status:** documentation audit completed; remaining items are tracked as explicit compatibility/runtime gaps.
**Scope:** reusable engine capabilities only. No game-specific project, title assets or per-game rules are included.

## 🌈 Executive result

The first built-in catalogue (52 plugins, 33 behaviors, 44 effects and 1,008 ACEs) was a useful ImpossibleEngine capability snapshot, not a verified C2 clone. The official C2 manual lists 44 plugins and 26 behaviors, and advertises 70+ visual effects. The catalogue also includes ImpossibleEngine-native abstractions, so raw counts must never be reported as parity.

This audit corrected the most consequential structural differences:

- Added object-scoped C2 compatibility behaviors for Timer, Pathfinding, Jump-thru, No Save and Shadow Caster.
- Removed separate project-global Timer and Pathfinding plugins; C2-style object-attached behaviors are the only user-facing add-ons.
- Moved Blend Mode to the common object/compositor surface and hid/deprecated the old visual-effect alias.
- Made System and common Object surfaces non-insertable picker entries.
- Added C2 `fake_trigger` and `static` ACE condition flags.
- Declared the per-tag Audio DSP chain separately from visual effects.
- Added metadata-only third-party package discovery from the root `add-ons/` folder, with path traversal prevention, duplicate-ID rejection and non-fatal diagnostics.

## 🌈 C2 built-in catalogue

C2 documents 44 built-in plugins and 26 built-in behaviors. The complete lists and the current mapping gaps are in [CONSTRUCT-2-COMPATIBILITY.md](CONSTRUCT-2-COMPATIBILITY.md), sections 8A and 8B.

Known C2 plugin gaps are 9-Patch, File chooser, Geolocation, List and Sprite font, plus provider-specific purchase, advertising, analytics, social and platform plugins which need explicit aliases and availability policies. UI Controls, Advertising, Social and Game Services are useful native abstractions, not proof of identical provider behavior.

Known C2 behavior gaps after the corrections are Custom Movement and Rotate. The Sine-to-Oscillator mapping remains provisional until conformance tests prove phase, period, axes, initial state and expressions. C3 adds further behaviors such as Billboard, Follow, Move To, Tile Movement and Tween; those must be tagged as version-specific, not backported into the C2 inventory.

C2's effect reference advertises 70+ visual effects. ImpossibleEngine currently has 44 effect descriptors. The exact missing effect inventory, effect-specific parameter parity and concrete renderer support remain open. Do not fill the gap with invented effect names.

## 🌈 Add-on categories and attachment model

C2 plugins have three distinct object forms: world objects which are placed on layouts, hidden/object plugins which are not placed directly, and project-wide single-global plugins which have one instance. The System object is already available in every project and is not inserted by the user.

Behaviors are attached to object types, not as independent global systems. They apply to all instances of the object type; a behavior may be enabled or disabled per instance. Behaviors can be attached to Families and inherited by their member object types. The editor must show behavior properties in the object's Properties Bar and expose the behavior's ACEs on the object type.

Effects are visual processing passes, normally attached to objects or layers and to layouts only where the specific effect supports that target. Effect order matters: each effect receives the result from the preceding pass. C2 shader effects require WebGL; unsupported render paths need an explicit fallback or diagnostic. Blend Mode is a common compositor property, not one of those shader effects.

## 🌈 ACE semantics that were missing

The C2 SDK distinguishes true triggers, fake triggers, static conditions, non-invertible conditions, trigger-incompatible conditions, deprecated conditions and looping conditions.

A true trigger is dispatched by the runtime. A fake trigger is merely displayed with trigger-like editor treatment and is still evaluated passively. A static condition runs once for an event rather than once per picked instance, with the condition implementation owning picking. The looping marker does not create the loop by itself; the runtime condition implementation must do that work.

The registry now declares the missing fake-trigger and static flags. A remaining import requirement is to record exact source numeric ACE IDs and positional parameter mappings from verified C2 SDK/source data. Native namespaced string IDs are not a substitute for source compatibility IDs.

Deprecated source ACEs must remain resolvable by old projects while being hidden or marked deprecated in new-event menus. Never recycle an ACE ID.

## 🌈 Audio and media boundaries

C2 Audio has a per-tag ordered signal-processing chain with analyser, compressor, convolution, delay, distortion, filter, flanger, gain, phaser, tremolo and ring modulator nodes. This is separate from visual shader effects and is now described by a dedicated `audioProcessing` metadata block. The DSP execution path and host adapter are still specification-only.

C2 User Media includes capture, speech recognition and speech synthesis. The native ImpossibleEngine split between User Media and Text to Speech is acceptable, but the C2 importer must distribute the source ACEs across both. C3 further separates Speech Recognition, Speech Synthesis and Video Recorder add-ons.

## 🌈 Construct 3 deltas

C3 uses a different add-on SDK and package format. A C3 package uses `.c3addon` and its own manifest, ACE, localization, icon and runtime/editor module layout. A C2 `.c2addon` is not a C3 add-on and neither format is an executable ImpossibleEngine package.

C3 supports themes in addition to plugins, behaviors and effects, and supports WebGL/WebGPU effect implementations (GLSL/WGSL). The native ImpossibleEngine manifest is intentionally its own format. A future importer must translate source metadata and preserve C2 source IDs; it must not load C2/C3 source files as if they were ImpossibleEngine runtime modules.

## 🌈 Third-party add-ons: drop-in folder

The built-in registry remains in `addons/builtin-v1.json`. Third-party packages are discovered from the root `add-ons/` directory, recursively looking for `addon.json`. Each package must contain an `impossible.addon-package` v1 manifest and one valid native add-on descriptor.

The loader validates metadata, safe relative entrypoint/icon paths, dependencies and namespaced IDs. It refuses built-in ID shadowing and records malformed packages as diagnostics while keeping built-ins available. It does not execute JavaScript, Python, native libraries or WASM. Entry points are declarations only until a versioned, capability-scoped runtime ABI and sandbox exist.

See [add-ons/README.md](../add-ons/README.md) and [addon-package-v1.schema.json](../schemas/addon-package-v1.schema.json).

## 🌈 Current verification boundary

All built-in descriptors remain `specification_only` and `engine_runtime = false`. Adding a metadata descriptor does not implement the behavior. A feature is executable only when its ACE resolves to typed IR, the runtime system and host adapter are connected, and conformance tests pass.

The audit and corrected metadata are committed to the open PR. The remaining gaps above are intentionally visible rather than silently counted as completed compatibility.

## 🌈 Official documentation

- C2 [Plugin reference](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference) and [Behavior reference](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference).
- C2 [Effects](https://www.construct.net/en/construct-2/manuals/construct-2/project-primitives/objects/effects), [Effect dialog](https://www.construct.net/en/construct-2/manuals/construct-2/interface/effects-dialog) and [Third-party add-ons](https://www.construct.net/en/construct-2/manuals/construct-2/installing/third-party-addons).
- C2 SDK [Plugin settings](https://www.construct.net/en/make-games/manuals/construct-2/plugin-sdk), [Conditions](https://www.construct.net/en/make-games/manuals/construct-2/plugin-sdk/conditions), [Actions](https://www.construct.net/en/make-games/manuals/construct-2/plugin-sdk/actions) and [Expressions](https://www.construct.net/en/make-games/manuals/construct-2/plugin-sdk/expressions).
- C2 [Timer](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/timer), [Pathfinding](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/pathfinding), [Custom Movement](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/custom-movement), [Jump-thru](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/jump-thru), [No Save](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/no-save) and [Shadow caster](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/shadow-caster).
- C2 [Audio](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/audio) and [User Media](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/user-media).
- C3 [Add-on SDK overview](https://www.construct.net/en/make-games/manuals/addon-sdk), [Add-on format](https://www.construct.net/en/make-games/manuals/addon-sdk/addon-format), [C2 add-on porting](https://www.construct.net/en/make-games/manuals/addon-sdk/porting-from-construct-2) and [C2-to-C3 project changes](https://www.construct.net/en/construct-3/project-primitives/construct-2-compatibility).

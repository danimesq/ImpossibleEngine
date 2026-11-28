# Add-on system and built-in feature catalogue

The built-in catalogue is machine-readable at `addons/builtin-v1.json`. It is
independent from GTK, the future add-on selector and any specific runtime.

For the complete generic legacy compatibility map, source-observed ACE inventory,
behavior coverage and verification boundary, see
[Construct 2 compatibility profile](CONSTRUCT-2-COMPATIBILITY.md).

## Construct 2 and Construct 3 inspiration

Construct 2's `GetPluginSettings()` declares stable plugin identity,
version, description, author, help URL, category, world/object type,
rotatability and flags. Each ACE separately declares a stable ID, list name,
category, Event Sheet display string, description and runtime function name.
Condition flags cover triggers, looping, inversion and deprecation. C2's `cf_looping` displays a looping marker in the editor; the marker does not itself implement iteration. The condition's runtime implementation must perform the loop. C2 also distinguishes fake triggers (`cf_fake_trigger`) from true runtime triggers (`cf_trigger`), and has a static-condition flag for conditions which perform their own picking.

Construct 3 separates `addon.json`, `aces.json`, localization files,
icons and editor/runtime scripts. Plugins, behaviors and effects have
different picker categories. ACEs are grouped into localized categories and
can be highlighted or deprecated without deleting their identity. Effects
declare renderer support, background/depth sampling, cross-sampling,
opaqueness, animation, pre-draw requirements, 3D direct-rendering support,
bounding-box extension and typed shader parameters.

Impossible combines these ideas in one registry, with UI presentation and
runtime/compiler metadata kept separate.

## Picker identity and icons

Every add-on has a stable ID, name, version, description, author, docs
reference, picker category and icon reference. Icon references use a shared
built-in vector icon key or an asset path. They are references, not per-plugin
image files generated in this round. The later Python selector can render
these icons or substitute custom SVG assets without changing add-on identity.

Plugin/object categories, behavior categories, effect categories and ACE
categories are distinct taxonomies. Add-on category answers "where do I find
this object/behavior/effect?". ACE category answers "which group of actions,
conditions or expressions do I want inside it?".

## ACE contract

Each condition/action/expression carries:
- stable namespaced ID;
- display name and help description;
- execution class: trigger, predicate, command or pure;
- typed parameters with label, help text, required flag, defaults and enum choices;
- object-selection policy and state domains written;
- list name, Event Sheet display string, ACE category ID/label and localization key;
- UI markers and flags for trigger, looping, inversion, incompatibility,
  deprecation and highlighting.

Conditions are triggers or predicates. Actions are commands. Expressions are
pure reads and may not perform hidden I/O or mutation. IDs are never recycled.
Once a feature has shipped, future changes should deprecate rather than delete
the ACE identity to preserve old projects.

## Catalogue scope and parity

The current ImpossibleEngine catalogue is a mixed native capability catalogue, not a one-to-one copy of Construct 2 or Construct 3. The corrected built-in snapshot contains 52 plugins, 38 behaviors and 44 visual effects. It intentionally includes ImpossibleEngine-native abstractions. Do not use these counts as a Construct parity claim.

Construct 2's official manual lists 44 built-in plugins and 26 built-in behaviors. Its visual-effects reference advertises 70+ effects. A larger or smaller native count does not establish compatibility; source identifiers, properties, ACE semantics and target support must be audited individually.

The System object is always present in every C2 project and is not inserted by users. ImpossibleEngine exposes its System ACEs as an always-available core surface, not as a picker item. The common Object ACE/property surface is also not a separately insertable object.

## Built-in plugins

System, Object, Sprite, Tiled Background, Text, Button Control, Text Input,
Advanced Text Input, Slider Bar, Progress Bar, Keyboard, Mouse, Touch,
Gamepad (mapped/raw input), Input Actions, Audio, Game Services, Camera, Collision & Picking, Function, Timer,
Date and Clock, Time Manager, Random, Array, Dictionary, JSON, XML, Storage,
HTTP, WebSocket, Multiplayer Sessions, Particles, Tilemap, UI Controls, Video,
SVG Canvas, Embedded Web Frame, CSS Stylesheet, Layout Transition, User Media,
Haptics, Text to Speech, Browser & Platform, Social Integration, Advertising,
Physics World, Pathfinding, 3D Model, Debug & Diagnostics, Timeline and
Flowchart & Dialogue.

## Built-in behaviors

Platform Movement, Eight Direction, Bullet Movement, Vehicle Dynamics, Arcade Car Movement,
Oscillation, Scroll To / Camera Follow, Persist, Anchor to Viewport,
Destroy Outside Layout, Solid / Static Collider, Physics Body, Fade, Flash,
Tween, Rotate To Target, Turret, Line of Sight, Seek, Pursuit & Evade, Arrive,
Wander, Flocking, Path Follower, Drag & Drop, Pin / Follow Object, Orbit,
Spring, Wrap Around Layout, Bounce, Grid Movement, Platform Solid, object-scoped Timer, object-scoped Pathfinding, Jump-thru, No Save and Shadow Caster.

Behaviors are grouped by runtime subsystem, not one crate per behavior:
movement/steering, physics/collision, camera/world bounds, animation/timeline,
AI sensing/navigation and input. A behavior owns per-instance data but consumes
shared engine services.

## Built-in effects

Alpha, Color Matrix, Grayscale, Sepia, Tint, Hue Rotate,
Saturation, Brightness & Contrast, Invert, Threshold/Posterize, Blur,
Gaussian Blur, Directional Blur, Radial Blur, Zoom Blur, Bloom, Glow, Outline,
Drop Shadow, Vignette, Pixelate, Mosaic, Dissolve, Displacement Map, Ripple,
Wave Distortion, Chromatic Aberration, Scanlines, Film Grain/Noise, CRT,
Lens Distortion, Mask, Motion Trail, Distance Field Outline, Fog,
Normal Map Lighting, Texture Tiling, Glass/Refraction, Inner Shadow,
Edge Detection, Posterize, Halftone and Swirl Distortion.

Visual effects form an ordered stack: each pass receives the output of the previous pass. C2 supports effects on objects and layers, and on layouts where the specific effect supports that target. Effects may require WebGL; unsupported renderers need an explicit fallback or diagnostic. Blend Mode is a common compositor property, not a shader effect, and is therefore exposed through the common object/layer blend-mode contract; the old `effect.blend-mode` ID is kept hidden and deprecated for migration only.

Effects specify render-graph stage and compositor constraints. A renderer may
reject an unsupported effect only with an explicit diagnostic; no effect may
silently disappear or be replaced with an unrelated approximation.

## Ownership boundaries

ImpossibleEngine owns add-on metadata, typed ACE contracts, Event Sheet
validation/lowering, gameplay semantics and effect descriptors.
Runtime adapters own concrete movement, collision, physics, animation,
rendering and I/O execution.
RustMultiConsoleFoundation owns cross-platform build/package services and
concrete host/transport adapters that belong below the engine.

C2 behaviors attach to object types, affect all instances of that type, and can be inherited through Families. Per-instance enable/disable state is distinct from attachment. The editor must preserve object-type attachment and Family inheritance rather than treating behaviors as independent project-wide objects.

Timer and Pathfinding are object-attached behaviors, matching Construct 2. ImpossibleEngine does not expose separate project-global `plugin.timer` or `plugin.pathfinding` services. Attach `behavior.timer` or `behavior.pathfinding` to the object type, and use their ACEs/properties. Shared implementation internals may be engine services, but they must not become separate Event Sheet picker objects or user-facing project-global add-ons.

The C2 Audio plugin also owns an ordered per-tag DSP chain (analyser, compressor, convolution, delay, distortion, filter, flanger, gain, phaser, tremolo and ring modulator). This signal-processing chain is distinct from the visual object/layer effect stack.

Gamepad exposes both normalized mapped controls and raw axes/buttons for unusual devices. Text-to-Speech owns synthesis and voice selection, while User Media owns camera/microphone capture, source enumeration, snapshots, canvas recording, recognition and ambient-light readings. Advertising exposes provider-neutral banner placements as well as interstitial and rewarded lifecycles. Game Services owns sign-in, profile, achievements and leaderboards through host adapters. WebSocket is a transport, not multiplayer gameplay. Multiplayer separately
models sessions, rooms, peers, authority, input replication, state replication
and interpolation. Input devices are normalized into semantic actions before
they reach behavior-specific controls.

## Runtime status

See [the runtime implementation roadmap](RUNTIME-IMPLEMENTATION-ROADMAP.md) for the verified implementation gap and ordered work to connect all 1060 ACEs to typed Rust execution, implement the 38 behavior systems, build concrete host adapters, and eventually add GLSL/WGSL-backed effects to the renderer.

All current catalogue entries are explicitly marked `specification_only` and
`engine_runtime = false`. Metadata does not implement a feature. Runtime
support requires implementation, adapter wiring and conformance tests.

## Third-party drop-in packages

Built-ins live in `addons/builtin-v1.json`. User/vendor packages are discovered separately from the repository-root `add-ons/` directory. A package contains an `addon.json` manifest with `format: impossible.addon-package`, `manifestVersion: 1`, and one complete `addon` descriptor. See [the package folder instructions](../add-ons/README.md) and `schemas/addon-package-v1.schema.json`.

The loader validates and registers package metadata, checks relative entrypoint/icon paths and dependency IDs/capabilities, refuses built-in ID shadowing, and records invalid packages as diagnostics without disabling built-ins. It does not execute package code. JavaScript, Python, native and WASM entrypoints are references only until a versioned, capability-scoped runtime ABI and sandbox exist. C2 `.c2addon` and C3 `.c3addon` packages are not directly executable ImpossibleEngine add-ons.

## Python API

```python
from impossible.addons import AddonRegistry

registry = AddonRegistry.load()
print(registry.counts())
sprite = registry.get("plugin.sprite")
ace = registry.find_ace("plugin.sprite.on_animation_finished")
input_plugins = registry.by_category("input", kind="plugin")
steering = registry.search("steering", kind="behavior")
blur = registry.search("blur", kind="effect")
```

## Deliberately deferred

- Python Event Sheet GUI and add-on selector;
- runtime implementation of all descriptors;
- GLSL/WGSL shaders and renderer backend passes;
- game-specific projects or reference-game assets;
- generic legacy-project importer.

## Next gates

1. Compiler-side ACE resolver to typed Event Sheet IR.
2. Scheduler, trigger/loop context, object picking and lifecycle.
3. Movement, collision and physics conformance fixtures.
4. Host adapter capability negotiation.
5. Effect render graph, shader variants, alpha policy and sampling tests.
6. Registry migrations, localization tooling and deprecation workflow.

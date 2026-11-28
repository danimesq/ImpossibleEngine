# 🌈 Construct 2 compatibility profile

This document defines a generic compatibility target for importing legacy Construct 2 projects. It contains no project-specific gameplay rules or assets. The compatibility layer translates legacy object/plugin/behavior identifiers into ImpossibleEngine's native, stable add-on IDs.

## 🌈 1. Audited source surface

The audited C2 project snapshot identifies:

| Surface | Inventory |
|---|---:|
| Object types | 164 |
| Declared plugins | 25 |
| Declared behaviors | 7 |
| Declared effects | 1 |
| Event-sheet files | 23 |
| `<event-block>` nodes | 151 |
| Condition nodes | 190 |
| Action nodes | 436 |
| Animation declarations | 231 |

Condition/action totals count occurrences in the source XML, not distinct ACE definitions. Event sheets use includes, so import must preserve include relationships instead of flattening them into unrelated duplicate events.

## 🌈 2. Plugin compatibility map

The left column is the legacy C2 plugin identifier. The right column lists the generic ImpossibleEngine add-on(s) that provide its native object/runtime contract.

| Legacy plugin identifier | ImpossibleEngine add-on |
|---|---|
| `AJAX` | `plugin.http` |
| `AdvTextBox` | `plugin.advanced-text-input` |
| `Audio` | `plugin.audio` |
| `CJSAds` | `plugin.advertising` (banner placement through a provider adapter) |
| `Browser` | `plugin.browser` + `plugin.haptics` |
| `Button` | `plugin.button-control` |
| `C2WebSocket` | `plugin.websocket` |
| `CAMFTimeManager` | `plugin.time-manager` |
| `CSS_import` | `plugin.css-styles` |
| `Clock` | `plugin.clock` |
| `Function` | `plugin.function` |
| `gamepad` | `plugin.gamepad` |
| `googleplay` | `plugin.game-services` (provider-neutral identity, achievements and leaderboards) |
| `HTML_iFrame_Pode` | `plugin.embedded-frame` |
| `Keyboard` | `plugin.keyboard` |
| `LocalStorage` | `plugin.storage` |
| `Mouse` | `plugin.mouse` |
| `SVGCanvas` | `plugin.svg-canvas` |
| `Sprite` | `plugin.sprite` + common `plugin.object` |
| `Text` | `plugin.text` |
| `TextBox` | `plugin.text-input` |
| `TiledBg` | `plugin.tiled-background` |
| `Touch` | `plugin.touch` |
| `UserMedia` | `plugin.user-media` + `plugin.text-to-speech` |
| `WebStorage` | `plugin.storage` |
| `XML` | `plugin.xml` |
| `hmmg_layoutTransition` | `plugin.layout-transition` |
| `progressbar` | `plugin.progress-bar` |
| `sliderbar` | `plugin.slider` |
| `video` | `plugin.video` |

The generic controls are intentionally distinct add-ons. A button, text input, advanced text input, slider and progress bar may share host rendering infrastructure, but they must not collapse into one undifferentiated control type: their properties, editor pickers, parameter types and ACEs differ.

## 🌈 3. Behaviors and effects

| Legacy behavior/effect | ImpossibleEngine add-on | Compatibility requirements |
|---|---|---|
| `Anchor` | `behavior.anchor` |
| `Car` | `behavior.car-movement` |
| `bound` | `behavior.bound-to-layout` |
| `EightDir` | `behavior.eight-direction` | Direction modes, default/custom controls, simulated controls, speed, acceleration, deceleration, enable/disable, direction and speed queries |
| `Fade` | `behavior.fade` | Activate-at-start, fade-in/wait/fade-out phases, destroy-after-fade, stage-completion triggers, restart/start and timing setters |
| `Persist` | `behavior.persist` | Retain instance state, instance variables, created/destroyed state and identity while changing layouts |
| `Pin` | `behavior.pin` | Pin/unpin, position-and-angle/position-only/angle-only/rope/bar modes, pinned state and pinned UID |
| `Platform` | `behavior.platform` | Ground/fall/jump state, jump trigger, simulated controls, max speed, jump strength, acceleration/deceleration, gravity and input enablement |
| `scrollto` | `behavior.scroll-to` | Center/follow target, enable/disable and camera shake |
| `solid` | `behavior.solid` | Solid enabled state, enable/disable and collision response |
| `overlay` | `effect.blend-mode` |
| `swirl` | `effect.swirl` | Radial distortion with editable center, radius, angle and quality |

Behaviors are attached to object types and extend the object's ACE list and Properties Bar. They are not independent gameplay modules or hard-coded rules. This matches the C2 behavior model.

## 🌈 3A. Additional 2D interaction and platform capability profile

The native catalogue covers a broad, source-independent set of capabilities that commonly appear together in 2D projects. No source project identity, per-game rules, artwork or game-specific project container is part of this profile.

| Capability family | Native contract |
|---|---|
| Arcade vehicle movement | Dedicated `behavior.car-movement`, separate from general vehicle dynamics; signed speed, acceleration/deceleration, steering, drift recovery, friction and simulated controls |
| Viewport anchoring | `behavior.anchor` with enabled state, viewport-edge constraints and margins; anchoring is resolved against the viewport rather than the scrolling world |
| Layout bounds | `behavior.bound-to-layout` supports edge-based and origin-based bounds |
| Solid response | `behavior.solid` exposes collision participation and enabled state; simple solid contacts remain distinct from rigid-body physics |
| Repeating textures | Tiled surfaces support texture offset/scale, source dimensions and asynchronous URI-backed image replacement |
| Speech | `plugin.text-to-speech` supports language, voice URI, volume, rate, pitch and utterance lifecycle; `plugin.user-media` separately covers speech recognition and capture |
| Banner advertising | `plugin.advertising` exposes banner-specific show/hide/position operations alongside generic interstitial and rewarded placements |
| Game services | `plugin.game-services` provides asynchronous player identity, authentication, achievement and leaderboard contracts without binding projects to one provider |
| Input | Keyboard, pointer, touch and gamepad inputs can be normalized into semantic actions while retaining raw device-specific state and analog values |
| Display and layers | Logical viewport/orientation/scale policy, loader layout, layer parallax/zoom/transparency/opacity/blend modes and stable instance transforms |
| Event execution | OR condition blocks, groups, includes, global/instance variables, trigger-once state and non-blocking Wait continuations |
| Presentation | Sprite animations, per-frame durations, hotspots, collision polygons, text/font properties, blend modes, layers, z-order and per-instance transforms |

These contracts describe capabilities, not a sample game. They belong in reusable add-ons, runtime services, platform adapters and anonymous conformance fixtures. Do not create one native project file per reference title.

The arcade movement behavior is intentionally distinct from generic 3D or rigid-body vehicle dynamics. It models a controllable 2D object with forward speed, steering and drift state. Its movement system consumes collision contacts from the shared collision world and must remain deterministic under the configured simulation delta policy.

Platform services are asynchronous. Authentication, profile, achievement, leaderboard, speech, media and advertising results re-enter the Event Sheet scheduler through typed completion/failure events. A request must not block a simulation tick or report success before its host adapter confirms the operation.

## 🌈 4. Event-sheet ACE compatibility

The following are the source-observed ACE operations that the importer/compiler must resolve to native contracts. Some are provided by the common object/system surface rather than by an object's specialized plugin.

### System and common object surface

- Conditions: layout start, every tick, compare variable, compare two values, else, trigger once while true, collision/overlap, on-screen, visible and instance-variable comparisons.
- Actions: set variable, add/subtract, wait, change layout, change to next/previous layout, set position/X/Y, visibility, opacity, layer order, effect enablement, and set position relative to another object.
- Object expressions and picking must preserve the selected instance set through nested events, loops and subevents. A condition cannot merely return a boolean while losing the source editor's picked-instance semantics.

### Specialized plugins

| Plugin family | Source-observed ACE surface |
|---|---|
| HTTP/AJAX | Request URL and completion trigger, with response data and request tag available to expressions |
| Audio | Play, play by name, play at object, set listener object, stop, stop all, and playing-state query |
| Gamepad | Connection lifecycle, mapped and raw buttons/axes, analog dead zones, multiple devices and pressure-aware button values |
| User Media / speech | Permission lifecycle, source enumeration, capture/snapshot/canvas recording, ambient light and speech recognition; synthesis and voice enumeration use the separate Text-to-Speech contract |
| Game services | Sign-in lifecycle, player profile, achievement metadata/progression, leaderboard requests/submission and indexed results |
| Advertising | Banner lifecycle and visibility/position operations alongside interstitial and rewarded placements |
| Tiled Background | Repeating texture transform, source dimensions and asynchronous image-URL loading |
| Browser/platform | Online state, went-online/went-offline triggers and vibration |
| Sprite | Set animation, set mirrored, animation completion, frame changes, collision geometry and common transforms |
| Text | Set text, set web font, text measurement |
| Text input | Compare text, text-changed trigger, set placeholder and focus |
| Keyboard | Key pressed and key-down checks |
| Mouse | Object clicked and cursor-over-object |
| Touch | Any-touch-start, touched-object and is-touching-object, with touch identity/coordinates |
| Storage | Set local value, compare stored value as text, read local value |
| XML | Load XML and XPath `StringValue`/node-value access |
| Function | On function, call function, set return value, parameter access and parameter count |
| Time manager | Start/count/time-counter action and named time-value expression |
| Layout transition | Entrance/exit transition actions and transition-ended/completed conditions |
| Progress bar | Set progress |
| SVG canvas, CSS, embedded frame, clock, slider and video | First-class object/add-on contracts and importable properties; preserve source configuration even where no event-sheet ACE invocation was found in the audited snapshot |

ImpossibleEngine's registry now includes stable ACE declarations for the source-observed operations and generic contracts for all declared object/plugin types. Legacy names are aliases at the import boundary; native IDs remain namespaced and stable.

## 🌈 5. Import and editor requirements

1. Resolve each legacy plugin/behavior/effect identifier through an explicit compatibility map. Never infer an add-on from the object's display name.
2. Preserve object type, instance, layout/layer, animation/frame, hotspot, collision polygon, properties, instance variables, behavior properties, effect settings and persistent IDs.
3. Preserve the Event Sheet tree: includes, event order, conditions, actions, subevents, groups, disabled blocks, local/global variables, comments, parameters, and source UIDs.
4. Resolve every condition/action/expression to a typed ACE contract. Preserve parameter types, defaults, enum values, source expressions, trigger/predicate classification and selection policy.
5. Preserve asynchronous boundaries. HTTP/WebSocket/storage completion callbacks must re-enter the scheduler as events, not block a simulation tick.
6. Preserve form-control layering and focus rules. Native controls can be rendered by the host above the canvas while remaining anchored to layout coordinates.
7. Keep unknown plugin data losslessly in the project model and show a clear unsupported-extension diagnostic. Never silently discard an unknown ACE or substitute an unrelated operation.
8. Keep a compatibility report per import with exact, adapted, metadata-only and unsupported status for each source item.

## 🌈 6. Verification boundary

This profile is a declaration and import-compatibility target, not a claim of finished runtime support. Every add-on in `addons/builtin-v1.json` remains marked `specification_only` with `engine_runtime = false`. The Rust runtime still needs the generic typed Event Sheet IR, ACE resolver, scheduler, picking model, lifecycle/state store, concrete host adapters and conformance tests before these declarations can be executed.

The audited project snapshot contains third-party extension identifiers, but it does not include the corresponding original extension source packages. Therefore the exact complete ACE menus of those third-party extensions cannot be reconstructed from the project XML alone. This profile includes every source-observed operation and a generic capability contract for each declared object type; exact parity with undocumented extension ACE menus requires their original `.c2addon` packages or source archives.

## 🌈 7. Official C2 semantics consulted

- [Plugin reference](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference)
- [Behavior reference](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference)
- [Behaviors and ACE inheritance](https://www.construct.net/en/construct-2/manuals/construct-2/project-primitives/objects/behaviors)
- [Sprite](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/sprite)
- [Text](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/text)
- [Text box](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/textbox)
- [Button](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/button)
- [Slider bar](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/slider-bar)
- [Progress bar](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/progress-bar)
- [AJAX](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/ajax)
- [Audio](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/audio)
- [WebStorage](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/webstorage)
- [XML](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/xml)
- [Function](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/function)
- [Touch](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/touch)
- [User Media](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/user-media)
- [Gamepad](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/gamepad)
- [Google Play](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/google-play)
- [Tiled Background](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/tiled-background)
- [Car behavior](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/car)
- [Anchor behavior](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/anchor)
- [Bound to Layout behavior](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/bound-layout)
- [Scroll To behavior](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/scroll)
- [Solid behavior](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/solid)
- [Browser](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/browser)
- [Persist](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/persist)
- [Platform](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/platform)
- [8 Direction](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/8-direction)
- [Solid](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/solid)
- [Pin](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/pin)
- [Scroll To](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/scroll-to)
- [Fade](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/fade)

## 🌈 8. Official Construct 2 built-in inventory and correction results

The compatibility mapping above is based on one imported project snapshot (25 plugin identifiers, 7 behaviors and 1 effect). It is not the complete built-in C2 catalogue. The official C2 manual lists 44 plugins and 26 behaviors, and its visual-effects reference advertises 70+ effects.

### 🌈 8A. Construct 2 plugin inventory (44)

9-Patch, AdMob, AJAX, Array, Audio, Browser, Button, Dictionary, Facebook, File chooser, Function, Game Center, Gamepad, Geolocation, Google Play, iAd, IAP, Intel AGI, Keyboard, List, Local Storage, Mouse, Multiplayer, NW.js, Particles, Progress bar, pubCenter, Scirra Arcade, Shadow light, Slider bar, Sprite, Sprite font, Text, Textbox, Tiled Background, Tilemap, Touch, Twitter, User Media, Video, WebSocket, WebStorage, Windows Store and XML.

The native catalogue is broader but still has explicit gaps in one-to-one legacy coverage: 9-Patch, File chooser, Geolocation, List and Sprite font do not yet have dedicated matching native descriptors. IAP and platform/provider-specific services (AdMob, iAd, pubCenter, Intel AGI, Scirra Arcade, Windows Store, Game Center and Google Play) need explicit provider/availability aliases rather than silent claims of parity. Existing UI Controls, Social, Advertising and Game Services abstractions are useful building blocks, but are not automatically identical to each source plugin.

### 🌈 8B. Construct 2 behavior inventory (26)

8 Direction, Anchor, Bound to layout, Bullet, Car, Custom Movement, Destroy outside layout, Drag & Drop, Fade, Flash, Jump-thru, Line-of-sight, No Save, Pathfinding, Persist, Physics, Pin, Platform, Rotate, Scroll to, Shadow caster, Sine, Solid, Timer, Turret and Wrap.

The audit added native object-scoped contracts for Timer, Pathfinding, Jump-thru, No Save and Shadow Caster. The following remain open parity gaps or require a more exact equivalence review: Custom Movement and Rotate; `behavior.oscillator` is not assumed to be a drop-in Sine replacement without phase, period, movement-axis and initial-state conformance tests. C3 additionally documents Billboard, Follow, Move To, Tile Movement and Tween behaviors; these are version-specific additions rather than C2 built-ins.

### 🌈 8C. Corrections to previous classifications

- `behavior.timer` is the sole user-facing Timer add-on and attaches to object types, matching C2's per-object behavior. C2 Timer's ACE surface is On timer, Start timer, Stop timer, CurrentTime, Duration and TotalTime; no project-global Timer plugin is exposed.
- `behavior.pathfinding` is the sole user-facing Pathfinding add-on and attaches to object types, matching C2. It models object-scoped navigation, obstacle-map properties, path movement and speed/acceleration/rotation controls. The project-global Pathfinding plugin is removed.
- Blend Mode is not a C2 visual effect. It is a common compositor setting which also works without WebGL. The old `effect.blend-mode` ID remains as a hidden/deprecated migration alias; new projects use common object/layer blend-mode state.
- The System object is always present in a C2 project. Its ACEs are core Event Sheet operations, not a user-inserted object. The common Object surface is likewise inherited by object types rather than inserted as its own placed instance.
- C2 behaviors attach to object types; they affect each instance of that type and can be attached to Families. Per-instance enabling/disabling does not change the attachment scope.
- C2 Audio signal-processing effects are a separate per-tag audio DSP chain, not visual shader effects. The built-in catalogue now declares that separate chain as metadata, but its DSP runtime/host adapter is not implemented.
- C2 User Media includes camera/microphone, speech recognition and speech synthesis. ImpossibleEngine may keep capture/recognition in User Media and synthesis in Text to Speech, but a C2 import must map the source plugin's ACEs across both native add-ons.
- C2's visual-effects reference advertises 70+ effects. ImpossibleEngine's 44 effect descriptors are a native subset/catalogue, not complete C2 effect parity. Per-effect parameters, background blending, target surface, render ordering and fallback support need individual coverage.

### 🌈 8D. ACE metadata and runtime semantics

The C2 SDK distinguishes true triggers, fake triggers, static conditions, non-invertible conditions, trigger-incompatible conditions, deprecated conditions and looping conditions. The registry now carries explicit `fake_trigger` and `static` flags alongside its existing metadata.

- A true trigger is dispatched by the runtime and has trigger ordering/placement constraints.
- A fake trigger is visually presented as a trigger in the editor but remains a passively evaluated condition.
- A static condition runs once for the event rather than once per picked instance; its implementation owns any picking.
- The looping marker is editor metadata. The condition implementation must actually perform the loop.
- Deprecated ACEs should disappear from new-event menus where appropriate, but remain resolvable for old projects. IDs must never be recycled.
- C2 ACE and parameter IDs are numeric/positional source identifiers. The current registry's namespaced IDs are stable native IDs, but the importer still needs an explicit source-ID/parameter-order mapping populated from verified C2 SDK metadata. Do not infer those numbers from display names or array order.

### 🌈 8E. Effects and renderer boundaries

C2 visual effects form an ordered chain; effects are applied to an object, layer or (where compatible) layout. Background-sampling effects have additional target constraints. C2 requires WebGL for shader effects, so disabling WebGL changes what can be rendered. ImpossibleEngine currently describes renderer intent for WebGL 2/WebGPU, but an empty `supported_renderers` array means no concrete shader backend is declared as supported. Keep unsupported effects visible in project diagnostics; never silently substitute a different pass.

### 🌈 8F. Official C2/C3 documentation references

- C2 [Plugin reference](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference) and [Behavior reference](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference).
- C2 [Effects](https://www.construct.net/en/construct-2/manuals/construct-2/project-primitives/objects/effects), [Effect dialog](https://www.construct.net/en/construct-2/manuals/construct-2/interface/effects-dialog) and [Third-party add-ons](https://www.construct.net/en/construct-2/manuals/construct-2/installing/third-party-addons).
- C2 SDK [Plugin settings](https://www.construct.net/en/make-games/manuals/construct-2/plugin-sdk), [Conditions](https://www.construct.net/en/make-games/manuals/construct-2/plugin-sdk/conditions), [Actions](https://www.construct.net/en/make-games/manuals/construct-2/plugin-sdk/actions) and [Expressions](https://www.construct.net/en/make-games/manuals/construct-2/plugin-sdk/expressions).
- C2 [Timer](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/timer), [Pathfinding](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/pathfinding), [Custom Movement](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/custom-movement), [Jump-thru](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/jump-thru), [No Save](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/no-save) and [Shadow caster](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/shadow-caster).
- C2 [Audio](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/audio) and [User Media](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/user-media).
- C3 [Add-on SDK overview](https://www.construct.net/en/make-games/manuals/addon-sdk), [Add-on format](https://www.construct.net/en/make-games/manuals/addon-sdk/addon-format), [C2 add-on porting](https://www.construct.net/en/make-games/manuals/addon-sdk/porting-from-construct-2) and [C2-to-C3 project changes](https://www.construct.net/en/construct-3/project-primitives/construct-2-compatibility).

## 🌈 9. Third-party extension loading boundary

Construct 2 installs third-party add-ons through `.c2addon` packages and its legacy JavaScript SDK. Construct 3 uses a separate `.c3addon` package and SDK. ImpossibleEngine does not execute either format directly.

ImpossibleEngine's own third-party package discovery uses the root `add-ons/` directory and `impossible.addon-package` v1 manifest. The current implementation registers validated metadata only; entrypoint references are not executed. See [Third-party add-ons](../add-ons/README.md).

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
| `Browser` | `plugin.browser` + `plugin.haptics` |
| `Button` | `plugin.button-control` |
| `C2WebSocket` | `plugin.websocket` |
| `CAMFTimeManager` | `plugin.time-manager` |
| `CSS_import` | `plugin.css-styles` |
| `Clock` | `plugin.clock` |
| `Function` | `plugin.function` |
| `HTML_iFrame_Pode` | `plugin.embedded-frame` |
| `Keyboard` | `plugin.keyboard` |
| `Mouse` | `plugin.mouse` |
| `SVGCanvas` | `plugin.svg-canvas` |
| `Sprite` | `plugin.sprite` + common `plugin.object` |
| `Text` | `plugin.text` |
| `TextBox` | `plugin.text-input` |
| `TiledBg` | `plugin.tiled-background` |
| `Touch` | `plugin.touch` |
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
| `EightDir` | `behavior.eight-direction` | Direction modes, default/custom controls, simulated controls, speed, acceleration, deceleration, enable/disable, direction and speed queries |
| `Fade` | `behavior.fade` | Activate-at-start, fade-in/wait/fade-out phases, destroy-after-fade, stage-completion triggers, restart/start and timing setters |
| `Persist` | `behavior.persist` | Retain instance state, instance variables, created/destroyed state and identity while changing layouts |
| `Pin` | `behavior.pin` | Pin/unpin, position-and-angle/position-only/angle-only/rope/bar modes, pinned state and pinned UID |
| `Platform` | `behavior.platform` | Ground/fall/jump state, jump trigger, simulated controls, max speed, jump strength, acceleration/deceleration, gravity and input enablement |
| `scrollto` | `behavior.scroll-to` | Center/follow target, enable/disable and camera shake |
| `solid` | `behavior.solid` | Solid enabled state, enable/disable and collision response |
| `swirl` | `effect.swirl` | Radial distortion with editable center, radius, angle and quality |

Behaviors are attached to object types and extend the object's ACE list and Properties Bar. They are not independent gameplay modules or hard-coded rules. This matches the C2 behavior model.

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
- [Browser](https://www.construct.net/en/construct-2/manuals/construct-2/plugin-reference/browser)
- [Persist](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/persist)
- [Platform](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/platform)
- [8 Direction](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/8-direction)
- [Solid](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/solid)
- [Pin](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/pin)
- [Scroll To](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/scroll-to)
- [Fade](https://www.construct.net/en/construct-2/manuals/construct-2/behavior-reference/fade)

# Generic 2D interaction and platform capability profile

This profile records reusable engine capabilities needed by a broad class of 2D projects. It describes engine features only. It is not a game design, sample project, project migration or per-title implementation.

## Capability inventory

| Domain | Required capability | Native contract |
|---|---|---|
| Object identity | Stable object and instance identity | Object types, persistent instance handles, instance variables and selection context |
| Scene lifecycle | Initialization, scene entry/exit and transitions | System lifecycle triggers and queued scene operations |
| Event execution | Groups, includes, nested events and OR conditions | Ordered Event Sheet tree, explicit group state and source-mapped scheduler |
| Timing | Frame/tick, waits, delayed continuations and time scaling | Simulation clock, deterministic scheduler and non-blocking Wait |
| Input | Keyboard, pointer, touch and gamepad | Per-device plugins plus semantic Input Actions |
| Analog input | Axis values and dead zones | Typed axes, dead-zone settings and stable device identity |
| 2D movement | Arcade car-style forward movement and steering | `behavior.car-movement` |
| Camera | Follow target, look-ahead, smoothing and shake | Camera plugin and `behavior.scroll-to` |
| Viewport layout | Anchor objects to viewport edges and margins | `behavior.anchor` |
| World bounds | Keep origin or full object geometry inside layout bounds | `behavior.bound-to-layout` |
| Collision | Solid obstacles, collision polygons and picked-object semantics | Collision system, `behavior.solid` and typed picking |
| Animation | Named animations, frame timing, playback speed and frame triggers | Sprite animation data and runtime animation state |
| Tiled surfaces | Repeat textures, offset/scale sampling and URL-backed images | Tiled Background plugin with asynchronous asset lifecycle |
| Text | Dynamic text, font selection, alignment, wrapping and measurement | Text plugin and font asset pipeline |
| Audio | Playback, looping, tags, positional sound and completion events | Audio plugin and host audio adapter |
| Speech | Voice enumeration and per-utterance language/voice/volume/rate/pitch | Text-to-Speech plugin |
| Recognition and capture | Camera/microphone permission, speech recognition and transcript events | User Media plugin and host media adapter |
| Storage | Persistent and session-scoped values | Storage plugin and host storage adapter |
| Network | HTTP request, progress, response and errors | HTTP plugin with async scheduler callbacks |
| Structured data | XML loading, node/attribute lookup and iteration | XML plugin |
| Game services | Sign-in, profile, achievements and leaderboards | Game Services plugin and provider adapter |
| Advertising | Banner lifecycle and placement, interstitial and rewarded events | Advertising plugin and provider adapter |
| Platform services | Focus, online/offline, fullscreen, orientation, clipboard, share and vibration | Browser & Platform and Haptics adapters |
| Visual compositing | Opacity and blend modes | Object properties and renderer effect stack |
| Localization | Runtime language selection and locale-aware speech | Localization catalog and Text-to-Speech host adapter |

## Architecture rules

1. Keep capabilities reusable. A feature belongs in a plugin, behavior, effect, core subsystem or host adapter, never in an engine rule named after one game.
2. Keep project files user-authored. Do not add a new `.ieproj` merely to preserve a reference project's title, screens, assets, levels, object names or gameplay rules.
3. Use anonymous conformance fixtures. Each fixture should isolate a contract, for example input-axis normalization, non-blocking waits, viewport anchoring, car steering, speech callback ordering or leaderboard result decoding.
4. Keep source compatibility at the import boundary. Legacy plugin names must resolve to stable ImpossibleEngine IDs; the runtime must not depend on legacy names.
5. Keep asynchronous work asynchronous. Media, speech, storage, HTTP, advertising and game-services callbacks must re-enter the scheduler as typed events.
6. Negotiate host capabilities. Unsupported platform services must produce explicit diagnostics. They must not silently report success or become no-op implementations.
7. Preserve deterministic simulation. Device sampling and host callbacks are timestamped or queued; gameplay state changes occur at documented scheduler boundaries.
8. Keep external secrets out of project data and generated source. Provider credentials belong in host/build configuration.

## Conformance fixture plan

- `fixture_input_keyboard_pointer_gamepad_001`: semantic action mapping, analog dead zones and device disconnect.
- `fixture_event_or_include_wait_002`: OR branches, include ordering, groups and non-blocking continuation.
- `fixture_car_movement_solid_contact_003`: acceleration, deceleration, steering, drift recovery and solid collision.
- `fixture_viewport_anchor_bounds_004`: resize, viewport margins and edge/origin bounds.
- `fixture_tiled_texture_async_005`: image URI success/failure and texture offset/scale preservation.
- `fixture_speech_locale_voice_006`: voice selection, locale, pause/resume and completion/error ordering.
- `fixture_game_services_async_007`: sign-in, achievement update, leaderboard request and failure callbacks.
- `fixture_banner_placement_008`: banner load, show, move, hide and unsupported-provider reporting.

These fixture names describe isolated behaviors and are not project or game names.

## Current implementation boundary

The built-in registry defines editor/compiler contracts. It does not make the new add-ons executable. The current catalogue marks all entries as `specification_only` and `engine_runtime = false`. Runtime support requires a typed compiler binding, executable implementation, required host adapter and passing conformance tests for each supported target.

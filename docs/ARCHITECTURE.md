# Impossible Engine architecture notes

## Frontend
The first GUI prototype uses GTK 3, PyGObject, GtkBuilder and GTK CSS. The
editor shell is replaceable and must not own project semantics.

## Project model
Project data, Event Sheets, logical objects, assets, platform profiles and
sparse platform overrides are represented independently from GTK.

## Add-on registry
Built-in plugins, behaviors and effects live in `addons/builtin-v1.json` and
are validated by `impossible.addons`. The registry includes picker categories,
icon references, ACE category groups, localization keys, typed parameters,
execution kinds, selection policies, state writes and render-pipeline
constraints.

Plugin picker categories, behavior categories, effect categories and ACE
categories are different concepts. Add-on category helps find the object,
behavior or effect. ACE category organizes commands inside Event Sheets.
The Python GUI and add-on selector must consume the shared registry rather
than duplicate definitions in widget code.

All current descriptors report `specification_only`. The registry is an
editor/compiler contract, not proof of runtime implementation.

## Runtime subsystems
Do not create one crate per behavior. Group behaviors by reusable runtime
subsystems:
- movement and steering;
- collision, picking and physics;
- camera and world bounds;
- animation, timeline and tween;
- AI sensing and navigation;
- input normalization and semantic action maps;
- renderer effects and render graph;
- media and host services.

Behaviors own per-instance state but consume shared engine services.
Plugins expose capabilities and ACEs. Host adapters provide platform I/O.

## Foundation boundary
ImpossibleEngine owns add-on metadata, ACE resolution, typed Event Sheets,
gameplay semantics and effect descriptors. RustMultiConsoleFoundation owns
portable build/package services and concrete host/transport adapters below
the engine.

Separate networking layers into raw transport, session/signalling, rooms and
peers, authority, input replication, state replication and interpolation.
WebSocket is not a multiplayer implementation by itself.

## Validation
Keep fixtures for:
- add-on/ACE IDs, versioning, categories, icon references and localization;
- parameter typing, enum options, defaults and bounds;
- trigger/loop semantics, event order, object picking and mutation lifecycle;
- Platform, Eight Direction, Bullet, Vehicle and Oscillation;
- collision polygons, hotspots, frame geometry, solids and rigid bodies;
- timers, continuations, RNG and animation lifecycle;
- effect stack order, alpha, background/depth sampling and target diagnostics;
- input hotplug, multiple controllers, deadzones and remapping;
- explicit host-service errors for storage, audio, video, HTTP and networking.

No source construct may disappear silently. Descriptor presence is not
implementation: features become runtime-supported only after code, adapters
and conformance tests.

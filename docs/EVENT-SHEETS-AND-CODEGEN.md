# Event Sheets and deterministic Rust code generation

## Goal

Event Sheets are a declarative gameplay language, not strings of Rust and not
free-form expressions. The project JSON is the source of truth. The exporter
must either produce a fully validated build or fail with actionable diagnostics;
it must never silently guess what an event means.

The first executable target is Bevy. The project format and compiler frontend
must remain engine-neutral so a future runtime adapter can consume the same
validated intermediate representation.

## Compilation pipeline

1. **Parse** JSON while preserving array order and source locations.
2. **Validate schema** and reject unknown schema/compiler features.
3. **Resolve symbols**: object IDs, component/property IDs, event IDs and asset
   IDs must resolve exactly once.
4. **Type-check** every condition and action against the registry. For example,
   `score.player` is an integer, `ball.velocity.x` is a fixed-point number,
   and `Ball` is an object type, not a string expression.
5. **Lower** to a typed, engine-neutral intermediate representation (IR).
6. **Validate determinism**: reject wall-clock reads, unseeded randomness,
   unordered iteration, implicit floating-point gameplay math and unsupported
   side effects in deterministic simulation events.
7. **Generate Rust** using stable symbol names, stable ordering and explicit
   runtime calls. Do not emit source by concatenating user-provided expressions.
8. **Format and compile** generated Rust, then run behavior tests and golden
   output tests.

The generated source should include the project schema version, compiler
version, target profile and a content hash. Identical normalized input plus
identical compiler version and target configuration must produce byte-identical
output.

## Event Sheet document model

An Event Sheet is a first-class project resource and the sole container of its
root events. Events do not live in a project-global event collection and are
not independently attached to sheets after parsing. The project owns an ordered
`event_sheets` collection; each sheet owns an ordered `events` tree. Each event
owns its conditions, actions and nested `children` events.

A standard event contains a single ordered condition list. Trigger conditions
are entries in that same list, distinguished by `kind: "trigger"`; ordinary
conditions use `kind: "condition"`. There is no parallel top-level `trigger`
field. This keeps the Construct-style event structure intact and allows the
editor to preserve condition order. An event's `type` identifies its node kind;
`standard` is the initial supported type. Future node types (for example,
groups, includes, loops and else branches) must receive explicit schema and
compiler semantics rather than being approximated as standard events.

The hierarchy is therefore:

`Project -> Event Sheets -> Events -> Conditions / Actions / Child Events`.

## Event execution semantics

- Event Sheets are compiled in project declaration order; root events and child
  events retain their declaration order.
- Conditions within one event are evaluated left-to-right. All conditions must
  pass for the event's actions to run; trigger conditions participate in this
  ordered condition list and are not stored in a separate trigger property.
- Actions execute left-to-right and complete in that order.
- Child events execute only in the documented parent-event context and after
  the parent event's conditions pass; the exact context inheritance rules must
  be versioned before adding subevent types.
- Gameplay events run on a numbered fixed simulation tick, never once per
  rendered frame.
- Input is sampled into a tick-indexed input frame. Replays record those frames.
- Collision facts are collected during the physics phase and consumed in a
  documented collision-event phase. Collision pair ordering is canonicalized
  by stable object instance IDs.
- Entity creation/destruction and other structural changes are queued and
  applied at a defined phase boundary, not halfway through an event list.
- A disabled event is omitted from the IR. An unknown operation is a compile
  error, never a no-op.

The initial Pong simulation should use integer/fixed-point gameplay values.
Bevy transforms and rendering may use floats as presentation output, but they
must not feed back into authoritative gameplay state. This reduces platform
floating-point drift and makes replay tests meaningful. Fixed timestep alone
does not guarantee bit-identical results across platforms.

## JSON shape

A project contains:
- `schema_version`: version of the authoring data format.
- `compiler`: minimum compiler contract and deterministic mode.
- `runtime`: backend adapter and fixed simulation rate.
- `objects`: stable logical object IDs and typed components/properties.
- `input_maps`: named, platform-resolvable input actions.
- `event_sheets`: ordered Event Sheet resources; each resource owns its ordered
  event tree, and each event owns its conditions, actions and child events.
- `assets`: logical asset IDs with platform variants.

Use stable string IDs for references. Display names are editable and are never
used as generated Rust identifiers. Array order is meaningful; object-key order
is not. The normalizer emits canonical JSON before hashing.

## Initial plugin-owned operation registry

The compiler discovers operations from plugins, not a hard-coded catalog. Initial split:
- System triggers: `game.started`, `simulation.fixed_tick`, `score.reached`; conditions `game.state_is`, `score.at_least`; actions `game.set_state`, `score.add`, `game.restart_round`.
- Input condition: `input.axis_nonzero`.
- Collision trigger and condition: `collision.entered`, `collision.involves`.
- Audio action: `audio.play`.
- Demo gameplay operations: `paddle.move_axis`, `paddle.track_ball`, `ball.spawn`, `ball.bounce_from_paddle`, `ball.bounce_from_wall`, `ball.despawn`.

Each operation has a versioned schema, typed arguments, a defined execution
phase, and a Rust lowering implementation. Do not expose arbitrary Bevy system
names or arbitrary Rust snippets in project JSON.

## Bevy adapter boundary

The Bevy adapter maps logical objects to ECS entities and typed components.
Generated systems are registered into explicit Bevy schedules/system sets.
Authoritative gameplay runs in `FixedUpdate`; rendering, UI and audio
presentation can run in frame schedules. The adapter owns Bevy-specific
components, queries, resources and asset handles. The project IR does not.

Bevy ECS is built around entities, components, resources and systems, and its
schedules support explicit ordering constraints. Bevy's fixed clock is intended
for logic that needs a consistent timestep. See:
- https://docs.rs/bevy/latest/bevy/ecs/
- https://docs.rs/bevy/latest/bevy/time/struct.Fixed.html

## First demo: Impossible Pong

Impossible Pong is the vertical slice for this contract:
- one first-class `Gameplay` Event Sheet containing the ordered gameplay event tree;
- stable IDs for paddles, ball, walls and score;
- fixed-tick movement and collision processing;
- player input mapped separately from the gameplay rules;
- score and round state expressed as actions;
- generated Bevy systems, not hand-authored gameplay hidden beside the JSON.

The initial sample JSON lives at
`demos/impossible-pong/project.json`. Its `arena_bounds` component reserves
stable built-in collider IDs `wall-top`, `wall-bottom`, `goal-left` and
`goal-right`; these are synthesized by the arena adapter and are not ordinary
user-authored objects. `paddle.track_ball` is a deterministic bounded tracking
rule, not a general-purpose scripting hook. `game.restart_round` queues ball
despawn, waits the declared number of fixed ticks, then spawns the next ball.
The Bevy game adapter and compiler are incremental work; the sample is a data
contract, not a claim that code generation already exists.


## Construct compatibility extensions: typed conditions, actions and expressions

The initial Pong sample demonstrates a typed-operation direction, but a
real-world Event Sheet language needs more structure than flat arrays of
condition/action strings. The following additions are required before
Construct compatibility can be claimed.

### Condition groups and selection-aware evaluation

Preserve Event Sheets as first-class ordered resources. Every sheet owns its
event tree; every event owns ordered conditions, actions and child events.
Shared sheets are linked by ordered include references. Includes are not
copied into consumers and event trees are never flattened into a global list.

The initial all-AND condition list must evolve to a structural condition-group
AST that can represent AND and OR without losing source order or branch
identity. Inversion belongs to the condition node and must be evaluated
together with its selection effect. A condition may return truth while also
filtering selected object instances; a boolean-only API is insufficient.

### Typed ACE calls

A condition or action node contains a permanent Impossible operation ID and
ordered typed arguments. The operation is resolved through the plugin registry
and validated against its ACE descriptor. Construct IDs, labels and addon
names are importer aliases, not runtime identities.

Object plugin ACEs and attached behavior ACEs compose for the compatible
object type. Project/global plugins contribute ACEs without requiring scene
instances. The compiler core resolves and validates these calls; it does not
hard-code every Construct operation.

### Expressions and symbol scopes

Expression text is parsed to an AST with source spans, then type-checked
against project symbols and plugin-provided functions. It must support typed
literals, references, dotted object/behavior properties, arithmetic,
comparisons, boolean operators, function calls and parentheses.

Variable resolution distinguishes project/global, Event Sheet/local,
object-type and per-instance scopes. Expressions such as `dt` remain explicit
clock-domain values until the imported project profile determines their
meaning. Random expressions use declared deterministic RNG state and preserve
argument and draw order.

### Selection context

The Event Sheet evaluator carries an explicit ordered selection context. A
collision or overlap condition may filter the current instances, and subsequent
actions must target those selected instances rather than all instances of the
object type. The context is scoped across parent/child events and must define
behavior for OR branches, inversion, else branches, includes and Wait
continuations.

See [CONSTRUCT-ACE-AND-IMPORT.md](CONSTRUCT-ACE-AND-IMPORT.md) for the proposed
typed AST, expression grammar, Selection System, compatibility diagnostics and
engine-neutral IR contract. See [CONSTRUCT-REFERENCE-STUDY.md](CONSTRUCT-REFERENCE-STUDY.md)
for the Alien-Parcor and Flappy Madruga source cases.

The current editor and model still store condition/action rows as text. These
sections define the next schema/compiler work; they do not claim that this
parser, evaluator or importer exists yet.

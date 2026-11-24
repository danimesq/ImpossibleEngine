# Construct 2 reference-project study

## Purpose and boundary

Alien-Parcor and Flappy Madruga are research references for Impossible Engine's
ACE catalog, object/plugin model, behaviors, event semantics and compatibility
tests. They are not hand-authored import targets and they do not define a
Construct 2 input format for Impossible.

The intended migration route is:

`Construct 2 project -> external C2-to-C3 project conversion -> Construct 3 project -> Impossible importer`

The Impossible importer starts at the Construct 3 boundary. The original C2
projects remain valuable as provenance and semantic evidence: when a C2
construct appears ambiguous, its original XML and behavior are consulted, but
the production importer does not parse C2 XML.

This distinction is intentional. It prevents a second, competing C2 parser from
being created inside Impossible and keeps the C3 project representation as the
single supported interchange input.

## Reference projects

### Alien-Parcor

- Repository: https://github.com/danimesq/Alien-Parcor
- Upstream fork lineage: https://github.com/IshanArya/Alien-Parcor
- Construct 2 project with multiple layouts and a platform-gameplay focus.
- The source scan identified eight Event Sheets: `Event sheet 1`,
  `Level 1 Event Sheet`, `Level 2 Event`, `Level 3 Event`,
  `Level Event`, `Setting Event`, `Settings Event`, and `Title Evet`.
  The spelling `Title Evet` is retained here as it appears in the source.
- The project is useful for studying a richer platformer: player movement,
  enemies, lives, projectiles/explosions, level progression, camera following,
  animation state and keyboard/mouse/touch input.
- The current inventory scan found references to Platform, Bullet, Fade,
  Flash, Destroy outside layout, Scroll To and Solid behaviors. This is a
  research inventory, not a final claim that every possible behavior parameter
  and edge case has been catalogued.

The project is the platformer/behavior reference. It exercises the boundary
between an object's base plugin, attached behaviors, collision participation,
animation state and event-driven gameplay.

### Flappy Madruga

- Repository: https://github.com/danimesq/Flappy-Ramon
- Project title: Flappy Madruga.
- Construct 2 project saved with Construct 2 r214 (the project metadata records
  `saved-with-version = 21400`).
- Three layouts: `Chaves`, `Continuous` and `Start`.
- Five Event Sheets: `Common in-game`, `Common in-levels`,
  `Continuous events`, `Start events` and `Chaves`.
- The scanned project contains 17 object types, including Sprite, Button,
  Tiled Background, Text, Audio, Browser, Touch, Keyboard, WebStorage,
  Facebook and GooglePlay.
- The `Madruga` Sprite uses the Platform behavior. Pipe and tiled-background
  objects use Solid where declared. The `BottomPipe` object carries a
  boolean `Scored` instance variable; `Madruga` carries a boolean `Queda`
  instance variable.
- Event groups in `Common in-game` include `Start`, `Movement`,
  `Collisions`, `Scoring`, `Background` and `Obstacle`.

Flappy Madruga is the compact arcade reference. It concentrates the kinds of
features that are easy to flatten incorrectly: OR conditions, inverted
conditions, selected instances, nested events, includes, instance variables,
timers, waits, expressions involving `dt`, random values and global services.

## Include graph and Event Sheet identity

The project contains shared Event Sheets. The scanned include relationships
include:

- `Chaves` includes `Common in-game` and `Common in-levels`.
- `Continuous events` includes `Common in-game`.
- `Start events` is a separate sheet for the start layout.

Therefore `Common in-game` is a shared resource, not a block of events to be
copied into each consumer. The Impossible project model must preserve each
Event Sheet as a first-class resource and preserve ordered include references.
The compiler may resolve an include graph for analysis, but it must not mutate
the authored project into duplicated or flattened event trees. Include cycles
must be detected and reported.

This also reinforces the existing Impossible decision:
`Project -> Event Sheets -> ordered event tree -> conditions/actions/children`.
Events do not become a project-global flat list.

## Comparative feature matrix

| Semantic area | Alien-Parcor contribution | Flappy Madruga contribution |
|---|---|---|
| Layouts and progression | Multiple platform levels, title/settings flow | Three explicit layouts, including start and two game modes |
| Event Sheet organization | Multiple per-level and shared sheets | Shared sheets and a concrete include graph |
| Object/behavior composition | Platformer objects and a broader behavior mix | Sprite + Platform, pipe/background + Solid |
| Movement | Platform movement and enemy/player behavior | Jump impulse, angle, rotation and scrolling |
| Collision | Gameplay collision and projectile/enemy interactions | Pipe collision, ground/background collision and selected pipe instances |
| State | Lives, movement/animation states and gameplay variables | Global score/speed/timing variables and instance flags |
| Timing | Animation and movement timing | `dt`, Every X seconds, Wait and delayed animation changes |
| Expressions | Movement/behavior parameters and event expressions | Arithmetic, variable/object references, `random()` and `dt` |
| Input | Keyboard, mouse and touch paths | Touch-start OR Space-key jump path |
| Services | Project-level dependencies to be audited | Audio, Browser, WebStorage, Facebook and GooglePlay |
| Selection | Platformer and collision-related instance picking | Collision picking and per-pipe `Scored` instance state |

This is a semantic comparison, not a numeric feature-coverage score. The two
projects were chosen because their mechanics complement one another.

## Flappy Madruga: source-backed semantic cases

The following observations are especially valuable as conformance targets.
They are described semantically; the source XML remains the provenance record.

### Jump input and nested guard

The Movement group accepts a touch-start trigger OR a Space-key press. A
nested guard checks that `Madruga.Queda` is false before applying the jump
vector, changing the angle and switching the animation. A Wait action delays
the later animation reset.

This one example requires all of the following to survive conversion:

- OR structure and branch-local trigger semantics;
- an instance-variable reference with boolean type;
- inversion without accidentally discarding selection effects;
- an object/behavior action with typed arguments;
- ordered actions;
- a non-blocking temporal continuation for Wait;
- preservation of the relevant event execution context.

### Per-instance scoring

When the lower pipe crosses the player, the event checks that the pipe's
`Scored` instance variable is false, increments the global score, updates
the score text and sets that pipe's `Scored` value to true.

This is a high-value Selection System test. The action must affect the selected
pipe instance, not every instance of the BottomPipe object type. The global
score variable and the per-instance flag must remain distinct scopes.

### Collision and game-over flow

The collision path checks the player's fallen state, detects obstacle
collision, sets the fallen flag, stops scrolling/spawn intervals, changes audio
playback and exposes the relevant UI control. Nested events read and update
the high-score storage for the Continuous layout.

This exercises collision conditions, selected-object context, ordered
side-effects, event children, audio operations and an external persistence
plugin. The persistence service must be represented as a capability/plugin,
not silently treated as a normal deterministic gameplay variable.

### Scrolling and obstacle generation

The Background group moves pipes and tiled backgrounds using
`SCROLLSPEED * dt`, wraps backgrounds at boundaries and destroys pipes after
they leave the playable region. The Obstacle group runs every configured
interval, creates a pipe pair at a randomized vertical position and initializes
the lower pipe's `Scored` flag.

This requires explicit time-delta typing, interval/timer semantics, seeded
randomness with preserved draw order, object creation/destruction boundaries
and instance-variable initialization.

## ACE and plugin families to cover

The reference corpus implies that Impossible's plugin architecture must
distinguish at least these ownership families:

1. **Core/System operations**: layout/game flow, tick/time, variables and
   generic event control. System is project-global and mandatory.
2. **Object plugins**: Sprite, Text, Button and Tiled Background-style logical
   object types. They define base properties and their own ACEs.
3. **Behavior plugins**: Platform, Solid, Bullet, Fade, Flash, Scroll To and
   Destroy outside layout-style capabilities. A behavior contributes ACEs to
   compatible object types and carries its own serialized parameters/state.
4. **Project/global plugins**: Keyboard, Mouse, Touch, Audio, Browser,
   WebStorage, Facebook and GooglePlay-style services. They do not need to be
   represented as visible scene instances merely because they expose ACEs.
5. **Presentation/effect extensions**: animation, visual effects and audio
   operations whose side effects must be separated from authoritative
   gameplay state.

An object's available ACE set is composed from its object plugin plus the
behaviors attached to its object type. Project/global plugins register
operations without inventing scene objects. The compiler core resolves IDs
and types; it does not hard-code every ACE implementation in a monolithic
switch statement.

## What these projects do not prove

- They do not define every Construct 2 or Construct 3 feature.
- They do not prove exact semantics for every OR/inverted branch, wait
  continuation, timer edge case or selection-context transition.
- They do not establish a complete list of third-party addons or licenses.
- They do not make their images, audio, fonts or character art safe to
  redistribute.
- They do not authorize using their C2 XML as the production import format.

Where a semantic detail is uncertain, the compatibility document records it as
an investigation/test requirement instead of guessing.

## Fixture policy

The initial fixture catalogue is at
`fixtures/construct-reference/cases.json`. It records small semantic cases,
their source provenance and the behavior they must preserve. It is not an
alternate project format and is not fed to the importer.

After the C2-to-C3 migration tool is identified and pinned, the full reference
projects can be converted automatically into C3 project fixtures. Those C3
outputs, together with their converter logs and source checksums, become the
actual end-to-end importer fixtures. The original C2 sources remain reference
material for diagnosing semantic differences.

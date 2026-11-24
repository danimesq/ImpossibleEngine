# Project Clock Contract and Reference-Behavior Fidelity

## Status and scope

This document defines the proposed project-level contract for time, simulation
ticks, scheduling, pause behavior, temporal Event Sheet operations and
reference-behavior fidelity in Impossible Engine.

The central rule is:

> Every Impossible project declares a versioned clock contract. The runtime
> must interpret that contract explicitly; it must never silently substitute
> host timing, renderer cadence or backend defaults.

This is an architecture and format contract. It does not claim that the clock
runtime, scheduler, trace harness or Street Chaves port is already implemented.

This work is intentionally separate from the plugin-registry implementation.
The System plugin may expose temporal operations, but the clock contract and
scheduler are runtime/compiler infrastructure, not a pile of special cases
inside System.

## Goals

- Allow each project to select and version its own timing semantics.
- Keep authoritative gameplay independent of render FPS and host scheduling.
- Reproduce reference-game timing, update order and state transitions as closely
  as practical, including legacy quirks when those quirks affect behavior.
- Make timing behavior serializable, inspectable, testable and replayable.
- Make incompatible semantic changes explicit through contract versions and
  migrations.
- Support projects that need different tick rates, rational rates, pause rules,
  catch-up policies, time scales and logical timers.
- Keep presentation clocks separate from authoritative simulation time.
- Provide deterministic diagnostics that identify the first divergence from
  a reference trace.

## Non-goals

- Requiring every project to use Street Chaves' timing values.
- Assuming one universal 60 Hz or 28 ms clock.
- Treating fixed timestep alone as proof of determinism.
- Requiring byte-identical machine code, memory layout or executable output.
- Making the Pascal implementation's internal architecture the architecture
  of Impossible.
- Letting wall-clock time, renderer frame count or operating-system timers
  silently influence gameplay.

## Versioning model

Clock semantics have their own explicit version, independent of the overall
project JSON schema and the compiler version.

A project should carry:

- `schema_version`: version of the serialized project document.
- `clock_contract.version`: semantic version of clock and scheduler rules.
- `compiler.minimum_version` (or equivalent): minimum compiler contract
  required to interpret the project.
- A named clock profile ID and its fully serialized settings.

A change that alters observable gameplay timing is a clock-contract semantic
change, even if the JSON shape remains identical. Examples include changing
whether a wait resumes in the current or next phase, whether time scale affects
timers, whether catch-up ticks are dropped, or how input edges are assigned.

The compiler/runtime must reject an unsupported clock-contract major version.
It must not guess. Compatible additive fields may be introduced under a
documented minor-version policy; changes to execution meaning require a new
major contract version or an explicit migration.

Build fingerprints and replay metadata include the normalized clock contract,
profile ID, compiler/runtime versions and relevant plugin versions. A replay
must not be considered compatible merely because its project JSON parses.

## Clock domains

Impossible distinguishes at least four domains. They must not be conflated.

### 1. Host clock

A monotonic platform clock used only by the outer scheduler to measure elapsed
real time and decide when simulation work is due.

- It is not an authoritative gameplay source.
- Wall-clock/calendar time is not used for gameplay.
- Host clock reads are not exposed as deterministic Event Sheet expressions.
- Platform sleep, debugger pauses and scheduler jitter must not rewrite
  simulation history.

### 2. Simulation clock

The authoritative sequence of discrete simulation ticks.

- Identified by an integer `tick_index`.
- Advances only when the runtime executes a simulation tick.
- Owns deterministic gameplay updates, input-frame consumption, collision
  facts, event evaluation and authoritative state changes.
- Is independent of render FPS.
- Is the primary time coordinate for deterministic replay and reference traces.

A simulation tick is an ordered transaction over the project's declared
simulation phases. The tick index advances exactly once per completed tick.

### 3. Game clock

A logical project/game-time domain derived from simulation ticks according to
the selected profile.

It may support:
- pause and resume;
- time scale;
- logical timers and countdowns;
- game-specific timer units;
- gameplay waits.

A game clock is not automatically equivalent to elapsed SI seconds. A legacy
game may intentionally display one timer second after a fixed number of
simulation ticks. That behavior must be represented as a named, versioned
timer rule, not silently converted to wall-clock seconds.

### 4. Render/presentation clock

The cadence at which frames are presented.

- May be variable, capped, vsynced or backend-controlled.
- May interpolate between authoritative simulation snapshots.
- May update non-authoritative UI, particles or visual effects where allowed.
- Must not decide how many gameplay updates occur in one simulation tick.
- Must not feed interpolated presentation values back into authoritative state.

Audio presentation may have its own device cadence, but audio callbacks must
not mutate authoritative gameplay state.

## Project clock profile

A project's clock profile is serialized in project data. The following is an
illustrative shape, not yet a finalized schema:

```json
{
  "clock_contract": {
    "version": "1.0.0",
    "profile": "impossible.fixed-rational/1",
    "simulation": {
      "mode": "fixed",
      "tick_rate": {
        "numerator": 125,
        "denominator": 3
      },
      "catch_up": "all",
      "max_ticks_per_host_pump": 0
    },
    "game_time": {
      "mode": "ticks",
      "time_scale": {
        "numerator": 1,
        "denominator": 1
      },
      "pause_policy": "freeze"
    },
    "suspension": {
      "policy": "exclude_suspended_time"
    },
    "input": {
      "sampling": "tick_indexed",
      "edge_assignment": "first_due_tick"
    },
    "render": {
      "mode": "independent",
      "interpolation": true
    },
    "schedule": {
      "profile": "impossible.default-gameplay/1"
    }
  }
}
```

The example rate is illustrative. A project may instead declare an integer
period in nanoseconds, a rational frequency, or a versioned legacy timing
profile. The serialized representation must preserve exact values and must
not require floating-point accumulation.

The runtime validates ranges, denominator nonzero, supported modes, policy
combinations and profile compatibility before starting gameplay.

## Fixed-step scheduling and accumulator rules

For fixed-step projects, the scheduler accumulates monotonic host elapsed time
in an integer or exact rational representation.

- It executes a tick whenever the accumulator reaches the declared tick
  duration.
- It subtracts exactly one tick duration for each executed tick.
- It retains the fractional/remainder time for the next host pump.
- It does not round the remainder away.
- The configured catch-up policy determines what happens after a long stall.
- The render loop may run zero, one or many times between simulation ticks.

The default fidelity-oriented catch-up policy is `all`: execute every due
simulation tick and preserve the full logical history. A project may explicitly
choose a bounded or dropping policy for a different class of game, but that
choice changes observable behavior and belongs in the versioned contract.

If a safety cap is used, it must not silently discard overdue ticks. The
runtime must either retain backlog for later pumps or apply an explicitly
declared overflow policy and surface diagnostics.

Never derive simulation delta from the time between rendered frames. Never
multiply authoritative movement by an unqualified render delta.

## Time scale, pause and suspension

These are separate concepts and must be specified separately.

- **Pause** is a project/game state. The contract states whether simulation
  ticks continue for selected systems, whether game time freezes, and which
  input/UI operations remain active.
- **Time scale** changes the rate at which the game-time domain advances. It
  does not necessarily change the simulation tick cadence. The contract
  specifies which timers and systems observe scaled time.
- **Host suspension** occurs when the application is backgrounded, minimized,
  suspended or otherwise not scheduled. The profile states whether suspended
  duration is excluded or accumulated.
- **Hit-stop** is a gameplay mechanic, not host suspension. It must be modeled
  as explicit simulation/gameplay state and phase gating, preserving any
  reference-specific exceptions (for example, selected counters or effects
  continuing during hit-stop).

No global assumption may be made that pause, hit-stop, time scale and
application suspension are interchangeable.

## Input sampling and tick assignment

Input devices are sampled outside or at the boundary of simulation ticks, then
converted into deterministic, tick-indexed input frames.

The contract specifies:
- how held states are sampled;
- how press/release edges are retained if no tick is due;
- which due tick receives a pending edge during catch-up;
- whether multiple physical transitions between ticks are coalesced or queued;
- how focus loss clears held inputs and prevents stuck buttons;
- how replay records the resulting logical input frames.

A useful default is to preserve pending edges until a simulation tick is due,
assign them to the first due tick, and apply held state to subsequent catch-up
ticks. This is a proposed default, not a claim about every legacy reference.
Reference profiles must encode the observed behavior of their source game.

Replays record logical input frames, not raw OS events or host timestamps.

## Game timers and temporal Event Sheet operations

Temporal operations are owned by the System plugin API, but implemented against
the project clock contract.

Potential operations include:

- `simulation.on_tick` / `simulation.fixed_tick`;
- `system.every_n_ticks`;
- `system.tick_count`;
- `system.game_time`;
- `system.timer_start`, `system.timer_elapsed`;
- `system.wait_ticks`;
- `system.wait_game_time`;
- `system.set_time_scale`;
- `system.pause_game` and `system.resume_game`.

These IDs are proposals, not a claim that they are registered today. Their
schemas, units, phase behavior and versioning must be specified before they
become part of the language.

### Wait is a continuation, not a blocking sleep

A wait action must never block the runtime thread, a Bevy system or the Event
Sheet interpreter.

It creates a serializable logical continuation containing at least:
- originating Event Sheet/event identity;
- the continuation position after the wait action;
- the selected clock domain;
- target tick or logical deadline;
- resume phase/policy;
- relevant event execution context.

When due, the continuation resumes according to the declared phase policy.
It does not use an OS timer and does not rely on a thread sleeping. The
continuation is part of authoritative state if it can affect future gameplay,
so it must be replayable and serializable.

The contract must distinguish waiting N simulation ticks from waiting N game
time units. A time-scaled wait and an unscaled wait are not interchangeable.

## Ordered simulation phases

A fixed tick is not a single undifferentiated update. It is an ordered sequence
of phases. The schedule is part of the project's behavioral contract.

The runtime owns a phase scheduler. Plugins declare the phases in which their
operations may execute, their read/write effects, RNG usage, structural
mutations and determinism constraints. The project schedule determines the
actual order. Plugins cannot reorder phases implicitly.

A generic schedule may include:
1. input-frame consumption;
2. pre-simulation/global state;
3. command recognition and AI decisions;
4. object/fighter updates;
5. frame/state selection;
6. behavior and movement updates;
7. effect/projectile updates;
8. collision detection and fact generation;
9. collision/body-hit resolution;
10. physics and hit-stop handling;
11. post-simulation/game timer and round state;
12. Event Sheet dispatch at explicitly defined boundaries;
13. authoritative snapshot/replay checkpoint.

This list is a vocabulary and candidate decomposition, not a universal fixed
order and not a claim that Street Chaves uses this exact sequence. Some
reference games require effects to move before body-hit resolution, a frame
script to update hitboxes before collision, a hit to change a victim's state
before physics, or a counter to advance during hit-stop. Those details belong
in the reference profile's exact ordered schedule.

The schedule format must support named phases, stable ordering, explicit
before/after constraints, phase versioning and validation for cycles or
ambiguous order. For maximum fidelity, a profile may define a fully ordered
phase list rather than rely on unordered dependency resolution.

### Structural mutation boundaries

Entity/object creation, destruction, scene changes and similar structural
mutations must occur at explicitly declared boundaries. Operations may enqueue
a mutation during a phase, but the schedule decides when it becomes visible.
A reference profile may require a specific boundary to reproduce same-tick
visibility. This must be tested, not guessed.

### RNG order

Randomness is authoritative state. A deterministic project declares its
algorithm, seed/state representation and draw-consumption rules. Trace records
must include draw count and, where practical, RNG state checkpoints. Reordering
systems or changing branch evaluation can change future gameplay even if the
same seed is used.

## Reference profile: Street Chaves

Street Chaves is a first-class fidelity target for Impossible. The goal is to
reproduce its observable gameplay behavior from the Pascal reference and the
Rust reconstruction, even if the Impossible implementation is architecturally
different and does not reproduce the original executable byte-for-byte.

The port must preserve, where observable:
- simulation tick cadence and accumulator behavior;
- game timer semantics and counters;
- pause, hit-stop and suspension behavior;
- input edge/held-state assignment;
- command recognition and CPU decision timing;
- fighter/object update order;
- animation/frame-script timing;
- hitbox and hurtbox lifecycle;
- effect/projectile movement and collision order;
- defense, hit resolution and victim reactions;
- physics and knockback timing;
- HUD, round, timeout and dialogue timing;
- RNG algorithm, seed and draw-consumption order;
- structural mutation visibility within a tick;
- state transitions and all same-tick side effects.

### Known timing values to preserve as profile data

The current Street Chaves research notes identify a 28 ms fixed tick and a
game timer that increments one displayed second every 25 ticks (700 ms at an
uninterrupted 28 ms cadence). These are Street Chaves-specific observations,
not Impossible defaults. They must be checked against the current Pascal
reference trace and Rust implementation before being treated as final golden
constants.

The profile should represent the timer as a tick-based rule, for example
`displayed_second_every_n_ticks = 25`, rather than converting it to a
real-time timer. This preserves the legacy game's intentional relationship
between game time and simulation ticks.

### Pascal fidelity is behavioral, not architectural

Impossible does not need to imitate Pascal units, global variables, procedure
layout or memory organization. It must reproduce the behavior those structures
produce.

The Rust/Impossible runtime may use ECS, plugins, typed IR and different data
structures, provided that the externally observable state transitions and
timing match the reference within the agreed comparison scope.

Byte-perfect executable reproduction is explicitly not a requirement for this
port. Behavioral equivalence is the target.

### Reference phase schedule

The Pascal update order must be reconstructed from source inspection and
instrumented traces, not inferred from a generic engine loop. The existing
Street Chaves investigation points to behavior distributed across fight state,
shared sprite logic, character scripts, effects, collision and HUD/round logic.

A candidate decomposition includes fight initialization, camera/stage/audio/
HUD setup, input and command processing, CPU decisions, stage objects,
fighter/frame updates, defense, effects and movement, collision/body-hit
resolution, hit-stop/physics, timers and terminal state handling. This is a
research map, not yet a normative phase order. The final Street Chaves profile
must cite source procedures and trace evidence for every ordering constraint.

When the reference order is uncertain, mark it as unknown and add an
instrumentation/test task. Do not promote a hypothesis to a compatibility rule.

## Reference tracing, replay and differential validation

The fidelity harness is a core development tool, not an optional debug extra.

### Trace records

A structured JSONL trace should be able to record:
- tick index and clock-domain counters;
- phase name and phase-local sequence number;
- event/script/procedure identity;
- object/instance stable ID;
- state before and after;
- relevant positions, velocities, frame IDs and collision boxes;
- input frame and command-recognition state;
- collision pairs and resolution outcome;
- timer/counter values;
- RNG draw index and checkpoint state;
- queued/applied structural mutations;
- emitted side effects and their logical ordering.

Trace output must be canonical: stable field ordering, stable IDs, normalized
numeric representations and deterministic event ordering.

### Differential comparison

Given the same initial state and logical input frames, run the Pascal
reference, StreetChavesRust and Impossible implementation and compare their
traces.

The comparator should report the first divergence with:
- tick;
- phase;
- phase-local sequence;
- entity/object;
- field or event;
- expected/reference value;
- actual value;
- last matching event;
- RNG draw count/state;
- relevant source location or script identity.

Do not stop at a final score or screenshot. A game can end in the same state
after diverging for many ticks. The first divergence is the useful diagnostic.

### Validation layers

1. **Clock contract tests:** exact tick count, remainder retention, pause,
   catch-up, suspension and time-scale semantics.
2. **Input tests:** edge retention, catch-up assignment, focus loss and replay.
3. **Timer tests:** tick-based legacy counters, pause and hit-stop exceptions.
4. **Phase-order tests:** explicit ordering and same-tick visibility.
5. **Operation tests:** every temporal/System operation and continuation.
6. **Deterministic replay:** same project, seed and logical input frames produce
   the same authoritative trace.
7. **Reference differential tests:** Pascal vs StreetChavesRust vs Impossible.
8. **Gameplay scenario tests:** neutral, movement, defense, hit, combo, knockback,
   round transition, timeout and other representative scenarios.
9. **Visual checkpoints:** compare animation/camera/HUD at selected ticks,
   supplementary to state traces rather than a substitute for them.

## Bevy and other runtime adapters

The project clock contract is engine-neutral. A Bevy adapter may use Bevy's
fixed schedule as a host integration point, but it must not delegate semantic
decisions to backend defaults.

- The adapter feeds exact project tick opportunities into the runtime.
- Project phases map to explicitly ordered Bevy system sets.
- Bevy frame schedules handle rendering and presentation.
- Any backend time resource is an implementation detail, not the project
  contract.
- The same validated schedule and clock semantics must be portable to a
  headless runner and future WASM/native adapters.

The headless runner is the canonical environment for deterministic tests and
reference comparison. Rendering must not be required to advance the game.

## Compatibility and migration rules

- Every project has an explicit clock contract or receives a documented,
  deterministic migration to one.
- No silent fallback from unsupported profile/version to a default clock.
- Changing tick rate, timer units, pause semantics, input assignment, phase
  order, wait-resume phase or catch-up policy is a behavior change.
- Migration tools must show which behavior changes and preserve the original
  contract for rollback.
- Replay files record the clock-contract version and normalized profile.
- Plugins declare clock-domain and phase requirements for temporal operations.
- Build and replay diagnostics print the active profile and contract version.

## Implementation sequence

1. Land this project-level clock and fidelity contract.
2. Implement typed clock-profile parsing, validation and canonical
   serialization.
3. Implement the integer/rational fixed-step scheduler and exact accumulator
   tests.
4. Implement clock domains, pause/time-scale/suspension policies and
   tick-indexed input frames.
5. Add versioned phase schedules and plugin phase declarations.
6. Add temporal System operations and serializable wait continuations.
7. Build a headless simulation runner and deterministic replay format.
8. Add Street Chaves reference profile with source-backed schedule and exact
   legacy timer behavior.
9. Instrument Pascal/Rust/Impossible and add differential trace comparison.
10. Port Street Chaves gameplay incrementally, requiring first-divergence
    analysis for every fidelity regression.

## Acceptance criteria for the Street Chaves target

The Street Chaves port is not considered faithful merely because it looks or
feels similar in a short manual play session.

At minimum:
- its project declares a versioned Street Chaves clock profile;
- all authoritative gameplay advances on the declared simulation ticks;
- timer/counter behavior matches the reference;
- input, pause, hit-stop and catch-up behavior are trace-tested;
- the reference phase order is source-backed and explicit;
- deterministic replays reproduce identical authoritative traces;
- representative Pascal reference scenarios match the Impossible trace up to
  the documented comparison boundary;
- every known mismatch is recorded, classified and covered by a regression
  test;
- no claim of byte-perfect executable equivalence is made or required.

The intended standard is **behavioral fidelity with evidence**: preserve what
the player and the reference state machine can observe, and make every
intentional deviation explicit.

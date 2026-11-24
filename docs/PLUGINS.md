# Impossible plugin architecture

## Purpose

Event Sheet operations (conditions, actions, triggers and expressions) are contributed by plugins. A plugin owns stable IDs, argument schemas, types, validation, execution phase, deterministic constraints and typed IR lowering. The compiler core discovers plugins, resolves IDs, validates declarations and invokes compiler hooks. It must not become a giant switch statement of game-specific actions.

Plugins initially are statically linked Rust registrations, not dynamic libraries. This is portable and deterministic; external plugins may later use a separately designed sandboxed ABI.

## Construct inspiration, Impossible identity

Construct 3 provides object plugins, project-wide plugins, behaviors, effects and themes. Impossible borrows the extensibility idea but avoids requiring scene objects for global capabilities and forbids arbitrary backend snippets as plugin operations.

Initial kinds: mandatory Core infrastructure; Event plugins registering triggers/conditions/actions/expressions; Object plugins defining logical types/components and ACEs; Behaviors attached to object types; Renderer/effect plugins isolated from deterministic gameplay; Editor extensions for panels, inspectors, importers and tools. The first implementation focuses on Event registry and object/behavior registry. Other kinds are extension points, not completed features.

## Plugin contract

Each plugin has a permanent vendor/reverse-domain ID, semantic version, compatible Impossible API, kind, dependencies/optional dependencies, capability declarations, built-in flag, operation schemas, validation and typed IR lowering, explicit phase and determinism classification, optional editor descriptors, docs and tests. IDs never derive from display labels. Duplicate operation IDs, dependency cycles, incompatible API versions or missing dependencies are errors. Registry ordering is canonical by plugin ID, independent of filesystem enumeration; event order remains declared order and plugins cannot reorder it.

Third-party plugins eventually use a restricted interface with explicit permissions. No implicit filesystem, network, clock or process access. Native plugins are trusted code initially and must be labelled as such.

## Built-in plugins

### System (mandatory)

Always available, project-global, no scene instance, cannot be removed. Owns generic flow/game state, fixed-tick and global score/variable operations. Moved from the existing Event Sheet contract: triggers game.started, simulation.fixed_tick, score.reached; conditions game.state_is, score.at_least; actions game.set_state, score.add, game.restart_round.

System does not own object movement, input devices, collisions, audio or rendering.

### Input (built-in, optional capability)

Owns input mapping/sampling concepts and condition input.axis_nonzero. Input maps remain project data.

### Collision (built-in, optional capability)

Owns trigger collision.entered and condition collision.involves. Collision facts arise in deterministic physics phase and are consumed canonically.

### Audio (built-in, optional capability)

Owns action audio.play. Audio is presentation and cannot change authoritative gameplay state.

### Pong gameplay extensions

paddle.move_axis, paddle.track_ball, ball.spawn, ball.bounce_from_paddle, ball.bounce_from_wall and ball.despawn are demo/game-specific, not System. They may initially be demo plugins and later become generic object behaviors or physics operations. game.restart_round stays System and queues structural changes; game-specific ball spawn remains delegated.

## Compiler integration

1. Resolve declared and built-in plugins.
2. Check API compatibility and dependencies.
3. Build immutable registry of operation IDs and schemas.
4. Validate Event Sheets and argument types.
5. Invoke plugin validation and lowering into typed IR.
6. Run determinism checks using plugin metadata and operation checks.
7. Generate output from IR plus backend adapters.

Reject duplicate IDs, missing capabilities/dependencies, cycles and unstable ordering. Build fingerprints include normalized plugin IDs/versions and compiler version.

## Manifest example

```json
{
  "id": "impossible.system",
  "name": "System",
  "version": "0.1.0",
  "api": "impossible-plugin/1",
  "kind": "event",
  "builtin": true,
  "mandatory": true,
  "dependencies": [],
  "operations": ["trigger:game.started", "trigger:simulation.fixed_tick", "trigger:score.reached", "condition:game.state_is", "condition:score.at_least", "action:game.set_state", "action:score.add", "action:game.restart_round"]
}
```

This is a design contract, not a claim that a loader/exporter already exists. The next slice should implement registry types, manifest parsing, built-in registrations and tests, then migrate the operation catalog through that API.
# Arcade Car Movement behavior

## Purpose

Arcade Car Movement provides top-down 2D forward movement and steering for a single object instance. It is intentionally separate from Vehicle Dynamics and from rigid-body physics. It models an arcade movement controller, not a suspension, wheel, drivetrain or tire simulation.

The behavior owns per-instance speed and steering state. It consumes normalized controls and the shared collision system, and it updates the object's 2D transform through the normal simulation pipeline.

## Properties

| Property | Type | Default | Meaning |
|---|---|---:|---|
| Maximum speed | Number | 400 | Maximum absolute forward speed |
| Acceleration | Number | 600 | Rate used while accelerating |
| Deceleration | Number | 300 | Rate used while braking or releasing throttle |
| Steer speed | Number | 180 | Base steering rate |
| Drift recovery | Number | 90 | Rate at which lateral drift is damped |
| Collision friction | Number | 0.5 | Friction factor used when resolving solid contacts |
| Set object angle | Boolean | true | Rotate the object to follow its movement direction |
| Default controls | Boolean | true | Enable the default semantic input mapping |
| Turn while stopped | Boolean | false | Allow steering when forward speed is zero |
| Enabled | Boolean | true | Enable or suspend behavior updates |

## Conditions

- Compare speed: compare signed or absolute speed using the requested comparison mode.
- Is enabled: report whether behavior updates are active.
- Is moving: report whether the magnitude of forward speed exceeds the runtime movement epsilon.

## Actions

| Action | Parameters | Contract |
|---|---|---|
| Set acceleration | value | Replace the acceleration rate |
| Set deceleration | value | Replace the deceleration rate |
| Set drift recovery | value | Replace the lateral drift damping rate |
| Set collision friction | value | Replace the solid-contact friction factor |
| Set maximum speed | value | Clamp future throttle targets to the new maximum |
| Set steer speed | value | Replace the steering rate |
| Set enabled | enabled | Enable/disable behavior updates without detaching the behavior |
| Set ignoring input | ignore | Ignore controls while preserving current velocity |
| Set speed | speed | Set signed forward speed, clamped to the current maximum |
| Simulate control | control | Inject left, right, up or down for the current simulation step |
| Stop | none | Set current forward and lateral speed to zero |
| Set default controls | enabled | Enable/disable default semantic input mapping |
| Set turn while stopped | enabled | Allow/disallow stationary steering |

## Expressions

- Acceleration, Deceleration, Drift recovery, Collision friction, Maximum speed and Steer speed expose the current configuration.
- Moving angle exposes the current movement heading.
- Speed exposes signed forward speed.
- Velocity X and Velocity Y expose the current world-space velocity components.

## Simulation semantics

1. Read a normalized control snapshot for the current simulation step.
2. Apply acceleration, braking and deceleration using simulation delta time.
3. Clamp signed forward speed to the configured maximum.
4. Apply steering according to speed, steer rate and the stationary-turn option.
5. Update the movement heading and optional object angle.
6. Integrate position using the resolved velocity.
7. Resolve contacts against enabled solid colliders through the shared collision subsystem.
8. Apply collision friction and drift recovery, then expose the resulting state to Event Sheets.

The implementation must define a stable order relative to collision detection and Event Sheet execution. It must use simulation time, not wall-clock time, and produce deterministic results for an identical input/event trace and simulation-step sequence.

## Collision boundary

Solid is an obstacle/collision-participation behavior. It is not a substitute for a rigid-body solver. Arcade Car Movement may use collision normals and contact response supplied by the shared collision subsystem, but it must not create a private physics world.

## Input boundary

Default controls are semantic actions, not hard-coded platform keycodes. A project may map keyboard keys, gamepad axes/buttons or other device inputs to the same movement controls. `Simulate control` is available to Event Sheets and automated tests.

## Runtime status

This is a specification-only behavior contract. Do not mark it runtime-supported until movement integration, collision response, properties, all ACEs and deterministic conformance fixtures are implemented.

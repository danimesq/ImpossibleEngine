# 🌘 Rust Gaming Eclipse: ImpossibleEngine integration plan

**Status:** Architecture proposal, 2026-11-24.  
**Scope:** Define the boundary between the ImpossibleEngine authoring/compiler pipeline, RustMultiConsoleFoundation, and consumer games such as StreetChavesRust.  
**Implementation status:** Documentation only. The current GTK/PyGObject prototype is not yet a typed compiler, Rust runtime, or exporter.

## 🌘 1. Three different responsibilities

Rust Gaming Eclipse aligns three independent projects without merging them:

| Project | Owns | Must not own |
|---|---|---|
| **ImpossibleEngine** | Authoring model, Event Sheets, schema, semantic rules, typed IR, lowering, generated project structure, target selection, build orchestration | SDL/Orbital internals, per-console system APIs, generic platform runtime implementations |
| **RustMultiConsoleFoundation** | Stable platform contracts, capability profiles, adapters, runtime services, asset adaptation, toolchain and packaging integrations | Event Sheet semantics, game-specific rules, the Impossible project format |
| **StreetChavesRust** | Street Chaves game domain, deterministic behavior, source evidence, game-specific data and tests | Generic compiler/runtime abstractions |

The projects remain separate repositories with one-way dependency flow. The Foundation must never depend on ImpossibleEngine or StreetChavesRust. ImpossibleEngine may generate an application that depends on the Foundation. StreetChavesRust may independently consume the same public Foundation API.

## 🌘 2. The compiler pipeline

The intended modern/native pipeline is:

```text
Impossible project JSON
        |
        v
versioned schema + parser + validation
        |
        v
typed semantic IR
        |
        v
target lowering + capability checks
        |
        v
generated Rust project / runtime composition
        |
        v
RustMultiConsoleFoundation public API
        |
        v
selected host/platform adapter
        |
        v
build, link, asset conversion, package
```

This is an intended pipeline, not an implemented feature. The current editor can open/save JSON and edit text-based condition/action rows; typed schemas, semantic validation, Rust code generation, engine adapters, and console toolchains remain future work.

The compiler must preserve the Event Sheet's semantics rather than treating the JSON as a visual script that can be translated approximately. The semantic IR must define event traversal, subevent order, triggers, per-tick conditions, loops, object identity/lifetime, variable width/conversion, waits, timers, animation, collisions, RNG, and scheduling explicitly.

## 🌘 3. Foundation is a target runtime contract, not the compiler

ImpossibleEngine consumes Foundation APIs at the generated-game boundary. The editor and compiler core should not need a platform runtime just to edit, parse, validate, or transform a project.

Recommended ownership:

- **ImpossibleEngine:** parses project data, validates semantics, chooses an output strategy, generates a Rust crate/application, and writes build manifests.
- **RustMultiConsoleFoundation:** provides the stable APIs and adapters used by generated applications on supported native/web targets, plus target capabilities, asset adaptation, build and packaging facilities.
- **Generated game:** owns the generated or user-authored gameplay code and calls the selected runtime contract.

The Foundation repository currently has a Cargo workspace containing only `foundation-packaging`. It does not yet expose the proposed general-purpose runtime crate. Therefore this PR deliberately does not add a Cargo dependency, invent an import path, or claim that ImpossibleEngine can already link against the Foundation.

The first integration gate is for the Foundation to publish a documented API crate, with a versioned contract, feature list, target matrix, capability model, and a minimal compiling example. Until then, ImpossibleEngine should target a written integration specification and test its generated output with a small local mock/fixture contract rather than a guessed dependency.

After the API exists, pin a tagged release or immutable Git revision during development. Move to a crates.io semver dependency when the Foundation publishes stable releases. Do not depend on a moving branch or silently vendor/copy Foundation code.

## 🌘 4. Platform, runtime, engine, and physics are separate axes

ImpossibleEngine must not conflate a platform with the engine that runs on it.

| Axis | Examples | Meaning |
|---|---|---|
| Target platform | Windows, Linux, Web, Android, PSP, GBA, PS1 | Where the game is built or executed |
| Host/runtime adapter | Foundation-native SDL, browser host, Orbital, console SDK | How platform services are reached |
| Game engine integration | Standalone game core, Bevy-hosted app, custom runtime | How the game's systems are organized and scheduled |
| Physics provider | Game-specific rules, standalone Rapier, Bevy Rapier plugin | How a selected simulation workload is calculated |

A project profile should select compatible combinations, not pretend that choosing “PSP” automatically selects a usable Bevy or Foundation backend.

Bevy is an optional engine integration, not a console target and not the Foundation itself. In Bevy-hosted mode, Bevy owns its own application schedule and the Bevy-managed rendering/window/input stack. A Foundation bridge must adapt to that ownership rather than opening a second window or event loop.

In Foundation-hosted mode, the Foundation owns the selected platform adapter and host loop. A generated game can use its own Rust systems without Bevy. These modes are mutually exclusive for duplicated host responsibilities.

Physics is separately selectable. Rapier 2D can be used through `bevy_rapier2d` when a Bevy host is selected, or potentially through standalone Rapier. ImpossibleEngine should not inject Rapier into every game simply because it is available.

## 🌘 5. Bevy and Rapier policy

The current research snapshot (2026-11-24) finds Bevy 0.20.1 and `bevy_rapier2d` 0.37.0, whose dependency is Bevy `^0.20`. Their versions must be selected as a compatible pair. Bevy's official overview lists Windows, macOS, Linux, Web, iOS, and Android; it does not establish the classic-console coverage required by the ImpossibleEngine roadmap. Bevy's published crate documentation also warns about frequent breaking releases and an MSRV close to current stable Rust.

These facts lead to the following policy:

- Keep Bevy optional and feature/adapter-scoped.
- Never make a Bevy dependency part of the generic Foundation contract.
- Keep Event Sheet IR independent from Bevy ECS types, Bevy asset handles, and Bevy schedule types.
- Use a Bevy integration only when the selected target/runtime profile supports it and the project benefits from Bevy's engine facilities.
- Keep a Foundation-native or specialized lowering path for targets that cannot use Bevy.
- Pin compatible Bevy and Rapier versions in each concrete application/adapter; do not float versions in generated builds.

References:

- https://github.com/bevyengine/bevy/releases
- https://bevy.org/news/bevy-0-20/
- https://bevy.org/
- https://docs.rs/crate/bevy/0.20.1
- https://docs.rs/crate/bevy_rapier2d/0.37.0
- https://www.rapier.rs/docs/user_guides/bevy_plugin/getting_started_bevy/

## 🌘 6. StreetChavesRust is a validation project, not an engine dependency

StreetChavesRust is a strong end-to-end consumer because its current research defines timing-sensitive game semantics, deterministic RNG, collision boundaries, data-driven fighter behavior, renderer-neutral output, and a planned Web/native split.

Use it to validate:

1. Import of project metadata and assets without changing source provenance.
2. Mapping of a bounded, verified subset of game behavior into typed Event Sheet IR.
3. Explicit representation of behavior that remains in a native Rust module.
4. Generated-project composition with the Foundation API when it exists.
5. Deterministic replay and regression comparisons across the original and generated/hosted implementations.

Do not make ImpossibleEngine depend on the `street-chaves-rust` Cargo package. Do not copy its fighter logic, RNG, data, or source into generic compiler/runtime crates. An importer may read a StreetChaves project or a documented export format, but it must preserve licensing and provenance and report unsupported constructs instead of silently dropping them.

The existing ImpossibleEngine architecture already names Street Chaves as the first long-term migration/validation project. This document makes the integration boundary explicit without claiming that the conversion is currently possible.

## 🌘 7. Recommended implementation sequence

1. **Specify semantics:** version Event Sheet JSON and define a typed IR with deterministic event/tick ordering.
2. **Specify the runtime seam:** coordinate the minimal Foundation API and capability report; keep a mock contract for compiler tests until the real crate exists.
3. **Build a minimal generated app:** generate a tiny native Rust app that calls the mock/Foundation contract and reports requested versus available capabilities.
4. **Foundation reference consumer:** make multiPong prove the Foundation's own platform path; make StreetChavesRust prove a more demanding real-game path.
5. **Add engine adapters:** evaluate Foundation-native and Bevy-hosted composition as distinct runtime modes.
6. **Import StreetChaves incrementally:** start with project/assets and bounded behavior slices, retain native modules where necessary, and gate each migration with deterministic fixtures.
7. **Expand console lowering:** use target-specific source/assembly/binary paths where a native Rust runtime is absent or unsuitable. The Foundation game-runtime API is not mandatory for every target.

## 🌘 8. Architecture acceptance criteria

- No dependency cycle among the three repositories.
- The compiler can parse and validate projects without GTK and without a platform runtime.
- The IR has explicit, tested ordering and type-conversion semantics.
- Generated apps depend only on public, versioned Foundation contracts or a clearly identified specialized target runtime.
- Bevy and Rapier are opt-in integrations, never implicit defaults for every target.
- Platform capability failures are explicit and actionable.
- StreetChaves import preserves provenance and never claims lossless conversion without complete semantic coverage.
- Build manifests pin compilers, adapters, dependencies, and asset tooling sufficiently for repeatable builds.

## 🌘 9. Questions intentionally left open

- Exact Foundation runtime crate and public API naming.
- Whether the eventual Bevy bridge lives in the Foundation repository or a sibling integration crate.
- Which Event Sheet semantics should compile to the Foundation runtime versus a specialized runtime.
- Whether a StreetChaves importer should read the current Rust project, its source data, or a future interchange package.
- How target profiles represent a Bevy-hosted desktop/Web build versus a bare-metal/custom console pipeline.



## 🌘 10. StreetChaves import is hybrid, not a Rust-to-Event-Sheets rewrite

StreetChavesRust is an independent reference implementation and future import/validation fixture. The goal is not to translate every Rust source file into Event Sheets or to make ImpossibleEngine depend on the StreetChaves Cargo package.

A future importer should combine project/source inspection, a documented interchange format, and semantic analysis to map only verified constructs into ImpossibleEngine's versioned project model and typed Event Sheet IR. The migration boundary is explicit:

- **Typed IR:** metadata, assets, data, and bounded behaviors whose semantics have a complete representation and tests.
- **Native Rust modules:** complex, performance-sensitive, source-specific, or otherwise unsupported behavior that should remain native behind a documented interface.
- **Unsupported constructs:** anything that cannot yet be represented or safely retained, reported as a diagnostic rather than silently approximated or dropped.

Imported elements must preserve source provenance and a migration status. Deterministic fixtures should compare the original StreetChaves implementation with each migrated/generated behavior slice. Do not claim complete or lossless conversion until every required semantic has a tested mapping. The compiler owns import, semantic analysis, typed IR and lowering; StreetChaves owns its game-specific rules; Foundation owns reusable host/platform services.

## 🌘 11. Keep the game boundary separate from the host boundary

| Generated/game-specific responsibility | Foundation or selected host responsibility |
|---|---|
| Simulation, rules, RNG, fixed-step policy and game state | Window, event loop, physical input polling |
| Logical action meaning and game-specific input mapping | Physical-to-logical input normalization and capability reporting |
| Renderer-neutral draw intent, asset meaning, animation/effect state and ordering | Actual rendering, presentation, platform resource lifecycle and asset adaptation |
| Semantic audio requests | Audio device/backend initialization and playback |

In Bevy-hosted mode, Bevy owns its managed host responsibilities; a Foundation bridge must adapt to that ownership without creating duplicate windows, event loops, input systems, renderers, or audio owners. In Foundation-hosted mode, the selected Foundation adapter owns those host services. The generated game's simulation and presentation intent remain its own.

A generated project must not gain an SDL dependency merely because a desktop adapter happens to use SDL internally. SDL is an implementation choice behind a host contract, not the contract itself. The Foundation runtime API is not mandatory for specialized console lowering where no suitable runtime exists.

## 🌘 12. Foundation runtime scaffold: integration is still gated

[Foundation runtime API PR #9](https://github.com/danimesq/RustMultiConsoleFoundation/pull/9) adds an initial foundation-runtime API scaffold and mock-host example. Treat it as an early contract implementation, not a production host or proof of target support. It does not yet provide a production SDL adapter, real window/event loop, physical input polling, renderer, audio backend, storage implementation, or validated desktop/Web/console matrix.

Compiler tests may use a mock contract, but generated-project integration must wait for a real, versioned API and a compiling consumer adapter on the selected target. Capability requests must remain explicit and fail visibly when unavailable. The host's variable frame delta must not replace the game's fixed-step semantics: StreetChaves, for example, retains its 28 ms logical tick and deterministic update ordering. Generated games must define their own simulation timing policy independently of host frame pacing.

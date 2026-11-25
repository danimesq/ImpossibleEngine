
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

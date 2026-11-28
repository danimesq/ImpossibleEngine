# Game Services add-on

## Purpose

Game Services is a provider-neutral contract for player identity, authentication, profile data, achievements and leaderboards. The editor and Event Sheets refer to stable ImpossibleEngine IDs; host adapters map those operations to platform-specific services.

The add-on does not embed an SDK, provider secret or platform credential in the project file.

## Initialization and authentication

The runtime exposes readiness and signed-in state. Sign-in and sign-out are asynchronous. Successful authentication publishes a player identifier; failures and user cancellation arrive through explicit failure events.

Profile retrieval is a separate request so projects can choose when they need display name or avatar data. Do not assume that authentication automatically returns every profile field.

## Achievements

The contract covers:
- Requesting the player's achievement list, optionally filtered by hidden, revealed or unlocked state.
- Requesting achievement metadata such as display name, description and state-specific icon URI.
- Revealing and unlocking an achievement.
- Incrementing or setting progress for incremental achievements.
- Reading achievement IDs, names, descriptions, progress steps, total steps, type and icon URI from the latest successful result.

Achievement operations are provider-dependent. Adapters must report unsupported operation or invalid achievement configuration explicitly.

## Leaderboards

The contract covers:
- Requesting a leaderboard by stable provider leaderboard ID.
- Selecting public or social collections where supported.
- Selecting today, weekly or all-time time spans.
- Requesting top scores or scores around the current player.
- Limiting the returned page size.
- Submitting a numeric score with an optional public tag.
- Requesting a provider-native leaderboard presentation when supported.

The latest successful page exposes count, total count when available, score, formatted score, rank, formatted rank, player display name and tag by index. Personal-best score, rank, formatted values and tag are also exposed where the provider supplies them.

A provider that cannot implement a requested collection, time span, position mode or presentation must return a typed unsupported-capability result.

## Event Sheet contract

Actions start requests and return control immediately. Completion, failure and service-state changes re-enter the scheduler as typed events. Request IDs correlate responses with the initiating operation.

The runtime must distinguish at least:
- not initialized;
- unsupported service;
- sign-in required;
- user cancelled;
- permission or consent denied;
- network failure;
- provider error;
- invalid identifier or parameters;
- successful result with an empty collection.

A failed request must never be represented as a successful empty result.

## Security and platform boundaries

- Provider credentials, application secrets and signing material belong in host/build configuration.
- Never serialize secrets into `.ieproj`, Event Sheet JSON, generated Rust or asset manifests.
- Player identifiers and profile data are runtime values, not authoring-time constants.
- Social visibility and consent rules are enforced by the provider adapter and platform policy.
- Adapters must support explicit sign-out and cleanup when the host application leaves the active lifecycle.

## Runtime status

This is a specification-only add-on. Each provider adapter and ACE must be implemented and tested independently before the editor or compiler reports runtime support for a target.

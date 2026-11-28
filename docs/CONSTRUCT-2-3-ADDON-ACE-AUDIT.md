# Construct 2 / Construct 3 Add-on and ACE Audit (Pending)

This follow-up is intentionally a research checkpoint. The earlier capability expansion has already been merged; it should not be treated as an authoritative clone of Construct's add-on model until this audit is completed.

## User-requested audit

Review the official online documentation for both Construct 2 and Construct 3 to establish how add-ons/plugins are actually structured and surfaced in the editor, including:

- Add-on/plugin/behavior/effect categories and their boundaries.
- Add-on selection UI: category grouping, icons, names, descriptions, search and selection flow.
- ACE taxonomy and presentation: Conditions, Actions and Expressions, category/subcategory grouping, iconography, display names, descriptions and editor affordances.
- ACE semantics: trigger vs predicate conditions, looping, invertibility, parameter types, selection/picking, expressions and return types, side effects, asynchronous callbacks and runtime behavior.
- Plugin-specific APIs and how similar capabilities differ across C2 and C3.
- Cross-version changes, deprecated/renamed features, and platform/runtime differences.

Use official documentation wherever possible. Record each finding with the exact documentation URL and version (C2 or C3). Distinguish confirmed facts from assumptions and unresolved questions. Do not invent add-ons or ACEs to fill gaps.

## Specific follow-up cautions

- Re-audit the add-on catalogue for duplicated, overlapping, miscategorized or unsupported entries. The existing count of 52 plugins is a snapshot, not a guarantee of correctness.
- Confirm the audio/media taxonomy from source docs. In particular, verify sound playback and audio APIs against User Media/capture APIs rather than assuming their responsibilities.
- Provider-neutral Game Services remains a useful engine capability, but it is an ImpossibleEngine abstraction, not a claim that Construct 2/3 have a native plugin with the same scope. Candidate adapters may include Google Play Games, Xbox Live, Steam and Gamlr Onchain.
- Text-to-Speech is retained as a future wishlist item and is explicitly not a priority for implementation.
- Do not import title-specific project files, game names, assets or gameplay rules. The goal is capability fidelity and architecture, not reproducing games.

## Deliverables after the audit

1. A sourced C2/C3 add-on inventory and comparison.
2. A sourced ACE taxonomy and editor/UI comparison.
3. Corrections to ImpossibleEngine's built-in add-on registry, including removing duplicates and fixing categories or semantics.
4. A revised capability/compatibility profile and tests that check the corrected contracts.
5. A summary of confirmed coverage, intentional ImpossibleEngine-only abstractions, and remaining runtime implementation work.

## Status

**Pending:** online documentation audit in a separate conversation. This PR remains open to track the research and subsequent registry corrections.
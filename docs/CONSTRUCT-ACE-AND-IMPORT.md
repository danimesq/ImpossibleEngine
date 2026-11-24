# Construct compatibility, typed ACEs and C3 import contract

## 1. Architectural decision

Impossible must reproduce the semantics of real Construct projects, not only
imitate the visual appearance of Construct's editor.

The two C2 projects Alien-Parcor and Flappy Madruga are **foundation references**
for the ACE, object-plugin, behavior-plugin and runtime-semantics model. They
are not manually imported into Impossible and their C2 XML is not the
production importer input.

The supported migration boundary is Construct 3:

~~~text
Construct 2 project
      |
      v
external C2 -> C3 project migration tool
      |
      v
Construct 3 project (.c3p archive or folder project)
      |
      v
Impossible C3 importer
      |
      v
normalized project model -> typed Event Sheet AST -> typed IR
      |
      v
plugin lowering -> deterministic Rust code generation
~~~

The external C2-to-C3 migration step is a separate tool/process. Impossible
does not implement a second C2 XML importer. The importer in this repository
must accept C3 project data only.

The exact GitHub repository for the **project-level** C2-to-C3 converter has
not yet been pinned in this specification. That is a pre-implementation gate:
verify its repository, license, supported C2 versions, output format,
dependencies, command interface and conversion behavior before vendoring or
invoking it. Do not substitute a similarly named addon converter.

### Addon conversion is a separate problem

The repository
[TobyReeno/c2-addon-assistant](https://github.com/TobyReeno/c2-addon-assistant)
documents a `C2C3AddonConverter` that generates Construct 3 addon source from
Construct 2 addon source. That is useful research for addon/ACE metadata
migration, but it is not evidence of a complete C2 game-project converter.
The two pipelines must remain separate:

- **Project migration:** C2 project -> C3 project.
- **Addon migration/availability:** C2 addon -> C3 addon or equivalent
  supported C3 addon.
- **Impossible import:** C3 project -> Impossible project/IR.

The C3 editor itself also documents importing C2 `.capx` projects, but that
native editor path is not a replacement for identifying the GitHub project
converter that the product pipeline intends to reuse.

## 2. Input contract: Construct 3 projects only

The importer accepts:

- a local Construct 3 folder project; or
- a single-file `.c3p` project archive (a ZIP-based package containing the
  project folder).

A C3 project is JSON-based and may refer to separate layout, Event Sheet,
object, animation, asset and addon data. The importer must inspect the project
manifest and discover referenced data; it must not assume that one JSON file
contains the whole project.

The importer rejects raw C2 `.capx`, `.caproj` and C2 Event Sheet XML as
input with an actionable diagnostic:

~~~text
Unsupported input format: Construct 2 project.
Convert the project to Construct 3 first, then import the resulting C3 project.
~~~

### Archive and source safety

Before parsing project contents:

- validate the ZIP signature and archive structure;
- reject path traversal, absolute paths, symlink entries and duplicate
  normalized paths;
- enforce configurable limits for total uncompressed size, entry count and
  individual file size;
- preserve original path case and relative directory structure;
- never execute project scripts, addon code or embedded commands during import;
- retain source file names and source spans in diagnostics where possible.

Folder and archive inputs must normalize to the same logical project content.

### Version and provenance

Record at least:

- Construct 3 saved-with release/build metadata;
- source container kind (folder or `.c3p`);
- importer version and schema version;
- project content digest;
- resolved addon/plugin/behavior identifiers and versions;
- the C2-to-C3 converter identity, version/commit and source-project checksum
  when the project came through that migration path;
- converter logs and warnings, without treating them as proof of semantic
  equivalence.

A project from a newer or unknown Construct release must not be silently
interpreted using the newest known schema. The importer should report whether
the release is supported, partially understood or outside its tested range.

## 3. ACEs are the plugin interface

ACE means **Action, Condition and Expression**. Triggers are event-dispatching
conditions and remain conditions in the Event Sheet model. They are not a
parallel field bolted onto each event.

Each ACE is a typed operation descriptor owned by a plugin. It must include:

- stable Impossible operation ID, independent of display name;
- ACE kind: condition, action or expression;
- argument names, order, types, optionality and defaults;
- source aliases for known Construct generations/addons;
- supported object types and required behaviors, if applicable;
- selection effect and target selection context;
- execution phase and clock domain;
- deterministic classification and RNG usage;
- side-effect/capability declarations;
- validator and typed IR lowering implementation;
- version and deprecation/migration information.

C3 source IDs are compatibility aliases, not Impossible's permanent operation
IDs. Display labels and localized descriptions must never be used as primary
identity.

### Plugin ownership model

The registry must support these distinct kinds:

| Plugin kind | Responsibility |
|---|---|
| Core | Project schema, compiler, scheduler, selection context and runtime infrastructure |
| System/Event | Project-global triggers, conditions, actions and expressions |
| Object | Object type definition, common properties, instance data and base ACEs |
| Behavior | Reusable behavior attached to compatible object types; contributes ACEs and state |
| Global service | Input, Audio, Browser, storage and platform services that need no scene instance |
| Presentation/effect | Animation, render effects and non-authoritative audiovisual operations |
| Editor/importer | Inspectors, palettes, format readers and migration diagnostics |

System remains mandatory and project-global. Object plugins define object
types. Behaviors attach to object types and extend their available ACE set.
Global services register project-wide ACEs without requiring a visible object
instance.

A Sprite object with Platform and Fade behaviors, for example, exposes the
union of Sprite ACEs, Platform ACEs and Fade ACEs, subject to compatibility
checks. The behavior's parameters and state remain separately addressable.

### Example manifest shape

The following is illustrative. Its IDs are Impossible IDs, not claimed
Construct ACE IDs:

~~~json
{
  "id": "impossible.object.sprite",
  "kind": "object",
  "version": "1.0.0",
  "api": "impossible-plugin/1",
  "aces": [
    {
      "id": "sprite.set-angle",
      "kind": "action",
      "arguments": [
        { "name": "angle", "type": "number" }
      ],
      "selection": "apply-to-selected-instances",
      "phase": "event-actions",
      "determinism": "deterministic"
    },
    {
      "id": "sprite.compare-x",
      "kind": "condition",
      "arguments": [
        { "name": "comparison", "type": "comparison-op" },
        { "name": "value", "type": "expression<number>" }
      ],
      "selection": "filter-selected-instances",
      "phase": "event-conditions",
      "determinism": "deterministic"
    }
  ]
}
~~~

A real manifest must also include source aliases, validation, capability
requirements, lowering hooks and supported object/behavior relationships.

## 4. Typed Event Sheet blocks

Conditions and actions must no longer be opaque text strings in the language
model. The editor may offer a text-entry affordance for expressions, but the
saved model must contain typed operation references and typed arguments.

Conceptual structure:

~~~text
Project
  EventSheet[]
    EventNode[]
      ConditionGroup
        Condition[]
          operation_id
          arguments[]
          inversion
          selection_effect
      Action[]
        operation_id
        arguments[]
        selection_target
        side_effects[]
      ChildEvent[]
~~~

Each Event Sheet is a first-class, ordered resource. Each event owns its
conditions, actions and child events. Includes are references between sheets,
not copied event arrays. Groups, comments, else branches, loops, disabled
events and other C3 node types require explicit AST variants and semantics;
they must not be coerced into a generic standard event.

The typed model must preserve:

- condition/action declaration order;
- event and child-event hierarchy;
- trigger conditions in the condition collection;
- condition grouping, including OR and AND;
- inverted conditions;
- event enabled/disabled state;
- object and behavior references;
- global, sheet/local, object-type and instance variable scopes;
- include references and source provenance;
- expression source spans for actionable diagnostics.

## 5. Expression parser

Expressions are parsed into a typed AST before IR lowering. String concatenation
of user-authored expressions into generated Rust is prohibited.

Initial grammar vocabulary:

~~~text
expression   := logical_or
logical_or   := logical_and ( "or" logical_and )*
logical_and  := comparison ( "and" comparison )*
comparison   := additive ( compare_op additive )?
additive     := multiplicative ( ("+" | "-") multiplicative )*
multiplicative := unary ( ("*" | "/" | "%") unary )*
unary        := ("not" | "!" | "+" | "-") unary | primary
primary      := number | string | boolean | reference
              | function_call | "(" expression ")"
function_call := identifier "(" arguments? ")"
reference    := identifier ("." identifier)*
arguments    := expression ("," expression)*
~~~

The first parser iteration should support literals, parenthesized arithmetic,
comparisons, boolean operators, unary operators, function calls and dotted
references. It must retain exact source spans and original text for diagnostics.

### Type checking

Resolve references through a symbol table:

- project/global variables;
- Event Sheet/local variables;
- object-type variables;
- instance variables;
- object properties and behavior properties;
- System values such as `dt`;
- plugin-provided expressions and function signatures.

Types must distinguish at least number, integer, boolean, string, object type,
instance reference, selected-instance collection, vector, color and unknown.
Unknown is a diagnostic state, not an implicit conversion to string or number.

Function resolution is plugin-owned. The parser knows syntax; the registry knows
which functions exist and their argument/result types.

### The `dt` expression

`dt` is not a magical untyped float. It is a time-delta value whose source
clock domain and units must be resolved using the imported project's runtime
semantics and the selected clock contract.

The same expression spelling can have different behavior under different
runtime/clock profiles. Do not silently replace `dt` with render-frame delta,
fixed-tick duration or wall-clock seconds. Preserve it as an explicit typed
clock expression until the clock profile resolves it.

### Random expressions

Functions such as `random(a, b)` are represented as explicit RNG operations.
Argument evaluation order and draw consumption are part of deterministic
semantics. Do not constant-fold, reorder or duplicate random calls unless the
compiler proves that the transformation preserves the RNG stream.

## 6. Selection System

Construct conditions often do more than return true or false: they filter or
pick object instances for the rest of the event. The Impossible model therefore
needs an explicit **selection context** (the Construct concept commonly
described as SOL, or selected object list).

A conceptual selection context contains:

- object-type ID;
- ordered selected instance IDs;
- parent/child event scope;
- originating event and condition branch;
- whether the selection is default/all, filtered, explicitly picked or empty;
- provenance for diagnostics and replay.

Selection order must be preserved wherever iteration order is observable. Do
not replace an ordered selection with an unordered hash set. Stable instance
IDs identify instances; they do not automatically define source iteration
order.

### Selection effects

An ACE descriptor must declare whether it:

- leaves the selection unchanged;
- filters the current selection;
- selects all instances;
- picks by UID/instance ID;
- selects or excludes instances by a query;
- iterates a selected collection;
- creates a new selection scope;
- consumes a deterministic random selection.

Collision/overlap conditions are selection-producing operations when the
source semantics pick the participating instances. They cannot be reduced to
a plain boolean `overlaps(a, b)` and then followed by actions over every
instance of the object type.

### Scope and branch semantics

Selection context must be explicit across:

- parent and child events;
- nested conditions;
- OR branches;
- inverted conditions;
- else branches;
- included Event Sheets;
- wait/timer continuations.

The exact merge/restore behavior for OR, inversion, else and asynchronous
continuations must be versioned from the C3 runtime contract and covered by
fixtures. Do not assume that logical `not` or `any` alone captures selection
side effects.

## 7. Runtime semantics

The runtime contract is project data plus core scheduler semantics. Plugins
declare their phase, clock domain, selection effects, RNG use and side effects;
they do not secretly pick their own execution order.

### Event ordering

- Event Sheets are evaluated in declared project order unless an imported
  project explicitly defines another ordering rule.
- Root events and child events preserve authored order.
- Conditions are evaluated in source order within their declared groups.
- Actions execute in source order.
- Child events run only in their defined parent-event context.
- Disabled nodes are retained in imported source data but omitted from active
  execution with an explicit report entry.
- Includes remain ordered graph edges; no implicit duplication or flattening.

### Triggers

A trigger is a condition with dispatch semantics. The importer records the
trigger identity and event binding, and the runtime dispatches it at the
declared phase. Triggers must not be approximated by polling once per render
frame. Re-triggering, one-shot behavior and same-tick dispatch ordering must
be explicit.

### AND, OR and inversion

Store condition groups structurally. A flat list of booleans cannot preserve
OR groups or branch-local selection. Inversion is represented on the typed
condition node and interpreted together with its selection effect; it is not
always equivalent to wrapping an arbitrary boolean in `!`.

The Flappy Madruga touch-start OR Space-key path and the inverted
`Madruga.Queda` guard are required conformance cases.

### Waits and timers

Wait is a logical continuation, never a blocking thread sleep. A continuation
records at least:

- project/Event Sheet/event identity;
- condition/action branch context;
- next action position;
- due clock domain and logical deadline;
- selection context and captured variables according to the verified source
  semantics;
- deterministic insertion sequence;
- resume phase and event-reentry policy.

The exact policy for preserving selected instances and local event context
across a Wait must be verified against imported C3 behavior. It is a test
requirement, not a permissive assumption.

Timers use the project's declared clock domains. Repeating intervals,
one-shot timers, cancellation, pause/time-scale behavior and same-deadline
ordering must be explicit. A runtime may not translate every timer into an OS
timer or render-loop accumulator.

The project clock contract from `CLOCKS-AND-FIDELITY.md` owns the actual time
domains, fixed stepping, catch-up and pause policies.

### Behaviors and phase ordering

Behavior ACEs declare their required runtime phase and read/write effects.
For example, Platform movement and Solid collision participation are not
interchangeable generic transforms. The scheduler decides when behavior
updates, collision facts and Event Sheet conditions become visible.

Structural mutations such as object creation and destruction are applied at
declared boundaries. The Flappy Madruga obstacle generator and pipe cleanup
are regression cases for same-tick visibility.

### External services

Audio, Browser, WebStorage, Facebook and GooglePlay operations declare
capabilities and side effects. They may be unavailable on a selected platform.
Nondeterministic service results must be captured as external inputs for replay
or excluded from authoritative simulation. No importer may silently replace
an unavailable service with a no-op.

## 8. Importer compatibility report

Every import creates a machine-readable report plus human-readable diagnostics.
Each feature/ACE/plugin/behavior is classified as one of:

| Status | Meaning |
|---|---|
| supported | Imported with equivalent modeled semantics |
| emulated | Imported through an explicit compatibility implementation |
| partial | Some properties or semantics are not reproduced |
| unsupported | No compatible implementation exists |
| missing-dependency | Required plugin, behavior, addon or capability is unavailable |

Every non-supported result identifies:

- source project file and location;
- C3 plugin/behavior/addon ID and version;
- source ACE identity and arguments;
- affected object/event/layout;
- lost or changed behavior;
- suggested remediation or required plugin;
- severity and whether compilation is blocked.

The report is part of the imported project provenance. The importer never
silently drops unknown actions, conditions, expressions, object properties,
behaviors or layout data.

A default strict mode may stop before code generation if unsupported
authoritative behavior exists. A user may explicitly request a lossy import,
but the report must remain attached and all losses must be visible. Unknown
operations must not compile as no-ops.

## 9. Engine-neutral typed IR and Rust code generation

The typed IR is independent of GTK, Construct file layout and Bevy. It includes:

- project, layout and Event Sheet resources;
- object types, instances, layers and asset references;
- plugin/behavior composition and resolved ACE descriptors;
- variable declarations with explicit scopes and types;
- ordered condition groups and typed action lists;
- expression AST nodes;
- selection-context operations;
- triggers and event dispatch metadata;
- timer/wait continuations and clock domains;
- capability requirements and compatibility diagnostics.

Lowering follows:

1. Parse and normalize the C3 project.
2. Resolve object, behavior, plugin, ACE, variable and asset symbols.
3. Build the ordered Event Sheet resource/include graph.
4. Parse and type-check expressions.
5. Validate condition/action signatures and selection effects.
6. Lower source event nodes to typed, engine-neutral IR.
7. Validate clock/phase, determinism, RNG and side-effect constraints.
8. Invoke plugin-owned lowering hooks.
9. Generate Rust using stable IDs and canonical ordering.
10. Format, compile and run deterministic/golden behavior tests.

Generated Rust is produced from trusted compiler templates and plugin lowering
implementations. Project data can select registered operations and provide
typed values; it cannot inject arbitrary Rust source, Bevy system names or
unrestricted function bodies.

For identical normalized project input, plugin registry, compiler version and
target configuration, generated Rust output must be byte-identical. Build
fingerprints include those inputs. Determinism does not mean banning
randomness: it means a declared algorithm, seed/state, draw order and replayable
consumption.

## 10. Conformance and implementation phases

The following phases intentionally separate research contracts from executable
capabilities:

1. **Reference catalogue:** preserve Alien-Parcor and Flappy Madruga semantic
   cases, source locations and plugin/behavior inventory.
2. **ACE registry extension:** typed operation schemas, source aliases,
   object/behavior composition, selection effects and capability metadata.
3. **Expression frontend:** lexer, Pratt parser, typed AST, symbol resolution
   and expression diagnostics.
4. **Selection and event semantics:** explicit selection context, condition
   groups, OR/inversion, triggers and nested event scope.
5. **Temporal runtime:** clock-aware timers, Wait continuations and deterministic
   scheduler integration.
6. **C3 importer:** safe archive/folder reader, version detection, resource
   graph, addon resolution and compatibility report.
7. **Typed IR and code generation:** engine-neutral IR, plugin lowering,
   deterministic Rust output and headless tests.
8. **End-to-end C3 fixtures:** convert the two reference projects through the
   selected C2-to-C3 project converter, preserve logs/checksums, import their
   C3 outputs and compare against the semantic reference catalogue.

A phase is not complete because a document describes it. The repository must
contain implementation, tests and observed validation before the README or
release notes claim support.

## 11. Acceptance criteria for the compatibility foundation

- Alien-Parcor and Flappy Madruga are documented as semantic references, not
  C2 files that Impossible imports directly.
- The production importer accepts C3 projects only.
- The project-conversion tool is tracked separately from addon conversion and
  its exact repository/commit/license is verified before integration.
- ACEs are typed plugin-owned definitions with stable IDs and schemas.
- Object plugins, behaviors and project/global plugins have distinct
  ownership/lifecycle rules.
- Event Sheets remain first-class ordered resources with includes preserved.
- Expressions, variables, selection effects, triggers, OR and inversion have
  explicit typed representations.
- Waits and timers are logical clock-aware continuations, not blocking sleeps.
- Unknown or unsupported semantics produce a compatibility report and are
  never silently discarded.
- A validated engine-neutral IR is the only source for Rust generation.
- Reproducible codegen and deterministic replay are tested, not merely asserted.

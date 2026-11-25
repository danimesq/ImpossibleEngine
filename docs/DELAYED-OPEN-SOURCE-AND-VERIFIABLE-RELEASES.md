#🌈 Delayed Open Source, DUL and verifiable releases

**Status:** Proposal / research specification  
**Date:** 2026-11-24  
**Scope:** Source-availability policy, distributor-side licensing framework, release provenance, reproducible builds and delayed source publication.

> This document records a product and engineering direction. It is not a finalized legal license, a claim of current implementation, or a guarantee that every target can already be built reproducibly.

##🌈 1. Executive summary

Impossible Engine and other DaniMesq-distributed software may adopt a **Delayed Open Source** model:

1. A release may initially be distributed as closed-source software under a proprietary commercial grant and a version-specific delayed-publication commitment.
2. Each release publishes a cryptographically signed manifest committing to the exact source snapshot, build instructions, build inputs and distributed artifacts.
3. Independent parties should be able to reproduce the official artifacts from the committed source and declared build environment.
4. At the release's predeclared change date, the committed source is published and relicensed under the open-source license named in that release's manifest.
5. The opening date, conversion license and already-granted rights cannot be postponed or narrowed unilaterally after publication.

The goal is **commercial protection without unverifiable provenance**. A customer should not have to trust a promise that source code will eventually appear: the release should leave evidence today that can be checked later.

This proposal separates three concerns:

| Layer | Working name | Responsibility |
| --- | --- | --- |
| License framework | DaniMesq Universal License (DUL) | Distributor-configurable legal terms and release-specific grants |
| Publication protocol | Delayed Open Source Protocol (DOSP) | Release commitments, publication schedule and verification requirements |
| Verification profile | Delayed Open Verification (DOV) | Hashes, signatures, build attestations, reproducibility and transparency evidence |

These names are working names. They do not imply that a standard, license text, implementation or certification program already exists.

##🌈 2. Terminology and design principles

- **Release:** an immutable, identified distribution unit, normally a tagged version plus its complete set of official artifacts.
- **Source snapshot:** the exact source tree used for a release, including submodules or other source dependencies where applicable.
- **Build recipe:** scripts, compiler/toolchain versions, flags, configuration and documented steps needed to reproduce an artifact.
- **Build inputs:** dependencies, toolchains, generated inputs and other materials that can affect the output.
- **Artifact:** a distributed binary, package, installer, archive, container image or other release output.
- **Change Date:** the predeclared date on which the release's source-availability and license-conversion terms take effect.
- **Distributor:** the entity publishing a release and selecting the permitted options under the DUL framework.
- **Commitment:** a cryptographic digest and signed record binding a release identifier to declared source and build materials.

Core principles:

1. **Release immutability:** published manifests and Change Dates are append-only commitments, not mutable marketing metadata.
2. **No retroactive surprise:** a later release may have different terms, but it cannot silently rewrite the terms attached to an earlier release.
3. **Explicit scope:** source, binaries, assets, trademarks, hosted services and third-party components may have different rights.
4. **Verifiability:** a hash is a commitment to bytes, not proof that those bytes are safe or that a build was performed correctly.
5. **Interoperability:** project formats, documented interfaces and user data should not be made needlessly dependent on the proprietary editor.
6. **Honest status:** a release must disclose whether its build is reproducible, partially reproducible or not yet reproducible.

##🌈 3. DUL — DaniMesq Universal License framework

DUL is envisioned as a **distributor-side licensing framework**: a structured family of terms from which a distributor can select and publish a release-specific license profile.

It should not be a magic license that lets a distributor change anything at will. The actual rights granted to recipients, restrictions, exceptions, Change Date and conversion license must be fixed and published for each release.

### 3.1 Configurable dimensions

A DUL profile may define, subject to legal review:

- permitted personal, educational, evaluation and commercial use;
- number and type of seats, devices or installations;
- redistribution permissions and conditions;
- modification and derivative-work permissions;
- attribution, notices and trademark boundaries;
- whether source is available during the restricted period and under what terms;
- permitted hosting, managed-service or competing-product use;
- exceptions for plugins, integrations, interoperability and user-created content;
- the Change Date and the license that takes effect on that date;
- treatment of security fixes, support, updates and discontinued services.

The profile must distinguish copyright permissions from product entitlements, hosted services, trademarks and contractual support promises.

### 3.2 Immutable release commitments

Once a release is published, its manifest must fix at least:

- DUL profile identifier and exact text/version or immutable content digest;
- source-availability status;
- Change Date and the event from which it is calculated;
- conversion license identifier and exact version/text digest;
- scope of the code covered by conversion;
- exclusions for separately licensed dependencies, assets, trademarks or other materials;
- any additional rights already granted to recipients.

A distributor may offer more permissive terms later. It must not unilaterally delay the Change Date, remove a promised conversion, or reduce rights already granted for that release.

### 3.3 Relationship to BUSL and other models

The Uniswap v3 Core license used the Business Source License 1.1 with a conversion mechanism. DUL may learn from source-available licenses and delayed-open-publication practices, but it must not be described as BUSL 1.1 if it changes that license's text or terms.

In particular, a fifteen-year delay should be implemented as a newly drafted and reviewed license, not by casually editing BUSL 1.1. The DUL framework must also avoid implying that source-available terms are OSI-approved open source during the restricted period.

### 3.4 Example policy profile (illustrative, not legal text)

```yaml
license:
  framework: DaniMesq-Universal-License
  profile: delayed-commercial-15y
  profile_version: 1

  grant:
    commercial_use: restricted_by_profile
    redistribution: restricted_by_profile
    modification: restricted_by_profile
    interoperability: documented_exceptions

  delayed_opensource:
    enabled: true
    duration: P15Y
    clock_start: first_public_distribution
    change_date: fixed_in_release_manifest
    conversion_license: Apache-2.0
    conversion_license_version: "2.0"

  immutability:
    change_date: immutable
    conversion_license: immutable
    granted_rights: immutable
    source_commitment: immutable

  exclusions:
    - third_party_components_follow_their_own_licenses
    - trademarks_are_not_granted_by_source_release
    - hosted_services_are_not_guaranteed
```

This example is a policy sketch only. The final DUL text must define what each field means, how conflicting terms are resolved, governing law, consumer rights, termination, exceptions, sublicensing and enforceability.

##🌈 4. Fifteen-year delayed publication policy

The proposed default is **fifteen years per release**, measured from that release's first public distribution date.

Example: if release 1.0.0 is first publicly distributed on 2026-11-24, its scheduled Change Date is 2041-11-24, subject to the final license's date and time-zone rules.

Each release has its own clock:

- 1.0.0 published in 2026 → scheduled opening in 2041.
- 1.1.0 published in 2027 → scheduled opening in 2042.
- 2.0.0 published in 2029 → scheduled opening in 2044.

The exact schedule must be calculated and published at release time. The policy should define leap-day handling, time zone, cutoff instant, prereleases, hotfixes, repackaging and withdrawn releases.

A distributor may choose a shorter period or immediate open source for a particular component or release. It should not be able to choose a longer period after recipients have relied on the published commitment.

### 4.1 Release-level versus component-level clocks

The preferred model is release-level commitments with explicit component scope. Components can have separate manifests and Change Dates when they are independently versioned or distributed.

The manifest must identify which source paths, packages or components are covered. It must not imply that third-party dependencies, fonts, media, SDKs, trademarks or customer content become open source when the engine source opens.

### 4.2 Business continuity and escrow

A hash alone cannot recover missing source code. To make the promise resilient if DaniMesq ceases operations, consider depositing the exact source snapshot, build recipe and necessary metadata with an independent escrow custodian or other durable publication mechanism.

Escrow release conditions, confidentiality, encryption, key custody, integrity checks and the custodian's duties require separate legal and operational design. The public commitment should identify whether escrow exists and what it covers without exposing confidential material prematurely.

##🌈 5. DOSP — Delayed Open Source Protocol

DOSP defines the lifecycle and evidence for a delayed-open release.

### 5.1 Required release lifecycle

1. **Prepare:** freeze the source snapshot and build inputs for the release.
2. **Build:** build official artifacts using the declared recipe and environment.
3. **Rebuild independently:** have an independent builder reproduce the artifacts where feasible.
4. **Commit:** create the release manifest containing source and artifact digests, build metadata, license profile and Change Date.
5. **Sign:** sign the manifest and relevant attestations using controlled release keys.
6. **Publish:** distribute the artifacts and publish the manifest in a durable transparency log.
7. **Monitor:** preserve the source snapshot, build materials and verification evidence throughout the restricted period.
8. **Open:** on the Change Date, publish the committed source and apply the predeclared conversion license.
9. **Verify:** let recipients and independent builders compare the revealed source and rebuilt artifacts with the original commitments.

### 5.2 Release manifest

A DOSP manifest should be machine-readable, versioned, canonicalized before hashing and signed. It should contain at least:

- protocol name and manifest schema version;
- publisher identity and signing-key identifier;
- product, component, release version and publication timestamp;
- source repository and immutable commit/tree identifier where public;
- source archive digest and hash algorithm;
- source snapshot inventory or Merkle-tree root where appropriate;
- build recipe digest and build-environment identity;
- dependency and toolchain inventory, including lockfiles and pinned references;
- artifact names, target platforms, sizes and cryptographic digests;
- reproducibility status and independent builder attestations;
- DUL profile identifier and immutable license text digest;
- Change Date, clock-start rule and conversion license identifier/version/digest;
- exclusions, known non-reproducible inputs and verification instructions;
- transparency-log inclusion proof or reference.

Example (illustrative values only):

```json
{
  "schema": "dosp-manifest/v1",
  "product": "ImpossibleEngine",
  "release": "1.0.0",
  "published_at": "2026-11-24T00:00:00Z",
  "source": {
    "snapshot": "sha256:SOURCE_DIGEST",
    "tree": "git:IMMUTABLE_TREE_ID",
    "archive": "sha256:ARCHIVE_DIGEST"
  },
  "build": {
    "recipe": "sha256:RECIPE_DIGEST",
    "environment": "sha256:ENVIRONMENT_DIGEST",
    "reproducibility": "independently-reproduced"
  },
  "artifacts": [
    {
      "name": "impossible-engine-linux-x86_64.tar.zst",
      "digest": "sha256:ARTIFACT_DIGEST"
    }
  ],
  "license": {
    "framework": "DUL",
    "profile": "delayed-commercial-15y",
    "text_digest": "sha256:LICENSE_TEXT_DIGEST",
    "change_date": "2041-11-24T00:00:00Z",
    "conversion_license": "Apache-2.0",
    "conversion_version": "2.0"
  },
  "transparency": {
    "log": "LOG_IDENTIFIER",
    "entry": "LOG_ENTRY_REFERENCE"
  }
}
```

The schema must be formally specified before implementation. Example digests and identifiers above are placeholders, not valid release evidence.

##🌈 6. DOV — Delayed Open Verification

DOV is the verification profile used by DOSP. It combines source integrity, artifact integrity, build provenance and independent reproducibility.

### 6.1 Two different questions

**Source integrity:** Is the source published on the Change Date byte-for-byte equivalent to the source snapshot committed at release time?

**Build integrity:** Can the committed source and declared build inputs reproduce the official artifact that users received?

These are separate checks. A matching source hash does not prove that the distributed binary was built from that source. A matching binary hash does not prove that the source is safe or free of malicious behavior.

### 6.2 Hash commitments

For each release, publish cryptographic digests for:

- the canonical source archive;
- the source tree or a well-defined Merkle representation;
- build recipes and relevant configuration;
- dependency and toolchain inventories;
- every official binary and package;
- the manifest and attestations themselves.

Use a standardized, unambiguous canonicalization and archive format. Record the algorithm alongside every digest and design for algorithm agility. SHA-256 is a reasonable baseline; additional algorithms may be published for long-term agility. Do not concatenate ambiguous fields or hash an archive whose metadata changes nondeterministically.

A hash is a commitment to a particular byte sequence. It does not reveal the source, establish authorship by itself, prove safety or guarantee that a future algorithm will remain secure.

### 6.3 Reproducible builds

A release is reproducible when independent builders can follow the declared process and produce byte-identical artifacts, or when any documented normalization procedure yields an objectively equivalent output.

The build environment should pin or identify:

- compiler, linker, SDK and build-system versions;
- dependencies and transitive dependencies;
- source generators and generated files;
- build flags, target triples and feature selections;
- environment variables and relevant configuration;
- timestamps, locale, filesystem ordering and other sources of nondeterminism;
- signing, packaging and post-processing steps.

Where exact reproduction is impossible, disclose why and isolate the non-reproducible step. Do not label a release fully reproducible merely because the source archive has a hash.

### 6.4 Independent rebuild

At least one independent builder should reproduce each artifact for the strongest conformance profile. The builder should not rely solely on the publisher's prebuilt output or trust the publisher's build machine.

Compare the independently produced artifact digest with the official artifact digest. Preserve builder identity, environment, logs and attestations so a later verifier can inspect the evidence.

### 6.5 Signatures and transparency

Sign manifests and attestations with release keys held outside the build environment where practical. Document key rotation, revocation, compromise handling and historical signature validation.

Publish append-only transparency records. A transparency log makes silent replacement or backdating harder to conceal, especially when independent monitors retain and compare log checkpoints. A log is not a substitute for signatures, independent witnesses or source escrow.

Relevant technologies and prior art to evaluate include:

- Reproducible Builds: <https://reproducible-builds.org/>
- SLSA supply-chain security framework: <https://slsa.dev/>
- in-toto attestations: <https://in-toto.io/>
- Sigstore signing and transparency ecosystem: <https://www.sigstore.dev/>
- The Update Framework (TUF): <https://theupdateframework.io/>

These are candidate building blocks, not mandatory dependencies or claims of conformance.

##🌈 7. Verification at delayed opening

On or after the Change Date:

1. Publish the source snapshot and source archive using the format committed in the manifest.
2. Publish the exact build recipe, pinned dependencies, toolchain references and required metadata, subject to third-party license restrictions.
3. Publish the conversion license text or an immutable reference and verify that its digest matches the manifest.
4. Recompute the source archive and tree digests.
5. Compare them with the original signed manifest.
6. Rebuild the release in an independent environment.
7. Compare the resulting artifact digest with the original distributed artifact.
8. Publish verification reports, logs and any deviations.

Expected outcomes:

| Check | Result | Meaning |
| --- | --- | --- |
| Source digest matches | Pass | Revealed source matches the committed source bytes |
| Source digest differs | Fail | Source publication does not match the original commitment |
| Independent artifact digest matches | Pass | The declared build can reproduce the distributed artifact |
| Independent artifact digest differs | Investigate / fail | Build inputs, environment or artifact may differ |
| Build cannot be reproduced | Inconclusive | The source commitment may still pass, but build provenance is not fully verified |

A source digest match does not prove the absence of backdoors, malicious logic, compromised dependencies or unsafe behavior. It proves identity with the committed source snapshot. Security review remains a separate activity.

##🌈 8. DOSP conformance levels

Conformance levels describe evidence quality, not a security certification.

| Level | Requirements |
| --- | --- |
| DOSP-1 — Committed | Source and artifact digests; versioned manifest; published Change Date and conversion license |
| DOSP-2 — Attested | DOSP-1 plus signed manifest, build recipe, pinned dependency inventory and verification instructions |
| DOSP-3 — Rebuildable | DOSP-2 plus documented reproducible build and at least one independent rebuild for supported artifacts |
| DOSP-4 — Transparent | DOSP-3 plus append-only transparency publication, independent monitoring and durable preservation/escrow arrangements |

A product must not display a higher DOSP level than the evidence supports. If only some targets are reproducible, publish conformance per artifact or target rather than hiding the exception in a global badge.

##🌈 9. Scope boundaries and interoperability

Delayed publication should not become a reason to lock away user data or make interoperability impossible.

Prefer to publish or document independently of the delayed source schedule:

- project file schemas and migration rules;
- documented import/export formats;
- extension and plugin interfaces;
- public APIs and protocol specifications;
- user data export tools;
- format compatibility and versioning policies.

These surfaces can have their own permissive terms where appropriate. They do not automatically grant rights to proprietary implementation code.

The delayed-open commitment applies only to materials the distributor has the right to license. Third-party dependencies retain their original licenses. Fonts, images, audio, video, SDKs, console development kits, trademarks, customer assets and generated content require explicit inventory and treatment. A source release must not accidentally redistribute confidential or restricted third-party materials.

##🌈 10. Security, operations and key management

- Keep signing keys separate from ordinary source-control credentials and build workers.
- Use protected release workflows and multi-party approval for production signing where practical.
- Publish key fingerprints and rotation/revocation procedures.
- Preserve old public keys and verification metadata for long-term signature checks.
- Pin dependencies and record their provenance.
- Keep secrets, signing keys, credentials and private customer data out of source snapshots and build artifacts.
- Treat compromised release keys, compromised dependencies and reproducibility failures as security incidents.
- Publish corrected releases as new immutable records; never rewrite historical manifests.
- Preserve source snapshots, build recipes, logs and artifacts for the full delayed-publication period and beyond where feasible.
- Ensure the Change Date can be honored if the distributor is acquired, reorganized or ceases operations; escrow and successor obligations need explicit legal design.

##🌈 11. Rollout proposal for DaniMesq / Impossible Engine

### Phase 0 — Policy and legal design
- Draft DUL framework and one or more release profiles.
- Commission legal review of the fifteen-year Change Date, conversion mechanism, consumer rights and distributor obligations.
- Define DOSP manifest schema and canonicalization.
- Decide which components are proprietary, immediately open, source-available or excluded.
- Inventory all existing contributions and dependency licenses before applying any new policy.

### Phase 1 — Release evidence prototype
- Generate a manifest for a development release.
- Hash source snapshots, build recipes and artifacts.
- Sign manifests and verify signatures in a separate tool.
- Store manifests in an append-only public location.
- Document verification commands and expected output.

### Phase 2 — Reproducible build pipeline
- Pin Rust, Python, GTK and platform build dependencies as applicable.
- Identify nondeterministic build inputs.
- Rebuild artifacts in a clean, independent environment.
- Publish per-target reproducibility status.
- Add CI checks that prevent a release from claiming unsupported conformance.

### Phase 3 — Delayed-publication operations
- Publish release-specific DUL profile, Change Date and conversion license.
- Preserve source and build materials in durable storage.
- Establish escrow or successor arrangements.
- Test a simulated delayed opening before using the policy for a commercial release.

### Phase 4 — Production adoption
- Require DOSP manifests for every official release covered by the policy.
- Publish independent verification evidence.
- Maintain transparency-log monitoring and key-rotation procedures.
- Audit the process periodically and after major toolchain changes.

##🌈 12. Acceptance criteria

The policy is ready for production only when:

- each covered release has an immutable, version-specific license profile;
- the Change Date and conversion license are public and cannot be unilaterally postponed;
- source and artifact commitments are published before or with distribution;
- manifests are signed and verifiable using documented tools;
- build inputs and known nondeterminism are disclosed;
- reproducibility claims are backed by independent rebuild evidence;
- source snapshots and build materials are preserved for delayed publication;
- third-party components and excluded materials are clearly identified;
- a simulated opening successfully verifies source identity and, where claimed, artifact reproducibility;
- users can access their projects and documented interchange formats without requiring a blockchain or hosted service.

##🌈 13. Open decisions

1. Is fifteen years the default for every covered release, or only for selected proprietary components?
2. Does the clock begin at first public distribution, first paid distribution or another precisely defined event?
3. Which conversion licenses are approved profiles: Apache-2.0, MIT, GPL-3.0-or-later or others?
4. Will source snapshots be held by an independent escrow custodian?
5. Which transparency-log technology and independent monitors will be used?
6. Which artifacts and platforms must be reproducible before a release can ship?
7. How are proprietary SDKs and platform-specific toolchains handled?
8. Will DUL be a single legal instrument with schedules, or a family of separate license texts?
9. What happens to releases after a corporate acquisition, insolvency or product discontinuation?
10. Which components, if any, remain open source from day one?

##🌈 14. References and prior art

- Uniswap v3 Core license repository: <https://github.com/Uniswap/v3-core/blob/main/LICENSE>
- Open Source Initiative, *Delayed Open Source Publication: A Survey of Historical and Current Practices*: <https://opensource.org/initiatives/delayed-open-source-publication>
- Reproducible Builds: <https://reproducible-builds.org/>
- SLSA: <https://slsa.dev/>
- in-toto: <https://in-toto.io/>
- Sigstore: <https://www.sigstore.dev/>
- The Update Framework: <https://theupdateframework.io/>

##🌈 Non-goals

This proposal does not itself create an enforceable license, guarantee that a fifteen-year restriction is valid in every jurisdiction, certify software as secure, prove that a binary is benign, implement a build system, or make all platform artifacts reproducible. It does not retroactively relicense existing public contributions. Those tasks require separate implementation, rights review, testing and legal approval.

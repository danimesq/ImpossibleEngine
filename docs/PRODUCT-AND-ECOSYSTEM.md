# Product and ecosystem strategy

**Status:** Proposal / architecture study  
**Date:** 2026-11-24  
**Scope:** Product direction, business model, identity, collectibles and publishing. This document does not claim that any of these services or integrations are implemented.

## 1. Vision

Impossible Engine is intended to grow from a game-authoring tool into a professional game-creation and publishing ecosystem.

The proposed value chain is:

1. Developers create games with Impossible Engine.
2. They acquire a clearly scoped, perpetual software license.
3. They can publish digital editions and, where commercially viable, physical editions.
4. Plasmmer Accounts provide a consistent identity and account experience across products.
5. Plasmium Chain can provide verifiable edition, license and collectible records through the proposed NFT2 model.
6. A display-first collectibles app lets people curate and share their game-related collections.

The guiding principle is **everybody wins**: creators retain practical control over their projects, buyers understand what they purchased, collectors get meaningful presentation, and the platform earns revenue by providing useful software and publishing infrastructure.

This is a product strategy, not a promise that every component will ship or that blockchain is required to use the engine.

## 2. Product boundaries

The ecosystem should be composed of products with explicit responsibilities:

| Product / layer | Primary responsibility |
| --- | --- |
| Impossible Engine | Authoring, project management, runtime/export pipeline and developer tooling |
| Impossible licensing | Software entitlements, license terms, seats and version/update rights |
| Plasmmer Accounts | Account identity, authentication, recovery and linked services |
| Plasmium Chain | Verifiable records for licenses, editions and collectibles, subject to the NFT2 specification |
| NFT Showcase | Display, curation and sharing of supported digital collectibles |
| Publishing services | Digital distribution metadata and physical-edition workflows |

These components should communicate through documented interfaces. The engine must not become tightly coupled to a single wallet provider, chain RPC, marketplace or showcase frontend.

## 3. Source availability and proprietary product direction

The proposed commercial direction is for the professionally distributed Impossible Engine product to become closed-source and proprietary.

That is a product and licensing decision, not an instruction to silently change this repository's visibility as part of this documentation proposal. The repository is currently public. A future transition needs its own explicit plan covering:

- which code, tools and assets become proprietary;
- the release boundary between public research/prototypes and the commercial product;
- ownership and license review for all existing contributions and dependencies;
- distribution, updates, activation and offline use;
- source archives, tags and already-published releases;
- what remains public for interoperability, education and community extension.

A proprietary editor/runtime does not require proprietary project files or undocumented integration surfaces. Prefer keeping project schemas, export/package formats, extension interfaces and developer-facing APIs documented and portable. A future SDK or command-line integration surface may remain openly documented even if the main application is closed-source.

Do not retroactively relicense existing contributions or imply that a public repository has already become proprietary. Any source-availability change requires a separate, reviewed legal and repository-migration decision.

## 4. Product principles

- **Professional minimum viable product:** reliability, clear documentation, predictable project formats, support boundaries and a credible release process matter more than a large feature checklist.
- **Perpetual core license:** the primary engine purchase should be a one-time payment rather than a mandatory recurring subscription.
- **Transparent entitlements:** distinguish use of a purchased version from access to future updates, hosted services, support and additional seats.
- **Blockchain optionality:** users must be able to create, open, build and export projects without owning tokens or maintaining a wallet.
- **Creator-first publishing:** developers should understand fees, royalties if any, distribution rights, edition limits and fulfillment responsibilities before publishing.
- **Display over speculation:** collectibles should be presented as cultural and creative artifacts, not primarily as financial instruments.
- **Interoperability:** documented exports, stable identifiers and portable metadata should reduce lock-in.
- **Honest provenance:** an on-chain record can establish that a record exists and has not been altered; it does not independently prove that a physical object is genuine or currently possessed.

## 5. Commercial direction

The proposed commercial model is a one-time purchase for a perpetual license, with multiple tiers for different usage contexts.

Possible audiences / packages to evaluate:

- **Indie:** an individual developer or small independent creator.
- **Studio:** teams and commercial organizations, with seat and organization terms.
- **Education:** schools, labs and teaching environments, with institution-friendly terms.
- **Founder's Edition:** a limited launch offer with clearly enumerated benefits and no ambiguous promises of permanent services.

These are working package names, not finalized products or prices. Tiers may differ in seats, support, collaboration, services and commercial terms. Essential authoring capabilities should not be artificially fragmented.

The business must explicitly distinguish:

- perpetual right to use a defined release or version range;
- entitlement to updates and upgrades;
- access to hosted services;
- support and maintenance periods;
- number of permitted users, devices or seats;
- commercial-use permissions and any revenue thresholds;
- transfer, resale, recovery and termination rules.

A perpetual license does not automatically mean lifetime updates, lifetime support or perpetual operation of hosted services. Any such promise must be explicit and financially sustainable.

## 6. Plasmmer Accounts

Plasmmer Accounts is the proposed identity layer shared by Impossible products and other participating Plasmmer services.

### Initial direction

- Evaluate WaaP.xyz as an initial wallet/account integration.
- Keep authentication and account identity distinct from the user's blockchain address.
- Support users who do not want to connect a wallet.
- Provide account linking and clear consent boundaries.
- Define recovery, session security, account deletion and data export before production use.

### Future research

Shamir Secret Sharing is a possible recovery building block. Future research may investigate combinations involving Aztec and Arcium, but these are not assumed to be interchangeable technologies or an already-designed recovery protocol.

Before implementation, specify the threat model, secret shares and thresholds, trust assumptions, device-loss scenarios, recovery authorization, privacy boundaries and the role of each network or service. Do not describe Shamir splitting alone as authentication, MPC or a complete wallet-recovery system.

## 7. NFT Showcase

The proposed companion app is a display-first collection and identity showcase.

Its primary jobs are:

- show supported collectibles in attractive, readable collections;
- organize game licenses, game editions, cartridges, boxes, badges and creator artifacts;
- create shareable public showcases;
- allow private or unlisted collections;
- explain provenance and edition metadata in plain language;
- distinguish verified on-chain facts from owner-provided descriptions or off-chain claims.

It should not default to trading charts, floor-price rankings or speculative prompts. Marketplace functions, if ever introduced, should remain separate from the core display experience.

The app should respect ownership and privacy settings. A public showcase must not silently expose every asset associated with an address. Users need controls for visibility, hiding items, account linking and disconnecting wallets.

## 8. NFT2 and Plasmium Chain

NFT2 is the working name for a proposed tokenized record model associated with Impossible licenses and published game editions.

The exact token standard, contract architecture, metadata schema, chain governance and transfer semantics are intentionally unresolved. The design must not assume that NFT2 is a particular ERC standard.

Candidate record categories:

- software-license entitlement records;
- digital game edition records;
- physical box and cartridge edition records;
- numbered or limited collector editions;
- bundles and collection membership.

A token or on-chain record must not be treated as a substitute for the legal license agreement, copyright ownership, consumer rights, a fulfillment contract or proof of physical possession.

Plasmium Chain should provide utility that is understandable without speculation: verifiable edition identity, public provenance events where appropriate, portable references and integration points for publishers and showcases.

## 9. Architecture and integration boundaries

- The engine's project format and local build pipeline remain usable offline.
- Licensing verification should support a documented grace/offline policy and a recovery path for service outages.
- The engine should consume a stable licensing interface rather than embed provider-specific wallet logic throughout the editor.
- Chain interactions should live behind adapters with explicit network and contract configuration.
- NFT metadata should be versioned, portable and resilient to marketplace or frontend disappearance.
- Showcase rendering should be able to consume supported metadata without requiring custody of user assets.
- Publishing services should not be required for local builds.
- No private keys, recovery secrets or sensitive account data should be embedded in game builds.

## 10. Risks and mitigations

| Risk | Design response |
| --- | --- |
| One-time revenue cannot fund indefinite maintenance | Scope update promises; price support and hosted services separately; maintain a sustainable release policy |
| Blockchain or wallet outage blocks development | Keep local authoring and builds independent from chain availability |
| NFT is mistaken for copyright or a software license | Separate token metadata, legal terms and software entitlement checks |
| Physical token is copied or detached from its item | Use tamper-evident identifiers and fulfillment records; state that QR/NFC alone is not proof of possession |
| Account recovery creates a new attack surface | Threat-model recovery, minimize stored secrets and audit integrations |
| Showcase becomes speculation-first | Make curation and display the primary navigation and product metric |
| Small physical runs are too expensive | Explore print-on-demand, manufacturing partners, preorders and transparent unit economics |
| Proprietary engine creates lock-in concerns | Document project formats, exports, APIs and user data portability |

## 11. Proposed implementation phases

### Phase 0 — Product and legal specification
- Define license terms, tiers, version rights and commercial-use rules.
- Define the NFT2 vocabulary and non-goals.
- Map product boundaries and data flows.
- Document privacy, account recovery and threat models.
- Validate physical-edition economics with small production scenarios.

### Phase 1 — Professional engine foundation
- Improve editor stability, project compatibility and release engineering.
- Define supported platforms and realistic export guarantees.
- Document extension APIs and portable project data.
- Keep the engine fully usable without Plasmmer Accounts or Plasmium Chain.

### Phase 2 — Licensing foundation
- Implement license entitlements behind a provider-independent interface.
- Add offline behavior, recovery and clear user-facing status.
- Add a one-time purchase flow only after terms and support obligations are finalized.

### Phase 3 — Plasmmer Accounts
- Prototype WaaP.xyz integration behind an adapter.
- Implement account linking and wallet-optional onboarding.
- Conduct security and privacy review before production launch.

### Phase 4 — NFT2 and Plasmium integration
- Publish the NFT2 specification.
- Prototype license and edition records on a test environment.
- Audit contracts and metadata lifecycle before handling real purchases.

### Phase 5 — NFT Showcase
- Build read-only collection display and privacy controls first.
- Add curated game and physical-edition views.
- Keep trading features out of the initial scope.

### Phase 6 — Publishing and physical media
- Establish digital edition metadata and publisher workflows.
- Pilot numbered box/cartridge editions with a small creator cohort.
- Test QR/NFC linking, tamper evidence, fulfillment and customer support.
- Expand only when unit economics and provenance limitations are understood.

## 12. Open decisions

The following decisions require research and explicit approval before implementation:

1. Which releases are covered by each perpetual license?
2. Are updates included forever, for a fixed period, or tied to major versions?
3. What are the actual tier limits, seat counts and prices?
4. What legal rights does the license NFT2 represent, and what remains in the separate license agreement?
5. What does NFT2 mean technically: token standard, contract model, transferability and metadata?
6. Is Plasmium Chain an independent chain, an existing network deployment or a later architecture decision?
7. What exact role should WaaP.xyz provide, and what happens if the provider changes?
8. What are the security assumptions for future Shamir, Aztec and Arcium research?
9. Which physical formats can be manufactured reliably and affordably?
10. Who handles fulfillment, returns, warranties, taxes and regional consumer obligations?

## 13. Success criteria

The strategy is ready to move from proposal to implementation when:

- license terms are understandable and testable;
- the engine remains usable without blockchain connectivity;
- a user can distinguish a license entitlement from a collectible display item;
- developers can publish a digital edition without requiring physical fulfillment;
- physical-edition claims accurately describe what is verified and what is not;
- account recovery and privacy have documented threat models;
- the economics of one-time licenses and optional services are sustainable;
- the first showcase experience is useful without speculative trading features.

## Non-goals of this proposal

This document does not implement a payment processor, wallet, chain, token contract, NFT marketplace, physical manufacturing pipeline or account recovery protocol. It does not finalize prices, token standards, legal terms or guarantees of lifetime updates. Those require separate specifications, validation and review.

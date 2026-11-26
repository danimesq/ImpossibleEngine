# Licensing and NFT2 entitlement model

**Status:** Proposal / research contract  
**Date:** 2026-11-24

## 1. Core proposal

Impossible Engine should use a one-time purchase as its primary software licensing model. A qualifying purchase grants a perpetual license under clearly defined terms.

The model is inspired by the appeal of classic perpetual desktop-software licenses, including the historical legacy visual-editor approach, but it should not assume that Impossible must copy legacy visual-editor's exact packages, revenue thresholds or update policy.

The commercial promise must be precise. "Lifetime" is not a complete legal or technical definition.

## 2. Separate five concepts

1. **License:** legal permission to use the software under stated terms.
2. **Entitlement:** machine-readable record of the purchased package, seats, version range and conditions.
3. **NFT2:** proposed verifiable tokenized representation or pointer to an entitlement.
4. **Updates:** the releases included in the purchase.
5. **Services:** optional hosted features, support, storage, collaboration or publishing services.

Owning or transferring an NFT2 must not silently transfer copyright, grant rights absent from the license agreement, or guarantee hosted services forever.

## 3. Candidate tiers

These names are exploratory and do not define prices or final entitlements.

| Tier | Intended audience | Questions to resolve |
| --- | --- | --- |
| Indie | Individual creators and small independent developers | Individual/commercial-use scope, revenue rules if any, device limits |
| Studio | Teams and commercial organizations | Seats, floating seats, organization administration, support |
| Education | Schools, labs and teaching | Student access, lab devices, classroom use, redistribution |
| Founder's Edition | Early supporters | Limited quantity, precisely documented benefits, no vague lifetime-service promise |

Avoid withholding core authoring capabilities solely to force upgrades. Differentiation should focus on legitimate differences in scale, seats, services, support and commercial terms.

## 4. Perpetual license versus lifetime updates

The license should specify:

- the software product and covered versions;
- whether the right to use a purchased version is perpetual;
- whether minor and major updates are included;
- whether updates are time-limited or version-limited;
- whether security fixes are treated differently;
- whether support is included and for how long;
- what happens if the company discontinues a hosted service;
- whether the license is transferable and under which conditions.

A perpetual right to use a version does not imply that servers, online services, support or future upgrades will exist forever.

## 5. Entitlement data model

A future entitlement record should be versioned and minimally contain:

- stable entitlement identifier;
- product and tier identifier;
- purchase or issuance reference;
- covered version range or release policy;
- seat/organization scope;
- commercial-use scope;
- issue and optional expiration timestamps;
- status and revocation/suspension reason where legally appropriate;
- reference to the governing license terms and their version;
- optional on-chain token reference.

Do not put personal data, payment details, email addresses, recovery secrets or confidential business data in public token metadata.

## 6. NFT2 relationship

NFT2 is a working name, not a finalized token standard.

The design must answer:

- Is the token transferable?
- If transferable, does a transfer move the software license, only a collectible, or neither?
- How is a license recovered if a wallet is lost?
- Can an entitlement be represented without exposing a public wallet address?
- How are refunds, chargebacks, fraud and revocations handled?
- What happens if a token contract or chain becomes unavailable?
- Can the license be checked offline for a reasonable period?
- How are duplicate or wrapped representations prevented from creating duplicate seats?

The legal license agreement remains authoritative. The on-chain record can provide verifiable evidence and interoperability, but it is not the complete legal instrument.

## 7. Offline-first licensing

The editor and local project workflow must remain usable without a blockchain RPC or wallet provider.

Possible architecture:

- signed entitlement receipt cached locally;
- public-key verification in the client;
- explicit cache validity and grace policy;
- controlled refresh when online;
- clear UI when an entitlement cannot be refreshed;
- account recovery and support procedures;
- no private signing keys shipped in the editor.

The exact offline window and revocation policy require abuse analysis and commercial/legal review.

## 8. Security and privacy

- Never store user seed phrases or Shamir shares in plaintext.
- Do not equate wallet connection with account authentication.
- Keep payment processing outside the game project and exported runtime.
- Avoid putting personal data in immutable public metadata.
- Provide a documented account unlinking and recovery process.
- Audit contract and entitlement verification logic before production.

## 9. Acceptance criteria for a future implementation

- Terms distinguish perpetual use from updates and services.
- Entitlements can be verified without coupling the editor to one wallet provider.
- Local authoring and builds work during chain or provider outages.
- NFT2 metadata does not expose personal or payment information.
- Token transfer semantics are explicit and tested.
- Refund, recovery, revocation and duplicate-seat behavior are specified.
- Users can understand what they own and what they are licensed to do.

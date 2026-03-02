---
sidebar_position: 3
title: Open Questions
description: "Tracking of resolved specification questions from v1.0 and v1.1 review rounds with links to their resolutions."
keywords:
  - open questions
  - specification
  - review
  - resolved
  - governance
  - protocol design
---

# Open Questions

All open questions from the v1.0 and v1.1 spec review rounds have been resolved with concrete specifications.

## Previously Resolved

### v1.1 Resolutions (11 Questions)

#### Architectural — Design Decisions

| # | Question | Resolution | Location |
|---|----------|-----------|----------|
| 1 | **Protocol Governance** — How does the protocol upgrade? | MEP (Mehr Enhancement Proposal) process with trust-weighted version signaling. Nodes signal MEP support via TLV extension in announces; acceptance at ≥67% trust-weighted support. Cross-fork compatibility via gateway bridges. Sunset clause prevents indefinite version limbo. | [Versioning — Governance](/docs/L1-network/versioning#governance) |
| 2 | **Secret Ballot Voting** — Commitment schemes on partition-prone mesh | Two-phase commit/reveal with partition-safe rules: reveal_period = 2× voting_period, 80% reveal threshold for valid tally, INCONCLUSIVE status for >20% unrevealed commits. Deliberate withhold penalized (0.5x weight after 3 consecutive non-reveals). Partition reconciliation via merged re-tally. | [Voting — Secret Ballot](/docs/L6-applications/voting#secret-ballot-protocol) |
| 3 | **Post-Quantum VRF** — No production-ready standard | Two-track approach: lattice-based VRF candidate when standardized; hash-chain committed lottery as fallback. The fallback uses epoch-committed secrets (not proof-of-work) — one Blake3 hash per packet, no grinding. Per-channel migration via existing cryptographic migration phases. | [Versioning — PQ VRF Strategy](/docs/L1-network/versioning#post-quantum-vrf-strategy) |

#### Implementation — Specification

| # | Question | Resolution | Location |
|---|----------|-----------|----------|
| 4 | **AppManifest State Migration** — Execution semantics | Full state delivered via LOAD opcode as CBOR. Success requires HALT + valid CBOR output + schema conformance + within max_cycles. All-or-nothing (no partial migration). Determinism enforced; hash comparison detects violations. No automatic rollback — users pin old manifest hash. | [MHR-App — Migration](/docs/L5-services/mhr-app-upgrades#migration-contract-execution-semantics) |
| 5 | **AppManifest Schema Compatibility** — Formal definition | Programmatic compatibility checker: no removed fields, no type changes, new fields with defaults only, required→optional allowed. CRDT types cannot change between versions. Unknown fields from newer schemas preserved via LWW fallback during merge. | [MHR-App — Schema Compatibility](/docs/L5-services/mhr-app-upgrades#schema-compatibility-rules) |
| 6 | **MHR-Name Cross-Scope Query Routing** — Vague algorithm | DHT-guided scope routing: nodes register as ScopeAnchors at Blake3(scope_string) in DHT. Cross-scope queries look up the scope key, route to nearest anchor by trust distance → hop count → XOR distance. TTL = 5 × gossip_interval (adapts to transport speed). SCOPE_UNREACHABLE returned if no anchor exists. Hierarchical registration ensures ancestor scopes are queryable. | [MHR-Name — Cross-scope queries](/docs/L5-services/mhr-name#trust-weighted-propagation) |
| 7 | **Visibility-Controlled Claim Updates** — Key rotation + versioning | Revoked peers lose forward access (new key), retain historical access (old key). Claims versioned by (claimant, claim_type, qualifier) with created timestamp ordering. Encrypted claims cached as ciphertext; decrypted on key receipt. Partition key rotation reconciled via KEY UNIFICATION when claimant reconnects. | [MHR-ID — Key Rotation and Claim Updates](/docs/L5-services/mhr-id#key-rotation-and-claim-update-semantics) |
| 8 | **Payment Channel Settlement Atomicity** — Protocol not fully specified | Two-phase signing with 120-gossip-round timeout. Half-signed records are never published. After 3 failed attempts: unilateral settlement with 2,880-round challenge window. Strictly all-or-nothing — CRDT ledger only accepts dual-signed records. Channel close via standard 4-epoch abandonment rules. | [Payment Channels — Settlement](/docs/L3-economics/payment-channels#bilateral-payment-channels) |
| 9 | **Gossip Bandwidth Under Congestion** — Enforcement missing | Dedicated gossip token bucket with 2% floor guarantee (min 10 bytes/sec). Gossip throttled (queued), not dropped. Tier 1-2 never dropped. Starvation recovery mode (20% budget) triggered after 10 missed gossip intervals. Weighted fair queuing with strict floor preemption. | [Network Protocol — Gossip Congestion](/docs/L1-network/network-protocol#gossip-congestion-handling) |
| 10 | **Cryptographic Compute Verification** — ZK costs TBD | Decision matrix by workload size. ZK proofs (RISC Zero/SP1/Jolt) viable for contracts up to ~10^6-10^8 cycles at 500-1000x prover overhead. TEE attestation (AMD SEV-SNP, NVIDIA H100 CC) for large models at ~5% overhead. Consumer chooses verification tier; protocol provides framework, market determines adoption. | [MHR-Compute — Cryptographic Verification](/docs/L5-services/mhr-compute#cryptographic-verification-details) |
| 11 | **Voting Hardware Liveness** — No quantified error rates | Multi-feature radio fingerprinting: RSSI pattern (w=0.5) + clock drift/CFO (w=0.35) + timing offset (w=0.15). False positive ~1-5% depending on environment. ~15-30 radios reliably distinguished per km² with 3+ witnesses. Remote voters rely on trust flow + personhood vouching (no hardware liveness); capped at Verified (not StronglyVerified) geo multiplier. | [Voting — Radio Fingerprinting](/docs/L6-applications/voting#radio-fingerprinting-algorithm) |

### v1.0 Resolutions (28 Questions, 5 Rounds)

All questions from the v1.0 spec review rounds (5 rounds, 28 questions total) have been resolved with concrete specifications. The resolution history is preserved in the git log. Key resolution areas:

- **Wire format**: Serialization rules, endianness, TLV extensions, CompactPathCost encoding
- **Timing**: Epoch triggers, DHT rebalancing, beacon collision handling, fragment reassembly
- **Economics**: Settlement timing, channel sequence semantics, credit rate-limiting, difficulty targets
- **Security**: Nonce handling, session key rotation, KeyCompromiseAdvisory replay, reputation initialization
- **Infrastructure**: WASM sandbox tiers, capability bitfield, Ring 1 aggregation, DHT metadata format
- **Design decisions**: Group admin model, reputation gossip, onion routing, MHR-Byte opcodes, emission schedule, protocol bridges, formal verification targets

---
sidebar_position: 3
title: Open Questions
---

# Open Questions

All questions — architectural and implementation-level — have been resolved. This page tracks the full resolution history.

## Resolved in v1.0 Spec Review (Round 4)

Implementation-level questions resolved with concrete specifications added to the relevant pages:

| # | Question | Resolution | Location |
|---|----------|------------|----------|
| 1 | Token Bucket Bandwidth Measurement | EMA with 60-second half-life; reset on transport change; 10% protocol overhead reserve | [Network Protocol](../protocol/network-protocol#congestion-control) |
| 2 | Epoch Active Set Conflict Resolution | 5% settlement count threshold for ACK vs NAK; 3-round wait before re-propose; post-merge reconciliation | [CRDT Ledger](../economics/crdt-ledger#epoch-proposer-selection) |
| 3 | Mutable Object Fork Detection Reporting | 5-step protocol: record, block 24h, gossip advisory, 7-day dedup, resolution via KeyCompromiseAdvisory | [NXS-Store](../services/nxs-store#mutable) |
| 4 | CongestionSignal on Multi-Interface Nodes | Replaced link_id with scope enum (ThisLink/AllOutbound); 3 bytes total | [Network Protocol](../protocol/network-protocol#congestion-control) |
| 5 | DHT Rebalancing Timing | 2 gossip rounds convergence on join; 6 additional missed rounds before re-replication; graceful degradation | [NXS-DHT](../services/nxs-dht#rebalancing) |
| 6 | Beacon Collision Handling | Density adaptation: interval doubles at 50% utilization, triples at 75%; Ring 1 gossip provides redundancy | [Discovery](../marketplace/discovery#presence-beacons) |
| 7 | Fragment Reassembly | 30s per-chunk timeout, exponential backoff (3 retries), 5-min overall, resumable via ChunkRequest | [NXS-Store](../services/nxs-store#reassembly) |
| 8 | Transitive Credit Rate-Limiting | Per-epoch, per-grantee tracking via CreditState struct; epoch-boundary reset; vouching peer absorbs defaults | [Trust Neighborhoods](../economics/trust-neighborhoods#trust-based-credit) |

## Resolved in v1.0 Spec Review (Round 3)

Protocol-level gaps identified in the third comprehensive review, resolved inline:

| Gap | Resolution | Location |
|-----|-----------|----------|
| Serialization format (endianness, encoding) | Little-endian, fixed-size binary, TLV for extensions, normalized scores on decoded values | [Specification](../specification#serialization-rules) |
| CompactPathCost normalization ambiguity | Normalization uses decoded values, not log-encoded wire values | [Network Protocol](../protocol/network-protocol#greedy-forwarding-with-cost-weighting) |
| Agreement lifecycle (expiry, renewal, billing) | Defined Active/Expired/Grace/Closed states, per-capability expiry behavior, renewal protocol | [Agreements](../marketplace/agreements#agreement-lifecycle) |
| Settlement timing (eager vs lazy) | Settlements to CRDT ledger are not per-win; created on cooperative close, dispute, or periodic finalization | [Payment Channels](../economics/payment-channels#settlement-timing) |
| Channel sequence semantics | Sequence is monotonic version number; replay protection via final_sequence comparison | [Payment Channels](../economics/payment-channels#sequence-number-semantics) |
| CapabilitySummary cost encoding | Identical log₂ formula to CompactPathCost; 0x0000=free, 0xFFFF=unknown | [Discovery](../marketplace/discovery#ring-1--2-3-hops) |
| Merkle root trust for constrained nodes | Signed by proposer; trusted peers accept immediately; untrusted requires 2-source quorum | [CRDT Ledger](../economics/crdt-ledger#merkle-root-trust) |
| Reputation initialization values | New peers start at 0; referrals capped at 5000; first-hand replaces after 5 interactions | [Security](../protocol/security#how-reputation-is-earned) |

## Resolved in Implementation Spec (Phase 1-2)

| # | Question | Resolution | Location |
|---|----------|------------|----------|
| 1 | WASM Sandbox Specification | Wasmtime runtime; Light (16 MB, 10^8 fuel, 5s) and Full (256 MB, 10^10 fuel, 30s) tiers; 10 host imports mirroring NXS-Byte System opcodes | [NXS-Compute](../services/nxs-compute#wasm-full-execution) |
| 2 | Presence Beacon Capability Bitfield | 8 assigned bits (relay, gateway, storage, compute-byte, compute-wasm, pubsub, dht, naming); bits 8-15 reserved | [Discovery](../marketplace/discovery#presence-beacons) |
| 3 | Ring 1 Capability Aggregation Format | `CapabilitySummary` struct: 8 bytes per type (type, count, min/avg cost, min/max hops) | [Discovery](../marketplace/discovery#ring-1--2-3-hops) |
| 4 | DHT Metadata Format | `DHTMetadata` struct: 129 bytes (key, size, content_type, owner, ttl, lamport_ts, Ed25519 signature) | [NXS-DHT](../services/nxs-dht#metadata-format) |
| 5 | Negotiation Protocol Wire Format | Single-round take-it-or-leave-it; 30-second timeout; `CapabilityRequest` + `CapabilityOffer` with nonce replay prevention | [Agreements](../marketplace/agreements#negotiation) |

## Resolved in v1.0 Spec Review

| # | Question | Resolution | Design Decision |
|---|----------|------------|-----------------|
| 1 | Multi-admin group messaging | Delegated co-admin model (up to 3 co-admins, no threshold signatures) | [Design Decisions](design-decisions#group-admin-delegated-co-admin-no-threshold-signatures) |
| 2 | Reputation gossip vs. first-hand only | Bounded 1-hop trust-weighted referrals, capped at 50%, advisory only | [Design Decisions](design-decisions#reputation-bounded-trust-weighted-referrals) |
| 3 | Onion routing for high-threat environments | Per-packet layered encryption, opt-in via PathPolicy, 3 hops default, 21% overhead on LoRa | [Design Decisions](design-decisions#onion-routing-per-packet-layered-encryption-opt-in) |
| 4 | NXS-Byte full opcode specification | 47 opcodes in 7 categories, reference interpreter in Rust, ESP32-calibrated cycle costs | [Design Decisions](design-decisions#nxs-byte-47-opcodes-with-reference-interpreter) |
| 5 | Bootstrap emission schedule parameters | 10^12 μNXS/epoch initial, discrete halving every 100K epochs, 0.1% tail floor | [Design Decisions](design-decisions#emission-schedule-epoch-counted-discrete-halving) |
| 6 | Protocol bridge design (SSB, Matrix, Briar) | Standalone gateway services, identity attestation, bridge operator pays NEXUS costs | [Design Decisions](design-decisions#protocol-bridges-standalone-gateway-services) |
| 7 | Formal verification targets | TLA+ priority-ordered: CRDT merge, payment channels, epoch checkpoints; composition deferred | [Design Decisions](design-decisions#formal-verification-priority-ordered-tla-targets) |

## Resolved in v1.0 Spec Hardening

Protocol-level gaps identified during comprehensive spec review, all resolved inline in the relevant spec pages:

| Gap | Resolution | Location |
|-----|-----------|----------|
| Announce propagation frequency | Event-driven + 30-min periodic refresh, 128-hop limit, 3-round link failure detection | [Network Protocol](../protocol/network-protocol#announce-propagation-rules) |
| ChaCha20 nonce handling | 64-bit counter per session key, zero-padded to 96 bits | [Security](../protocol/security#link-layer-encryption-hop-by-hop) |
| Session key rotation timing | Local monotonic clock, either side can initiate | [Security](../protocol/security#link-layer-encryption-hop-by-hop) |
| KeyCompromiseAdvisory replay | Added monotonic `sequence` field | [Security](../protocol/security#key-compromise-advisory) |
| Difficulty target formula | Local per-link computation, `win_prob = target_updates / observed_packets` | [Payment Channels](../economics/payment-channels#adaptive-difficulty) |
| Settlement validation | Every node validates (2 sig checks + hash + GSet lookup), invalid dropped silently | [CRDT Ledger](../economics/crdt-ledger#settlement-flow) |
| Active set definition | Nodes appearing as party in at least 1 settlement in last 2 epochs | [CRDT Ledger](../economics/crdt-ledger#epoch-lifecycle) |
| Bloom filter construction | k=13 Blake3-derived hash functions, 19.2 bits/element at 0.01% FPR | [CRDT Ledger](../economics/crdt-ledger#bloom-filter-sizing) |
| Relay compensation tracking | RelayWinSummary with spot-check proofs, challengeable during grace period | [CRDT Ledger](../economics/crdt-ledger#relay-compensation-tracking) |
| Roaming cache fingerprint stability | 60% overlap threshold for area recognition | [Discovery](../marketplace/discovery#roaming-cache) |
| Credit-based fast start staleness | Rate-limited grants, 2× balance requirement for staleness tolerance | [Discovery](../marketplace/discovery#credit-based-fast-start) |
| Trust relationship revocation | Asymmetric, revocable at any time, downgrades stored data priority | [Trust Neighborhoods](../economics/trust-neighborhoods#the-trust-graph) |

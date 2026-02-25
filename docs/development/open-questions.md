---
sidebar_position: 3
title: Open Questions
---

# Open Questions

All architectural design questions have been resolved. This page tracks remaining implementation-level questions and the full resolution history.

## Implementation Questions (Phase 1-2)

### 1. Token Bucket Bandwidth Measurement

**Context**: `LinkBucket.refill_rate` is defined as `measured_bandwidth × (1 - protocol_overhead)`, but "measured bandwidth" is unspecified.

**Questions**:
- Measurement window: trailing 1 minute? 5 minutes? Exponential moving average?
- On transport change (LoRa to WiFi): how quickly does the bucket adapt?
- Is there hysteresis to prevent oscillation between two close estimates?

**Phase**: 1 (congestion control implementation)

### 2. Epoch Active Set Conflict Resolution

**Context**: When multiple partitions propose epochs with different `active_set_hash` values (because they've seen different settlement participants), the merge semantics are underspecified.

**Questions**:
- If two proposals have similar settlement counts but different active sets, which wins?
- How does a node decide whether to NAK and re-propose vs. accept the proposer's set?
- After partition merge, how is the active set reconciled?

**Phase**: 2 (CRDT ledger implementation)

### 3. Mutable Object Fork Detection Reporting

**Context**: NXS-Store describes fork detection (same sequence, different content) but doesn't specify the response data structure or gossip behavior.

**Questions**:
- What data structure records a detected fork?
- Is there a `ForkAlert` gossip message, or is it purely local?
- How long is the fork flag retained? How does KeyCompromiseAdvisory clear it?

**Phase**: 2 (NXS-Store implementation)

### 4. CongestionSignal on Multi-Interface Nodes

**Context**: `CongestionSignal.link_id` is a local u8 identifier. When a multi-interface node signals congestion on its WiFi link, upstream LoRa peers receive a `link_id` that's meaningless to them.

**Question**: Should the signal identify the congested transport type (LoRa/WiFi/Cellular) rather than a local link ID? Or should it only indicate "the path through me is congested" without specifying which interface?

**Phase**: 1 (congestion control implementation)

### 5. DHT Rebalancing Timing After Node Churn

**Context**: DHT rebalancing on node join/departure is described at a high level but lacks timing guarantees.

**Questions**:
- On node join: how many gossip rounds before key push begins? (Proposed: 2 rounds for convergence)
- On node departure: how long after detection before re-replication starts? (Proposed: 6 additional missed rounds)
- If no reachable replacement exists, does durability degrade gracefully or block?

**Phase**: 2 (NXS-DHT implementation)

### 6. Beacon Collision Handling in High-Density Deployments

**Context**: Presence beacons broadcast every 10 seconds on all interfaces. In dense deployments (100+ nodes in LoRa range), collisions are likely.

**Questions**:
- Should beacon interval adapt to density (e.g., 20s when channel utilization exceeds 50%)?
- Are beacons local-only (not relayed), or can Ring 1 gossip serve as redundancy?
- What's the expected discovery latency in a 200-node dense mesh?

**Phase**: 1 (discovery implementation)

### 7. Fragment Reassembly for Large Objects

**Context**: NXS-Store chunks large files into 4 KB pieces, but reassembly timeouts and retry behavior are unspecified.

**Questions**:
- Per-chunk timeout? (Proposed: 30 seconds)
- Retry policy? (Proposed: exponential backoff, 3 retries, then try alternate provider)
- Overall reassembly timeout? (Proposed: 5 minutes)
- Is resumable download supported? (Partial chunk request format)

**Phase**: 2 (NXS-Store implementation)

### 8. Transitive Credit Rate-Limiting Granularity

**Context**: Friend-of-friend credit is capped at 10% of direct limit, but the rate-limiting time window is unspecified.

**Questions**:
- Is 10% a per-epoch limit, per-gossip-round limit, or an absolute cap?
- Does each friend-of-friend get a separate 10% allocation?
- What tracking data structure is needed? (Current `TrustConfig` has no timestamp fields)

**Phase**: 2 (trust neighborhoods implementation)

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

---
sidebar_position: 1
title: Roadmap
---

# Implementation Roadmap

The NEXUS implementation is organized into four phases, progressing from core networking fundamentals to a full ecosystem. Each phase has concrete milestones with acceptance criteria.

## Phase 1: Foundation

**Focus**: Core networking and basic economics — the minimum to run a mesh with cost-aware routing and micropayments.

### Milestone 1.1: Transport + Identity

- Implement `NodeIdentity` (Ed25519 keypair generation, destination hash derivation, X25519 conversion)
- Link-layer encryption (X25519 ECDH + ChaCha20-Poly1305, counter-based nonces, key rotation)
- Packet framing (Reticulum-compatible: header, addresses, context, data)
- Interface abstraction (LoRa, WiFi, serial — at least 2 transports working)
- Announce generation and forwarding with Ed25519 signature verification

**Acceptance**: Two nodes on different transports (e.g., LoRa + WiFi) can establish an encrypted link, exchange announces, and forward packets to each other. Packet contents are encrypted and unauthenticated nodes are rejected.

### Milestone 1.2: Routing + Gossip

- `CompactPathCost` (6-byte encoding/decoding, log-scale math, relay update logic)
- Routing table (`RoutingEntry` with cost, latency, bandwidth, hop count, reliability)
- Greedy forwarding with `PathPolicy` scoring (Cheapest, Fastest, Balanced)
- Gossip protocol (60-second rounds, bloom filter state summaries, delta exchange)
- Bandwidth budget enforcement (4-tier allocation, constrained-link adaptation)
- Announce propagation rules (event-driven + 30-min refresh, hop limit, expiry, link failure detection)

**Acceptance**: A 5-node mesh (mixed LoRa + WiFi) converges routing tables within 3 gossip rounds. Packets are forwarded via cost-optimal paths. Removing a node causes re-routing within 3 minutes. Gossip overhead stays within 10% budget on all links.

### Milestone 1.3: Congestion Control

- CSMA/CA on half-duplex links (listen-before-talk with exponential backoff)
- Per-neighbor token bucket (fair share, payment-weighted priority)
- 4-level priority queuing (P0 real-time through P3 bulk, starvation prevention)
- Backpressure signaling (4-byte CongestionSignal)
- Dynamic cost response (quadratic formula, propagated via gossip)

**Acceptance**: Under synthetic load, P0 packets (voice) maintain latency below 500ms while P3 (bulk) is throttled. Congestion on one link causes traffic to reroute via cost increase. No link exceeds its bandwidth budget.

### Milestone 1.4: Payment Channels

- VRF lottery implementation (ECVRF-ED25519-SHA512-TAI per RFC 9381)
- Adaptive difficulty (local per-link, formula: `win_prob = target_updates / observed_packets`)
- `ChannelState` (200 bytes, dual-signed, sequence-numbered)
- Channel lifecycle (open, update on win, settle, dispute with 2,880-round window, abandon after 4 epochs)
- `SettlementRecord` generation and dual-signature

**Acceptance**: Two nodes relay 1,000 packets. The relay wins the VRF lottery approximately `1000 × win_probability` times (within 2σ). Channel updates occur only on wins. Settlement produces a valid dual-signed record. Dispute resolution correctly rejects old states.

### Milestone 1.5: CRDT Ledger

- `AccountState` (GCounter for earned/spent, GSet for settlements)
- GCounter merge (pointwise max per-node entries)
- Settlement flow (validation: 2 sig checks + Blake3 hash + GSet dedup, gossip forward)
- Balance derivation (`earned - spent`, reject negative)
- Gossip integration (settlements propagate via Tier 2 bandwidth budget)

**Acceptance**: Three nodes settle channels pairwise. All balances converge correctly across the mesh within O(log N) gossip rounds. Duplicate settlements are rejected. A forged settlement (bad signature) is silently dropped by all nodes.

### Milestone 1.6: Hardware Targets

- ESP32 + LoRa firmware (relay only: transport, routing, gossip, payment channels, CRDT ledger)
- Raspberry Pi software (bridge: all ESP32 capabilities + multi-interface bridging + basic CLI)
- CLI tools: `nexus-keygen`, `nexus-node` (start/stop), `nexus-status` (routing table, channels, balances), `nexus-peer` (add/remove trusted peers)

**Acceptance**: An ESP32 node relays packets and earns VRF lottery wins. A Raspberry Pi bridges LoRa to WiFi. CLI tools show correct routing table, channel states, and balances. ESP32 firmware fits in flash and runs within 520 KB RAM.

### Phase 1 Deliverable

A working mesh network with cost-aware routing, encrypted links, stochastic micropayments, and a convergent CRDT ledger — running on real hardware (ESP32 + Raspberry Pi) with CLI management tools.

---

## Phase 2: Economics

**Focus**: Real-world deployment, economic mechanisms, and the minimum viable marketplace.

### Milestone 2.1: Trust Neighborhoods

- `TrustConfig` implementation (trusted peers, cost overrides, community labels)
- Free relay logic (sender trusted AND destination trusted → no lottery)
- Transitive credit (direct: full, friend-of-friend: 10%, 3+ hops: none)
- Credit rate limiting per trust distance

**Acceptance**: Trusted peers relay traffic for free with zero economic overhead. A friend-of-friend gets exactly 10% of the direct credit line. An untrusted node gets no transitive credit.

### Milestone 2.2: Epoch Compaction

- Epoch trigger logic (3-trigger: settlement count, GSet size, small-partition adaptive)
- Epoch proposer selection (eligibility rules, conflict resolution)
- Bloom filter construction (k=13 Blake3-derived, 0.01% FPR)
- Epoch lifecycle (Propose → Acknowledge at 67% → Activate → Verify → Finalize)
- Settlement proof submission during grace period
- Merkle-tree snapshot (full on backbone, sparse on constrained)
- `BalanceProof` generation and verification (~640 bytes for 1M nodes)
- `RelayWinSummary` aggregation and spot-check verification

**Acceptance**: A 20-node test network triggers epochs correctly under all three conditions. Bloom filter FPR is within 2× of theoretical 0.01%. Late-arriving settlements are recovered during the grace period. ESP32 nodes operate with sparse snapshots under 5 KB.

### Milestone 2.3: Capability Discovery

- `NodeCapabilities` advertisement structure (connectivity, compute, storage, availability)
- `PresenceBeacon` (20 bytes, broadcast every 10 seconds)
- Discovery rings (Ring 0 full, Ring 1 summarized, Ring 2 periodic, Ring 3 query-only)
- Mobile handoff (beacon scan → relay selection → link establishment → channel open)
- Credit-based fast start (`CreditGrant` with staleness tolerance and rate limiting)
- Roaming cache (area fingerprint with 60% overlap tolerance, 30-day TTL)

**Acceptance**: A mobile node (laptop) moves between two WiFi areas and hands off to a new relay within 500ms. Credit-based fast start allows immediate traffic while the channel opens. Returning to the first area reuses the cached channel with zero handoff latency.

### Milestone 2.4: Reputation

- `PeerReputation` scoring (relay, storage, compute scores 0-10000)
- Score update formulas (success: diminishing gains, failure: 10% penalty)
- Trust-weighted referrals (1-hop, capped at 50%, weighted at 30% × trust, 500-round expiry)
- Reputation integration with credit line sizing and capability selection

**Acceptance**: A node that successfully relays 100 packets has a relay score above 5000. A node that fails 3 out of 10 agreements has a score below 3000. Referral scores are capped at 5000 and overwritten by first-hand experience.

### Milestone 2.5: Test Networks

- Deploy 3-5 physical test networks (urban, rural, indoor, mixed)
- Each network: 10-50 nodes across at least 2 transport types
- Instrument for: routing convergence time, payment overhead, epoch timing, gossip bandwidth
- Run for at least 4 weeks per network
- Document: failure modes, parameter tuning, real-world performance vs. spec predictions

**Acceptance**: Test networks operate continuously for 4 weeks. Routing converges within spec. Payment overhead stays within 0.5% on LoRa. At least one epoch completes successfully per network. Published test report with metrics.

### Phase 2 Deliverable

Test networks with functioning trust-based economics, epoch compaction, capability discovery, mobile handoff, and reputation scoring — validated on real hardware over multiple weeks.

---

## Phase 3: Services

**Focus**: Service primitives and first applications.

### Milestone 3.1: NXS-Store

- `DataObject` types (Immutable, Mutable, Ephemeral)
- Storage agreements (bilateral, pay-per-duration)
- Proof of storage (Blake3 Merkle challenge-response)
- Erasure coding (Reed-Solomon, default schemes by size)
- Repair protocol (detect failure → assess → reconstruct → re-store)
- Garbage collection (7-tier priority)

### Milestone 3.2: NXS-DHT

- DHT routing (XOR distance + cost weighting, α=0.7)
- k=3 replication with cost-bounded storage set
- Lookup and publication protocols
- Cache management (publisher TTL, 24-hour local cap, LRU eviction)
- Light client verification (3-tier: content-hash, signature, multi-source)

### Milestone 3.3: NXS-Pub

- Subscription types (Key, Prefix, Node, Neighborhood)
- Delivery modes (Push, Digest, PullHint)
- Bandwidth-adaptive mode selection

### Milestone 3.4: NXS-Compute (NXS-Byte)

- 47-opcode interpreter implementation in Rust
- Cycle cost enforcement (ESP32-calibrated)
- Resource limit enforcement (max_memory, max_cycles, max_state_size)
- Compute delegation via capability marketplace
- Reference test vector suite for cross-platform conformance

### Milestone 3.5: Applications

- Messaging (E2E encrypted, store-and-forward, group messaging with co-admin delegation)
- Social (profiles, feeds, followers, media tiering)
- NXS-Name (community-label-scoped naming, conflict resolution, petnames)

### Phase 3 Deliverable

Usable messaging and social applications running on the mesh, with decentralized storage, DHT-based content discovery, and contract execution on constrained devices.

---

## Phase 4: Ecosystem

**Focus**: Advanced capabilities and ecosystem growth.

### Milestone 4.1: Advanced Compute

- WASM execution environment for gateway/backbone nodes
- Private compute tiers (Split Inference, Secret Sharing, TEE)
- Heavy compute capabilities (ML inference, transcription, TTS)

### Milestone 4.2: Rich Applications

- Voice (Codec2 on LoRa, Opus on WiFi, bandwidth bridging)
- Forums (append-only logs, moderation contracts)
- Marketplace (listings, escrow contracts)
- Wiki (CRDT-merged collaborative documents)

### Milestone 4.3: Interoperability

- Third-party protocol bridges (SSB, Matrix, Briar) — [standalone gateway services](design-decisions#protocol-bridges-standalone-gateway-services) with identity attestation
- Onion routing implementation (`PathPolicy.ONION_ROUTE`, per-packet layered encryption)

### Milestone 4.4: Ecosystem Growth

- Hardware partnerships and reference design refinement
- Developer SDK and documentation
- Community-driven capability development

### Phase 4 Deliverable

A full-featured decentralized platform with rich applications, privacy-enhanced routing, and interoperability with existing protocols.

---

## Implementation Language

The primary implementation language is **Rust**, chosen for:

- Memory safety without garbage collection (critical for embedded targets)
- `no_std` support for ESP32 firmware
- Strong ecosystem for cryptography and networking
- Single codebase from microcontroller to server

## Test Network Strategy

Real physical test networks, not simulations:

- Simulation cannot capture the realities of LoRa propagation, WiFi interference, and real-world device failure modes
- Each test network should represent a different deployment scenario (urban, rural, indoor, mixed)
- Test networks validate both the protocol and the economic model

## Phase 1 Implementability Assessment

Phase 1 is **fully implementable** with the current specification. All protocol-level gaps have been resolved:

| Component | Spec Status | Key References |
|-----------|------------|----------------|
| Identity + Encryption | Complete | [Security](../protocol/security) |
| Packet format + CompactPathCost | Complete (wire format specified) | [Network Protocol](../protocol/network-protocol#nexus-extension-compact-path-cost) |
| Routing + Announce propagation | Complete (scoring, announce rules, expiry, failure detection) | [Network Protocol](../protocol/network-protocol#routing) |
| Gossip protocol | Complete (bloom filter, bandwidth budget, 4-tier) | [Network Protocol](../protocol/network-protocol#gossip-protocol) |
| Congestion control | Complete (3-layer, priority levels, backpressure) | [Network Protocol](../protocol/network-protocol#congestion-control) |
| VRF lottery + Payment channels | Complete (RFC 9381, difficulty formula, channel lifecycle) | [Payment Channels](../economics/payment-channels) |
| CRDT ledger + Settlement | Complete (validation rules, GCounter merge, GSet dedup) | [CRDT Ledger](../economics/crdt-ledger) |
| Hardware targets | Complete (ESP32 + Pi reference designs) | [Reference Designs](../hardware/reference-designs) |

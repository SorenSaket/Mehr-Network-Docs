---
sidebar_position: 1
title: Roadmap
description: "Four-phase implementation roadmap from Linux server MVP to full mobile mesh ecosystem with bridges and advanced compute."
keywords:
  - roadmap
  - implementation
  - phases
  - MVP
  - development
  - milestones
---

# Implementation Roadmap

The Mehr implementation follows a **server-first** strategy: get the protocol running on well-connected Linux servers over traditional internet, prove the core services work, then extend to phones and mesh radio. The protocol spec is comprehensive because it needs to be — but implementation is ruthlessly phased. Each phase delivers something people can use, not just something that passes tests.

```mermaid
graph LR
    P1["<b>Phase 1: Linux Server Node (MVP)</b><br/>TCP/IP transport<br/>Storage + DHT<br/>Trust graph<br/>Free tier only<br/><i>Users: server operators</i>"]
    P2["<b>Phase 2: Economics + Social</b><br/>Payment channels<br/>VRF lottery<br/>CRDT ledger<br/>Social feeds<br/><i>Users: economy bootstraps</i>"]
    P3["<b>Phase 3: Mobile + Mesh</b><br/>Phone apps<br/>LoRa relay nodes<br/>WiFi/BLE mesh<br/>Gateway operators<br/><i>Users: mobile communities</i>"]
    P4["<b>Phase 4: Full Ecosystem</b><br/>Advanced compute<br/>Licensing<br/>Onion routing<br/>Protocol bridges<br/><i>Users: mature ecosystem</i>"]

    P1 --> P2 --> P3 --> P4
```

**Principle**: Start where the resources are. Servers have bandwidth, uptime, storage, and compute. Debug the protocol on reliable hardware over reliable links, then extend to constrained devices and radio. The free tier (trusted peer communication) is a complete product on its own. MHR tokens, economics, and advanced features come only after there are real nodes generating real traffic. Token follows utility, never leads it.

---

## Phase 1: Server Node (MVP)

**Focus**: A Linux daemon that lets servers join a decentralized network, providing compute, storage, and relay services over standard internet connections. The free tier only — no tokens, no payment.

**Why server first**: Servers have public IPs (or easily configured port forwarding), reliable uptime, abundant bandwidth, and real storage and compute resources to offer. TCP/IP transport is trivial compared to radio. This is the fastest path to a working protocol — debug routing, gossip, storage, and DHT on hardware that can actually run them well, without fighting radio propagation, phone OS restrictions, or constrained-device limitations. The `no_std` constraint for ESP32 can be added later; starting with the full Rust standard library makes development significantly faster.

### Milestone 1.1: Core Protocol Library (Rust)

- `NodeIdentity` (Ed25519 keypair generation, destination hash derivation, X25519 conversion)
- Link-layer encryption (X25519 ECDH + ChaCha20-Poly1305, counter-based nonces, key rotation)
- Packet framing (Reticulum-compatible: header, addresses, context, data)
- TCP transport interface (outbound connections, bidirectional links, keepalive)
- Announce generation and forwarding with Ed25519 signature verification

**Acceptance**: Two Linux nodes establish an encrypted link over TCP, exchange announces, and forward packets. Unauthenticated nodes are rejected.

### Milestone 1.2: Bootstrap + Peer Discovery

- DNS-based genesis gateway discovery (well-known domain resolves to genesis gateway IPs — primary bootstrap method)
- Hardcoded bootstrap node list as fallback (known IP:port pairs, including genesis gateway addresses)
- Peer exchange protocol (connected peers share their known peer lists)
- Outbound-only NAT traversal (nodes behind NAT connect outbound to bootstrap nodes; TCP connection is bidirectional once established)
- Peer persistence (remember previously connected peers across restarts)

**Acceptance**: A new node discovers the genesis gateway via DNS and connects to the network within 30 seconds. After 3 gossip rounds, the node has discovered peers beyond the genesis gateway. Fallback to hardcoded list works when DNS is unavailable. A node behind NAT connects outbound and participates fully as a relay. Restarting a node reconnects to previously known peers without hitting the bootstrap list.

### Milestone 1.3: Routing + Gossip

- `CompactPathCost` (6-byte encoding/decoding, log-scale math, relay update logic)
- Routing table (`RoutingEntry` with cost, latency, bandwidth, hop count, reliability)
- Greedy forwarding with `PathPolicy` scoring (Cheapest, Fastest, Balanced)
- Gossip protocol (60-second rounds, bloom filter state summaries, delta exchange)
- Bandwidth budget enforcement (4-tier allocation)
- Announce propagation rules (event-driven + 30-min refresh, hop limit, expiry, link failure detection)

**Acceptance**: A 10-node network converges routing tables within 3 gossip rounds. Packets are forwarded via cost-optimal paths. Removing a node causes re-routing within 3 minutes. Gossip overhead stays within 10% budget.

### Milestone 1.4: Trust Graph + Free Relay

- `TrustConfig` implementation (trusted peers, cost overrides, scopes)
- Free relay logic (sender trusted AND destination trusted → no lottery, no channels)
- Adding/removing trusted peers

**Acceptance**: Trusted peers relay traffic for free with zero economic overhead. The full relay stack works with zero tokens in circulation.

### Milestone 1.5: MHR-Store

- `DataObject` types (Immutable, Mutable, Ephemeral)
- Storage agreements (bilateral, free between trusted peers initially)
- Proof of storage (Blake3 Merkle challenge-response)
- Erasure coding (Reed-Solomon, default schemes by size)
- Repair protocol (detect failure → assess → reconstruct → re-store)
- Garbage collection (7-tier priority)
- Chunking (4 KB chunks, parallel retrieval, resumable transfers)

**Acceptance**: A node stores a DataObject with replication factor 3 across the network. Proof-of-storage challenges pass. Erasure coding reconstructs from k of n chunks. Chunked transfer resumes after interruption.

### Milestone 1.6: MHR-DHT + MHR-Pub

- DHT routing (XOR distance + cost weighting, α=0.7)
- k=3 replication with cost-bounded storage set
- Lookup and publication protocols
- Subscription types (Key, Prefix, Node, Scope)
- Delivery modes (Push, Digest, PullHint)
- Bandwidth-adaptive mode selection

**Acceptance**: A node publishes a DataObject and it's discoverable via DHT lookup from any node in the network. MHR-Pub delivers notifications to subscribers within 2 gossip rounds.

### Milestone 1.7: Linux Daemon + CLI

- `mehrd` daemon (background process, systemd service file)
- Configuration file (bootstrap peers, listen address, storage path, trust config)
- CLI tool (`mehr`) for node management:
  - `mehr status` — node identity, connected peers, routing table summary
  - `mehr peers` — list connected peers with link quality metrics
  - `mehr trust add/remove <destination_hash>` — manage trusted peers
  - `mehr store put/get <file>` — store and retrieve data objects
  - `mehr dht lookup <key>` — query the DHT
- Logging and metrics (structured logs, Prometheus-compatible metrics endpoint)

**Acceptance**: A sysadmin can install the daemon, configure bootstrap peers, and join the network. The CLI provides full visibility into node state. The daemon runs unattended and recovers from restarts.

### Phase 1 Deliverable

**A network of Linux servers providing decentralized storage and relay.** Install the daemon, configure a few bootstrap peers, and your server joins the network — contributing storage, relay bandwidth, and DHT capacity. Trust your friends' servers for free relay. This is the foundation everything else builds on.

**Target audiences**: homelabbers, self-hosting enthusiasts, VPS operators, privacy-conscious sysadmins, distributed systems developers.

---

## Phase 2: Economic Layer + Social

**Focus**: MHR token genesis, payment infrastructure, and social features. With real servers generating real traffic and providing real storage, economics can be validated against actual usage patterns.

### Milestone 2.1: Payment Channels

- VRF lottery implementation (ECVRF-ED25519-SHA512-TAI per RFC 9381)
- Adaptive difficulty (local per-link, formula: `win_prob = target_updates / observed_packets`)
- `ChannelState` (200 bytes, dual-signed, sequence-numbered)
- Channel lifecycle (open, update on win, settle, dispute with 2,880-round window, abandon after 4 epochs)
- `SettlementRecord` generation and dual-signature

**Acceptance**: Two nodes relay 1,000 packets. The relay wins the VRF lottery approximately `1000 × win_probability` times (within 2σ). Channel updates occur only on wins. Settlement produces a valid dual-signed record. Dispute resolution correctly rejects old states.

### Milestone 2.2: CRDT Ledger + Epoch Compaction

- `AccountState` (GCounter for earned/spent, GSet for settlements)
- GCounter merge (pointwise max per-node entries)
- GCounter rebase at epoch compaction (prevents overflow from money velocity)
- Settlement flow (validation: 2 sig checks + Blake3 hash + GSet dedup, gossip forward)
- Balance derivation (`earned - spent`, reject negative)
- Epoch trigger logic (3-trigger: settlement count, GSet size, small-partition adaptive)
- Epoch lifecycle (Propose → Acknowledge at 67% → Activate → Verify → Finalize)
- Merkle-tree snapshot (full tree — servers have the memory for it)
- `BalanceProof` generation and verification

**Acceptance**: A 20-node network triggers epochs correctly. Balances converge across the network. GCounter rebase keeps counters bounded.

### Milestone 2.3: Token Genesis + Demand-Backed Mining

- Emission schedule implementation (10^12 μMHR/epoch, halving every 100,000 epochs, shift clamp at 63)
- Tail emission floor (0.1% of circulating supply annually)
- Genesis allocation to genesis gateway operator (transparent, visible in ledger from epoch 0)
- Demand-backed minting eligibility (VRF wins count only on funded-channel traffic)
- Revenue-capped minting (`effective_minting = min(emission_schedule, 0.5 × total_channel_debits)`)
- `RelayWinSummary` aggregation per epoch (demand-backed wins only)
- Mint distribution proportional to verified VRF lottery wins
- Channel-funded relay payments (coexist with minting)

**Acceptance**: The first epoch mints MHR and distributes it to relay nodes. Genesis allocation is visible in the ledger. Distribution is proportional to demand-backed wins. Minting on unfunded-channel traffic is rejected. Revenue cap limits minting to 50% of channel debits. Minting and channel payments coexist. Token supply follows the emission schedule.

### Milestone 2.4: Reputation + Credit

- `PeerReputation` scoring (relay, storage, compute scores 0-10000)
- Score update formulas (success: diminishing gains, failure: 10% penalty)
- Trust-weighted referrals (1-hop, capped at 50%)
- Transitive credit (direct: full, friend-of-friend: 10%, 3+ hops: none)
- `CreditState` tracking per grantee
- Credit rate limiting per trust distance and per epoch

**Acceptance**: Reliable nodes build reputation. Credit extends through trust graph. A friend-of-friend gets exactly 10% of the direct credit line. Default handling absorbs debt correctly.

### Milestone 2.5: Paid Storage + Kickback

- StorageAgreement with payment channel integration (pay-per-duration)
- Kickback fields (revenue sharing between storage node and content author)
- Self-funding content detection (kickback exceeds storage cost)
- Content propagation through scope hierarchy

**Acceptance**: Storage nodes earn for hosting data. Kickback flows correctly on retrieval. Self-funding content persists without author payment.

### Milestone 2.6: Social Layer

- `PostEnvelope` (free layer) + `SocialPost` (paid layer) — mutable DataObjects
- `UserProfile` (display name, bio, avatar, scopes, claims)
- Hierarchical scopes (Geo + Topic) with scope matching
- Five feed types: follow, geographic, interest, intersection, curated
- `CuratedFeed` with curator kickback
- Publishing flow (post_id generation, envelope propagation)
- Editing (mutable DataObject semantics, sequence versioning)
- Replies, boosts, references
- MHR-Name (scope-based naming, conflict resolution, petnames)

**Acceptance**: A user publishes a post tagged with geographic and interest scopes. The post's envelope appears in subscribers' feeds. Readers pay to fetch full content. Kickback flows to author. Curated feeds work end-to-end.

### Milestone 2.7: MHR-Compute

- 47-opcode MHR-Byte interpreter implementation in Rust
- Cycle cost enforcement
- Resource limit enforcement (max_memory, max_cycles, max_state_size)
- WASM execution environment (Wasmtime, Light + Full tiers)
- Compute delegation via capability marketplace
- Reference test vector suite for cross-platform conformance

**Acceptance**: A compute contract executes on a server node. MHR-Byte and WASM produce identical results for the same inputs. Compute delegation routes requests to capable nodes. Cycle cost metering terminates runaway contracts.

### Milestone 2.8: Test Network

- Deploy a 20-50 node test network across multiple server operators
- Instrument for: routing convergence, gossip bandwidth, storage reliability, economic dynamics, social UX
- Run for at least 8 weeks
- Document: failure modes, parameter tuning, real-world performance, economic balance

**Acceptance**: Test network operates continuously for 8 weeks. Storage proofs pass reliably. Token economy reaches equilibrium. Published test report with metrics.

### Phase 2 Deliverable

**A functioning decentralized economy on Linux servers.** MHR tokens enter circulation through proof-of-service. Server operators earn by relaying traffic and hosting storage. Content creators earn through kickback. Compute delegation works. The economic layer is live, validated on real servers with real traffic.

---

## Phase 3: Mobile + Mesh

**Focus**: Bring the proven protocol to phones and mesh radio. The protocol is already battle-tested on servers — now extend it to constrained devices and transport-independent operation.

### Milestone 3.1: `no_std` Core Library

- Factor the core protocol library into `no_std`-compatible crate
- Separate transport-specific code (TCP) from protocol logic
- Verify all crypto operations work without `std` (Ed25519, X25519, ChaCha20, Blake3)
- Sparse Merkle-tree snapshots for constrained devices (under 5 KB)

**Acceptance**: The core protocol library compiles for `no_std` targets. All protocol-level tests pass on both `std` and `no_std` builds.

### Milestone 3.2: Phone Apps

- Android app (Kotlin/Rust FFI) — Android first for broader device support and sideloading
- iOS app (Swift/Rust FFI) — follows Android
- Contact management (add trusted peers via QR code, NFC, or manual key entry)
- Messaging UI (conversations, groups, media sending adapted to link quality)
- E2E encrypted messaging (store-and-forward, offline delivery)
- Group messaging with co-admin delegation
- Voice on WiFi links (Opus codec)
- Connect to server network over internet (phone as a light client)
- WiFi Direct and BLE transport for local phone-to-phone mesh
- Background mesh relay (phone relays traffic while in pocket)
- Multi-transport handoff (internet ↔ WiFi Direct ↔ BLE, seamless)

**Acceptance**: A non-technical user can install the app, add a friend via QR code, and exchange messages. The app connects to the server network over internet for relay and storage. Phone-to-phone WiFi Direct messaging works without internet. Voice calls work on WiFi links.

### Milestone 3.3: LoRa Transport

- LoRa interface implementation (SX1276/SX1262 via `no_std` Rust)
- Off-the-shelf hardware support:
  - Heltec WiFi LoRa 32 (~$15)
  - LILYGO T-Beam (~$25, with GPS)
  - RAK WisBlock (~$30, modular)
  - RNode (Reticulum-native)
- LTE-M and NB-IoT interface support (carrier-managed LPWAN)
- Multi-interface bridging (phone WiFi ↔ LoRa relay ↔ WiFi ↔ server network)
- Solar relay firmware (ESP32 L1: transport, routing, gossip — runs on $30 solar kit)
- Congestion control tuning for constrained links (CSMA/CA, backpressure)

**Acceptance**: A LoRa relay extends the network to areas without internet. A phone sends a message that hops: phone → WiFi → LoRa relay → WiFi → server → destination. Solar relay runs unattended for 30+ days.

### Milestone 3.4: Gateway Operators

- Gateway trust-based onboarding (add consumer to trusted_peers, extend credit)
- Fiat billing integration (subscription, prepaid, pay-as-you-go — gateway's choice)
- Cloud storage via gateway (consumer stores files, gateway handles MHR)
- Gateway-provided connectivity (ethernet ports, WiFi access points)

The [genesis service gateway](../economics/token-economics#genesis-service-gateway) is the first instance of this pattern — it bootstraps the economy in Phase 2. This milestone generalizes gateway mechanics for any operator to deploy.

**Acceptance**: A consumer signs up with a gateway, pays fiat, and uses the network without seeing MHR. Traffic flows through gateway trust. Consumer can switch gateways without losing identity.

### Milestone 3.5: Mesh Test Networks

- Deploy 3-5 physical test networks (urban, rural, campus, event)
- Each network: 10-50 nodes (phones + LoRa relays + server backbone) across at least 2 transports
- Instrument for: routing convergence, gossip bandwidth, storage reliability, mesh UX
- Run for at least 4 weeks per network
- Document: failure modes, parameter tuning, real-world performance

**Acceptance**: Test networks operate continuously for 4 weeks. Users report messaging and mesh features work reliably. Published test report with metrics.

### Phase 3 Deliverable

**The full network: servers as backbone, phones as endpoints, mesh radio for off-grid.** Phone users get encrypted messaging and social feeds backed by the server network's storage and compute. LoRa relays extend coverage to areas without internet. Gateway operators bridge fiat consumers to the mesh economy. The same protocol runs from $30 ESP32 to datacenter servers.

---

## Phase 4: Full Ecosystem

**Focus**: Advanced capabilities, application richness, and ecosystem growth.

### Milestone 4.1: Identity + Governance

- Identity claims and vouches (GeoPresence, CommunityMember, KeyRotation, Capability, ExternalIdentity)
- RadioRangeProof (geographic verification via LoRa beacons)
- Peer attestation and transitive confidence
- Vouch lifecycle (create, gossip, verify, renew, revoke)
- Voting prerequisites (geographic eligibility from verified claims)

### Milestone 4.2: Rich Applications

- Voice (Codec2 on LoRa, Opus on WiFi, bandwidth bridging, seamless handoff)
- Digital licensing (LicenseOffer, LicenseGrant, verification chain, off-network verifiability)
- Cloud storage (client-side encryption, erasure coding, sync between devices, file sharing)
- Forums (append-only logs, moderation contracts)
- Marketplace (listings, escrow contracts)

### Milestone 4.3: Interoperability + Privacy

- Third-party protocol bridges (SSB, Matrix, Briar) — [standalone gateway services](design-decisions#protocol-bridges-standalone-gateway-services) with identity attestation
- Onion routing implementation (`PathPolicy.ONION_ROUTE`, per-packet layered encryption)
- Private compute tiers (Split Inference, Secret Sharing, TEE)

### Milestone 4.4: Ecosystem Growth

- Developer SDK and documentation
- Community-driven capability development
- Hardware partnerships and reference design refinement (informed by real deployment data)
- Custom hardware (only if demand justifies — let usage data guide form factors)

### Phase 4 Deliverable

A full-featured decentralized platform with rich applications, privacy-enhanced routing, identity governance, and interoperability with existing protocols.

---

## Implementation Language

The primary implementation language is **Rust**, chosen for:

- Memory safety without garbage collection (critical for embedded targets)
- `no_std` support for ESP32 firmware (added in Phase 3)
- Strong ecosystem for cryptography and networking
- Single codebase from microcontroller to server
- FFI to Kotlin (Android) and Swift (iOS) for phone apps

Phase 1-2 use the full standard library. The `no_std` factoring happens at the start of Phase 3 when embedded targets are introduced.

## Platform Targets

| Platform | Implementation | Phase |
|----------|---------------|-------|
| Linux server / desktop | Rust native daemon + CLI (full node) | Phase 1 |
| Raspberry Pi / Linux SBC | Rust native (bridge, gateway, storage) | Phase 1-2 |
| Android phone | Rust core + Kotlin UI via FFI | Phase 3 |
| iOS phone | Rust core + Swift UI via FFI | Phase 3 |
| ESP32 + LoRa | Rust `no_std` (L1 relay) | Phase 3 |

All implementations speak the same wire protocol and interoperate on the same network.

## Bootstrap Strategy

New nodes discover the network through a layered bootstrap mechanism:

1. **Hardcoded bootstrap list**: The daemon ships with a list of known bootstrap node IP:port pairs. These are well-connected, high-uptime servers operated by early network participants.
2. **DNS bootstrap**: A well-known domain resolves to current bootstrap node IPs. This allows updating the bootstrap list without software releases.
3. **Peer exchange**: Once connected to any node, the gossip protocol discovers the rest of the network. Connected peers share their known peer lists.
4. **Peer persistence**: Previously connected peers are remembered across restarts, so a node that has been online before rarely needs the bootstrap list.

The bootstrap list is a starting point, not a dependency. After initial connection, the announce mechanism and gossip protocol handle all peer discovery. Bootstrap nodes have no special protocol role — they are ordinary nodes that happen to be well-known.

## NAT Traversal

Most servers targeted in Phase 1 have public IPs or easily configured port forwarding. For nodes behind NAT:

- **Outbound TCP connections** traverse NAT automatically. A node behind NAT connects outbound to a known peer; the TCP connection is bidirectional once established. This covers the vast majority of home server setups.
- **Relay forwarding**: A node that cannot accept inbound connections is still reachable — traffic routes through peers that have direct links to it. This is standard Mehr relay operation.
- **UPnP/NAT-PMP** (optional): Automatic port forwarding on consumer routers, attempted on startup.
- **UDP hole punching** (Phase 3+): For phone-to-phone mesh scenarios where both parties are behind NAT.

No STUN/TURN servers are required. The Mehr relay mechanism itself provides the relay function that TURN would otherwise fill.

## Test Network Strategy

Real distributed test networks, not simulations:

- Phase 1 test networks are server-only (TCP/IP over internet)
- Phase 2 test networks enable economics and measure token dynamics on real traffic
- Phase 3 test networks add phones and LoRa relays, validating the full transport range
- Each test network should represent a different deployment scenario
- Test networks validate both the protocol and the user experience

## Why This Order

The previous roadmap (phone-mesh-first) would require solving radio transport, constrained-device limitations, phone OS restrictions, and `no_std` compatibility before any protocol logic could be tested. This roadmap gets the protocol running first on hardware where development is fast, then extends to harder targets:

| Phase | What Users Get | What the Network Gets |
|-------|---------------|---------------------|
| 1 | Decentralized storage + relay on Linux servers | Real nodes, real traffic, battle-tested protocol |
| 2 | Token economy, social feeds, compute | Real economic data, real market pricing |
| 3 | Phone apps, mesh radio, off-grid operation | Mobile users, mesh coverage, transport diversity |
| 4 | Rich apps, privacy, interoperability | Mature ecosystem |

Each phase is viable on its own. Phase 1 is a useful product even if phones never ship — a decentralized storage and relay network for server operators. Phase 2 adds a functioning economy. Phase 3 extends to mobile and mesh. No phase depends on token speculation or hardware manufacturing for its value.

**Key advantage**: By the time Phase 3 tackles constrained devices and radio, the protocol is already proven. Bugs in routing, gossip, storage, DHT, and economics have been found and fixed on servers where debugging is easy. The `no_std` factoring is a well-scoped engineering task applied to known-good code, not a simultaneous protocol design and embedded engineering challenge.

## Implementability Assessment

Phase 1 is **fully implementable** with the current specification. All protocol-level gaps have been resolved:

| Component | Spec Status | Key References |
|-----------|------------|----------------|
| Identity + Encryption | Complete | [Security](../protocol/security) |
| Packet format + CompactPathCost | Complete (wire format specified) | [Network Protocol](../protocol/network-protocol#mehr-extension-compact-path-cost) |
| Routing + Announce propagation | Complete (scoring, announce rules, expiry, failure detection) | [Network Protocol](../protocol/network-protocol#routing) |
| Gossip protocol | Complete (bloom filter, bandwidth budget, 4-tier) | [Network Protocol](../protocol/network-protocol#gossip-protocol) |
| Congestion control | Complete (3-layer, priority levels, backpressure) | [Network Protocol](../protocol/network-protocol#congestion-control) |
| Trust neighborhoods | Complete (free relay, credit, scopes) | [Trust & Neighborhoods](../economics/trust-neighborhoods) |
| MHR-Store | Complete (agreements, proofs, erasure coding, repair) | [MHR-Store](../services/mhr-store) |
| MHR-DHT + MHR-Pub | Complete (routing, replication, subscriptions) | [MHR-DHT](../services/mhr-dht), [MHR-Pub](../services/mhr-pub) |
| VRF lottery + Payment channels | Complete (RFC 9381, difficulty formula, channel lifecycle) | [Payment Channels](../economics/payment-channels) |
| CRDT ledger + Settlement | Complete (validation rules, GCounter merge, GSet dedup, rebase) | [CRDT Ledger](../economics/crdt-ledger) |

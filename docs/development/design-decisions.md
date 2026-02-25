---
sidebar_position: 2
title: Design Decisions
---

# Design Decisions Log

This page documents the key architectural decisions made during Mehr protocol design, including alternatives considered and the rationale for each choice.

## Network Stack: Reticulum as Initial Transport

| | |
|---|---|
| **Chosen** | Use [Reticulum Network Stack](https://reticulum.network/) as the initial transport implementation; treat it as a [swappable layer](#transport-layer-swappable-implementation) |
| **Alternatives** | Clean-room implementation from day one, libp2p, custom protocol |
| **Rationale** | Reticulum already solves transport abstraction, cryptographic identity, mandatory encryption, sender anonymity (no source address), and announce-based routing — all proven on LoRa at 5 bps. Mehr extends it with CompactPathCost annotations and economic primitives rather than reinventing a tested foundation. The transport layer is an implementation detail: Mehr defines the interface it needs and can switch to a clean-room implementation in the future without affecting any layer above. |

## Routing: Kleinberg Small-World with Cost Weighting

| | |
|---|---|
| **Chosen** | Greedy forwarding on a Kleinberg small-world graph with cost-weighted scoring |
| **Alternatives** | Pure Reticulum announce model, Kademlia, BGP-style routing, Freenet-style location swapping |
| **Rationale** | The physical mesh naturally forms a small-world graph: short-range radio links serve as lattice edges, backbone/gateway links serve as Kleinberg long-range contacts. Greedy forwarding achieves O(log² N) expected hops — a formal scalability guarantee. Cost weighting trades path length for economic efficiency. Unlike Freenet, no location swapping is needed because destination hashes are self-assigned and Reticulum announcements build the navigable topology. |

## Payment: Stochastic Relay Rewards

| | |
|---|---|
| **Chosen** | Probabilistic micropayments via VRF-based lottery (channel update only on wins) |
| **Alternatives** | Per-packet accounting, per-minute batched accounting, subscription-based, random-nonce lottery |
| **Rationale** | Per-packet and batched payment require frequent channel state updates, consuming ~2-4% bandwidth on LoRa links. Stochastic rewards achieve the same expected income but trigger updates only on lottery wins — reducing economic overhead by ~10x. Adaptive difficulty ensures fairness across traffic levels. The law of large numbers guarantees convergence for active relays. **The lottery uses a VRF (ECVRF-ED25519-SHA512-TAI, RFC 9381)** rather than a random nonce to prevent relay nodes from grinding nonces to win every packet. The VRF produces exactly one verifiable output per (relay key, packet) pair, reusing the existing Ed25519 keypair. |

## Settlement: CRDT Ledger

| | |
|---|---|
| **Chosen** | CRDT ledger (GCounters + GSet) |
| **Alternatives** | Blockchain, federated sidechain |
| **Rationale** | Partition tolerance is non-negotiable. CRDTs converge without consensus. A blockchain requires global ordering, which is impossible when network partitions are expected operating conditions. **Tradeoff**: double-spend prevention is probabilistic, not perfect. Mitigated by channel deposits, credit limits, reputation staking, and blacklisting — making cheating economically irrational for micropayments. |

## Communities: Emergent Trust Neighborhoods

| | |
|---|---|
| **Chosen** | Trust graph with emergent neighborhoods (no explicit zones) |
| **Alternatives** | Explicit zones with admin keys and admission policies (v0.8 design) |
| **Rationale** | Explicit zones require someone to create and manage them — centralized thinking in decentralized clothing. They impose UX burden and artificially fragment communities. Trust neighborhoods emerge naturally from who you trust: free communication between trusted peers, paid between strangers. No admin, no governance, no admission policies. Communities form the same way they form in real life — through relationships, not administrative acts. The trust graph provides Sybil resistance economically (vouching peers absorb debts). |

## Compaction: Epoch Checkpoints with Bloom Filters

| | |
|---|---|
| **Chosen** | Epoch checkpoints with bloom filters |
| **Alternatives** | Per-settlement garbage collection, TTL-based expiry |
| **Rationale** | The settlement GSet grows without bound. Bloom filters at 0.01% FPR compress 1M settlement hashes from ~32 MB to ~2.4 MB. A settlement verification window during the grace period recovers any settlements lost to false positives. Epochs are triggered by settlement count (~10,000 batches), not wall-clock time, for partition tolerance. |

## Compute Contracts: MHR-Byte

| | |
|---|---|
| **Chosen** | MHR-Byte (minimal bytecode, ~50 KB interpreter) |
| **Alternatives** | Full WASM everywhere |
| **Rationale** | ESP32 microcontrollers can't run a WASM runtime. MHR-Byte provides basic contract execution on even the most constrained devices. WASM is offered as an optional capability on nodes with sufficient resources. |

## Encryption: Ed25519 + X25519

| | |
|---|---|
| **Chosen** | Ed25519 for identity/signing, X25519 for key exchange (Reticulum-compatible) |
| **Alternatives** | RSA, symmetric-only |
| **Rationale** | Ed25519 has 32-byte public keys (compact for radio), fast signing/verification, and is widely proven. X25519 provides efficient Diffie-Hellman key exchange. Compatible with Reticulum's crypto model. RSA keys are too large for constrained links. |

## Source Privacy: No Source Address (Default)

| | |
|---|---|
| **Chosen** | No source address in packet headers (inherited from Reticulum) as the default; [opt-in onion routing](#onion-routing-per-packet-layered-encryption-opt-in) for high-threat environments |
| **Alternatives** | Mandatory onion routing for all traffic |
| **Rationale** | Onion routing adds 21% payload overhead on LoRa — unacceptable as a default for all traffic. Omitting the source address is free and effective against casual observation. Per-packet layered encryption is available opt-in via `PathPolicy.ONION_ROUTE` for users who need stronger traffic analysis resistance. |

## Naming: Neighborhood-Scoped, No Global Namespace

| | |
|---|---|
| **Chosen** | Community-label-scoped names (e.g., `alice@portland-mesh`) |
| **Alternatives** | Global names via consensus |
| **Rationale** | Global consensus contradicts partition tolerance. Community labels are self-assigned and informational — no authority, no uniqueness enforcement. Multiple disjoint clusters can share a label; resolution is proximity-based. Local petnames provide a fallback. |

## Cost Annotations: Compact Path Cost (No Per-Relay Signatures)

| | |
|---|---|
| **Chosen** | 6-byte constant-size `CompactPathCost` (running totals updated by each relay, no per-relay signatures) |
| **Alternatives** | Per-relay signed CostAnnotation (~84 bytes per hop), aggregate signatures, signature-free with Merkle proof |
| **Rationale** | Per-relay signatures make announces grow linearly with path length — 84 bytes × N hops. On a 1 kbps LoRa link with 3% routing budget, this limits convergence to ~1 announce per 22+ seconds. CompactPathCost uses 6 bytes total regardless of path length: log-encoded cumulative cost, worst-case latency, bottleneck bandwidth, and hop count. Per-relay signatures are unnecessary because routing decisions are local (you trust your link-authenticated neighbor), trust is transitive at each hop, and the market enforces honesty (overpriced relays get routed around, underpriced relays lose money). The announce itself remains signed by the destination node. |

## Congestion Control: Three-Layer Design

| | |
|---|---|
| **Chosen** | Link-level CSMA/CA + per-neighbor token bucket + 4-level priority queuing + economic cost response |
| **Alternatives** | Pure CSMA/CA only, rigid TDMA, end-to-end TCP-style congestion control |
| **Rationale** | A single mechanism is insufficient across the bandwidth range (500 bps to 10 Gbps). CSMA/CA handles collision avoidance on half-duplex radio. Token buckets enforce fair sharing across neighbors. Priority queuing ensures real-time traffic (voice) isn't starved by bulk transfers. Economic cost response (quadratic cost increase under congestion) signals scarcity through the existing cost routing mechanism, causing natural traffic rerouting without new protocol extensions. End-to-end congestion control (TCP-style) is wrong for a mesh — the bottleneck is typically a single constrained link, and hop-by-hop control responds faster. Rigid TDMA wastes bandwidth when some slots are unused. |

## Transport Layer: Swappable Implementation

| | |
|---|---|
| **Chosen** | Define transport as an interface with requirements; use Reticulum as the current implementation |
| **Alternatives** | Hard dependency on Reticulum, clean-room from day one |
| **Rationale** | Reticulum provides a proven transport layer tested at 5 bps on LoRa, saving significant implementation effort. But coupling Mehr to Reticulum's codebase or community roadmap creates fragility. Instead, Mehr defines the transport interface it needs (transport-agnostic links, announce-based routing, mandatory encryption, sender anonymity) and uses Reticulum as the current implementation. Mehr extensions are carried as opaque payload in the announce DATA field — a clean separation. Three participation levels (L0 transport-only, L1 Mehr relay, L2 full Mehr) ensure interoperability with the underlying transport. This allows a future clean-room implementation without affecting any layer above transport. |

## Storage: Pay-Per-Duration with Erasure Coding

| | |
|---|---|
| **Chosen** | Bilateral storage agreements, pay-per-duration, Reed-Solomon erasure coding, lightweight challenge-response proofs |
| **Alternatives** | Filecoin-style PoRep/PoSt with on-chain proofs; Arweave-style one-time-payment permanent storage; simple full replication |
| **Rationale** | Filecoin's Proof of Replication requires GPU-level computation (minutes to seal a sector) — impossible on ESP32 or Raspberry Pi. Arweave's permanent storage requires a blockchain endowment model and assumes perpetually declining storage costs. Both require global consensus. Mehr uses simple Blake3 challenge-response proofs (verifiable in under 10ms on ESP32) and bilateral agreements settled via payment channels. Erasure coding (Reed-Solomon) provides the same durability as 3x replication at 1.5x storage overhead. The tradeoff: we can't prove a node stores data *uniquely* (no PoRep), but we can prove it stores data *at all* — and the data owner doesn't care how the node organizes its disk. |

## Mobile Handoff: Presence Beacons + Credit-Based Fast Start

| | |
|---|---|
| **Chosen** | Transport-agnostic presence beacons, credit-based fast start, roaming cache with channel preservation |
| **Alternatives** | Pre-negotiated handoff (cellular-style), pure re-discovery from scratch, always-connected overlay |
| **Rationale** | Cellular handoff requires a central controller — incompatible with decentralized mesh. Pure re-discovery works but is slow for latency-sensitive sessions. Presence beacons (20 bytes, broadcast every 10 seconds on any interface) let mobile nodes passively discover local relays before connecting. Credit-based fast start allows immediate relay if the mobile node has visible CRDT balance, while the payment channel opens in the background. The roaming cache preserves channels for previously visited areas, enabling zero-latency reconnection on return. No explicit teardown needed — old agreements expire via `valid_until`. |

## Light Client Trust: Content Verification + Multi-Source Queries

| | |
|---|---|
| **Chosen** | Three-tier verification: content-hash check (Tier 1), owner-signature check (Tier 2), multi-source queries (Tier 3) |
| **Alternatives** | Merkle proofs over DHT state, SPV-style state root verification, full DHT replication on clients |
| **Rationale** | Merkle proofs require a global state root, which contradicts partition tolerance (no consensus). SPV-style verification has the same problem. Full DHT replication is too bandwidth-heavy for phones. Instead, content addressing (Tier 1) gives zero-overhead verification for the most common case — `Blake3(data) == key` proves authenticity regardless of relay honesty. Signed objects (Tier 2) prevent forgery of mutable data. Multi-source queries (Tier 3, N=2-3 independent nodes) detect censorship and staleness. Trusted relays skip to single-source for all tiers. Overhead is minimal: at most one extra 192-byte query for critical lookups via untrusted relays. |

## Epoch Triggers: Adaptive Multi-Criteria

| | |
|---|---|
| **Chosen** | Three-trigger system: settlement count ≥ 10,000 (large mesh), GSet size ≥ 500 KB (memory pressure), or partition-proportional threshold with gossip-round floor (small partitions) |
| **Alternatives** | Fixed 10,000-settlement-only trigger, wall-clock timer, per-node independent compaction |
| **Rationale** | A 20-node village on LoRa with low traffic might take months to reach 10,000 settlements. ESP32 nodes (520 KB usable RAM) would exhaust memory first. The adaptive trigger fires at max(200, active_set × 10) settlements with a 1,000-gossip-round floor (~17 hours), keeping GSet under ~6.4 KB for small partitions. The 500 KB GSet size trigger is a safety net regardless of partition size. Proposer eligibility adapts too — only 3 direct links needed (not 10) in small partitions. Wall-clock timers were rejected because they require clock synchronization. Per-node compaction was rejected because it fragments global state. |

## Ledger Scaling: Merkle-Tree Snapshots with Sparse Views

| | |
|---|---|
| **Chosen** | Merkle-tree account snapshot; full tree on backbone nodes, sparse view + Merkle root on constrained devices, on-demand balance proofs (~640 bytes) |
| **Alternatives** | Flat snapshot everywhere, sharded epochs, neighborhood-only ledgers |
| **Rationale** | At 1M nodes the flat snapshot is ~32 MB — unworkable on ESP32 or phones. Sharded epochs fragment the ledger and complicate cross-shard verification. Neighborhood-only ledgers lose global balance consistency. A Merkle tree over the sorted account snapshot gives the best of both: backbone nodes store the full tree (32 MB, feasible on SSD), constrained devices store only their own balance + channel partners + trust neighbors (~1.6 KB for 50 accounts) plus the Merkle root. Any balance can be verified on demand with a ~640-byte proof (20 tree levels × 32 bytes). No global state transfer needed. |

## Transforms/Inference: Compute Capability, Not Protocol Primitive

| | |
|---|---|
| **Chosen** | STT/TTS/inference as compute capabilities in the marketplace |
| **Alternatives** | Dedicated transform layer (considered in v0.5 draft) |
| **Rationale** | Speech-to-text, translation, and other transforms are just compute. Making them protocol primitives over-engineers the foundation. The capability marketplace already handles discovery, negotiation, execution, verification, and payment for arbitrary compute functions. |

## Group Admin: Delegated Co-Admin (No Threshold Signatures)

| | |
|---|---|
| **Chosen** | Delegated co-admin model: group creator signs delegation certificates for up to 3 co-admins; any co-admin can independently rotate keys and manage members |
| **Alternatives** | Threshold signatures (e.g., 2-of-3 Schnorr multisig), single admin only, leaderless consensus |
| **Rationale** | Threshold signatures (Schnorr multisig, FROST) require multi-round key generation and signing protocols that are too expensive for ESP32 and too complex for LoRa latency. Leaderless consensus contradicts the "no global coordination" principle. Instead, the group creator signs `CoAdminCertificate` records (admin public key + permissions + sequence number, ~128 bytes each) that authorize up to 3 co-admins. Any co-admin can independently add/remove members, rotate the group symmetric key, and promote/demote other co-admins (if authorized). Operations are sequence-numbered; conflicts are resolved by highest sequence number, ties broken by lowest admin public key hash. Overhead is one Ed25519 signature per admin action — no new cryptographic primitives needed. If all admins go offline, the group continues functioning with its current key; no key rotation or membership changes occur until at least one admin returns. |

## Reputation: Bounded Trust-Weighted Referrals

| | |
|---|---|
| **Chosen** | First-hand scores primary; 1-hop trust-weighted referrals as advisory bootstrap for unknown peers, capped and decaying |
| **Alternatives** | Pure first-hand only (no referrals), full gossip-based reputation, global reputation aggregation |
| **Rationale** | Pure first-hand scoring means new nodes have zero information about any peer until direct interaction — leading to poor initial routing and credit decisions. Full reputation gossip enables manipulation: a colluding cluster can flood the network with inflated scores. Global aggregation requires consensus. The chosen design: trusted peers (direct trust edges) can share their first-hand scores as referrals. Referrals are weighted by the querier's trust in the referrer (trust_score / max_score × 0.3) and capped at 50% of max reputation — a referral alone cannot make a peer fully trusted. Only 1-hop referrals are accepted (no transitive gossip), limiting the manipulation surface to corruption of direct trusted peers, which already breaks the trust model. Referral scores are advisory: they initialize a peer's reputation but are overwritten by first-hand experience after the first few direct interactions. Referrals expire after 500 gossip rounds (~8 hours) without refresh. This helps new nodes bootstrap while keeping the attack surface minimal. |

## Onion Routing: Per-Packet Layered Encryption (Opt-In)

| | |
|---|---|
| **Chosen** | Per-packet layered encryption via `PathPolicy.ONION_ROUTE`, stateless relays, 3 hops default, optional cover traffic |
| **Alternatives** | Circuit-based onion routing (Tor-style), mix networks, no onion routing (status quo) |
| **Rationale** | Circuit-based onion routing requires multi-round-trip circuit establishment — on a 1 kbps LoRa link with 2-second round trips, building a 3-hop circuit takes ~12 seconds before any data flows. Mix networks add latency by design (batching and reordering), which is unacceptable for interactive messaging. Per-packet layered encryption has zero setup: the sender wraps the message in N encryption layers (default N=3), each layer containing the next-hop destination hash and the inner ciphertext. Each relay decrypts one layer, reads the next hop, and forwards. No circuit state on relays — each packet is independently routable. Overhead: 32 bytes per hop (16-byte nonce + 16-byte Poly1305 tag), so 3 hops = 96 bytes, leaving 369 of 465 usable bytes on LoRa (~21% overhead). Relay selection: sender picks from known relays, requiring at least one relay outside the sender's trust neighborhood. Optional constant-rate cover traffic (1 dummy packet/minute, off by default) provides additional resistance to timing analysis on high-threat links. Onion routing is opt-in and not recommended for real-time voice (latency and payload overhead). The existing no-source-address design remains the default privacy layer for most traffic. |

## MHR-Byte: 47 Opcodes with Reference Interpreter

| | |
|---|---|
| **Chosen** | 47 opcodes in 7 categories, reference interpreter in Rust, cycle costs calibrated to ESP32 |
| **Alternatives** | Formal specification (Yellow Paper-style), minimal 20-opcode set, EVM-compatible opcode set |
| **Rationale** | A formal specification (Ethereum Yellow Paper style) would freeze the design prematurely — the opcode set needs real-world usage feedback before committing to a formal spec. An EVM-compatible set imports unnecessary complexity (256-bit words, gas semantics) that doesn't fit constrained devices. A minimal 20-opcode set omits crypto and system operations needed for the core use cases. The chosen 47 opcodes cover 7 categories: **Stack** (6): PUSH, POP, DUP, SWAP, OVER, ROT. **Arithmetic** (9): ADD, SUB, MUL, DIV, MOD, NEG, ABS, MIN, MAX — all 64-bit integer, overflow traps. **Bitwise** (6): AND, OR, XOR, NOT, SHL, SHR. **Comparison** (6): EQ, NEQ, LT, GT, LTE, GTE. **Control** (7): JMP, JZ, JNZ, CALL, RET, HALT, ABORT. **Crypto** (3): HASH (Blake3), VERIFY_SIG (Ed25519), VERIFY_VRF. **System** (10): BALANCE, SENDER, SELF, EPOCH, TRANSFER, LOG, LOAD, STORE, MSIZE, EMIT. Cycle costs are tiered: stack/arithmetic/bitwise/comparison (1–3 cycles), control (2–5), memory (2–3), crypto (500–2000), system (10–50). ESP32 is the reference platform (~1 μs per base cycle). Faster hardware executes more cycles per second but charges the same cycle cost — gas price in μMHR/cycle is set by each compute provider. A comprehensive test vector suite ensures cross-platform conformance. Formal specification is a post-stabilization goal. |

## Emission Schedule: Epoch-Counted Discrete Halving

| | |
|---|---|
| **Chosen** | Initial reward of 10^12 μMHR per epoch, discrete halving every 100,000 epochs, tail emission floor at 0.1% of circulating supply annualized |
| **Alternatives** | Continuous exponential decay, wall-clock halving (every 2 calendar years), fixed perpetual emission |
| **Rationale** | Wall-clock halving requires clock synchronization, which contradicts partition tolerance — partitioned nodes would disagree on the current halving period. Continuous decay is mathematically elegant but harder to reason about and implement correctly on integer-only constrained devices. Fixed perpetual emission provides no scarcity signal. Discrete halving every 100,000 epochs is epoch-counted (partition-safe), easy to compute (bit-shift), and predictable. At an estimated ~1 epoch per 10 minutes (varies with network activity since epochs are settlement-triggered), 100,000 epochs ≈ 1.9 years — close to the original 2-year target. Initial reward of 10^12 μMHR/epoch yields ~1.5% of the supply ceiling minted in the first halving period, providing strong bootstrap incentive. Tail emission activates when the halved reward drops below `0.001 × circulating_supply / estimated_epochs_per_year` (trailing 1,000-epoch moving average of epoch frequency). This ensures perpetual relay incentive while keeping inflation negligible. Partition minting interaction: each partition mints `(local_active_relays / estimated_global_relays) × epoch_reward`; on merge, GCounter max-merge preserves individual balances, and overminting is bounded by the existing partition_scale_factor tolerance (max 1.5×). |

## Protocol Bridges: Standalone Gateway Services

| | |
|---|---|
| **Chosen** | Bridges as standalone gateway services advertising in the capability marketplace; one-way identity attestation; bridge operator bears Mehr-side costs |
| **Alternatives** | Bridges as MHR-Compute contracts, bridge as protocol-level primitive, no bridge design (defer entirely) |
| **Rationale** | MHR-Compute contracts are sandboxed with no I/O or network access — bridges require persistent connections to external protocols (SSB replication, Matrix homeserver federation, Briar Tor transport). A protocol-level primitive over-engineers the foundation for what is fundamentally a gateway service. Bridges run as standalone processes that advertise their bridging capability in the marketplace like any other service. **Identity mapping**: Users create signed bridge attestations linking their Mehr Ed25519 key to their external identity. The bridge stores these attestations and handles translation. No global identity registry — the bridge is the only entity that knows the mapping. External users see messages as coming from the bridge identity in the external protocol. **Payment model**: Mehr-to-external traffic — the Mehr sender pays the bridge operator via a standard marketplace agreement. External-to-Mehr traffic — the bridge operator pays Mehr relay costs and recoups via the external protocol's economics (or operates as a public good). This keeps the Mehr economic model clean: the bridge is just another service consumer/provider. Bridge operators can support multiple protocols simultaneously and set their own pricing. |

## WASM Sandbox: Wasmtime with Tiered Profiles

| | |
|---|---|
| **Chosen** | Wasmtime (Bytecode Alliance) as WASM runtime; two tiers: Light (Community, 16 MB / 10^8 fuel / 5s) and Full (Gateway+, 256 MB / 10^10 fuel / 30s); 10 host imports mirroring MHR-Byte System opcodes |
| **Alternatives** | Wasmer, custom interpreter, single WASM profile for all devices |
| **Rationale** | Wasmtime is Rust-native (matches the reference implementation language), provides fuel-based metering that maps directly to MHR-Byte cycle accounting, and supports AOT compilation on Gateway+ nodes. Wasmer has a broader language ecosystem but less tight Rust integration. A custom interpreter would duplicate Wasmtime's battle-tested sandboxing. A single WASM profile either excludes Community-tier devices (too high limits) or handicaps Gateway nodes (too low limits). Two tiers match the natural hardware split: Pi Zero 2W (512 MB RAM, interpreted Cranelift) vs. Pi 4/5+ (4-8 GB, AOT). Host imports are restricted to 10 functions mirroring MHR-Byte System opcodes — no filesystem, network, clock, or RNG access. WASM execution remains pure and deterministic, enabling the same verification methods as MHR-Byte. Contracts exceeding Light limits are automatically delegated to a more capable node via compute delegation. |

## Presence Beacon: 8-Bit Capability Bitfield

| | |
|---|---|
| **Chosen** | 8 assigned capability bits in 16-bit field; bits 8-15 reserved for future use |
| **Alternatives** | Variable-length capability list, TLV-encoded capabilities, separate beacon per capability |
| **Rationale** | The beacon must fit in 20 bytes total and broadcast every 10 seconds on LoRa — every byte matters. A 16-bit bitfield encodes up to 16 boolean capabilities in 2 bytes, zero parsing overhead. The 8 assigned bits cover all current service types: relay (L1+), gateway, storage, compute-byte, compute-wasm, pubsub, DHT, and naming. Bits 8-15 are reserved (must be zero) for future services like inference, bridge, etc. Variable-length lists or TLV encoding would bloat the beacon and complicate parsing on ESP32. Separate beacons per capability would multiply broadcast bandwidth. |

## Ring 1 Discovery: CapabilitySummary Format

| | |
|---|---|
| **Chosen** | 8-byte `CapabilitySummary` per capability type: type (u8), count (u8), min/avg cost (u16 each, log₂-encoded), min/max hops (u8 each) |
| **Alternatives** | Full capability advertisements forwarded, Bloom filter of providers, free-text summaries |
| **Rationale** | Ring 1 gossips summaries every few minutes — bandwidth must stay under ~50 bytes per round. At 8 bytes per type and typically 5-6 types present in a 2-3 hop neighborhood, the total is 40-48 bytes — within budget even on LoRa. Forwarding full capability advertisements would scale linearly with provider count. Bloom filters compress provider identity but lose cost/distance information needed for routing decisions. The log₂-encoded cost fields match `CompactPathCost` encoding, keeping the representation consistent across the protocol. Count is capped at 255 (u8) — sufficient since Ring 1 covers only 2-3 hops. |

## DHT Metadata: 129-Byte Signed Entries

| | |
|---|---|
| **Chosen** | 129-byte `DHTMetadata`: 32-byte Blake3 key, u32 size, u8 content_type (Immutable/Mutable/Ephemeral), 16-byte owner, u32 TTL, u64 Lamport timestamp, 64-byte Ed25519 signature |
| **Alternatives** | Minimal key-only gossip (no metadata), full object gossip, variable-length metadata with optional fields |
| **Rationale** | DHT publication gossips metadata to let storage-set nodes decide whether to pull full data. Key-only gossip forces blind pulls — wasting bandwidth on unwanted or expired data. Full object gossip floods the gossip channel with arbitrarily large payloads. The 129-byte fixed format includes everything a storage node needs to decide: content hash (for deduplication), size (for storage budgeting), content type (for cache policy), owner (for mutable-object freshness ordering), TTL (for garbage collection), and Lamport timestamp (for mutable conflict resolution). The Ed25519 signature prevents metadata forgery — a node cannot falsely advertise objects it doesn't own. Content hash prevents data forgery on pull. For mutable objects, highest Lamport timestamp with valid signature wins; for immutable objects, the content hash is the sole arbiter. Cache invalidation is TTL-based with no push-invalidation — keeping the protocol simple and partition-tolerant. |

## Negotiation Protocol: Single-Round Take-It-or-Leave-It

| | |
|---|---|
| **Chosen** | Single round-trip negotiation: consumer sends `CapabilityRequest` (with desired cost, duration, proof preference, nonce); provider responds with `CapabilityOffer` (actual terms) or reject; consumer accepts or walks away. 30-second timeout. No counter-offers. |
| **Alternatives** | Multi-round bidding/auction, Dutch auction, sealed-bid auction, negotiation-free fixed pricing |
| **Rationale** | Multi-round negotiation is untenable on LoRa where each message takes seconds — a 3-round negotiation would take 30+ seconds before service begins. Auctions require multiple participants to discover each other simultaneously, which contradicts the bilateral, privacy-preserving nature of agreements. Fixed pricing (no negotiation) removes the consumer's ability to express budget constraints. The single-round protocol: the consumer states their maximum acceptable cost; the provider either meets it, undercuts it, or rejects. One round-trip, then service begins. The nonce in `CapabilityRequest` prevents replay attacks; the `request_nonce` echo in `CapabilityOffer` binds offer to request. Both messages are signed — the two signatures together form the `CapabilityAgreement`. If the consumer wants different terms, they send a new request with adjusted parameters — no counter-offer complexity. This keeps capability negotiation under 2 seconds on WiFi and under 10 seconds on LoRa. |

## Formal Verification: Priority-Ordered TLA+ Targets

| | |
|---|---|
| **Chosen** | TLA+ for concurrent protocol properties; 4-tier priority: (1) CRDT merge, (2) payment channels, (3) epoch checkpoints, (4) full composition deferred |
| **Alternatives** | Coq/Lean theorem proving, no formal verification (testing only), verify everything before v1.0 |
| **Rationale** | Coq/Lean have a steep learning curve that limits contributor access. Pure testing cannot prove absence of bugs in concurrent distributed protocols. Verifying everything delays launch indefinitely. TLA+ is battle-tested for distributed systems (used by Amazon for AWS services, by Microsoft for Azure) and has a practical learning curve. **Priority 1 — CRDT merge convergence** (must verify before v1.0): Prove commutativity, associativity, and idempotency of GCounter max-merge and GSet union. If merge diverges, the entire ledger is broken. **Priority 2 — Payment channel state machine** (must verify before v1.0): Prove no balance can go negative, dispute resolution always terminates within the challenge window, and channel states form a total order by sequence number. Direct financial impact if buggy. **Priority 3 — Epoch checkpoint correctness** (should verify): Prove no confirmed settlement is permanently lost after finalization, bloom filter false positive recovery covers all edge cases during the grace period. Property-based testing (QuickCheck-style) initially, formal TLA+ proof if resources allow. **Priority 4 — Full protocol composition** (defer to post-v1.0): Interaction between subsystems (e.g., channel dispute during epoch transition) is tracked as a long-term research goal. Individual component proofs provide sufficient confidence for launch. |

---
sidebar_position: 2
title: Design Decisions
---

# Design Decisions Log

This page documents the key architectural decisions made during NEXUS protocol design, including alternatives considered and the rationale for each choice.

## Network Stack: Reticulum as Foundation

| | |
|---|---|
| **Chosen** | Build on the [Reticulum Network Stack](https://reticulum.network/) for transport, identity, encryption, and announce-based routing |
| **Alternatives** | Clean-room implementation, libp2p, custom protocol |
| **Rationale** | Reticulum already solves transport abstraction, cryptographic identity, mandatory encryption, sender anonymity (no source address), and announce-based routing — all proven on LoRa at 5 bps. NEXUS extends it with cost annotations and economic primitives rather than reinventing a tested foundation. The Rust `no_std` reimplementation for ESP32 speaks the same wire protocol. |

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

## Compute Contracts: NXS-Byte

| | |
|---|---|
| **Chosen** | NXS-Byte (minimal bytecode, ~50 KB interpreter) |
| **Alternatives** | Full WASM everywhere |
| **Rationale** | ESP32 microcontrollers can't run a WASM runtime. NXS-Byte provides basic contract execution on even the most constrained devices. WASM is offered as an optional capability on nodes with sufficient resources. |

## Encryption: Ed25519 + X25519

| | |
|---|---|
| **Chosen** | Ed25519 for identity/signing, X25519 for key exchange (Reticulum-compatible) |
| **Alternatives** | RSA, symmetric-only |
| **Rationale** | Ed25519 has 32-byte public keys (compact for radio), fast signing/verification, and is widely proven. X25519 provides efficient Diffie-Hellman key exchange. Compatible with Reticulum's crypto model. RSA keys are too large for constrained links. |

## Source Privacy: No Source Address

| | |
|---|---|
| **Chosen** | No source address in packet headers (inherited from Reticulum) |
| **Alternatives** | Onion routing |
| **Rationale** | Onion routing adds significant overhead for radio links (multiple encryption layers, circuit establishment). Omitting the source address is free and effective against casual observation. Full traffic analysis resistance via onion routing is deferred to future work. |

## Naming: Neighborhood-Scoped, No Global Namespace

| | |
|---|---|
| **Chosen** | Community-label-scoped names (e.g., `alice@portland-mesh`) |
| **Alternatives** | Global names via consensus |
| **Rationale** | Global consensus contradicts partition tolerance. Community labels are self-assigned and informational — no authority, no uniqueness enforcement. Multiple disjoint clusters can share a label; resolution is proximity-based. Local petnames provide a fallback. |

## Storage: Pay-Per-Duration with Erasure Coding

| | |
|---|---|
| **Chosen** | Bilateral storage agreements, pay-per-duration, Reed-Solomon erasure coding, lightweight challenge-response proofs |
| **Alternatives** | Filecoin-style PoRep/PoSt with on-chain proofs; Arweave-style one-time-payment permanent storage; simple full replication |
| **Rationale** | Filecoin's Proof of Replication requires GPU-level computation (minutes to seal a sector) — impossible on ESP32 or Raspberry Pi. Arweave's permanent storage requires a blockchain endowment model and assumes perpetually declining storage costs. Both require global consensus. NEXUS uses simple Blake3 challenge-response proofs (verifiable in under 10ms on ESP32) and bilateral agreements settled via payment channels. Erasure coding (Reed-Solomon) provides the same durability as 3x replication at 1.5x storage overhead. The tradeoff: we can't prove a node stores data *uniquely* (no PoRep), but we can prove it stores data *at all* — and the data owner doesn't care how the node organizes its disk. |

## Transforms/Inference: Compute Capability, Not Protocol Primitive

| | |
|---|---|
| **Chosen** | STT/TTS/inference as compute capabilities in the marketplace |
| **Alternatives** | Dedicated transform layer (considered in v0.5 draft) |
| **Rationale** | Speech-to-text, translation, and other transforms are just compute. Making them protocol primitives over-engineers the foundation. The capability marketplace already handles discovery, negotiation, execution, verification, and payment for arbitrary compute functions. |

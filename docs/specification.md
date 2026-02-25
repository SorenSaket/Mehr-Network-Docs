---
sidebar_position: 100
title: Full Specification
---

import DownloadButton from '@site/src/components/DownloadButton';

<DownloadButton />

# NEXUS Protocol Specification v1.0

This page is the normative reference for the NEXUS protocol. Individual documentation pages provide detailed explanations; this page summarizes the protocol constants, wire formats, and layer dependencies in one place.

## Status

| | |
|---|---|
| **Version** | 1.0 |
| **Status** | Design complete, pre-implementation |
| **Normative sections** | Layers 0–5 (transport through services) |
| **Informative sections** | Layer 6 (applications), hardware reference, roadmap |

## Protocol Constants

| Constant | Value | Defined In |
|----------|-------|-----------|
| Gossip interval | 60 seconds | [Network Protocol](protocol/network-protocol#gossip-protocol) |
| Protocol overhead budget | ≤10% of link bandwidth | [Bandwidth Budget](protocol/network-protocol#bandwidth-budget) |
| CompactPathCost size | 6 bytes (constant) | [Network Protocol](protocol/network-protocol#nexus-extension-compact-path-cost) |
| NexusExtension magic byte | `0x4E` ('N') | [Network Protocol](protocol/network-protocol#nexus-extension-compact-path-cost) |
| Destination hash size | 16 bytes (128-bit) | [Network Protocol](protocol/network-protocol#identity-and-addressing) |
| Smallest NXS unit | 1 μNXS | [NXS Token](economics/nxs-token#properties) |
| Supply ceiling | 2^64 μNXS (asymptotic) | [NXS Token](economics/nxs-token#supply-model) |
| Default relay lottery probability | 1/100 | [Stochastic Rewards](economics/payment-channels#example) |
| Payment channel state size | 200 bytes | [Payment Channels](economics/payment-channels#channel-state) |
| Dispute challenge window | 2,880 gossip rounds (~48h) | [Payment Channels](economics/payment-channels#channel-lifecycle) |
| Channel abandonment threshold | 4 epochs | [Payment Channels](economics/payment-channels#channel-lifecycle) |
| Epoch trigger: settlement count | ≥10,000 batches | [CRDT Ledger](economics/crdt-ledger#epoch-triggers) |
| Epoch trigger: GSet memory | ≥500 KB | [CRDT Ledger](economics/crdt-ledger#epoch-triggers) |
| Epoch acknowledgment threshold | 67% of active set | [CRDT Ledger](economics/crdt-ledger#epoch-lifecycle) |
| Epoch verification window | 4 epochs after activation | [CRDT Ledger](economics/crdt-ledger#epoch-lifecycle) |
| Bloom filter FPR (epoch) | 0.01% | [CRDT Ledger](economics/crdt-ledger#bloom-filter-sizing) |
| DHT replication factor | k=3 | [NXS-DHT](services/nxs-dht#replication-factor) |
| DHT XOR weight (w_xor) | 0.7 | [NXS-DHT](services/nxs-dht#lookup-scoring-function) |
| Storage chunk size | 4 KB | [NXS-Store](services/nxs-store#chunking) |
| Presence beacon size | 20 bytes | [Discovery](marketplace/discovery#presence-beacons) |
| Presence beacon interval | 10 seconds | [Discovery](marketplace/discovery#presence-beacons) |
| Transitive credit limit | 10% per hop, max 2 hops | [Trust & Neighborhoods](economics/trust-neighborhoods#trust-based-credit) |

## Cryptographic Primitives

| Purpose | Algorithm | Output / Key Size |
|---------|-----------|-------------------|
| Identity / Signing | Ed25519 | 256-bit (32-byte public key) |
| Key Exchange | X25519 (Curve25519 DH) | 256-bit |
| Identity Hashing | Blake2b | 256-bit → 128-bit truncated |
| Content Hashing | Blake3 | 256-bit |
| Symmetric Encryption | ChaCha20-Poly1305 | 256-bit key, 96-bit nonce |
| Relay Lottery (VRF) | ECVRF-ED25519-SHA512-TAI (RFC 9381) | 80-byte proof |
| Erasure Coding | Reed-Solomon | Configurable k,m |

## Layer Dependency Graph

```
Layer 6: Applications
  ├── Messaging, Social, Voice, Naming, Forums, Hosting
  └── depends on ↓

Layer 5: Service Primitives
  ├── NXS-Store, NXS-DHT, NXS-Pub, NXS-Compute
  └── depends on ↓

Layer 4: Capability Marketplace
  ├── Discovery, Agreements, Verification
  └── depends on ↓

Layer 3: Economic Protocol
  ├── NXS Token, Stochastic Rewards, CRDT Ledger, Trust Neighborhoods
  └── depends on ↓

Layer 2: Security
  ├── Link encryption, E2E encryption, Authentication, Key management
  └── depends on ↓

Layer 1: Network Protocol
  ├── Identity, Addressing, Routing, Gossip, Congestion Control
  └── depends on ↓

Layer 0: Physical Transport
  └── LoRa, WiFi, Cellular, Ethernet, BLE, Fiber, Serial
```

Each layer depends **only** on the layer directly below it. Applications never touch transport details. Payment never touches routing internals.

## Serialization Rules

All NEXUS wire formats use the following conventions:

| Rule | Value |
|------|-------|
| **Byte order** | Little-endian for all multi-byte integers (u16, u32, u64, i64) |
| **Encoding** | Fixed-size binary fields; no self-describing framing (not CBOR, not JSON) |
| **TLV extensions** | Type (u8), Length (u8, max 255), Data (variable). Used in NexusExtension only |
| **Strings** | UTF-8, length-prefixed with u16 (community labels, function IDs) |
| **Hashes** | Raw bytes, no hex encoding on the wire |
| **Signatures** | Raw 64-byte Ed25519 signatures, no ASN.1/DER wrapping |
| **Normalized scores** | Computed on **decoded** values, then divided by the max decoded value in the candidate set. Result is IEEE 754 f32 on nodes that support FP; 16-bit fixed-point (Q0.16, value × 65535) on constrained nodes. Both yield equivalent routing decisions within rounding tolerance |

## Wire Format Summary

### Packet Format (Reticulum-derived)

```
[HEADER 2B] [DEST_HASH 16B] [CONTEXT 1B] [DATA 0-465B]
Max packet size: 484 bytes
Source address: NOT PRESENT (structural sender anonymity)
```

### NEXUS Announce Extension

```
[MAGIC 1B: 0x4E] [VERSION 1B] [CompactPathCost 6B] [TLV extensions...]
Minimum: 8 bytes. Carried in announce DATA field.
```

### CompactPathCost

```
[cumulative_cost 2B] [worst_latency_ms 2B] [bottleneck_bps 1B] [hop_count 1B]
Total: 6 bytes (constant regardless of path length)
```

### Payment Channel State

```
[channel_id 16B] [party_a 16B] [party_b 16B] [balance_a 8B]
[balance_b 8B] [sequence 8B] [sig_a 64B] [sig_b 64B]
Total: 200 bytes
```

## Specification Sections

| Spec Section | Documentation Page |
|-------------|-------------------|
| 0. Design Philosophy | [Introduction](introduction) |
| 1. Layer 0: Physical Transport | [Physical Transport](protocol/physical-transport) |
| 2. Layer 1: Network Protocol | [Network Protocol](protocol/network-protocol) |
| 3. Layer 2: Security | [Security](protocol/security) |
| 4. Layer 3: Economic Protocol | [NXS Token](economics/nxs-token), [Stochastic Relay Rewards](economics/payment-channels), [CRDT Ledger](economics/crdt-ledger), [Trust & Neighborhoods](economics/trust-neighborhoods), [Real-World Economics](economics/real-world-impact) |
| 5. Layer 4: Capability Marketplace | [Overview](marketplace/overview), [Discovery](marketplace/discovery), [Agreements](marketplace/agreements), [Verification](marketplace/verification) |
| 6. Layer 5: Service Primitives | [NXS-Store](services/nxs-store), [NXS-DHT](services/nxs-dht), [NXS-Pub](services/nxs-pub), [NXS-Compute](services/nxs-compute) |
| 7. Layer 6: Applications | [Messaging](applications/messaging), [Social](applications/social), [Voice](applications/voice), [Naming](applications/naming), [Community Apps](applications/community-apps), [Hosting](applications/hosting) |
| 8. Hardware Reference | [Reference Designs](hardware/reference-designs), [Device Tiers](hardware/device-tiers) |
| 9. Implementation Roadmap | [Roadmap](development/roadmap) |
| 10. Design Decisions | [Design Decisions](development/design-decisions) |
| 11. Open Questions | [Open Questions](development/open-questions) |

## Version History

| Version | Status | Description |
|---------|--------|-------------|
| v0.1-v0.5 | Superseded | Early design iterations |
| v0.8 | Superseded | Introduced explicit community zones (later replaced by trust neighborhoods) |
| **v1.0** | **Current** | Consolidated specification — Reticulum foundation, stochastic relay rewards, emergent trust neighborhoods |

---

*This specification consolidates design work from v0.1 through v1.0. The foundation — Reticulum-based transport, cryptographic identity, Kleinberg small-world routing, stochastic relay rewards, CRDT settlement, epoch compaction, emergent trust neighborhoods, and the capability marketplace — is the protocol. Everything above it — storage, compute, pub/sub, naming, and applications — are services built on that foundation.*

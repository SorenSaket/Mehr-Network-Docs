---
sidebar_position: 100
title: Full Specification
---

# NEXUS Protocol Specification v1.0

This page contains an overview of the protocol specification. For a guided walkthrough, start with the [Introduction](introduction) and navigate through the documentation sections.

## Specification Sections

The specification covers the following areas, each of which has a dedicated documentation page:

| Spec Section | Documentation Page |
|-------------|-------------------|
| 0. Design Philosophy | [Introduction](introduction) |
| 1. Layer 0: Physical Transport | [Physical Transport](protocol/physical-transport) |
| 2. Layer 1: Network Protocol | [Network Protocol](protocol/network-protocol) |
| 3. Layer 2: Security | [Security](protocol/security) |
| 4. Layer 3: Economic Protocol | [NXS Token](economics/nxs-token), [Stochastic Relay Rewards](economics/payment-channels), [CRDT Ledger](economics/crdt-ledger), [Trust & Neighborhoods](economics/community-zones) |
| 5. Layer 4: Capability Marketplace | [Overview](marketplace/overview), [Discovery](marketplace/discovery), [Agreements](marketplace/agreements), [Verification](marketplace/verification) |
| 6. Layer 5: Service Primitives | [NXS-Store](services/nxs-store), [NXS-DHT](services/nxs-dht), [NXS-Pub](services/nxs-pub), [NXS-Compute](services/nxs-compute) |
| 7. Layer 6: Applications | [Messaging](applications/messaging), [Social](applications/social), [Voice](applications/voice), [Naming](applications/naming), [Community Apps](applications/community-apps) |
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

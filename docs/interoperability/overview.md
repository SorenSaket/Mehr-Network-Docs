---
sidebar_position: 1
title: Cross-Network Compatibility
---

# Cross-Network Compatibility

Mehr is not an island. A decentralized mesh protocol that can't talk to other networks is a walled garden with extra steps. This page explores how Mehr connects to existing protocols, which projects are worth bridging, and the architectural principles that make interoperability possible without compromising Mehr's core design.

## Design Principle: Bridges as Services, Not Primitives

Mehr deliberately avoids building interoperability into the protocol layer. Instead, bridges are **standalone gateway services** that advertise in the [capability marketplace](../marketplace/overview) like any other service — storage, compute, or relay.

This was an explicit [design decision](../development/design-decisions#protocol-bridges-standalone-gateway-services). The rationale:

- **Protocol bridges need persistent connections** to external systems (Matrix federation, SSB replication, Nostr relays). MHR-Compute contracts are sandboxed with no network I/O — bridges don't fit the compute model.
- **Each external protocol evolves independently.** A protocol-level primitive would need to track Matrix spec changes, SSB protocol upgrades, and Nostr NIPs — an endless maintenance burden on the core spec.
- **The marketplace already solves service discovery.** A bridge is just another capability: discoverable, negotiable, verifiable, payable.
- **Bridge operators can specialize.** One operator runs a Matrix bridge. Another runs SSB. A third bridges both plus Nostr. They set their own pricing and compete on quality.

```
                Mehr Network
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────┴────┐  ┌────┴────┐  ┌───┴─────┐
   │ Matrix  │  │  SSB    │  │  Nostr  │
   │ Bridge  │  │ Bridge  │  │ Bridge  │
   │ (L2)    │  │ (L2)    │  │ (L2)    │
   └────┬────┘  └────┬────┘  └────┬────┘
        │            │            │
   Matrix Federation SSB Pubs   Nostr Relays
```

Each bridge is an L2 Mehr node that also speaks an external protocol. From the Mehr side, it's a service provider. From the external side, it's a participant in that protocol's network.

## Identity Attestation

The core interop mechanism is **one-way identity attestation** — a signed statement linking a Mehr identity to an external identity.

```
BridgeAttestation {
    mehr_pubkey: Ed25519PublicKey,       // Mehr identity
    external_protocol: enum {
        Matrix, SSB, Nostr, Briar, Meshtastic, LXMF
    },
    external_identity: Vec<u8>,          // protocol-specific ID
    bridge_node: NodeID,                 // which bridge created this
    timestamp: LamportTimestamp,
    signature: Ed25519Signature,         // signed by mehr_pubkey
}
```

**How it works**:

1. Alice has a Mehr identity (Ed25519 keypair) and a Matrix account (`@alice:example.org`)
2. She connects to a Matrix bridge service on the Mehr network
3. She signs an attestation linking her Mehr key to her Matrix identity
4. The bridge stores this attestation and handles message translation
5. Other Mehr nodes can verify the attestation (Alice's Mehr key signed it)

**What the bridge doesn't know**: The content of E2E encrypted messages passing through it. The bridge translates metadata and routing, not plaintext.

**What the bridge does know**: Which Mehr identity maps to which external identity. This is inherent — you can't bridge without knowing both sides. Users choose which bridges to trust with this mapping.

## Payment Flows

Bridge economics use existing Mehr primitives — no new payment mechanisms required.

### Mehr-to-External

Alice (Mehr) sends a message to Bob (Matrix):

```
Alice → [pays relay MHR] → Bridge Node → [Matrix federation, bridge pays] → Bob
```

- Alice pays Mehr-side relay costs via normal [payment channels](../economics/payment-channels)
- The bridge operator pays Matrix-side costs (homeserver hosting, bandwidth)
- Bridge recoups costs through service fees (per-message, subscription, or ad-supported)

### External-to-Mehr

Carol (Matrix) sends a message to Dave (Mehr):

```
Carol → [Matrix federation, free] → Bridge Node → [pays relay MHR] → Dave
```

- Carol sends via Matrix (free from her perspective)
- The bridge node bears Mehr-side relay costs
- Bridge recoups via Matrix-side monetization, donations, or operates as a public good
- Alternatively, Dave pays the bridge for inbound message delivery (pull model)

### Cross-Bridge

Alice (SSB) sends to Bob (Matrix), both connected to Mehr:

```
Alice → SSB Bridge → [Mehr relay] → Matrix Bridge → Bob
```

Both bridges participate in the Mehr network. The message traverses Mehr's mesh as ordinary encrypted traffic. Each bridge handles its own external protocol costs.

## What Makes a Good Bridge Target

Not every protocol is worth bridging. The best candidates share these properties:

| Property | Why It Matters |
|----------|---------------|
| **Decentralized identity** | Attestation works without asking permission from a central authority |
| **Offline tolerance** | Mehr's store-and-forward model maps naturally to protocols that handle delays |
| **Gossip or relay-based** | Similar distribution model; easier to translate |
| **Ed25519 or compatible crypto** | Reduces key management complexity |
| **Active community** | Bridge is only useful if people use the other side |
| **Open protocol** | Can implement a bridge without licensing or API keys |

Properties that make bridging harder:

| Property | Challenge |
|----------|-----------|
| **Requires always-on internet** | Bridge node must maintain persistent connection; can't operate in mesh-only mode |
| **Global consensus required** | Blockchain-based protocols add settlement latency and complexity |
| **Proprietary or closed** | Can't implement without reverse engineering or vendor cooperation |
| **Different encryption model** | E2E translation requires re-encryption at the bridge (breaks zero-knowledge) |

## Bridge Categories

### Transport-Level Bridges

These operate at Layer 0 — translating between Mehr's transport and another mesh protocol's transport. Packets flow between networks at the radio/link level.

**Example**: [Meshtastic](meshtastic) — LoRa mesh nodes that can forward Mehr packets as opaque payloads.

**Advantage**: Deepest integration. External nodes contribute physical infrastructure (radio coverage, relay hops) to the Mehr mesh.

**Challenge**: Requires the external protocol to support opaque payload forwarding.

### Protocol-Level Bridges

These operate at the application layer — translating messages, posts, or data between Mehr's service primitives and an external protocol's data model.

**Examples**: [Matrix](matrix) (room ↔ topic), [Scuttlebutt](scuttlebutt) (feed ↔ DHT), Nostr (event ↔ pub).

**Advantage**: No changes needed to the external protocol. The bridge is just another client/server on both sides.

**Challenge**: Semantic mismatch. Mehr's immutable DataObjects don't map 1:1 to Matrix's mutable room state or SSB's append-only feeds. Each bridge needs protocol-specific translation logic.

### Ecosystem Bridges

These connect Mehr to protocols it already shares infrastructure with — particularly the [Reticulum ecosystem](reticulum-ecosystem).

**Example**: LXMF messages carried natively on the same Reticulum transport Mehr uses.

**Advantage**: Near-zero translation overhead. Same wire format, same crypto, same transport.

**Challenge**: Coordinating upgrade paths as Mehr adds economic extensions that pure Reticulum nodes don't understand.

## Compatibility Landscape

### Tier 1 — High Alignment, Build First

| Project | Bridge Type | Key Alignment | Detailed Page |
|---------|------------|---------------|---------------|
| **Meshtastic** | Transport | Same LoRa hardware, massive deployed base | [Meshtastic Bridge](meshtastic) |
| **Reticulum / LXMF** | Ecosystem | Shared transport layer, native coexistence | [Reticulum Ecosystem](reticulum-ecosystem) |
| **Scuttlebutt (SSB)** | Protocol | Gossip-based, offline-first, Ed25519, aligned values | [Scuttlebutt Bridge](scuttlebutt) |

### Tier 2 — Good Fit, Build Second

| Project | Bridge Type | Key Alignment | Notes |
|---------|------------|---------------|-------|
| **Matrix** | Protocol | Federated, well-specified, transitive bridge access to dozens of protocols | [Matrix Bridge](matrix) |
| **Nostr** | Protocol | Simple event model, sovereignty-focused, growing community | Relay ↔ MHR-Pub translation |
| **Yggdrasil** | Transport | Encrypted mesh overlay; alternative backbone for internet-connected nodes | Could supplement Reticulum for IP links |

### Tier 3 — Interesting, Community-Driven

| Project | Bridge Type | Key Alignment | Notes |
|---------|------------|---------------|-------|
| **IPFS / libp2p** | Protocol | Content-addressing, libp2p as alternative transport | Heavy bandwidth assumptions conflict with constrained links |
| **Briar** | Protocol | Tor-based, offline-capable, similar threat model | Tor dependency adds complexity |
| **Althea** | Protocol | Paid relay economics, shared incentive model | Ethereum dependency, different economic model |

### Tier 4 — Watch, Don't Build

| Project | Why Watch | Why Wait |
|---------|-----------|----------|
| **Holochain** | Agent-centric like Mehr, CRDT-compatible | Heavy runtime, small community |
| **GNUnet** | Privacy-focused mesh, strong academic foundation | Small community, complex protocol |
| **Dat / Hypercore** | Append-only logs, good P2P sync | Niche adoption, no incentive layer |

## What Mehr Does NOT Bridge

Some things are deliberately out of scope:

- **Cross-protocol atomic swaps.** Mehr's CRDT ledger has different finality guarantees than blockchains. Token exchange happens through gateway operators or bilateral agreement, not protocol-level swap primitives.
- **Universal identity federation.** Mehr doesn't maintain a global directory mapping all identities across all protocols. Each bridge maintains its own attestation set. Users choose which bridges they trust.
- **Protocol-level name resolution for external systems.** Mehr's [naming system](../applications/naming) resolves Mehr names. External names resolve through their own systems, with bridges translating at the boundary.
- **Backward compatibility shims.** Bridge operators handle version mismatches. The Mehr protocol doesn't adapt its wire format to accommodate external protocol changes.

## Building a Bridge

For developers wanting to create a bridge service:

1. **Run an L2 Mehr node** — full protocol stack, marketplace participation
2. **Advertise bridging as a capability** — `compute.offered_functions` includes bridge-specific function IDs
3. **Implement identity attestation** — store and serve `BridgeAttestation` records
4. **Handle message translation** — protocol-specific logic for each direction
5. **Manage payment** — collect fees via Mehr [service agreements](../marketplace/agreements), pay external protocol costs
6. **Gossip attestation availability** — so other Mehr nodes can discover which identities are reachable through your bridge

The bridge is a regular Mehr service. It earns MHR through service agreements, pays for relay through payment channels, and builds reputation through the [trust system](../economics/trust-neighborhoods). No special protocol support is needed — the marketplace handles everything.

## Roadmap Integration

Cross-network bridges are planned for [Phase 4](../development/roadmap#phase-4-full-ecosystem) (Milestone 4.3), after the core protocol, economics, mobile apps, and mesh radio are proven. This is deliberate — bridges depend on a stable, battle-tested protocol. Building bridges before the foundation is solid creates fragile integrations that break with every protocol change.

The phasing:

| Phase | Interop Activity |
|-------|-----------------|
| Phase 1 | TCP/IP transport only — servers talk to each other |
| Phase 2 | Economics validated — bridge payment model can be tested |
| Phase 3 | Multi-transport proven — bridge nodes can run on diverse hardware |
| Phase 4 | **Protocol bridges ship** — SSB, Matrix, Briar as standalone gateway services |

Early community experimentation with bridges during Phase 2-3 is encouraged — the marketplace is designed to support it. But official bridge implementations come after the protocol stabilizes.

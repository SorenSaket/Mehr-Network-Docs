---
sidebar_position: 6
title: BitTorrent Bridge
description: "A BitTorrent bridge that brings torrent content into the Mehr mesh, translating between content-addressed systems."
keywords:
  - BitTorrent
  - torrent
  - bridge
  - content addressing
  - gateway
  - file sharing
---

# BitTorrent Bridge

[BitTorrent](https://www.bittorrent.org/) is the world's most widely deployed content distribution protocol, with 10–25 million active DHT nodes at any given time. It shares a key property with Mehr: **content addressing** — a torrent's info hash uniquely identifies its content, just as Blake3 hashes identify DataObjects in [MHR-Store](../services/mhr-store).

A BitTorrent bridge brings the entire BitTorrent content library into the Mehr mesh. Mesh-only users — even those on LoRa with no internet — can request torrent content through the bridge. The bridge fetches it from the BitTorrent network, verifies piece hashes, stores it as DataObjects in MHR-Store, and serves it to mesh users through normal Mehr protocols.

## Protocol Alignment

| Property | BitTorrent | Mehr | Compatibility |
|----------|-----------|------|---------------|
| **Content addressing** | SHA-1 info hash (v1) or SHA-256 Merkle root (v2) | Blake3 DataObject hash | High — both content-addressed, different hash functions |
| **Identity** | Random 20-byte peer ID (no cryptographic binding) | Ed25519 keypair → destination hash | None — BitTorrent has no identity system |
| **DHT** | Mainline DHT: Kademlia over UDP, 160-bit XOR, k=8 | [MHR-DHT](../services/mhr-dht): Kademlia-style, k=3, XOR + cost weighting | Moderate — same algorithmic family, different parameters |
| **Transport** | uTP (UDP) or TCP, requires IP addresses | Transport-agnostic (LoRa, WiFi, etc.), no IP required | Low — bridge must proxy between IP and mesh addressing |
| **Mutable data (BEP-44)** | Ed25519-signed DHT entries, 1 KB max, monotonic sequence | Ed25519-signed IdentityClaims, NameBindings | High — same curve, same signing pattern |
| **Encryption** | MSE/PE: obfuscation only (RC4), not security | ChaCha20-Poly1305 E2E encryption | Bridge re-encrypts at boundary |
| **Piece verification** | SHA-1 per piece (v1), SHA-256 Merkle tree (v2) | Blake3 per DataObject | Bridge verifies BT hashes, then re-hashes as Blake3 |
| **Economics** | None — volunteer seeders | MHR token, payment channels | Bridge charges for bandwidth + storage |

## Bridge Architecture

The BitTorrent bridge is a **gateway node** (internet-connected) that participates in both networks simultaneously:

```
                Mehr Mesh                           Internet
                   │                                   │
    [Mesh Node A]──┤                                   │
    [Mesh Node B]──┤                                   │
                   │                                   │
              ┌────┴────┐                              │
              │   BT    │──── Mainline DHT (UDP) ──────┤
              │ Bridge  │──── BitTorrent peers (uTP) ──┤
              │  (L2)   │──── Trackers (HTTP/UDP) ─────┤
              └────┬────┘                              │
                   │                                   │
    [Mesh Node C]──┤                                   │
```

The bridge runs a full BitTorrent client (DHT, peer wire protocol, tracker announcements) and a full Mehr L2 node (MHR-Store, MHR-DHT, marketplace). It translates between the two worlds.

## Content Flow: BitTorrent → Mehr

When a mesh user wants torrent content:

```
Request flow:

  1. User provides info hash (magnet link or torrent file)
     e.g., magnet:?xt=urn:btih:abc123...

  2. Bridge resolves the info hash:
     - Queries Mainline DHT for peers
     - Contacts trackers if specified
     - Downloads metadata via BEP-9 (ut_metadata extension)

  3. Bridge downloads the content:
     - Connects to BitTorrent peers via uTP or TCP
     - Downloads pieces, verifies SHA-1/SHA-256 piece hashes
     - Assembles complete files

  4. Bridge stores content in MHR-Store:
     - Chunks files into 4 KB DataObjects (Mehr's chunk size)
     - Hashes each chunk with Blake3
     - Creates a manifest DataObject linking chunks
     - Stores with configurable replication

  5. Bridge returns Blake3 root hash to the requesting user
     User fetches DataObjects from MHR-Store via normal Mehr protocols

  6. Bridge caches the content — subsequent mesh requests
     are served directly from MHR-Store, no re-download
```

### Content Verification

The bridge performs a **hash translation**: it verifies BitTorrent integrity (SHA-1/SHA-256 piece hashes) during download, then produces Blake3 hashes for Mehr storage. The user trusts the bridge to have performed this translation honestly.

To reduce trust requirements:

- **Multiple bridges**: If two independent bridges produce the same Blake3 root hash for the same info hash, the content is almost certainly correct. Clients can query multiple bridges and compare.
- **Bridge reputation**: Bridges build [reputation](../protocol/security#reputation) through the standard trust system. A bridge that serves corrupted content loses reputation and trust.
- **Torrent file forwarding**: The bridge can forward the original torrent metadata (piece hashes) to the user. The user can verify individual pieces against the original SHA-1/SHA-256 hashes if they want to cross-check the bridge's Blake3 hashing.

## Content Flow: Mehr → BitTorrent

The bridge can also seed Mehr content into the BitTorrent network:

```
Seeding flow:

  1. Mehr user publishes content to MHR-Store (Blake3-addressed DataObjects)
  2. User requests the bridge to seed the content on BitTorrent
  3. Bridge fetches DataObjects from MHR-Store, reassembles files
  4. Bridge creates a torrent file (computes SHA-1/SHA-256 piece hashes)
  5. Bridge announces to the Mainline DHT and begins seeding
  6. BitTorrent users can now download via magnet link or torrent file
  7. Bridge is paid by the Mehr user for outbound bandwidth via payment channels
```

This makes Mehr content available to the billions of devices running BitTorrent clients, without those clients needing to know anything about Mehr.

## Naming Integration

BitTorrent content can be given human-readable names via [MHR-Name](../services/mhr-name):

```
Name binding:
  my-distro@topic:linux → ContentHash(Blake3 root of Ubuntu ISO fetched via bridge)
  paper-collection@topic:science → ContentHash(Blake3 root of archive fetched via bridge)
```

A user can register a name pointing to the Blake3 hash of content originally sourced from BitTorrent. Other mesh users look up the name and fetch the content from MHR-Store — they never need to know it came from BitTorrent.

For content that updates (e.g., a regularly updated dataset), the bridge can use the torrent's BEP-46 mutable torrent feature: a mutable DHT entry (Ed25519-signed, monotonic sequence number) points to the latest info hash. The bridge maps this to an MHR-Name binding that updates when the mutable torrent updates.

## BEP-44 Alignment

BitTorrent's BEP-44 (arbitrary DHT data storage) uses the same cryptographic primitives as Mehr:

| BEP-44 | Mehr Equivalent |
|--------|----------------|
| Ed25519 public key (32 bytes) | Ed25519 public key (32 bytes) |
| Ed25519 signature (64 bytes) | Ed25519 signature (64 bytes) |
| Monotonic sequence number | Monotonic sequence number (NameBinding, Vouch, etc.) |
| Mutable DHT entry (1 KB max) | IdentityClaim, NameBinding (~122–465 bytes) |
| Immutable DHT entry (keyed by SHA-1 of value) | Immutable DataObject (keyed by Blake3 of content) |

A bridge can translate between BEP-44 mutable entries and Mehr NameBindings or IdentityClaims with minimal impedance. Both systems support the pattern: "signed record, monotonically increasing version, stored in a DHT."

## Economic Model

The bridge is a [capability marketplace](../marketplace/overview) service, discoverable and payable like any other:

| Cost | Who Pays | Mechanism |
|------|---------|-----------|
| BitTorrent download bandwidth | Bridge operator (internet costs) | Recouped from requester's service fee |
| Mesh-side storage (MHR-Store) | Requester | Standard [storage pricing](../services/mhr-store) |
| Mesh-side relay to requester | Requester | Standard [relay payment channels](../economics/payment-channels) |
| Bridge seeding (Mehr → BT) | Content owner | Pays bridge for outbound internet bandwidth |

The bridge advertises `Capability(bittorrent_bridge, ...)` and competes with other bridges on price, speed, and reliability. Popular torrents get cached in MHR-Store and served from the mesh — subsequent requests don't go through the bridge at all.

## Constraints and Limitations

**Internet required**: The bridge must have internet access to reach the BitTorrent network. Mesh-only nodes access BitTorrent content indirectly through the bridge.

**Latency**: Downloading a torrent takes time (seconds to minutes depending on swarm size and content). The bridge uses store-and-forward — the user's request is asynchronous. For popular content already cached in MHR-Store, latency is just mesh relay time.

**Bandwidth mismatch**: BitTorrent assumes broadband; Mehr supports LoRa at 500 bps. Large files (multi-GB) are practical only for mesh nodes on WiFi or better. The bridge can serve partial content (specific files from a multi-file torrent) to reduce bandwidth.

**No E2E encryption with BitTorrent peers**: BitTorrent's MSE/PE is obfuscation, not encryption. The bridge sees the cleartext content. Mesh-side delivery is encrypted end-to-end via Mehr's standard E2E layer — but the bridge itself is a trust boundary for content integrity.

**Legal**: BitTorrent is a neutral protocol used for both legitimate and infringing content. Bridge operators are responsible for compliance with applicable law, just as BitTorrent tracker operators are today. The bridge is a service, not infrastructure — operators choose what to cache and serve.

## Comparison

| | Direct BitTorrent | Via Mehr Bridge |
|---|---|---|
| **Requires internet** | Yes | No (bridge proxies) |
| **Requires IP address** | Yes (for peering) | No (mesh addressing) |
| **Content cached locally** | Only while seeding | Stored in MHR-Store, served from mesh |
| **Payment** | None (volunteer seeding) | MHR micropayments for bridge + relay + storage |
| **Content discovery** | Magnet links, trackers, DHT | MHR-Name + magnet links via bridge |
| **Works on LoRa** | No | Yes (for small files; bridge handles BT-side) |
| **Content integrity** | SHA-1/SHA-256 piece hashes | Bridge verifies BT hashes + Blake3 for Mehr storage |
| **Identity** | None (anonymous peer IDs) | Mehr Ed25519 identity for requesting user |

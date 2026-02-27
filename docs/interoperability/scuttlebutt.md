---
sidebar_position: 4
title: Scuttlebutt Bridge
---

# Scuttlebutt Bridge

[Scuttlebutt](https://scuttlebutt.nz/) (SSB) is the protocol most philosophically aligned with Mehr. Both are gossip-based, offline-first, community-centric, and built on Ed25519 cryptographic identity. Both reject global consensus in favor of local-first operation. Both believe social networks should emerge from relationships, not platforms.

The differences are complementary: SSB has a mature social ecosystem with thousands of users. Mehr has economic incentives, radio mesh transport, and a capability marketplace. A bridge between them lets each side benefit from what the other provides.

## Protocol Alignment

| Property | SSB | Mehr | Compatibility |
|----------|-----|------|---------------|
| **Identity** | Ed25519 keypair → feed ID (`@...=.ed25519`) | Ed25519 keypair → destination hash | High — same key type, different derivation |
| **Data model** | Append-only signed log per identity | Immutable/mutable DataObjects in DHT | Moderate — log entries map to DataObjects |
| **Replication** | Social graph-based gossip (friends + friends-of-friends) | DHT + Pub/Sub + trust neighborhoods | Moderate — different scoping models |
| **Discovery** | LAN broadcast, pub servers, room servers | [Concentric ring discovery](../marketplace/discovery), DHT lookup | Low friction — bridge advertises in marketplace |
| **Encryption** | Secret Handshake (SHS) for connections, private-box for DMs | X25519 ECDH link encryption, E2E per-message | Compatible — both use Curve25519-derived keys |
| **Offline tolerance** | Excellent — feeds are self-contained | Excellent — store-and-forward, partition-tolerant | Native alignment |
| **Economics** | None — volunteer pubs | MHR token, VRF relay lottery, CRDT ledger | Bridge handles economic boundary |

## Identity Bridge

SSB and Mehr both use Ed25519 — but derive identities differently.

**SSB**: Feed ID = base64-encoded Ed25519 public key, prefixed with `@` and suffixed with `.ed25519`
```
@pAhDFHPLFCKPAlGrOAO9Pn5GBlsVsCj6EZLbT8FMCVU=.ed25519
```

**Mehr**: Destination hash = truncated Blake3 hash of the Ed25519 public key (16 bytes)
```
a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
```

### Key Reuse vs. Key Attestation

Two approaches:

**Option A: Same Keypair (Recommended for new users)**

A user generates one Ed25519 keypair and uses it for both SSB and Mehr. Their SSB feed ID and Mehr destination hash both derive from the same public key. The bridge can verify this cryptographically:

```
Verify same key:
    ssb_pubkey = base64_decode(ssb_feed_id)
    mehr_destination = Blake3(mehr_pubkey)[0:16]
    assert ssb_pubkey == mehr_pubkey  // same key → same person
```

No attestation needed. The bridge just verifies the math.

**Option B: Separate Keypairs (Existing SSB users)**

Users who already have an SSB identity create a separate Mehr keypair and link them via attestation:

```
SSBBridgeAttestation {
    mehr_pubkey: Ed25519PublicKey,
    ssb_feed_id: String,              // "@...=.ed25519"
    proof_ssb: SSBMessage,            // signed SSB message containing mehr_pubkey
    proof_mehr: Ed25519Signature,     // Mehr key signs ssb_feed_id
    bridge_node: NodeID,
    timestamp: LamportTimestamp,
}
```

Both keys sign the other's identifier — bidirectional proof of ownership. The bridge stores these attestations and serves them to either network on request.

## Data Model Translation

### SSB Feeds → Mehr DataObjects

SSB organizes data as append-only logs. Each user has one feed — a sequence of signed JSON messages. Mehr organizes data as content-addressed DataObjects stored in a DHT.

```
SSB Feed Message                    Mehr DataObject
┌──────────────────────┐            ┌──────────────────────┐
│ previous: %hash      │            │ hash: Blake3(content) │
│ author: @feedID      │            │ owner: NodeID         │
│ sequence: 42         │            │ type: Immutable       │
│ timestamp: 1706...   │            │ created: Lamport(ts)  │
│ content: {           │   Bridge   │ data: {               │
│   type: "post",      │  ────────→ │   ssb_type: "post",   │
│   text: "Hello SSB", │            │   text: "Hello SSB",  │
│   channel: "#mehr"   │            │   scope: "topic:mehr", │
│ }                    │            │   ssb_sequence: 42,   │
│ signature: ...       │            │   ssb_previous: %hash │
│                      │            │ }                     │
└──────────────────────┘            └──────────────────────┘
```

**Translation rules**:

| SSB Field | Mehr Field | Notes |
|-----------|-----------|-------|
| `author` | `owner` | Mapped via identity bridge |
| `sequence` | Stored in metadata | Preserves SSB ordering |
| `previous` | Stored in metadata | Preserves SSB feed chain |
| `content.type` | DataObject metadata | `post`, `contact`, `vote`, `about` |
| `content.text` | DataObject data | Unmodified content |
| `content.channel` | [Scope](../economics/trust-neighborhoods) | `#channel` → `topic:channel` |
| `content.mentions` | DataObject references | Hash references to other objects |
| `signature` | Stored alongside | SSB signature preserved for verification |

**Key invariant**: The bridge preserves SSB's append-only property. Each SSB message becomes an immutable Mehr DataObject. The SSB `previous` hash chain is stored in metadata so the full feed can be reconstructed from Mehr's DHT.

### Mehr DataObjects → SSB Messages

Going the other direction, Mehr social posts become SSB feed messages:

1. Bridge receives a Mehr [social post](../applications/social) (`PostEnvelope` DataObject)
2. Bridge translates it into an SSB message on its own feed (bridge identity)
3. SSB message `content.text` includes the post text
4. SSB message `content.mentions` includes a reference to the Mehr author
5. SSB users see: `[mehr:a1b2c3d4] posted: "Hello from Mehr mesh"`

**Attribution**: The bridge's SSB feed clearly attributes content to Mehr authors. SSB users can follow the bridge feed to see all Mehr-bridged content, or use clients that display bridged content inline.

### Private Messages

SSB uses `private-box` (asymmetric encryption for up to 7 recipients). Mehr uses per-recipient E2E encryption.

**Bridge handling**: Private messages require re-encryption at the bridge. The bridge decrypts from one format and re-encrypts in the other. This means:

- The bridge operator can read private messages that cross the bridge
- Users are warned about this trust requirement
- For truly sensitive conversations, both parties should use the same protocol
- Bridge can optionally support a **sealed mode** where both parties establish an E2E channel through the bridge using Mehr's native E2E, with the bridge only translating the routing

## Gossip Model Translation

SSB and Mehr both use gossip — but scope it differently.

### SSB Gossip

SSB replicates feeds based on social graph:
- **Hops = 1**: Replicate feeds of accounts you follow
- **Hops = 2**: Replicate feeds of accounts your follows follow
- **Hops = 3**: Broader network awareness (optional, bandwidth-heavy)

Each SSB node has a different view of the network, determined by who it follows.

### Mehr Gossip

Mehr gossips based on [concentric rings](../marketplace/discovery):
- **Ring 0**: Direct neighbors (full detail)
- **Ring 1**: 2-3 hops (summarized capabilities)
- **Ring 2**: Trust neighborhood (periodic)
- **Ring 3**: Beyond neighborhood (on-demand)

### Bridge Translation

The bridge reconciles these models:

```
SSB social graph    →  Mehr trust graph
─────────────────     ─────────────────
follow(@alice)     →  trust_peer(alice_mehr_id)
block(@bob)        →  (no Mehr equivalent — bridge filters)
hops=2 replication →  Ring 1 gossip scope
pub server         →  Bridge node (L2 service)
```

**SSB follows → Mehr trust**: When an SSB user follows an account that has a Mehr bridge attestation, the bridge can optionally add them to the Mehr trust graph. This is **not automatic** — it requires user consent, since Mehr trust relationships have economic implications (free relay).

**SSB channels → Mehr scopes**: SSB channels (`#topic`) map to Mehr topic scopes (`topic:topic`). The bridge subscribes to relevant SSB channels and publishes/relays content to the corresponding Mehr scopes.

## Bridge Architecture

```
┌─────────────────────────────────────────┐
│            SSB-Mehr Bridge Node          │
│                                          │
│  ┌──────────────┐  ┌──────────────────┐ │
│  │  SSB Stack    │  │   Mehr L2 Stack  │ │
│  │              │  │                  │ │
│  │ • ssb-db2    │  │ • MHR-Store     │ │
│  │ • ssb-conn   │  │ • MHR-DHT      │ │
│  │ • ssb-friends│  │ • MHR-Pub      │ │
│  │ • ssb-blobs  │  │ • Marketplace   │ │
│  └──────┬───────┘  └────────┬─────────┘ │
│         │                    │           │
│  ┌──────┴────────────────────┴─────────┐ │
│  │        Translation Layer             │ │
│  │                                      │ │
│  │  • Identity attestation registry    │ │
│  │  • Feed ↔ DataObject translator     │ │
│  │  • Channel ↔ Scope mapper           │ │
│  │  • Blob ↔ DataObject mapper         │ │
│  │  • Private message re-encryptor     │ │
│  └──────────────────────────────────────┘ │
│                                          │
│  Advertised capability:                  │
│    bridge.protocols: [SSB]               │
│    bridge.ssb_feeds_indexed: 1,234       │
│    bridge.ssb_channels: [mehr, ...]      │
└─────────────────────────────────────────┘
```

**Hardware requirements**: Raspberry Pi 4 or equivalent. SSB's database (ssb-db2) and Mehr's full L2 stack both need storage and memory. Minimum 2 GB RAM, 32 GB storage.

**Not suitable for ESP32**: SSB requires JavaScript (ssb-db2 is Node.js) or Go (go-ssb). Neither runs on microcontrollers. The bridge is an L2 service, not a constrained-device operation.

## SSB Blob ↔ Mehr DataObject

SSB stores binary content (images, files) as blobs — content-addressed by SHA-256 hash. Mehr stores content as DataObjects — content-addressed by Blake3 hash.

```
SSB Blob                          Mehr DataObject
────────                          ───────────────
&hash.sha256  ←── rehash ──→  Blake3(content)
```

**Bridge approach**:

1. SSB blob arrives at bridge
2. Bridge stores it as a Mehr immutable DataObject (Blake3-addressed)
3. Bridge maintains a mapping: `sha256_hash → blake3_hash`
4. Mehr users request by Blake3 hash; SSB users request by SHA-256 hash
5. Bridge serves both, translating the hash reference

**Bandwidth consideration**: Blobs (images, files) are large. On constrained Mehr links (LoRa), the bridge respects Mehr's `min_bandwidth` field — large blobs are only replicated to nodes with sufficient bandwidth. Metadata (post text, references) flows everywhere; blobs flow only where bandwidth permits.

## Practical Scenarios

### Alice (SSB) posts to #mesh channel

1. Alice publishes on SSB: `{ type: "post", text: "Great LoRa range today", channel: "#mesh" }`
2. Bridge replicates Alice's feed (follows Alice on SSB)
3. Bridge creates Mehr DataObject with scope `topic:mesh`
4. Mehr users subscribed to `topic:mesh` via [MHR-Pub](../services/mhr-pub) receive the post
5. Mehr users see Alice's post attributed to her SSB identity (via bridge attestation)

### Bob (Mehr) sends a DM to Alice (SSB)

1. Bob looks up Alice's Mehr identity via bridge attestation in [MHR-DHT](../services/mhr-dht)
2. Bob sends E2E encrypted message to bridge, addressed to Alice's Mehr-side identity
3. Bridge decrypts, re-encrypts with Alice's SSB public key (private-box)
4. Bridge publishes as SSB private message on its own feed, encrypted for Alice
5. Alice's SSB client decrypts and displays the message

### Community mesh (Mehr) shares content with SSB Scuttleverse

1. Community operates a local Mehr mesh with LoRa relays
2. Bridge node has both LoRa (Mehr mesh) and internet (SSB pubs) connectivity
3. Local posts tagged `topic:community-name` are translated to SSB channel `#community-name`
4. Global SSB users discover the community's content through the bridge's SSB feed
5. SSB replies flow back through the bridge to the local Mehr mesh

## Why SSB Before Other Social Protocols

| Factor | SSB | Nostr | Mastodon/ActivityPub |
|--------|-----|-------|---------------------|
| **Offline-first** | Native — designed for it | No — requires relay connectivity | No — requires server |
| **Gossip-based** | Yes — social graph replication | No — relay-based | No — HTTP federation |
| **Ed25519 identity** | Yes | No (secp256k1) | No (server-issued) |
| **No server dependency** | Yes (pubs optional) | Relays required | Server required |
| **Community ethos** | Aligned — off-grid, community, privacy | Partially aligned | Different philosophy |
| **Partition tolerant** | Excellent | Moderate | Poor |

SSB is the closest match to Mehr's design philosophy. Bridging SSB first creates the strongest ideological and technical alignment, and the SSB community is most likely to appreciate what Mehr adds (economic incentives for the infrastructure they currently run as volunteers).

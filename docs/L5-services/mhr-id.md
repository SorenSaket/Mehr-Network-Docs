---
sidebar_position: 1
title: "MHR-ID: Identity & Claims"
description: "MHR-ID self-sovereign identity system — Ed25519 key pairs, per-field visibility controls, trust graph identity, and profile management."
keywords: [identity, self-sovereign, Ed25519, decentralized identity, MHR-ID]
---

# MHR-ID: Identity & Claims

Mehr identity is **self-certifying** — your public key is your identity, and no authority can revoke it. But identity is more than a key. People want to know: *Where are you? What do you care about? Are you the same person who used to have a different key?* Identity claims and vouches answer these questions through mesh-native peer attestation.

## Claims

An **IdentityClaim** is a signed assertion by a node about itself:

```
IdentityClaim {
    claimant: NodeID,
    public_key: Ed25519PublicKey,   // enables self-verification without prior key exchange
    claim_type: enum {
        GeoPresence {
            scope: HierarchicalScope,       // "I am in Portland"
        },
        CommunityMember {
            scope: HierarchicalScope,       // "I'm in the Pokemon community"
        },
        KeyRotation {
            old_key: PublicKey,             // previous identity
            new_key: PublicKey,             // current identity
        },
        Capability {
            cap_type: CapabilityType,      // "I operate a relay" / "I have 100GB storage"
            evidence: Option<Blake3Hash>,   // hash of proof data
        },
        ExternalIdentity {
            platform: String,              // "github", "twitter", etc.
            handle: String,                // username on that platform
            challenge: Option<IdentityChallenge>,  // verification evidence
        },
        ProfileField {
            key: String,                   // field name (e.g., "display_name", "avatar")
            value: Vec<u8>,                // plaintext or encrypted (depends on visibility)
            value_type: u8,                // 0=Text, 1=ContentHash, 2=Coordinates, 3=Integer
        },
    },
    visibility: Visibility,         // who can read this claim
    evidence: Option<Evidence>,     // proof backing the claim (embedded in claim_data)
    created: Timestamp,
    expires: Option<Timestamp>,     // None = no expiry (must be renewed by vouches)
    signature: Ed25519Sig,          // signed by claimant
}
```

:::info[Specification]
IdentityClaims are self-certifying: signed by the claimant's Ed25519 key, with per-field visibility controls (Public, TrustNetwork, DirectTrust, Named). Six claim types cover geographic presence, community membership, key rotation, capabilities, external identity, and profile fields. Minimum wire size: 126 bytes.
:::

### Claim Types

| Type | ID | Purpose | Verification Method |
|------|----|---------|-------------------|
| **GeoPresence** | 0 | "I am present in this place" | [RadioRangeProof](./mhr-id-verification#radiorangeproof), [trust graph corroboration](./mhr-id-verification#trust-graph-corroboration), peer vouches. Virtual: application-specific attestation |
| **CommunityMember** | 1 | "I participate in this interest community" | Self-declared; peer vouches for closed/moderated communities |
| **KeyRotation** | 2 | "My old key migrated to this new key" | Must be signed by both old and new keys |
| **Capability** | 3 | "I provide this service" | [Proof-of-service](/docs/L4-marketplace/verification) challenge-response |
| **ExternalIdentity** | 4 | "I am this person on an external platform" | [Identity linking](./mhr-id-verification#identity-linking) — crawler or OAuth challenge |
| **ProfileField** | 5 | Arbitrary profile key-value pair | Peer vouches (same as any claim) |

**CommunityMember claims are self-declared by default** — anyone can claim interest in Pokemon. The value comes from the social graph: if 50 nodes you trust all claim `Topic("gaming", "pokemon")`, that's a real community. For **closed or moderated communities**, existing members can vouch for newcomers (high confidence) or dispute fraudulent claims (confidence: 0). A community like `Topic("portland-mesh-collective")` might informally require vouches from 2+ existing members before other nodes treat the claim as credible — this emerges from trust-weighted vouch aggregation, not from any protocol-level gate.

**ExternalIdentity** claims link your Mehr identity to external platforms. Verification uses [crawler or OAuth challenges](./mhr-id-verification#identity-linking), similar to [FUTO ID](https://docs.polycentric.io/futo-id/). This is optional and only relevant for nodes with internet access — most mesh nodes don't have internet.

**ProfileField** claims are general-purpose key-value pairs for profile information. See [Profile Fields](#profile-fields) for standard keys and value types.

## Profile Fields

A `ProfileField` claim (type 5) is a key-value pair describing something about you. Each field is a separate IdentityClaim — you publish one claim per field, each with its own [visibility](#visibility-controls) and vouch history.

### Standard Keys

These keys are conventions that clients recognize for display. Keys are free-form strings — users can add any key they want.

| Key | Value Type | Example |
|-----|-----------|---------|
| `display_name` | Text | "Alice Chen" |
| `bio` | Text | "Mesh enthusiast from Portland" |
| `avatar` | ContentHash | Blake3 hash of image in MHR-Store |
| `banner` | ContentHash | Blake3 hash of banner image |
| `email` | Text | "alice@example.com" |
| `phone` | Text | "+1-555-0123" |
| `website` | Text | "my-site@topic:tech" (MHR-Name) |
| `address` | Text | "123 Hawthorne Blvd, Portland" |
| `coordinates` | Coordinates | Lat/lon as two i32 (fixed-point, 1e-7 degrees) |
| `pronouns` | Text | "she/her" |
| `achievement` | Text | "3x EU Chess Champion" |
| `organization` | Text | "Portland Mesh Collective" |

### Value Types

| ID | Type | Encoding |
|----|------|----------|
| 0 | Text | UTF-8 string |
| 1 | ContentHash | 32-byte Blake3 hash (references a DataObject in MHR-Store) |
| 2 | Coordinates | 8 bytes: lat (i32 LE) + lon (i32 LE), fixed-point at 1e-7 degrees |
| 3 | Integer | 8 bytes: i64 LE |

### Vouchable Profile Fields

ProfileField claims use the existing vouch system. Your "3x EU Chess Champion" claim can be vouched for (confidence: 255) by peers who know it's true, or disputed (confidence: 0) by peers who know it's false. Trust-weighted vouch aggregation determines how credible each field appears to each viewer.

Sensitive fields like `email` or `phone` should use [DirectTrust or Named visibility](#visibility-controls) — there's no reason to broadcast your phone number to the entire mesh.

## Visibility Controls

Every IdentityClaim has a `visibility` field that controls who can read it. Public claims work like before — gossiped freely, readable by anyone. Non-public claims are encrypted so only authorized nodes can read the `claim_data`.

```
Visibility {
    Public,              // 0 — gossip freely, anyone can read (default)
    TrustNetwork,        // 1 — encrypted for trusted peers + friends-of-friends (2 hops)
    DirectTrust,         // 2 — encrypted for direct trusted peers only
    Named(Vec<NodeID>),  // 3 — encrypted for specific listed nodes
}
```

### Encryption per Visibility Level

All encryption uses existing Mehr primitives — no new cryptographic algorithms.

**Public** (0): `claim_data` is plaintext. Current behavior, no change.

**DirectTrust** (2): The claimant generates a symmetric group key and encrypts `claim_data` with ChaCha20-Poly1305. The group key is distributed individually to each direct trusted peer via an [E2E envelope](/docs/L2-security/security#end-to-end-encryption-data-payloads) (X25519 → ChaCha20-Poly1305), the same pattern used for [group messaging key distribution](/docs/L6-applications/messaging#key-management). When trust relationships change (peer added or removed), the group key rotates — new key distributed to current trusted peers.

**TrustNetwork** (1): Same as DirectTrust, but each direct trusted peer also re-encrypts and forwards the group key to *their* direct trusted peers (one additional hop). This extends visibility to friends-of-friends. Each forwarding peer wraps the key in an E2E envelope for the next recipient.

**Named** (3): `claim_data` is encrypted individually for each listed NodeID's public key via E2E envelope. Only those specific nodes can decrypt. The `vis_data` field carries the recipient list: count (u8) + NodeID (16 bytes each).

### Gossip Behavior by Visibility

| Visibility | Propagation | Who Can Decrypt |
|-----------|-------------|----------------|
| Public | Gossips within scope (current behavior) | Anyone |
| TrustNetwork | Gossips to trusted peers and their peers (2-hop max) | Direct + friend-of-friend peers |
| DirectTrust | Gossips to direct trusted peers only (1-hop max) | Direct trusted peers only |
| Named | Sent directly to named recipients, not gossiped | Only listed NodeIDs |

Non-public claims still propagate their **existence** — other nodes can see that a claim exists (claimant, claim_type, visibility level) but cannot read the encrypted `claim_data`. This lets the trust graph account for hidden claims without revealing their contents.

### Group Key Management

The per-claimant group key follows the same lifecycle as [group messaging keys](/docs/L6-applications/messaging#key-management):

- **Creation**: Claimant generates a ChaCha20 key and distributes it via E2E envelopes to each authorized peer (~100 bytes per recipient)
- **Rotation**: When the trust set changes (peer added/removed), generate new key, distribute to current set. Old keys retained so peers can decrypt previously-received claims
- **Practical limit**: ~100 trusted peers (same as group messaging), bounded by key distribution bandwidth

### Key Rotation and Claim Update Semantics

When a user updates a DirectTrust or TrustNetwork claim, the interaction between group key rotation and claim versioning follows these rules:

```
Trust revocation and key rotation:

  Alice revokes trust of Bob:
    1. Alice generates new group key K_new
    2. Alice distributes K_new to all CURRENT trusted peers (excluding Bob)
    3. NEW claims are encrypted with K_new
    4. OLD claims encrypted with K_old are NOT re-encrypted
       → Bob retains access to historical claims encrypted with K_old
       → Bob cannot read any claims encrypted with K_new
    Rationale: Re-encrypting old claims is impractical on constrained
    devices and creates a bandwidth storm. Historical access is acceptable
    because Bob already saw the data when he was trusted. The security
    property is forward secrecy: revoked peers lose access to FUTURE claims.

  Alice adds trust of Carol:
    1. Alice distributes current group key K_current to Carol via E2E envelope
    2. Carol can decrypt all claims encrypted with K_current
    3. Carol cannot decrypt claims encrypted with older keys
       (unless Alice explicitly re-distributes old keys — optional)
```

### Claim Versioning

Claims support monotonic versioning for updates to the same claim type and key:

```
Claim versioning rules:

  Each IdentityClaim has an implicit version derived from:
    claim_version_key = (claimant, claim_type, claim_qualifier)

  Where claim_qualifier is:
    GeoPresence:     scope string
    CommunityMember: scope string
    KeyRotation:     old_key hash
    Capability:      cap_type
    ExternalIdentity: platform + handle
    ProfileField:    key string

  Version ordering:
    Claims with the same claim_version_key are ordered by created timestamp.
    A newer claim (higher created timestamp) supersedes an older one.
    Nodes that receive both keep only the newer claim.

  Vouch migration:
    Vouches reference claims by claim_hash. When a claim is superseded:
      - Existing vouches for the old claim remain valid for that claim
      - The new claim needs fresh vouches
      - Vouchers are notified via MHR-Pub that the claim was updated
      - Vouchers can publish new vouches for the updated claim
```

### Encrypted Claim Caching

When a node fetches an encrypted claim but doesn't hold the decryption key:

```
Encrypted claim caching behavior:

  Node receives an encrypted claim it cannot decrypt:
    1. Store the encrypted ciphertext in local cache
    2. Record: (claim_hash, claimant, claim_type, visibility_level)
       — metadata is visible even for encrypted claims
    3. Cache TTL: same as unencrypted claims (scope-based gossip TTL)
    4. Do NOT retry decryption proactively

  When to attempt re-decryption:
    - When the node receives a new group key distribution from the claimant
      (indicates the node was added to the trust set)
    - The node checks all cached encrypted claims from that claimant
      and attempts decryption with the new key
    - Successfully decrypted claims are promoted to the readable cache

  The node does NOT poll or request keys. Key distribution is push-based
  (claimant → authorized peers). If the trust relationship changes and
  the node receives a key, it can retroactively decrypt cached claims.
```

### Partition Key Rotation Reconciliation

If two partitions both rotate group keys independently:

```
Partition key rotation reconciliation:

  Scenario: Alice is in partition A, some trusted peers in partition B.
  Both sides may rotate keys independently (e.g., Alice revokes someone
  in partition A; a co-admin rotates in partition B for a group).

  On merge:
    1. Both key versions are valid — they encrypt different claims
    2. Claims encrypted with K_A are decryptable by partition A peers
    3. Claims encrypted with K_B are decryptable by partition B peers
    4. Peers in both partitions may hold both keys

  Resolution:
    The claimant (Alice) performs a KEY UNIFICATION after merge:
      1. Generate a fresh key K_merged
      2. Distribute K_merged to the CURRENT trusted set (union of both partitions)
      3. Publish new claims encrypted with K_merged
      4. Old claims remain readable by whoever holds K_A or K_B

  If the claimant is offline after merge:
    No unification occurs. Both key lineages coexist.
    Peers with both keys can read all claims.
    Peers with only one key can read only that lineage's claims.
    Unification happens whenever the claimant next comes online.

  This is consistent with Mehr's eventual consistency model —
  temporary divergence is acceptable, convergence happens naturally.
```

## Profile Assembly

Clients build a user's profile locally by fetching their claims and filtering by visibility. Different viewers see different fields depending on their trust relationship with the profile owner.

```
Profile assembly (performed locally by each viewer):

  1. Fetch UserProfile DataObject for the target node (from social layer)
  2. For each claim hash in UserProfile.claims:
     a. Fetch IdentityClaim from MHR-Store or MHR-DHT
     b. Check visibility:
        - Public: read plaintext claim_data
        - DirectTrust/TrustNetwork: attempt decryption with held group key
        - Named: attempt decryption with own private key
        - If decryption fails: field exists but is hidden
     c. Check verification: aggregate trust-weighted vouches from local trust graph
     d. Categorize by claim_type:
        - GeoPresence → location section
        - CommunityMember → communities/interests section
        - ExternalIdentity → linked accounts (with verification status)
        - ProfileField → structured profile fields
        - Capability → services offered
  3. Render profile locally — each viewer sees a different subset
     based on their trust relationship with the profile owner
```

The [UserProfile](/docs/L6-applications/social#profile) DataObject in the social layer references claims by hash. The profile is a **view** assembled from claims — not a separate data structure. When a user updates a profile field, they publish a new IdentityClaim (higher sequence or new claim hash) and update the UserProfile's claim list.

### Wire Format

| Field | Size | Description |
|-------|------|-------------|
| `claimant` | 16 bytes | Destination hash |
| `public_key` | 32 bytes | Ed25519 verifying key (enables self-verification without prior key exchange) |
| `claim_type` | 1 byte | 0=GeoPresence, 1=CommunityMember, 2=KeyRotation, 3=Capability, 4=ExternalIdentity, 5=ProfileField |
| `visibility` | 1 byte | 0=Public, 1=TrustNetwork, 2=DirectTrust, 3=Named |
| `vis_data_len` | 1 byte | Length of visibility metadata (0 for Public/TrustNetwork/DirectTrust) |
| `vis_data` | variable | For Named: count (u8) + NodeID list. Empty for others |
| `claim_data_len` | 2 bytes | Length of claim_data (u16 LE) |
| `claim_data` | variable | Type-specific payload (includes evidence if applicable). Encrypted for non-Public visibility |
| `created` | 8 bytes | Unix timestamp |
| `expires` | 1–9 bytes | 1 byte flag (0=no expiry, 1=has expiry) + 8 bytes timestamp if flag=1 |
| `signature` | 64 bytes | Ed25519 signature (covers all fields including visibility, computed over plaintext before encryption) |

Minimum claim size: 126 bytes (no data, no expiry, Public visibility). Fits comfortably in a single LoRa frame.

**Backward compatibility**: Claims without the `visibility` and `vis_data_len` fields (from older nodes) default to Public visibility. New nodes detect old-format claims by checking if the byte at the visibility offset is a valid claim_data_len high byte — since visibility values are 0–3 and old claim_data_len is u16 LE, the disambiguation is unambiguous for all practical payloads.

## Vouches

A **Vouch** is a trust-weighted endorsement of someone else's claim:

```
Vouch {
    voucher: NodeID,                // who is vouching
    claim_hash: Blake3Hash,         // Blake3 hash of the IdentityClaim being vouched for
    confidence: u8,                 // 0-255: how confident the voucher is
    sequence: u64,                  // monotonic counter for superseding/revoking
    signature: Ed25519Sig,          // signed by voucher
}
```

### Vouch Properties

- **Trust-weighted**: A vouch from a node you trust directly is worth more than one from a stranger. Vouch weight decays with trust distance, just like [transitive credit](/docs/L3-economics/trust-neighborhoods#trust-based-credit): 100% for direct trusted peers, 10% for friend-of-friend, 0 beyond 2 hops.
- **Expiring**: Vouches are valid for a configurable period (default: 30 epochs). After expiry, the vouch must be renewed or the claim loses its verified status. This prevents stale geographic claims from persisting after someone moves.
- **Revocable**: A voucher can publish a revocation (vouch with `confidence: 0` for the same `claim_hash`) at any time.
- **Cumulative**: Multiple vouches for the same claim increase confidence. A geographic claim vouched by 10 trusted peers is stronger than one vouched by 1.

### Vouch Wire Format

| Field | Size | Description |
|-------|------|-------------|
| `voucher` | 16 bytes | Destination hash |
| `claim_hash` | 32 bytes | Blake3 hash of the claim |
| `confidence` | 1 byte | 0-255 |
| `sequence` | 8 bytes | Monotonic counter (LE). Higher sequence supersedes older vouches for the same (voucher, claim_hash) pair. |
| `signature` | 64 bytes | Ed25519 signature |

Total: 121 bytes. Lightweight enough to gossip freely.

## Claim Lifecycle

```
1. CREATE: Node publishes IdentityClaim (signed, stored as immutable DataObject)
2. GOSSIP: Claim propagates via MHR-DHT within relevant scope
3. VOUCH: Peers who can verify the claim publish Vouches
4. VERIFY: Other nodes calculate trust-weighted verification level
5. RENEW: Vouches expire after 30 epochs; vouchers re-vouch if claim still valid
6. REVOKE: Claimant publishes a new claim superseding the old one,
           or vouchers publish confidence=0 revocations
```

### Storage and Propagation

- Claims are stored as **immutable DataObjects** in [MHR-Store](./mhr-store)
- Geographic claims propagate within the claimed scope (a Portland claim gossips within Portland)
- Interest claims propagate within the interest scope
- Vouches propagate with the claims they reference
- Both are lightweight enough for LoRa (~121–126 bytes)

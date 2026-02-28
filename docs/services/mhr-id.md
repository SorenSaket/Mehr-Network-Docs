---
sidebar_position: 6
title: "MHR-ID"
---

# Identity & Claims (MHR-ID)

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

### Claim Types

| Type | ID | Purpose | Verification Method |
|------|----|---------|-------------------|
| **GeoPresence** | 0 | "I am present in this place" | [RadioRangeProof](#radiorangeproof), [trust graph corroboration](#trust-graph-corroboration), peer vouches. Virtual: application-specific attestation |
| **CommunityMember** | 1 | "I participate in this interest community" | Self-declared; peer vouches for closed/moderated communities |
| **KeyRotation** | 2 | "My old key migrated to this new key" | Must be signed by both old and new keys |
| **Capability** | 3 | "I provide this service" | [Proof-of-service](../marketplace/verification) challenge-response |
| **ExternalIdentity** | 4 | "I am this person on an external platform" | [Identity linking](#identity-linking) — crawler or OAuth challenge |
| **ProfileField** | 5 | Arbitrary profile key-value pair | Peer vouches (same as any claim) |

**CommunityMember claims are self-declared by default** — anyone can claim interest in Pokemon. The value comes from the social graph: if 50 nodes you trust all claim `Topic("gaming", "pokemon")`, that's a real community. For **closed or moderated communities**, existing members can vouch for newcomers (high confidence) or dispute fraudulent claims (confidence: 0). A community like `Topic("portland-mesh-collective")` might informally require vouches from 2+ existing members before other nodes treat the claim as credible — this emerges from trust-weighted vouch aggregation, not from any protocol-level gate.

**ExternalIdentity** claims link your Mehr identity to external platforms. Verification uses [crawler or OAuth challenges](#identity-linking), similar to [FUTO ID](https://docs.polycentric.io/futo-id/). This is optional and only relevant for nodes with internet access — most mesh nodes don't have internet.

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

**DirectTrust** (2): The claimant generates a symmetric group key and encrypts `claim_data` with ChaCha20-Poly1305. The group key is distributed individually to each direct trusted peer via an [E2E envelope](../protocol/security#end-to-end-encryption-data-payloads) (X25519 → ChaCha20-Poly1305), the same pattern used for [group messaging key distribution](../applications/messaging#key-management). When trust relationships change (peer added or removed), the group key rotates — new key distributed to current trusted peers.

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

The per-claimant group key follows the same lifecycle as [group messaging keys](../applications/messaging#key-management):

- **Creation**: Claimant generates a ChaCha20 key and distributes it via E2E envelopes to each authorized peer (~100 bytes per recipient)
- **Rotation**: When the trust set changes (peer added/removed), generate new key, distribute to current set. Old keys retained so peers can decrypt previously-received claims
- **Practical limit**: ~100 trusted peers (same as group messaging), bounded by key distribution bandwidth

## Identity Linking

ExternalIdentity claims (type 4) link your Mehr identity to accounts on external platforms. Verification uses two methods inspired by [FUTO ID](https://docs.polycentric.io/futo-id/#identity-linking): crawler challenges and OAuth challenges.

### Enhanced ExternalIdentity

```
ExternalIdentity {
    platform: String,                      // "github", "twitter", "mastodon", etc.
    handle: String,                        // username on that platform
    challenge: Option<IdentityChallenge>,  // verification evidence (None = unverified)
}

IdentityChallenge {
    method: u8,                            // 0=CrawlerChallenge, 1=OAuthChallenge
    challenge_hash: Blake3Hash,            // Blake3 hash of the challenge string
    verified_by: Option<NodeID>,           // oracle that performed verification
    verified_at: Option<u64>,              // epoch when verified
}
```

### Crawler Challenge

The user posts a signed challenge string on their external platform profile, and a verification oracle crawls the platform to confirm it.

```
Crawler challenge flow:
  1. User generates challenge string:
       "mehr-id:<NodeID_hex>:<nonce>:<signature>"
     where signature = Ed25519Sign(NodeID || platform || handle || nonce)

  2. User posts challenge string on their platform profile/bio/gist/post

  3. User publishes ExternalIdentity claim with:
       challenge.method = 0 (CrawlerChallenge)
       challenge.challenge_hash = Blake3(full challenge string)

  4. Verification oracle (gateway node with internet) crawls the platform URL

  5. Oracle verifies:
       - Challenge string contains the correct NodeID
       - Ed25519 signature is valid for the claimant's public key
       - Platform handle matches the claim

  6. Oracle publishes a Vouch for the claim with high confidence (200–255)

  7. Multiple independent oracles increase confidence
```

### OAuth Challenge

The user authenticates with the external platform via an OAuth flow mediated by a verification oracle. The oracle never receives the user's platform password.

```
OAuth challenge flow:
  1. User connects to a verification oracle (gateway node with internet + OAuth config)
  2. Oracle redirects user to platform's OAuth authorization page
  3. User authenticates directly with platform (password never touches oracle)
  4. Platform confirms identity to oracle via OAuth token
  5. Oracle verifies platform username matches the ExternalIdentity claim handle
  6. Oracle publishes a Vouch for the claim with high confidence (200–255)
```

### Verification Oracles

Verification oracles are **regular gateway nodes** — not special infrastructure. They:

- Advertise `Capability(verification_oracle, ...)` in their own IdentityClaims
- Have internet access (gateway tier or higher)
- Run crawler and/or OAuth verification software
- Publish vouches like any other peer
- Are subject to the same trust graph — a vouch from a trusted oracle carries more weight than one from an unknown oracle

No single oracle is authoritative. Multiple independent oracles vouching for the same ExternalIdentity claim increases confidence through the standard vouch aggregation mechanism.

### Self-Verification (No Oracle)

A user can verify their own ExternalIdentity without any oracle:

1. Post the crawler challenge string on the external platform
2. Publish the ExternalIdentity claim with the challenge hash
3. Include the platform profile URL in the claim data
4. Any peer with internet access can manually visit the URL and verify the challenge string
5. Peers who verify it publish vouches directly

This works without any oracle infrastructure — just normal peer vouching applied to a publicly visible challenge.

### Supported Platforms

Platforms are free-form strings. These are conventions clients should recognize:

| Platform | Crawler URL Pattern | OAuth Support |
|----------|-------------------|---------------|
| `github` | `github.com/{handle}` (bio or gist) | Yes |
| `twitter` | `twitter.com/{handle}` (bio) | Yes |
| `mastodon` | `{instance}/@{handle}` (bio) | Yes |
| `reddit` | `reddit.com/user/{handle}` (bio) | Yes |
| `keybase` | `keybase.io/{handle}` | No (crawler only) |
| `dns` | TXT record at `{handle}` domain | No (crawler only) |

The `dns` platform enables domain verification — post a TXT record containing the challenge string at your domain, proving you control the domain.

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

The [UserProfile](../applications/social#profile) DataObject in the social layer references claims by hash. The profile is a **view** assembled from claims — not a separate data structure. When a user updates a profile field, they publish a new IdentityClaim (higher sequence or new claim hash) and update the UserProfile's claim list.

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

- **Trust-weighted**: A vouch from a node you trust directly is worth more than one from a stranger. Vouch weight decays with trust distance, just like [transitive credit](../economics/trust-neighborhoods#trust-based-credit): 100% for direct trusted peers, 10% for friend-of-friend, 0 beyond 2 hops.
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

## Verification Methods

```
                    Verification Hierarchy

  Country ─── aggregation of regions ──────────────── Lowest precision
     │
  Region ──── aggregation of cities
     │
  City ────── aggregation of neighborhoods
     │
  Neighborhood ── RadioRangeProof (LoRa beacons) ──── Highest precision
     │
  ┌──┴────────────────────────────────────────┐
  │  [Alice]  ···radio···  [Bob]              │
  │     │                    │                │
  │   witness              witness            │
  │     │                    │                │
  │     └──── [Prover] ─────┘                 │
  │           broadcasts                      │
  │           signed beacon                   │
  └───────────────────────────────────────────┘
```

### RadioRangeProof

The mesh-native equivalent of physical presence verification. If you can hear a node's LoRa radio, you're within physical range.

```
RadioRangeProof {
    prover: NodeID,                 // node proving presence
    witnesses: Vec<Witness>,        // nodes that heard the prover
    timestamp: Timestamp,
}

Witness {
    node_id: NodeID,
    rssi: i8,                       // received signal strength (dBm)
    snr: i8,                        // signal-to-noise ratio (dB)
    signature: Ed25519Sig,          // witness signs the observation
}
```

**How it works:**

1. Node broadcasts a signed presence beacon on LoRa (this already happens every 10 seconds via [presence beacons](../marketplace/discovery#presence-beacons))
2. Nearby nodes that receive the beacon can sign a Witness attestation: "I heard this node at this signal strength at this time"
3. Multiple witnesses from known locations triangulate the prover's approximate position
4. Witnesses with verified GeoPresence claims for the same area provide stronger attestation

**Range and precision:**

| Transport | Typical Range | Position Precision |
|-----------|-------------|-------------------|
| LoRa (rural) | 5–15 km | City/neighborhood level |
| LoRa (urban) | 1–5 km | Neighborhood level |
| WiFi | 30–100 m | Building level |
| Bluetooth | 10–30 m | Room level |

RadioRangeProof verifies **neighborhood-level** physical geo claims. It cannot verify city, region, or country claims directly — those use bottom-up aggregation. It also cannot verify virtual geo scopes (game servers, organizations) — those use application-specific verification such as server-signed attestations, admin vouches, or invite-chain proofs, handled at the application layer.

### Bottom-Up Aggregation (Physical Geo Scopes)

Higher-level physical geo claims are verified by aggregating verified sub-scope claims:

```
Verification levels:

Neighborhood: RadioRangeProof
  "I'm in Hawthorne" ← proved by radio witnesses in Hawthorne

City: Aggregation of neighborhoods
  "Portland exists" ← N nodes have verified claims for Portland neighborhoods
  (hawthorne + pearl + alberta + ... = Portland)

Region: Aggregation of cities
  "Oregon exists" ← nodes have verified claims across Portland, Eugene, Bend

Country: Aggregation of regions
  And so on upward.
```

No single node proves "I'm in Oregon." The **network** proves Oregon exists collectively because many nodes have independently verified neighborhood-level presence across Oregon's geography. This is inherently Sybil-resistant — you can't fake physical presence across multiple locations simultaneously.

**Aggregation thresholds:**

| Level | Minimum Verified Sub-claims | Description |
|-------|---------------------------|-------------|
| City | 3+ verified neighborhoods | At least 3 distinct neighborhood clusters |
| Region | 2+ verified cities | At least 2 cities with verified neighborhoods |
| Country | 2+ verified regions | At least 2 regions with verified cities |

These thresholds are intentionally low — the system bootstraps from small meshes. As the network grows, the aggregation becomes denser and more trustworthy naturally.

### Peer Attestation

For claims that can't be machine-verified, trusted peers vouch based on personal knowledge:

```
Alice knows Bob is her neighbor:
    → Alice vouches for Bob's GeoPresence("...", "portland", "hawthorne")
    → Alice's vouch weight = her trust score relative to the verifier

Dave knows Eve runs a reliable relay:
    → Dave vouches for Eve's Capability(relay, ...)
    → Dave's vouch weight = his trust score relative to the verifier
```

Peer attestation is the **fallback** for everything. RadioRangeProof automates geographic verification, proof-of-service automates capability verification, but peer attestation always works — even for claims no machine can verify ("this person is a good curator").

### Trust Graph Corroboration

When the trust graph around a claimant is consistent with the claim, that's evidence the claim is legitimate — even without machine verification. This applies to **all claim types**, not just GeoPresence.

**GeoPresence**: If a node's trusted peers all have verified GeoPresence for Portland, and the node claims Portland too, the trust graph corroborates the claim — even without a RadioRangeProof.

**CommunityMember**: If a node claims `Topic("gaming", "pokemon")` and its trusted peers all have the same community claim, the trust graph corroborates membership — the node is embedded in that community.

**Capability**: If a node claims relay capability and its trusted peers have forwarded traffic through it successfully, the trust graph reflects real service history.

**ExternalIdentity**: If multiple trusted peers have independently vouched for the same ExternalIdentity claim (even without oracle verification), the social corroboration is meaningful.

```
Trust graph corroboration example (GeoPresence):

  Alice trusts: Bob, Carol, Dave, Eve (all verified Geo("portland"))
  Frank claims: Geo("portland"), no RadioRangeProof yet

  Alice's view of Frank's claim:
    - Frank is trusted by Bob and Carol (friend-of-friend)
    - Bob and Carol both have verified Portland claims
    - Frank's GeoPresence is corroborated: his trusted peers
      are in the same place he claims to be

  Corroboration score:
    count of trusted peers with verified matching claims
    ────────────────────────────────────────────────────
    total trusted peers who vouch for the claim
```

Trust graph corroboration is weaker than machine verification (a remote attacker could build trust relationships with Portland nodes without being in Portland). But it provides useful signal, especially during network bootstrap when RadioRangeProof witnesses or oracle infrastructure may be sparse. Nodes can weight corroboration below machine verification but above bare self-attestation in their local verification scoring.

### Transitive Confidence

Vouch weight decays with trust distance, following the same model as [transitive credit](../economics/trust-neighborhoods#trust-based-credit):

```
Vouch from direct trusted peer:      confidence × 1.0
Vouch from friend-of-friend:         confidence × 0.1
Vouch from 3+ hops away:             ignored (0 weight)
```

This means a node calculates the **effective verification level** of any claim by summing trust-weighted vouches from its own perspective. Different nodes may see different verification levels for the same claim, depending on their position in the trust graph. This is by design — there is no global authority on what's verified.

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

- Claims are stored as **immutable DataObjects** in [MHR-Store](mhr-store)
- Geographic claims propagate within the claimed scope (a Portland claim gossips within Portland)
- Interest claims propagate within the interest scope
- Vouches propagate with the claims they reference
- Both are lightweight enough for LoRa (~121–126 bytes)

## Geographic Mobility

What happens when you move from Portland to Tehran? Your cryptographic identity stays the same — [roaming](../applications/roaming) handles the transport layer seamlessly. But your GeoPresence claim, name bindings, and local trust relationships all need to adapt.

### Moving Between Locations

```
Alice moves from Portland to Tehran:

  1. UPDATE GEO SCOPE
     TrustConfig.scopes: Geo("portland") → Geo("tehran", "district-6")
     Publish new GeoPresence claim for Tehran (sequence+1)

  2. OLD CLAIMS FADE
     Portland GeoPresence vouches expire naturally (30 epochs)
     Portland name binding (alice@geo:portland) expires unless renewed
     Portland trusted peers still trust Alice — trust is location-independent

  3. NEW CLAIMS BUILD
     Tehran peers hear Alice's announces, witness RadioRangeProof
     Alice builds trust relationships with Tehran nodes
     Alice registers alice@geo:tehran
     Trust graph corroboration: Portland friends who trust Alice
       + Tehran peers who witness her presence = strong corroboration

  4. CROSS-LOCATION TRUST PERSISTS
     Portland friends can still message Alice (routed via mesh)
     Alice's reputation, vouches she gave, payment channels — all intact
     Only geo-scoped privileges change (can't vote on Portland issues anymore)
```

### Nomadic Users

Not everyone has a fixed location. Digital nomads, traveling merchants, mobile relay operators, and people between homes may not want a Geo scope at all.

**No Geo scope**: A node can operate without any Geo scope. Trust relationships, payment channels, and Topic-scoped communities all work regardless of location. The node simply can't participate in geo-scoped voting or register geo-scoped names.

**Broad Geo scope**: A nomad can use a broad scope like `Geo("north-america")` or `Geo("asia")` — accurate but imprecise. This enables regional content feeds without claiming a specific city.

**Frequent updates**: A node that moves often can update its Geo scope and GeoPresence claim each time. The 30-epoch vouch expiry means old location claims fade naturally. Trusted peers who travel with the node (e.g., family members, convoy partners) can vouch for each new location.

**Mobile relays**: A relay mounted on a vehicle (bus, truck, boat) changes location continuously. It can either use a broad Geo scope or update its GeoPresence claim at each stop. Its value as a relay is proven by [proof-of-service](../marketplace/verification), not by geographic stability — a mobile relay that reliably forwards traffic earns reputation regardless of where it is.

### Trust Portability

Trust relationships are **location-independent** — they are between identity keys, not between places. When Alice moves from Portland to Tehran:

- Bob in Portland still trusts Alice. His `trusted_peers` set contains Alice's NodeID, not "Alice in Portland."
- Alice can still use credit lines from Portland peers for Tehran-bound traffic
- Vouches Alice gave to Portland peers remain valid (until expiry)
- Alice's verification history travels with her key — new Tehran peers can see she was previously verified in Portland

The only things that change are **geo-scoped privileges**: geo-scoped voting eligibility, geo-scoped name bindings, and which local feeds her content appears in. Everything else — trust, reputation, payment channels, Topic-scoped communities — is portable.

## Integration with Existing Systems

### Reputation

Claims feed into the existing [reputation system](../protocol/security#sybil-resistance):

```
PeerReputation additions:
    claim_verification_level: u8,   // 0-255: aggregate verification score
    vouch_count: u16,               // number of active vouches received
```

The `claim_verification_level` is computed locally by each node based on the trust-weighted vouches it sees. A node with high verification level + high service reputation is the most trustworthy participant in the network.

### Key Rotation

The `KeyRotation` claim type works alongside the existing [KeyCompromiseAdvisory](../protocol/security#key-compromise-advisory):

```
Key migration flow:
  1. Generate new key pair
  2. Publish KeyRotation claim signed by BOTH old and new keys
     (equivalent to KeyCompromiseAdvisory with SignedByBoth evidence)
  3. Trusted peers vouch for the rotation
  4. Services (storage, compute, pub/sub) migrate agreements to new key
  5. Old key's reputation transfers to new key (trust-weighted)
```

KeyRotation claims with only the old key's signature are treated with suspicion (could be attacker with compromised key). Both-key signatures are strong evidence of legitimate migration.

### Naming

Geographic claims enable scoped naming: `alice@geo:portland` resolves only if Alice has a verified GeoPresence claim for Portland scope — see [MHR-Name](mhr-name).

### Voting

Verified geographic claims are **prerequisites for geographic voting** — a node cannot vote on Portland issues without a verified Portland-area GeoPresence claim. See [Voting](../applications/voting) for the eligibility model.

## Comparison with Other Identity Systems

| | FUTO ID (Polycentric) | Mehr Identity Claims |
|---|---|---|
| **Primary purpose** | Link centralized platform accounts | Verify mesh-native properties (location, service, community) + profile + platform linking |
| **Identity linking** | Crawler challenges + OAuth challenges | Same methods ([crawler](#crawler-challenge) + [OAuth](#oauth-challenge)), via decentralized verification oracles |
| **Verification** | Crawlers scrape platforms / OAuth challenges | RadioRangeProof / proof-of-service / peer attestation / crawler / OAuth |
| **Trust model** | PGP-style Web of Trust (binary vouch) | Trust-weighted vouches with transitive decay |
| **Visibility controls** | Not specified | [Per-claim visibility](#visibility-controls) — Public, TrustNetwork, DirectTrust, Named |
| **Profile fields** | Application-level | [Protocol-level claims](#profile-fields) with standard keys, vouchable |
| **Key recovery** | None | KeyRotation claim (signed by both keys) |
| **Internet required** | Yes (must reach platforms) | No (works on LoRa mesh with zero internet; identity linking needs internet) |
| **Geographic proof** | Not supported | RadioRangeProof via LoRa beacon witnesses |
| **Sybil resistance** | Social (number of vouches) | Economic (trust = absorb debts) + social (vouches) |
| **Confidence** | Binary (vouched or not) | Graduated (0–255 confidence × trust distance decay) |

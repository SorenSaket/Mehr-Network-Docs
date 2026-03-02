---
sidebar_position: 2
title: "MHR-ID: Verification & Linking"
description: "Identity verification methods — RadioRangeProof, bottom-up aggregation, peer attestation, trust graph corroboration, and external identity linking via crawler and OAuth challenges."
keywords: [identity verification, RadioRangeProof, identity linking, OAuth, peer attestation, MHR-ID]
---

# MHR-ID: Verification & Linking

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
:::info[Specification]
`RadioRangeProof` uses existing presence beacons (broadcast every 10 seconds) as the proof mechanism. Nearby nodes sign witness attestations with RSSI and SNR, triangulating the prover’s approximate position. It runs on constrained devices (ESP32) with no heavy crypto or GPU.
:::
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

1. Node broadcasts a signed presence beacon on LoRa (this already happens every 10 seconds via [presence beacons](/docs/L4-marketplace/discovery#presence-beacons))
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
:::tip[Key Insight]
Geographic verification is bottom-up: neighborhood claims are machine-verified via RadioRangeProof, then aggregated upward into city, region, and country claims. No single node proves a broad claim — the network collectively establishes geographic truth through independent neighborhood-level proofs.
:::
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

Vouch weight decays with trust distance, following the same model as [transitive credit](/docs/L3-economics/trust-neighborhoods#trust-based-credit):

```
Vouch from direct trusted peer:      confidence × 1.0
Vouch from friend-of-friend:         confidence × 0.1
Vouch from 3+ hops away:             ignored (0 weight)
```

This means a node calculates the **effective verification level** of any claim by summing trust-weighted vouches from its own perspective. Different nodes may see different verification levels for the same claim, depending on their position in the trust graph. This is by design — there is no global authority on what's verified.

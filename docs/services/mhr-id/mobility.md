---
sidebar_position: 3
title: "MHR-ID: Mobility & Integration"
description: "Geographic mobility, nomadic users, trust portability, and integration of MHR-ID with reputation, naming, voting, and key rotation systems."
keywords: [identity mobility, trust portability, key rotation, geographic mobility, MHR-ID]
---

# MHR-ID: Mobility & Integration

## Geographic Mobility

What happens when you move from Portland to Tehran? Your cryptographic identity stays the same — [roaming](../../applications/roaming) handles the transport layer seamlessly. But your GeoPresence claim, name bindings, and local trust relationships all need to adapt.

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

**Mobile relays**: A relay mounted on a vehicle (bus, truck, boat) changes location continuously. It can either use a broad Geo scope or update its GeoPresence claim at each stop. Its value as a relay is proven by [proof-of-service](../../marketplace/verification), not by geographic stability — a mobile relay that reliably forwards traffic earns reputation regardless of where it is.

:::caution[Trade-off]
Nomadic nodes sacrifice geo-scoped features (voting rights, local name bindings, local feed visibility) in exchange for location flexibility. A node without a Geo scope can fully participate in economics, trust, and Topic-scoped communities — but cannot vote on Portland issues or register `alice@geo:portland`.
:::

### Trust Portability

Trust relationships are **location-independent** — they are between identity keys, not between places. When Alice moves from Portland to Tehran:

- Bob in Portland still trusts Alice. His `trusted_peers` set contains Alice's NodeID, not "Alice in Portland."
- Alice can still use credit lines from Portland peers for Tehran-bound traffic
- Vouches Alice gave to Portland peers remain valid (until expiry)
- Alice's verification history travels with her key — new Tehran peers can see she was previously verified in Portland

The only things that change are **geo-scoped privileges**: geo-scoped voting eligibility, geo-scoped name bindings, and which local feeds her content appears in. Everything else — trust, reputation, payment channels, Topic-scoped communities — is portable.

:::tip[Key Insight]
Trust relationships are between identity keys, not between places. When you move cities, your entire trust graph, reputation history, and payment channels travel with you. Only geo-scoped privileges (local voting, local name bindings, local feed placement) change.
:::

## Integration with Existing Systems

### Reputation

Claims feed into the existing [reputation system](../../protocol/security#sybil-resistance):

```
PeerReputation additions:
    claim_verification_level: u8,   // 0-255: aggregate verification score
    vouch_count: u16,               // number of active vouches received
```

The `claim_verification_level` is computed locally by each node based on the trust-weighted vouches it sees. A node with high verification level + high service reputation is the most trustworthy participant in the network.

### Key Rotation

The `KeyRotation` claim type works alongside the existing [KeyCompromiseAdvisory](../../protocol/security#key-compromise-advisory):

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

Geographic claims enable scoped naming: `alice@geo:portland` resolves only if Alice has a verified GeoPresence claim for Portland scope — see [MHR-Name](../mhr-name).

### Voting

Verified geographic claims are **prerequisites for geographic voting** — a node cannot vote on Portland issues without a verified Portland-area GeoPresence claim. See [Voting](../../applications/voting) for the eligibility model.

## Comparison with Other Identity Systems

| | FUTO ID (Polycentric) | Mehr Identity Claims |
|---|---|---|
| **Primary purpose** | Link centralized platform accounts | Verify mesh-native properties (location, service, community) + profile + platform linking |
| **Identity linking** | Crawler challenges + OAuth challenges | Same methods ([crawler](./verification.md#crawler-challenge) + [OAuth](./verification.md#oauth-challenge)), via decentralized verification oracles |
| **Verification** | Crawlers scrape platforms / OAuth challenges | RadioRangeProof / proof-of-service / peer attestation / crawler / OAuth |
| **Trust model** | PGP-style Web of Trust (binary vouch) | Trust-weighted vouches with transitive decay |
| **Visibility controls** | Not specified | [Per-claim visibility](./index.md#visibility-controls) — Public, TrustNetwork, DirectTrust, Named |
| **Profile fields** | Application-level | [Protocol-level claims](./index.md#profile-fields) with standard keys, vouchable |
| **Key recovery** | None | KeyRotation claim (signed by both keys) |
| **Internet required** | Yes (must reach platforms) | No (works on LoRa mesh with zero internet; identity linking needs internet) |
| **Geographic proof** | Not supported | RadioRangeProof via LoRa beacon witnesses |
| **Sybil resistance** | Social (number of vouches) | Economic (trust = absorb debts) + social (vouches) |
| **Confidence** | Binary (vouched or not) | Graduated (0–255 confidence × trust distance decay) |

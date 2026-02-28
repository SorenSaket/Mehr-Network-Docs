---
sidebar_position: 5
title: "MHR-Name"
---

# Naming (MHR-Name)

MHR-Name provides human-readable names for the Mehr mesh. There is no global namespace and no central authority — names are **subjective**, resolved from each node's own position in the [trust graph](../economics/trust-neighborhoods). Two nodes may resolve the same name to different targets, and that's by design.

Names can point to three kinds of targets:
- **People and devices** — a NodeID (16-byte destination hash)
- **Content** — a ContentHash in [MHR-Store](mhr-store) (32-byte Blake3)
- **Services** — a running program (NodeID + service type + port)

## Name Format

Names follow the format `name@scope`:

```
maryam@geo:tehran
alice@geo:us/oregon/portland
relay-7@geo:backbone-west
pikachu-fan@topic:gaming/pokemon
my-blog@topic:tech/mesh-networking
```

The scope portion uses the [HierarchicalScope](../economics/trust-neighborhoods#hierarchical-scopes) format. Geographic scopes are prefixed with `geo:`, interest scopes with `topic:`. The `/` separator maps to hierarchy segments (e.g., `geo:us/oregon/portland` is `Geo("us", "oregon", "portland")`).

**Name constraints:**
- Max length: 64 bytes UTF-8
- Allowed characters: Unicode letters, digits, hyphens (`-`), underscores (`_`)
- No whitespace, no control characters, no `@` (reserved as scope delimiter)
- Names are normalized to NFKC Unicode form before registration and lookup

## Why No Global Namespace?

A global namespace requires global consensus on name ownership. Global consensus contradicts Mehr's partition tolerance requirement. If two partitioned networks both register the name "alice," there is no partition-safe way to resolve the conflict.

Scope-based names solve this:
- Names are locally consistent within their scope
- Different communities can have different "alice" users — they are `alice@geo:portland` and `alice@geo:tehran`
- No global coordination needed
- Scopes are self-assigned, not centrally managed

## Name Targets

A name can resolve to one of three target types:

```
NameTarget {
    NodeID(DestinationHash),           // person, device, or service operator (16 bytes)
    ContentHash(Blake3Hash),           // stored content — websites, documents (32 bytes)
    AppManifest(Blake3Hash),           // distributed application (32 bytes)
}
```

| Target Type | Use Case | Example |
|-------------|----------|---------|
| **NodeID** | People, devices, relays, service operators | `alice@geo:portland` resolves to Alice's node |
| **ContentHash** | Websites, documents, media | `my-blog@topic:tech` resolves to a blog stored in MHR-Store |
| **AppManifest** | Distributed applications | `forum-app@topic:apps/forums` resolves to an [AppManifest](distributed-apps#appmanifest) |

ContentHash targets are integrity-verified by definition — the hash guarantees the content hasn't been tampered with. AppManifest targets identify [distributed applications](distributed-apps#appmanifest) — the manifest binds together contract code, UI, and state schema into a single installable artifact. Live services (APIs, bots) are discovered through the [capability marketplace](../marketplace/discovery), not through naming — naming identifies *what* something is, the marketplace discovers *where* it's running.

## Name Registration

Names are registered by publishing a signed binding:

```
NameBinding {
    name: String,                       // max 64 bytes, NFKC normalized
    scope: HierarchicalScope,           // Geo("portland") or Topic("gaming", "pokemon")
    target: NameTarget,                 // what the name resolves to
    node_id: NodeID,                    // registrant's identity
    registered: u64,                    // epoch when first registered
    expires: u64,                       // expiry epoch (registered + 30 epochs)
    sequence: u32,                      // monotonic counter for updates
    signature: Ed25519Signature,        // signs all fields above
}
```

**Signature**: Covers all fields except the signature itself. Verified using the registrant's Ed25519 public key (obtained via announce or [MHR-ID](mhr-id) claims).

**Sequence number**: Must be strictly greater than any previous binding for the same `(name, scope, node_id)` tuple. This enables updates (changing a name's target) and prevents replay of old bindings.

**Expiry**: Bindings expire after 30 epochs (matching [vouch expiry](mhr-id#vouch-properties) in MHR-ID). Expired bindings are no longer returned in lookups. This prevents stale names from persisting after a node leaves the network.

Name bindings propagate via gossip within the matching scope — a binding for `alice@geo:portland` gossips among nodes with Portland-matching scopes.

## Name Resolution

Resolution is **subjective** — each node resolves names from its own trust graph position. When multiple bindings exist for the same name in the same scope, they are ranked by a 5-level priority:

### Resolution Priority

1. **Petname** (local override) — if the resolver has a local petname matching the query, it wins unconditionally. Petnames are never shared and cannot be overridden by network data.

2. **Trust distance** — scored from the resolver's trust graph. The binding registered by the more-trusted node wins.

   ```
   Trust score calculation:
     Direct trusted peer:        1.0
     Friend-of-friend:           Π(vouch_confidence × trust_decay) along shortest path
     Beyond 2 hops (untrusted):  0.01
   ```

   The trust score follows the same decay model as [transitive credit](../economics/trust-neighborhoods#trust-based-credit): full weight for direct peers, configurable ratio (default 10%) per hop, and a floor of 0.01 for completely untrusted nodes. Higher score wins.

3. **Verification level** — if trust scores are equal, bindings from nodes with stronger [MHR-ID](mhr-id) verification win. A node with vouched GeoPresence claims outranks one with only self-attested claims.

   ```
   Verification tiers:
     Vouched by trusted peers:   highest
     Self-attested claims only:  middle
     No identity claims:         lowest
   ```

4. **Scope specificity** — if verification levels are also equal, a binding registered with a more specific scope ranks higher. `alice@geo:us/oregon/portland` outranks `alice@geo:portland` because it's more precise.

5. **First-seen** (tiebreaker) — if all else is equal, the first binding your node received wins.

### Multi-Result Lookups

Lookups return a **ranked list** of matching bindings, not just a single result. Applications decide how to present results:
- **Auto-pick**: Use the top-ranked result silently (suitable for programmatic lookups)
- **Show list**: Present ranked candidates to the user (suitable for ambiguous names)
- **Prompt**: Ask the user to choose when the top two results are close in score

## Trust-Weighted Propagation

Name bindings propagate through the mesh via gossip, but propagation is shaped by trust:

**Within-scope gossip**: Bindings gossip among nodes whose scopes match the binding's scope. A binding for `Topic("gaming", "pokemon")` propagates among nodes with that topic scope.

**Propagation priority**: Nodes prioritize forwarding bindings from closer trust relationships. A binding from a direct trusted peer is gossiped immediately; a binding from an untrusted node may be delayed or dropped if bandwidth is constrained.

**Gossip filtering**: Nodes only forward bindings that score above a minimum trust threshold (0.01). Bindings from completely unknown, unconnected nodes are not propagated — they must build trust relationships first. This naturally limits Sybil flooding.

**Cross-scope queries**: To resolve a name in a different scope, the query propagates toward nodes whose scopes match the target. The nearest matching cluster responds with its local bindings. Results are cached locally with a TTL (default: 5 gossip intervals).

## Collision Handling

Collisions are a natural consequence of decentralized naming. MHR-Name handles them through three mechanisms:

### Display-Side Disambiguation

When a lookup returns multiple results, applications can show additional context from [MHR-ID](mhr-id) to help users distinguish between candidates:

```
Lookup: alice@geo:portland

Results:
  1. alice@geo:portland → 0x3a7f...  (trust: direct, verified: GeoPresence Portland/Hawthorne)
  2. alice@geo:portland → 0x8e2d...  (trust: 2-hop, verified: GeoPresence Portland/Pearl)
```

Verified GeoPresence claims, CommunityMember claims, and ExternalIdentity claims from MHR-ID all provide disambiguation context.

### Voluntary Scope Narrowing

Users can optionally register with a more specific scope to reduce collisions:

```
alice@geo:portland                    → broad scope, may collide
alice@geo:us/oregon/portland          → narrower, less collision risk
alice@geo:us/oregon/portland/pearl    → very specific, unlikely to collide
```

The protocol **never forces** a user to narrow their scope. This is always voluntary — a user in Portland, Oregon and a user in Portland, Maine can both register as `alice@geo:portland` if they choose. The trust-weighted resolution and display-side disambiguation handle the rest.

### Geographic Collision

Two different cities named "portland" (e.g., Portland, Oregon and Portland, Maine) would both match `geo:portland`. Proximity-based resolution handles this naturally — you'll reach whichever Portland is closer in the mesh. To disambiguate explicitly, use a longer scope path: `alice@geo:us/oregon/portland` vs. `alice@geo:us/maine/portland`.

## Name Lifecycle

```
1. REGISTER:  Node publishes NameBinding (signed, gossiped within scope)
2. GOSSIP:    Binding propagates to peers with matching scopes
3. RESOLVE:   Other nodes look up the name using trust-weighted resolution
4. RENEW:     Before expiry, re-publish with sequence+1 (same target = renewal)
5. UPDATE:    Publish with sequence+1 and new target (changes what the name points to)
6. REVOKE:    Publish with sequence+1 and a revocation flag (name is released)
7. EXPIRE:    After 30 epochs with no renewal, binding is removed from caches
```

**Renewal**: Re-publishing a binding with an incremented sequence number and the same target extends the expiry by another 30 epochs.

**Revocation**: A node can explicitly release a name by publishing a binding with the next sequence number and an empty/null target. This signals to the network that the name is no longer claimed.

**Garbage collection**: Nodes remove expired bindings from their local cache. There is no obligation to store bindings for names you don't query.

## Petnames

As a fallback and privacy feature, each user can assign **petnames** — local nicknames stored only on their own device:

```
User's petname mapping (local only, never shared):
  "Mom"       → NodeID(0x3a7f...b2c1)
  "Work"      → NodeID(0x8e2d...f4a9)
  "My Blog"   → ContentHash(0x1b5c...d3e7)
  "Forum"     → AppManifest(0x9f1a...c4d2)
```

Petnames:
- Override **all** network name resolution (highest priority in the resolution hierarchy)
- Are completely private (never shared, never gossiped)
- Can point to any target type (NodeID, ContentHash, AppManifest)
- Cannot be taken, censored, or disputed by anyone
- Are the most censorship-resistant naming possible

## Security Considerations

### 1. Name Squatting

**Attack**: An attacker registers popular names (e.g., `signal@topic:apps`) early, hoping to intercept traffic.

**Mitigation**: Trust-weighted resolution means squatted names only win for nodes that trust the squatter. For the vast majority of the network, the legitimate service — which has real trust relationships — will outrank the squatter. A name squatter with no trust connections resolves at the 0.01 floor, making their binding nearly invisible.

### 2. Sybil Name Flooding

**Attack**: Create many identities, each claiming variations of a target name, to pollute lookup results.

**Mitigation**: Gossip filtering by trust score. Sybil nodes with no trust relationships score 0.01 and their bindings are deprioritized during propagation. Because nodes only forward bindings above the minimum trust threshold, Sybil bindings don't propagate far. The cost of building genuine trust relationships limits the attacker's reach.

### 3. Partition Poisoning

**Attack**: During a network partition, inject false name bindings. After merge, these bindings compete with legitimate ones.

**Mitigation**: Sequence numbers prevent rollback — a legitimate node's higher-sequence binding always supersedes lower-sequence poison. Post-merge, trust-weighted resolution naturally favors the binding from the more-connected, more-trusted source.

### 4. Homoglyph Impersonation

**Attack**: Register `аlice@geo:portland` using Cyrillic 'а' (U+0430) instead of Latin 'a' (U+0061) to impersonate `alice@geo:portland`.

**Mitigation**: NFKC Unicode normalization on registration collapses many confusable characters. Applications should additionally display script-mixing warnings (e.g., "This name contains mixed Unicode scripts") and optionally reject names that mix scripts within a single label.

### 5. Key Compromise

**Attack**: A stolen private key is used to publish new name bindings, hijacking the victim's name.

**Mitigation**: The victim performs [key rotation](mhr-id#key-rotation) via MHR-ID. The new key publishes a higher-sequence binding for the same name. Trusted peers who vouch for the key rotation accelerate propagation of the legitimate binding. The old key's bindings become superseded.

### 6. Name-Content Binding Abuse

**Attack**: A trusted node registers a well-known name pointing to a ContentHash, then later updates it to point to malicious content.

**Mitigation**: ContentHash targets are integrity-verified — the hash itself proves the content is what was originally published. If the name's target changes (new sequence number, different ContentHash), applications should alert the user that the content behind a name has changed, similar to SSH host key warnings.

### 7. Global vs. Local Authority Conflict

**Attack**: A globally recognized application (e.g., a popular messaging service) uses the name `signal@topic:apps`. A local node in the same scope also registers `signal@topic:apps`.

**Mitigation**: There is no concept of "global authority" in Mehr — resolution is always subjective. The legitimate service will have trust relationships spanning the network, giving it a high trust score for most resolvers. The local squatter scores high only for nodes that directly trust them. For an attacker to successfully impersonate a well-known service, they would need to build trust relationships rivaling the legitimate service — which requires actually providing reliable service over time.

## Wire Format

### NameBinding

| Field | Size | Description |
|-------|------|-------------|
| `name_len` | 1 byte | Length of name in bytes (max 64) |
| `name` | variable | UTF-8 name, NFKC normalized |
| `scope` | variable | [HierarchicalScope wire format](../economics/trust-neighborhoods#wire-format) |
| `target_type` | 1 byte | 0x01=NodeID, 0x02=ContentHash, 0x03=AppManifest |
| `target` | variable | Target payload (see below) |
| `node_id` | 16 bytes | Registrant's destination hash |
| `registered` | 8 bytes | Registration epoch (u64 LE) |
| `expires` | 8 bytes | Expiry epoch (u64 LE) |
| `sequence` | 4 bytes | Monotonic counter (u32 LE) |
| `signature` | 64 bytes | Ed25519 signature |

**Target payloads:**

| Type | Tag | Payload Size | Contents |
|------|-----|-------------|----------|
| NodeID | 0x01 | 16 bytes | Destination hash |
| ContentHash | 0x02 | 32 bytes | Blake3 hash |
| AppManifest | 0x03 | 32 bytes | Blake3 hash of [AppManifest](distributed-apps#appmanifest) |

Minimum binding size: 1 + 1 + 3 + 1 + 16 + 16 + 8 + 8 + 4 + 64 = **122 bytes** (1-char name, minimal scope, NodeID target). Fits in a single Mehr packet (max 465 bytes data).

### Message Types

Name messages use context byte `0xF7` (social) with sub-types:

| Sub-Type | Name | Description |
|----------|------|-------------|
| `0x08` | NameRegister | Publish or update a name binding |
| `0x09` | NameLookup | Query for a name in a scope |
| `0x0A` | NameLookupResponse | Return matching bindings (ranked list) |

### Backward Compatibility

The old `name@community-label` format maps to the new scope format:

```
alice@portland-mesh    →  alice@geo:portland
relay-7@backbone-west  →  relay-7@geo:backbone-west
```

Old bindings without a `target_type` field default to NodeID using the `node_id` field. Old bindings without `expires` or `sequence` fields are treated as sequence 0 with no expiry (legacy behavior). Nodes running older software continue to use the flat `community_label` field. New nodes check both `scopes` and `community_label` for resolution.

## Integration Points

**[MHR-ID](mhr-id)**: Vouches feed trust scores used in name resolution. GeoPresence claims enable display-side disambiguation. KeyRotation claims enable name recovery after key compromise.

**[MHR-Store](mhr-store)**: ContentHash name targets point to stored content. Name bindings themselves can be stored as DataObjects for persistence beyond gossip TTL.

**[MHR-DHT](mhr-dht)**: Name bindings are replicated via DHT within their scope. Cross-scope lookups use DHT routing to find nodes with matching scopes.

**[Trust Graph](../economics/trust-neighborhoods)**: The trust graph is the foundation of name resolution. Trust distance determines binding priority. The `trust_decay` product along the shortest path yields the trust score.

**[MHR-Pub](mhr-pub)**: Applications can subscribe to name change events via pub/sub. When a name binding is updated (new sequence number), subscribers are notified — useful for contact list sync and service discovery.

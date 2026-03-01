---
sidebar_position: 2
title: "MHR-DHT: Distributed Hash Table"
description: "MHR-DHT maps keys to storage nodes using proximity-weighted gossip instead of strict Kademlia routing for mesh networks."
keywords:
  - DHT
  - distributed hash table
  - Kademlia
  - gossip
  - key-value
  - routing
---

# MHR-DHT: Distributed Hash Table

MHR-DHT maps keys to the nodes that store the corresponding data. It uses proximity-weighted gossip rather than Kademlia-style strict XOR routing, because link quality varies wildly on a mesh network.

### Distance Metrics: Routing vs. DHT

Mehr uses two different distance metrics for different purposes:

- **Ring distance** (routing layer): `min(|a - b|, 2^128 - |a - b|)` over the destination hash space. Used for [greedy forwarding](../protocol/network-protocol#small-world-routing-model) to route packets toward their destination. This is the Kleinberg small-world model.
- **XOR distance** (DHT layer): `a ⊕ b` over DHT key space. Used for determining storage responsibility — which nodes are "closest" to a given key and should store its data.

Both operate over 128-bit spaces derived from the same hash functions, but they serve different roles. Routing cares about navigating to a destination efficiently; the DHT cares about partitioning key-space responsibility among nodes.

## Why Not Kademlia?

Traditional Kademlia routes lookups based on XOR distance between node IDs and key hashes, assuming roughly uniform latency between any two nodes. On a Mehr mesh:

- A node 1 XOR-hop away might be 10 LoRa hops away
- A node 10 XOR-hops away might be a direct WiFi neighbor
- Link quality varies by orders of magnitude

MHR-DHT uses **proximity-weighted gossip** that considers both XOR distance and actual network cost when deciding where to route lookups. XOR distance determines the **target** (which nodes should store a key); network cost determines the **path** (how to reach those nodes efficiently).

## Routing Algorithm

### Lookup Scoring Function

Each DHT lookup hop selects the next node by minimizing:

```
dht_score(candidate, key) = w_xor × norm_xor_distance(candidate.id, key)
                          + (1 - w_xor) × norm_network_cost(candidate)
```

Where:
- `norm_xor_distance` = `xor(candidate.id, key) / max_xor_in_candidate_set`, normalized to [0, 1]
- `norm_network_cost` = `cumulative_cost_to(candidate) / max_cost_in_candidate_set`, normalized to [0, 1]
- `w_xor = 0.7` (default — favor key-space closeness, but avoid expensive paths)

This produces the same iterative-closest-node behavior as Kademlia but routes around expensive links rather than blindly following XOR distance.

:::info[Specification]
DHT lookups minimize `w_xor × norm_xor_distance + (1 - w_xor) × norm_network_cost` with default `w_xor = 0.7`. XOR distance determines the **target** (who stores the data); network cost determines the **path** (how to reach them efficiently).
:::

### Replication Factor

Each key is stored on the **k=3 closest nodes** in XOR distance that are reachable within a cost budget:

```
Storage responsibility:
  1. Sort all known nodes by xor(node.id, key)
  2. Walk the sorted list; skip nodes whose network cost exceeds 10× the cheapest
  3. First k=3 reachable nodes are the storage set
```

The cost filter prevents a node on the far side of a LoRa link from being assigned storage responsibility for a key it can barely reach. The XOR ordering ensures deterministic agreement on who stores what.

### Rebalancing

- **Node join**: A new node announces itself. Existing nodes check whether any stored keys are now closer (in XOR) to the new node. After **2 gossip rounds** (for announcement convergence), affected keys are pushed via gossip metadata. The new node pulls full data and becomes part of the storage set.
- **Node departure**: Detected via missed heartbeats (3 consecutive gossip rounds = ~3 minutes). The departed node is immediately marked down — no new writes are sent to it. After **6 additional missed rounds** (~6 minutes total since last response), remaining storage-set members initiate re-replication to the next-closest reachable node, restoring k=3. If no reachable replacement exists within the cost budget, durability is temporarily degraded (k=2 or k=1) and a warning is logged. Normal replication resumes when a suitable node becomes available.

## Lookup Process

```
DHT Lookup:
  1. Query direct neighbors for the key
  2. Each responds with either the data or a referral to a closer node
     (selected by dht_score — balancing XOR closeness and network cost)
  3. Follow referrals iteratively until data is found or all k closest nodes queried
  4. Cache result locally with TTL
  5. Parallel lookups: query α=3 nodes concurrently, use first valid response
```

### Bandwidth per Lookup

| Component | Size |
|-----------|------|
| Query | ~64 bytes |
| Response (referral) | ~48 bytes (node_id + cost hint) |
| Response (data found) | ~128 bytes + data size |
| Typical lookup (3-5 hops on LoRa) | 2-3 seconds |

## Publication Process

```
DHT Publication:
  1. Store the object locally
  2. Gossip key + metadata (not full data) to neighbors
  3. Nodes close to the key's hash (k=3 storage set) pull the full data
  4. Neighborhood-scoped objects gossip within the trust neighborhood only
```

Publication gossips only metadata — the full data is pulled on demand. This prevents large objects from flooding the gossip channel.

### Metadata Format

```
DHTMetadata {
    key: [u8; 32],           // Blake3 content hash (32 bytes)
    size: u32,               // object size in bytes (4 bytes)
    content_type: u8,        // 0=Immutable, 1=Mutable, 2=Ephemeral (1 byte)
    owner: [u8; 16],         // publisher's destination hash (16 bytes)
    ttl_remaining: u32,      // seconds until expiry (4 bytes)
    lamport_ts: u64,         // publisher's Lamport timestamp (8 bytes, for mutable ordering)
    signature: [u8; 64],     // Ed25519 signature over (key || size || content_type || lamport_ts) (64 bytes)
}
// Total: 129 bytes per metadata entry
// Signature prevents metadata forgery; content hash prevents data forgery
```

For **mutable objects**, `lamport_ts` determines freshness — the highest timestamp with a valid signature wins. For **immutable objects**, `lamport_ts` is the publication time and the content hash is sufficient for verification.

**Cache invalidation**: Mutable objects are invalidated by receiving a metadata entry with a higher `lamport_ts` for the same `owner` and logical key. There is no push-invalidation mechanism — caches rely on TTL expiry and periodic re-query of the storage set for freshness-critical data.

## Cache TTL

Cache lifetime follows a two-level policy:

- **Publisher TTL**: Set by the data owner. Maximum lifetime for the cached copy. Range: 60 seconds to 30 days.
- **Local cap**: `min(publisher_ttl, 24 hours)`. Prevents stale caches from persisting when publishers update their data.
- **Access refresh**: Accessing a cached item resets its local TTL to `min(remaining_publisher_ttl, 24 hours)`. Frequently accessed items stay cached; idle items expire.
- **Eviction**: When local cache exceeds its storage budget, least-recently-used entries are evicted first regardless of remaining TTL.

## Neighborhood-Scoped DHT

Objects can be scoped to a [trust neighborhood](../economics/trust-neighborhoods), meaning:

- Their metadata only gossips between trusted peers and their neighbors
- Only nodes within the trust neighborhood can discover them
- Storage nodes within the neighborhood are preferred
- Cross-neighborhood lookups require explicit queries (Ring 3 discovery)

This is useful for community content that doesn't need global visibility. Scoping emerges naturally from the trust graph — there is no explicit "zone" to configure.

## Caching

Lookup results are cached locally with a TTL (time-to-live). This means:

- Frequently accessed data is served from local cache
- The DHT is queried only when the cache expires
- Popular content naturally distributes across many caches
- Cache TTL is set by the data publisher

## Light Client Verification

Mobile nodes and other constrained devices delegate DHT lookups to a nearby relay rather than participating in the DHT directly. This creates a trust problem: how does the light client know the relay's response is honest?

Three verification tiers handle this, scaled by data type:

### Tier 1 — Content-Addressed Lookups (Zero Overhead)

Most DHT objects are stored by content hash. Verification is automatic:

```
Light client lookup by hash:
  1. Request key K from relay
  2. Relay returns data D
  3. Verify: Blake3(D) == K
  4. Match → data is authentic (relay honesty irrelevant)
  5. Mismatch → discard, flag relay, retry via different node
```

No extra bandwidth, no extra queries. The hash the client already knows is the proof.

### Tier 2 — Signed Object Lookups (Signature Check)

For mutable data (MHR-Name records, capability advertisements, profile updates), objects carry the owner's Ed25519 signature:

```
Light client lookup for mutable object:
  1. Request mutable key from relay
  2. Relay returns: { data, owner_pubkey, signature, lamport_timestamp }
  3. Verify: Ed25519_verify(owner_pubkey, data || timestamp, signature)
  4. Valid → data is authentic (relay cannot forge owner's signature)
  5. Invalid → discard, flag relay
```

A malicious relay can return **stale but validly signed** data. It cannot forge new data. Staleness is handled by Tier 3.

### Tier 3 — Multi-Source Queries (Anti-Censorship, Anti-Staleness)

For lookups where censorship or staleness matters, the client queries multiple independent nodes:

```
Multi-source lookup (quorum_size N):
  1. Send lookup to N independent nodes (relay + N-1 others from Ring 0/1)
  2. Collect responses with timeout
  3. Content-addressed: any valid response is sufficient
  4. Mutable: highest lamport_timestamp with valid signature wins
  5. "Not found" accepted only if unanimous across all N
  6. Divergent results: flag dissenting node(s), trust majority
```

Default quorum sizes:

| Lookup Type | Default N | Notes |
|------------|----------|-------|
| Content-addressed | 1 | Hash verification is sufficient |
| Name resolution | 2 | First resolution of unknown name uses N=3 |
| Mutable object | 2 | N=3 if freshness is critical |
| Service discovery | 1 | N=2 if results seem incomplete |

### Trusted Relay Shortcut

If the client's relay is in its [trust graph](../economics/trust-neighborhoods), single-source queries (N=1) are sufficient for all tiers. Multi-source queries are only needed for untrusted relays. A trusted relay has economic skin in the game — trust means absorbing the trusted node's debts, making dishonesty self-punishing.

### Overhead

| Scenario | Extra Queries | Extra Bandwidth |
|----------|--------------|----------------|
| Content-addressed, any relay | 0 | 0 |
| Mutable, trusted relay | 0 | 0 |
| Mutable, untrusted relay | +1 | ~192 bytes |
| Name resolution | +1 | ~192 bytes |

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>What is a DHT and why does Mehr need one?</summary>

A Distributed Hash Table (DHT) is a decentralized lookup system — given a key (like a content hash), it tells you which nodes store the corresponding data. Mehr needs it so any node can find any piece of data without asking a central server. Think of it as a phone book that’s spread across everyone’s devices instead of sitting in one place.

</details>

<details className="faq-item">
<summary>How do lookups work if some nodes are offline?</summary>

Each key is stored on k=3 nodes for redundancy. If one node is offline, the other two can still serve the data. Lookups query multiple nodes in parallel (α=3 concurrently) and use the first valid response. If a node goes offline for too long (~6 minutes), the remaining storage nodes re-replicate the data to a replacement, restoring full redundancy.

</details>

<details className="faq-item">
<summary>Are there limits on how much data I can store in the DHT?</summary>

The DHT itself stores only lightweight metadata (~129 bytes per entry) — not the full data. Full data lives in MHR-Store. The metadata includes the content hash, size, owner, and a signature. There’s no hard per-node limit, but cache eviction uses least-recently-used policy when local storage is full, and TTLs ensure stale entries expire.

</details>

<details className="faq-item">
<summary>Can a malicious node return fake data from a DHT lookup?</summary>

For content-addressed lookups (most common), fakery is impossible — the hash you already know *is* the proof. If `Blake3(returned_data) != requested_hash`, the data is rejected. For mutable data, the owner’s Ed25519 signature prevents forgery. A malicious relay can return stale data but cannot fabricate new data. Multi-source queries catch staleness.

</details>

<!-- faq-end -->

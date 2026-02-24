---
sidebar_position: 2
title: "NXS-DHT: Distributed Hash Table"
---

# NXS-DHT: Distributed Hash Table

NXS-DHT maps keys to the nodes that store the corresponding data. It uses proximity-weighted gossip rather than Kademlia-style strict XOR routing, because link quality varies wildly on a mesh network.

## Why Not Kademlia?

Traditional Kademlia routes lookups based on XOR distance between node IDs and key hashes, assuming roughly uniform latency between any two nodes. On a NEXUS mesh:

- A node 1 XOR-hop away might be 10 LoRa hops away
- A node 10 XOR-hops away might be a direct WiFi neighbor
- Link quality varies by orders of magnitude

NXS-DHT uses **proximity-weighted gossip** that considers both XOR distance and actual network cost when deciding where to route lookups.

## Lookup Process

```
DHT Lookup:
  1. Ask direct neighbors for the key
  2. They refer you to closer nodes (weighted by cost + XOR distance)
  3. Follow referrals until data is found
  4. Cache result locally with TTL
```

### Bandwidth per Lookup

| Component | Size |
|-----------|------|
| Query | ~64 bytes |
| Response | ~128 bytes per hop |
| Typical lookup (3-5 hops on LoRa) | 2-3 seconds |

## Publication Process

```
DHT Publication:
  1. Store the object locally
  2. Gossip key + metadata (not full data) to neighbors
  3. Nodes close to the key's hash pull the full data
  4. Neighborhood-scoped objects gossip within the trust neighborhood only
```

Publication gossips only metadata — the full data is pulled on demand. This prevents large objects from flooding the gossip channel.

## Neighborhood-Scoped DHT

Objects can be scoped to a [trust neighborhood](../economics/community-zones), meaning:

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

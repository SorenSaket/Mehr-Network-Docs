---
sidebar_position: 1
title: "NXS-Store: Content-Addressed Storage"
---

# NXS-Store: Content-Addressed Storage

NXS-Store is the storage layer of NEXUS. Every piece of data is addressed by its content hash — if you know the hash, you can retrieve the data from anywhere in the network.

## Data Objects

```
DataObject {
    hash: Blake3Hash,               // content hash = address
    content_type: enum { Immutable, Mutable, Ephemeral },
    owner: Option<NodeID>,          // for mutable objects
    created: Timestamp,
    ttl: Option<Duration>,          // for ephemeral objects
    size: u32,
    priority: enum { Critical, Normal, Lazy },
    min_bandwidth: u32,             // don't attempt transfer below this bps

    replication: enum {
        Local,                      // origin node only
        Neighborhood(label),        // within a trust neighborhood
        Network(n),                 // n copies globally
    },

    payload: enum {
        Inline(Vec<u8>),            // small objects
        Chunked([ChunkHash]),       // large objects (4 KB chunks)
    },
}
```

## Content Types

### Immutable

Once created, the content never changes. The hash is the permanent address. Used for: messages, posts, media files, contract code.

### Mutable

The owner can publish updated versions, signed with their key. The highest sequence number wins. Any node can verify the signature. Used for: profiles, status updates, configuration.

### Ephemeral

Data with a time-to-live (TTL). Automatically garbage-collected after expiration. Used for: presence information, temporary caches, session data.

## Bandwidth Adaptation

The `min_bandwidth` field is how bandwidth adaptation works at the data layer:

```
Example:
  A 500 KB image declares min_bandwidth: 10000 (10 kbps)

  LoRa node (1 kbps):
    → Propagates hash and metadata only
    → Never attempts to transfer the full image

  WiFi node (100 Mbps):
    → Transfers normally
```

This is not a separate "transform" layer. It is a property of the data object that the storage and routing layers respect. Applications set `min_bandwidth` based on the nature of the data, and the network automatically handles the rest.

## Replication Strategies

| Strategy | Scope | Use Case |
|----------|-------|----------|
| **Local** | Origin node only | Private data, temporary files |
| **Neighborhood** | Within a trust neighborhood | Community content, local announcements |
| **Network(n)** | n copies across the network | Important data requiring high availability |

## Chunking

Large objects are split into 4 KB chunks, each independently addressed by hash:

```
Large file (1 MB):
  → Split into 256 chunks of 4 KB each
  → Each chunk has its own Blake3 hash
  → The DataObject stores the list of chunk hashes
  → Chunks can be retrieved from different nodes in parallel
  → Missing chunks can be re-requested individually
```

Chunking enables:
- Parallel downloads from multiple peers
- Efficient deduplication (identical chunks across objects are stored once)
- Resumable transfers on unreliable links
- Fine-grained replication (hot chunks replicated more)

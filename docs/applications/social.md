---
sidebar_position: 2
title: Social
---

# Social

A decentralized social network built on NEXUS primitives. No central servers, no algorithmic recommendations — just chronological feeds assembled locally from followed users.

## Architecture

Each user has:

- **Profile**: A mutable DataObject containing display name, bio, avatar hash, etc.
- **Feed**: An append-only log of posts, where each post is an immutable DataObject
- **Followers**: Subscribers are tracked via NXS-Pub subscriptions

## Feed Assembly

Feed aggregation is entirely local. Each device:

1. Maintains a list of followed users (NodeIDs)
2. Subscribes to each followed user via [NXS-Pub](../services/nxs-pub)
3. Receives notifications when followed users publish new posts
4. Assembles the timeline locally in chronological order

There is no algorithmic recommendation. No engagement optimization. Just a reverse-chronological feed of content from people you follow.

## Media Tiering

Media adapts to available bandwidth using `min_bandwidth` on DataObjects:

| Content Type | Size | min_bandwidth | Available On |
|-------------|------|---------------|-------------|
| Text post | ~200 bytes | 0 (any link) | Everywhere |
| Blurhash thumbnail | ~64 bytes | 0 | Everywhere, including LoRa |
| Compressed image | ~50 KB | 10,000 (10 kbps) | WiFi and above |
| Full resolution image | ~500 KB | 100,000 (100 kbps) | WiFi and above |
| Video | >1 MB | 1,000,000 (1 Mbps) | High-bandwidth links only |

The application decides which tier to request based on current link quality:

```
let link = query_link_quality(author_node);

if link.bandwidth_bps < 1000 {
    // LoRa: text + blurhash only
    fetch(post.text);
    fetch(post.blurhash_thumbnail);
} else if link.bandwidth_bps < 100_000 {
    // Moderate: add compressed images
    fetch(post.compressed_image);
} else {
    // High bandwidth: full resolution
    fetch(post.full_image);
}
```

## Privacy

- Posts can be public (replicated broadly) or neighborhood-scoped (visible only within a trust neighborhood)
- No central server has a copy of anyone's social graph
- Following is a local operation — only you and the person you follow need to know
- Unfollowing is purely local — just stop subscribing

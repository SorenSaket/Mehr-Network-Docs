---
sidebar_position: 3
title: "MHR-Pub: Publish/Subscribe"
---

# MHR-Pub: Publish/Subscribe

MHR-Pub provides a publish/subscribe system for real-time notifications across the mesh. It supports multiple subscription types and delivery modes, allowing applications to choose the right tradeoff between immediacy and bandwidth.

## Subscriptions

```
Subscription {
    subscriber: NodeID,
    topic: enum {
        Key(hash),              // specific key changed
        Prefix(hash_prefix),    // any key with prefix changed
        Node(NodeID),           // any publication by this node
        Neighborhood(label),    // any publication in this community label
    },
    delivery: enum {
        Push,                   // immediate, full payload
        Digest,                 // batched summaries, periodic
        PullHint,               // hash-only notification
    },
}
```

## Subscription Topics

| Topic Type | Use Case |
|-----------|----------|
| **Key** | Watch a specific data object for changes (e.g., a friend's profile) |
| **Prefix** | Watch a category of keys (e.g., all posts in a forum) |
| **Node** | Follow all publications from a specific user |
| **Neighborhood** | Watch all activity from nodes with a given community label |

## Delivery Modes

### Push

Full payload delivered immediately when published. Best for high-bandwidth links where real-time updates matter.

**Use on**: WiFi, Ethernet, Cellular

### Digest

Batched summaries delivered periodically. Reduces bandwidth by aggregating multiple updates into a single digest.

**Use on**: Moderate bandwidth links, or when real-time isn't critical

### PullHint

Only the hash of new content is delivered. The subscriber decides whether and when to pull the full data.

**Use on**: LoRa and other constrained links where bandwidth is precious

## Application-Driven Delivery Selection

Delivery mode selection is the **application's responsibility**, informed by link quality. The protocol provides tools; the application decides:

```
// Application code (pseudocode)
let link = query_link_quality(publisher_node);

if link.bandwidth_bps > 1_000_000 {
    subscribe(topic, Push);       // WiFi: get everything immediately
} else if link.bandwidth_bps > 10_000 {
    subscribe(topic, Digest);     // moderate: batched summaries
} else {
    subscribe(topic, PullHint);   // LoRa: just tell me what's new
}
```

The pub/sub system doesn't make this decision — the application does, based on `query_link_quality()` from the capability layer.

## Bandwidth Characteristics

| Delivery Mode | Per-notification overhead | Suitable for |
|--------------|-------------------------|-------------|
| Push | Full object size | WiFi, Ethernet |
| Digest | ~50 bytes per item (hash + summary) | Moderate links |
| PullHint | ~32 bytes (hash only) | LoRa, constrained links |

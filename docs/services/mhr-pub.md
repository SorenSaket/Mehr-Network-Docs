---
sidebar_position: 3
title: "MHR-Pub: Publish/Subscribe"
description: "MHR-Pub provides publish/subscribe notifications across the Mehr mesh with topic-based subscriptions and multiple delivery modes."
keywords:
  - publish
  - subscribe
  - notifications
  - pub/sub
  - real-time
  - topics
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
        Neighborhood(label),    // any publication in this community label (deprecated)
        Scope(ScopeMatch),      // any publication matching a hierarchical scope
    },
    delivery: enum {
        Push,                   // immediate, full payload
        Digest,                 // batched summaries, periodic
        PullHint,               // hash-only notification
    },
}

ScopeMatch {
    scope: HierarchicalScope,   // from trust-neighborhoods
    match_mode: enum {
        Exact,                  // this scope level only
        Prefix,                 // this scope and all children
    },
}
```

## Subscription Topics

| Topic Type | Use Case |
|-----------|----------|
| **Key** | Watch a specific data object for changes (e.g., a friend's profile) |
| **Prefix** | Watch a category of keys (e.g., all posts in a forum) |
| **Node** | Follow all publications from a specific user |
| **Neighborhood** | Watch all activity from nodes with a given community label (deprecated — use Scope) |
| **Scope** | Watch all activity matching a [hierarchical scope](../economics/trust-neighborhoods#hierarchical-scopes) — geographic or interest |

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

:::tip[Key Insight]
Three delivery modes — Push, Digest, PullHint — let the application match notification overhead to link capacity. LoRa nodes receive 32-byte hash hints; WiFi nodes get full payloads. The protocol provides the tools; the application chooses the tradeoff.
:::

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

### Envelope-Aware Delivery

For [Social](../applications/social) content, MHR-Pub notifications carry the [PostEnvelope](../applications/social#postenvelope-free-layer) — the free preview layer — rather than the full post:

| Delivery Mode | What's Delivered | Reader Cost |
|--------------|-----------------|-------------|
| Push | Full PostEnvelope (~300-500 bytes) | Free |
| Digest | Batched envelopes (headline + hash per item) | Free |
| PullHint | Post hash only (32 bytes) | Free (envelope fetched on demand) |

In all modes, the reader browses envelopes at zero cost. Fetching the full [SocialPost](../applications/social#socialpost-paid-layer) content is a separate, paid retrieval from the storage node. This separation means even LoRa nodes on PullHint subscriptions can browse headlines and decide what's worth fetching over a higher-bandwidth link later.

## Scope Subscriptions

Scope subscriptions are the primary mechanism for geographic feeds, interest feeds, and community content discovery. They build on [Hierarchical Scopes](../economics/trust-neighborhoods#hierarchical-scopes) to enable structured content routing.

### Geographic Feeds

Subscribe to content from a geographic area at any level of the hierarchy:

```
// All posts from Portland
subscribe(Scope(Geo("north-america", "us", "oregon", "portland"), Exact), Push);

// All posts from anywhere in Oregon
subscribe(Scope(Geo("north-america", "us", "oregon"), Prefix), Digest);
```

Geographic scope subscriptions naturally bias toward local content — nearby nodes have cheaper relay paths and higher cache density, so local content arrives faster and costs less.

### Interest Feeds

Subscribe to content by topic at any level of the hierarchy:

```
// All Pokemon content globally
subscribe(Scope(Topic("gaming", "pokemon"), Prefix), Digest);

// Only competitive Pokemon
subscribe(Scope(Topic("gaming", "pokemon", "competitive"), Exact), Push);
```

Interest subscriptions are **sparse** — they span geography. A Pokemon subscription connects Portland, Tokyo, and Berlin through interest relay nodes that bridge geographic clusters.

### Intersection Feeds

A client can subscribe to both a geographic and interest scope simultaneously and filter locally for the intersection:

```
// Subscribe to Portland content AND Pokemon content
subscribe(Scope(Geo("north-america", "us", "oregon", "portland"), Exact), Push);
subscribe(Scope(Topic("gaming", "pokemon"), Prefix), Push);

// Client-side: show posts that appear in BOTH feeds
// Result: Portland Pokemon community
```

Intersection is always client-side — the protocol delivers by individual scope, and the application composes.

### Scope Routing

When a node publishes with scopes, notifications propagate to subscribers at each level:

```
Post published with scopes:
  Geo("north-america", "us", "oregon", "portland", "hawthorne")
  Topic("gaming", "pokemon")

Notifications delivered to:
  Scope(Geo("...", "hawthorne"), Exact)     ✓  exact match
  Scope(Geo("...", "portland"), Prefix)      ✓  portland covers hawthorne
  Scope(Geo("...", "oregon"), Prefix)        ✓  oregon covers portland
  Scope(Topic("gaming", "pokemon"), Exact)   ✓  exact match
  Scope(Topic("gaming"), Prefix)             ✓  gaming covers pokemon
  Scope(Geo("...", "seattle"), Exact)        ✗  wrong city
  Scope(Topic("science"), Prefix)            ✗  wrong topic
```

### Delivery Mode by Scope Level

Applications should select delivery mode based on both link quality and scope breadth:

| Scope Level | Typical Volume | Recommended Default |
|-------------|---------------|-------------------|
| Neighborhood | Low | Push |
| City | Moderate | Push or Digest |
| Region | High | Digest |
| Country/Global | Very high | PullHint |
| Narrow interest topic | Low-moderate | Push |
| Broad interest topic | High | Digest |

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>How is MHR-Pub different from regular messaging?</summary>

Messaging is point-to-point: Alice sends a message to Bob. MHR-Pub is publish/subscribe: Alice publishes to a topic, and anyone subscribed to that topic receives the notification. It’s the backbone for feeds, real-time updates, sync notifications, and event-driven applications — one publisher can reach many subscribers without knowing who they are.

</details>

<details className="faq-item">
<summary>Can I subscribe to topics from communities across the mesh, not just my local area?</summary>

Yes. Scope subscriptions support both geographic and interest-based topics at any level of the hierarchy. You can subscribe to `Topic("gaming", "pokemon")` globally or `Geo("us", "oregon", "portland")` locally. Cross-scope subscriptions are bridged by interest relay nodes that connect geographic clusters. Content from distant scopes just costs more in relay fees.

</details>

<details className="faq-item">
<summary>Won’t pub/sub flood my LoRa link with notifications?</summary>

No. MHR-Pub offers three delivery modes precisely for this. On LoRa, you’d use **PullHint** — only a 32-byte hash is delivered per notification. You decide what’s worth fetching later over a faster link. On WiFi, you can use **Push** for full payloads. The application selects the mode based on current link quality, so constrained links are never overwhelmed.

</details>

<details className="faq-item">
<summary>What happens to notifications if I’m offline?</summary>

Notifications are not stored indefinitely by the pub/sub system — it’s real-time delivery. However, applications handle offline scenarios by storing state in MHR-Store. When you come back online, your node queries MHR-Store and MHR-DHT to catch up on missed updates. For social feeds, the envelope/post architecture means you can quickly scan what’s new without downloading everything.

</details>

<!-- faq-end -->

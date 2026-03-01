---
sidebar_position: 6
title: Hosting & Websites
description: "Host websites on Mehr by storing DataObjects in MHR-Store — no server, no DNS, no certificate authority required."
keywords:
  - hosting
  - websites
  - static sites
  - MHR-Name
  - DataObjects
  - decentralized web
---

# Hosting on Mehr

Traditional web hosting requires a server, a domain name, a certificate, and ongoing payment to a hosting provider. On Mehr, hosting is just storing DataObjects and letting the network serve them. No server. No DNS. No certificate authority.

:::info[App Manifest]
Hosting is packaged as a **Static** (content only) [AppManifest](../services/mhr-app) for simple sites, or **Full** (UI + compute) for dynamic sites with server-side logic. It composes MHR-Store for HTML, CSS, JavaScript, and media DataObjects; MHR-Name for human-readable site addresses (e.g., `mysite@geo:portland`); and optionally MHR-Pub for feed updates and MHR-Compute for dynamic content generation or forum moderation contracts.
:::

## Hosting a Website

A "website" on Mehr is a collection of [DataObjects](../services/mhr-store) — HTML, CSS, JavaScript, images — stored in MHR-Store and addressed by content hash or human-readable [MHR-Name](../services/mhr-name).

### Static Site

```
Site structure:
  root = DataObject {
      hash: Blake3("index.html contents"),
      content_type: Immutable,
      payload: Inline("<html>...links to sub-objects...</html>"),
      replication: Network(5),    // 5 copies across the network
  }

  Sub-objects:
    style.css  → DataObject { hash: ..., replication: Network(5) }
    logo.png   → DataObject { hash: ..., replication: Network(3) }
    about.html → DataObject { hash: ..., replication: Network(5) }
```

A visitor retrieves the root DataObject by name (`mysite@portland-mesh`) or by hash. The root object links to sub-objects by their content hashes. The visitor's node fetches each sub-object from the nearest replica in the mesh.

### How Visitors Access Your Site

```
Access flow:
  1. Visitor queries MHR-Name: "mysite@portland-mesh"
  2. Name resolves to root DataObject hash
  3. Visitor's node fetches root from nearest MHR-Store replica
  4. Root contains hashes of sub-objects (CSS, images, etc.)
  5. Visitor's node fetches sub-objects (in parallel, from different replicas)
  6. Local browser or app renders the content
```

Content-addressed storage means:
- **No single server** — content is served from whichever node has a copy
- **No downtime** — as long as any replica is reachable, the site is available
- **No tampering** — content hash guarantees integrity
- **Global CDN by default** — popular content gets cached everywhere automatically

### Updating Your Site

For static content, publish new DataObjects and update the MHR-Name binding to point to the new root hash. Old content remains available at its hash (immutable), but the name now resolves to the new version.

For dynamic content (blog, profile, etc.), use **mutable DataObjects**:

```
Blog post feed:
  feed = DataObject {
      content_type: Mutable,
      owner: your_node_id,
      payload: Inline([post_id_1, post_id_2, ...]),
      // Owner can update the post list by publishing a new version
      // Each individual post is immutable — only the feed index changes
  }
```

## Hosting a Social Feed

A social feed is an append-only log of posts, served via [MHR-Pub](../services/mhr-pub):

```
Your feed:
  1. Profile: Mutable DataObject (name, bio, avatar hash)
  2. Posts: Mutable DataObjects (editable, versioned via sequence number)
  3. Feed index: Mutable DataObject listing post IDs in order
  4. Subscriber notifications via MHR-Pub
```

### Publishing a Post

```
Publishing flow:
  1. Create a mutable DataObject for the post content (keyed by post_id)
  2. Store it in MHR-Store with replication
  3. Update your feed index (mutable) to include the new post_id
  4. MHR-Pub notifies all subscribers of the update
```

### Following Someone

```
Following flow:
  1. Subscribe to their feed via MHR-Pub (topic: Node(their_node_id))
  2. Choose delivery mode based on your link quality:
     - WiFi: Push (full content immediately)
     - Moderate: Digest (batched summaries)
     - LoRa: PullHint (hash-only, pull content when convenient)
  3. Your device assembles your timeline locally from all followed feeds
```

No server assembles your feed. No algorithm decides what you see. Your device pulls from the people you follow, in chronological order.

## Cost of Hosting

| What | Cost | Notes |
|------|------|-------|
| Store a 10 KB page | ~50 μMHR/month | With 5 replicas |
| Store a 1 MB image | ~5,000 μMHR/month | With 3 replicas |
| MHR-Name registration | Free | First-seen-wins within your community label |
| Bandwidth when someone views your page | Paid by the viewer | You don't pay for serving — viewers pay relay costs |

The key economic difference from traditional hosting: **you pay for storage, not for traffic.** The viewer pays the relay cost to reach your content. Popular content is cheaper to host because it gets widely cached.

## Comparison with Traditional Hosting

| Aspect | Traditional Web | Mehr Hosting |
|--------|----------------|---------------|
| **Server** | Required (or hosting provider) | None — content lives in the mesh |
| **Domain name** | Rent from registrar ($10-50/year) | MHR-Name (free, self-registered) |
| **SSL certificate** | Required (free via Let's Encrypt, or paid) | Not needed — all links encrypted, content verified by hash |
| **Uptime** | Depends on your server/provider | Depends on replica count — more replicas = higher availability |
| **Bandwidth costs** | You pay for traffic spikes | Viewers pay their own relay costs |
| **Censorship resistance** | Server can be seized, domain can be seized | No single point to seize — content is replicated across the mesh |
| **Offline access** | Not possible | Cached content available even when original author is offline |

## Hosting a Community Forum

A forum is a more complex application, but the primitives are the same:

```
Forum structure:
  Forum config: Mutable DataObject (rules, moderator keys)
  Topic list: Mutable DataObject (list of topic hashes)
  Each topic: Mutable DataObject (list of post hashes)
  Each post: Immutable DataObject (content + author signature)
  Moderation: MHR-Compute contract enforcing community rules
```

New posts are published as DataObjects, appended to the topic log, and propagated via neighborhood-scoped MHR-Pub to all subscribers. Moderation rules are enforced by an MHR-Compute contract — see [Community Apps](community-apps) for details.

## Running a Service

Beyond static hosting, you can run persistent services on the network:

- **API endpoint**: An MHR-Compute contract that responds to requests
- **Bot/automation**: A node running custom logic, discoverable via the capability marketplace
- **Proxy service**: Bridge Mehr to the traditional web (serve Mehr content via HTTP, or fetch web content for mesh users)

Services are advertised as capabilities and discovered through the [marketplace](../marketplace/overview). Consumers find your service, form agreements, and pay via payment channels — all handled by the protocol.

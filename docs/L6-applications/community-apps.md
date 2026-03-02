---
sidebar_position: 5
title: Forums, Marketplace & Wiki
description: "Community applications — forums, marketplaces, and wikis — built on MHR-Compute contracts with CRDT state."
keywords:
  - forums
  - marketplace
  - wiki
  - community
  - CRDT
  - moderation
---

# Community Applications

Community applications — forums, marketplaces, and wikis — are built on [MHR-Compute](/docs/L5-services/mhr-compute) contracts managing CRDT state. All degrade gracefully to text-only on constrained links.

:::info[App Manifest]
Community apps are packaged as **Full** (UI + compute) [AppManifests](/docs/L5-services/mhr-app). Each variant (forum, marketplace, wiki) bundles MHR-Compute moderation and escrow contracts, MHR-Store for posts, listings, or wiki pages as CRDT DataObjects, MHR-Pub for neighborhood-scoped notifications, and MHR-DHT for local search indexing. The state schema defines CRDT merge rules per content type — append-only logs for forums, mutable registers for listings, and operational-transform text for wikis.
:::

## Forums

Forums are append-only logs managed by moderation contracts:

- **Posts** are immutable DataObjects, appended to a topic log
- **Moderation** is handled by an MHR-Compute contract that enforces community rules
- **Threading** is local — each client assembles thread views from the flat log
- **Propagation** uses neighborhood-scoped gossip for local forums, or wider replication for public forums

### Moderation Model

The moderation contract defines:
- Who can post (trusted peers, vouched users, anyone)
- Content rules (enforced at the contract level)
- Moderator keys (who can remove content)
- Appeal mechanisms

Since moderation is a contract, different forums can have different moderation policies. There is no platform-wide content policy.

## Marketplace

Marketplace listings are DataObjects with neighborhood-scoped propagation:

- **Listings** are mutable DataObjects (sellers can update price, availability)
- **Search** is local — each node indexes listings it has received
- **Transactions** happen off-protocol (physical exchange, external payment) or through MHR escrow contracts
- **Reputation** feeds back into the node's general [reputation score](/docs/L2-security/security#sybil-resistance)

### Escrow

For MHR-denominated transactions, an escrow contract can hold payment:

1. Buyer deposits MHR into escrow contract
2. Seller delivers goods/services
3. Buyer confirms delivery
4. Contract releases payment to seller
5. Disputes resolved by community moderators (trusted peers with moderator keys)

## Wiki

Wikis are CRDT-merged collaborative documents:

- **Pages** are mutable DataObjects using CRDT merge rules
- **Concurrent edits** merge automatically without conflicts (using operational transforms or CRDT text types)
- **History** is preserved as a chain of immutable snapshots
- **Permissions** managed by an MHR-Compute contract (who can edit, who can view)

## Bandwidth Degradation

All community applications degrade to text-only on constrained links:

| Application | Full Experience | LoRa Experience |
|------------|----------------|-----------------|
| Forums | Rich text, images, threads | Text posts, flat view |
| Marketplace | Photos, maps, categories | Text listings |
| Wiki | Formatted text, images, tables | Plain text |

The application layer handles this adaptation using `query_link_quality()` — the protocol doesn't need to know about the application's content format.

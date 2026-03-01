---
sidebar_position: 4
title: Trust & Neighborhoods
description: "Emergent communities formed from trust graphs where nodes set per-peer relay costs and define hierarchical scopes."
keywords:
  - trust
  - neighborhoods
  - community
  - trust graph
  - scopes
  - peer relationships
---

# Trust & Neighborhoods

Communities in Mehr are **emergent, not declared**. There are no admin-created "zones" to join, no governance to negotiate, no artificial boundaries between groups. Instead, communities form naturally from a trust graph — just like in the real world.

## The Trust Graph

Each node maintains a set of trusted peers:

:::info[Specification]
`TrustConfig` is the core social primitive: trusted peers get free relay, non-trusted traffic is priced per-byte, and transitive credit extends to friends-of-friends at a configurable ratio (default 10%, max 50%). Scopes are self-assigned hierarchical namespaces (max 1 Geo + 3 Topic, ≤ 1 KB total).
:::

```
TrustConfig {
    // Peers I trust — relay their traffic for free
    trusted_peers: Set<NodeID>,

    // What I charge non-trusted traffic
    default_cost_per_byte: u64,

    // Per-peer cost overrides (discount for friends-of-friends, etc.)
    cost_overrides: Map<NodeID, u64>,

    // Transitive credit ratio for friends-of-friends (default 0.10)
    transitive_credit_ratio: f32,           // range [0.0, 0.50], default 0.10
    transitive_ratio_overrides: Map<NodeID, f32>,  // per-peer override

    // Self-assigned scopes — geographic and interest (purely informational)
    scopes: Vec<HierarchicalScope>,     // max 1 Geo + up to 3 Topic; total ≤ 1 KB

    // DEPRECATED: use scopes instead. Kept for backward compatibility.
    community_label: Option<String>,    // e.g., "portland-mesh"
}
```

**Adding a trusted peer is the only social action in Mehr.** Everything else — free local communication, community identity, credit lines — emerges from the trust graph.

Trust relationships are **asymmetric and revocable at any time**. Removing a node from `trusted_peers` immediately ends free relay for that node and downgrades any stored data from "trusted peer" to normal priority in the [garbage collection policy](../services/mhr-store#garbage-collection). Cost overrides are unidirectional — they apply to outbound traffic pricing from the configuring node only.

## How Communities Emerge

When a cluster of nodes all trust each other, a **neighborhood** forms:

```mermaid
graph LR
    Alice["Alice"] <-->|trust| Bob["Bob"]
    Bob <-->|trust| Carol["Carol"]
    Alice <-->|trust| Dave["Dave"]
    Bob <-->|trust| Dave
    Carol <-->|trust| Dave
```

Alice, Bob, Carol, and Dave are a neighborhood. No one "created" it. No one "joined" it. It exists because they trust each other.

### Properties

- **No admin**: Nobody runs the neighborhood. It has no keys, no governance, no admission policy.
- **No fragmentation**: The trust graph is continuous. There are no hard boundaries between communities — neighborhoods overlap naturally when people have friends in multiple clusters.
- **No UX burden**: You just mark people as trusted. The same action you'd take when adding a contact.
- **Fully decentralized**: There is nothing to attack, take over, or censor.

## Free Local Communication

Traffic between trusted peers is **always free**. A relay node checks its trust list:

```
Relay decision:
  if sender is trusted AND destination is trusted:
    relay for free (no lottery, no channel update)
  else if sender is trusted:
    relay for free (helping a friend send outbound)
  else:
    relay with stochastic reward lottery
```

Note the asymmetry: a relay helps its trusted peers **send** traffic for free, but does not relay free traffic from strangers just because the destination is trusted. Without this rule, an untrusted node could route unlimited free traffic through you to any of your trusted peers, shifting relay costs onto you without compensation.

This means a village mesh where everyone trusts each other operates with **zero economic overhead** — no tokens, no channels, no settlements. The economic layer only activates for traffic crossing trust boundaries.

## Trust-Based Credit

When a node needs MHR (e.g., to reach beyond its trusted neighborhood), its trusted peers can vouch for it:

```
Transitive credit:
  Direct trust:           full credit line (set by trusting peer)
  Friend-of-friend (2 hops): configurable ratio of direct credit line (default 10%, max 50%)
  3+ hops of trust:        no credit (too diluted)

  If a credited node defaults, the vouching peer absorbs the debt.
  This makes trust economically meaningful — you only trust people
  you'd lend to.
```
:::tip[Key Insight]
Trust in Mehr has real economic cost: vouching for a peer means absorbing their potential debts. This makes the trust graph a natural Sybil defense — creating fake identities is free, but getting anyone to trust (and financially back) them is not.
:::
The credit line is **rate-limited** for safety:

| Trust Distance | Max Credit | Rate Limit |
|---------------|-----------|-----------|
| Direct trusted peer | Configurable by trusting node | Per-epoch (configurable) |
| Friend-of-friend | Configurable % of direct limit (default 10%, max 50%) | Per-epoch, per friend-of-friend |
| Beyond 2 hops | None | N/A |

```
Credit accounting:
  Each trusting node tracks outstanding credit per grantee:

  CreditState {
      grantee: NodeID,
      credit_limit: u64,              // max outstanding μMHR
      outstanding: u64,               // currently extended
      granted_this_epoch: u64,        // epoch-scoped rate limit
      last_grant_epoch: u64,          // for epoch-boundary reset
  }

  Rules:
    - Direct peers: each gets a separate credit_limit (set in TrustConfig)
    - Friend-of-friend: each gets transitive_credit_ratio × vouching peer's direct limit,
      tracked independently per grantee
    - granted_this_epoch resets to 0 at each epoch boundary
    - Outstanding credit that exceeds limit: no new grants until repaid
    - Default handling: vouching peer's outstanding balance increases by
      the defaulted amount (absorbs debt); grantee is flagged
```

## Hierarchical Scopes

Nodes self-assign **scopes** — hierarchical namespaces that describe where they are and what they care about. Scopes replace the flat `community_label` with a structured system that supports both place-based communities and interest communities.

```
HierarchicalScope {
    scope_type: enum {
        Geo,    // place hierarchy (physical or virtual)
        Topic,  // interest/community hierarchy
    },
    segments: Vec<String>,    // hierarchical path, max 8 levels, max 32 chars each
}

Scope constraints:
  Per node (TrustConfig):    max 1 Geo + up to 3 Topic (4 total)
  Per content (PostEnvelope): max 1 Geo + up to 3 Topic (4 total)
  Total scope bytes:          ≤ 1,024 bytes (UI shows remaining space)

Rationale:
  - You are physically in one place at a time
  - Voting is geo-scoped — multiple geo scopes would enable double-voting
  - RadioRangeProof verifies one location
  - Interests are multi-dimensional — multiple topics are natural
  - Hierarchical prefix matching means a single deep tag covers multiple query levels
  - 3 topics is expressive enough: most users have 1-2 primary interests
  - 1 KB cap keeps scope data small for constrained devices (ESP32)
```

Scopes are **hierarchical namespaces**, similar to URLs. The `segments` are arbitrary strings — they can describe physical locations, virtual spaces, organizations, or anything else. The `scope_type` signals **propagation intent**, not physicality: `Geo` means "this is a place where members are dense and nearby each other" (whether physically or virtually), while `Topic` means "this is an interest that spans across places."

### Geo Scopes

Geo scopes describe **places** — physical locations, virtual spaces, or any community with dense, place-like membership:

```
Geo scope examples:

  Physical locations:                    Virtual places:

  north-america                          cyberspace
  └── us                                 └── guild-wars
      ├── oregon                         │   ├── server-42
      │   ├── portland                   │   └── server-7
      │   │   ├── hawthorne ◀── Alice    │
      │   │   └── pearl     ◀── Bob     └── discord
      │   ├── eugene                         └── mehr-dev ◀── Dave
      │   └── bend
      └── california                     organizations
          └── ...                        └── university
                                             └── mit
  asia                                       └── csail ◀── Eve
  └── iran
      └── tehran
          └── district-6   ◀── Carol
```

```
Physical:  Geo("north-america", "us", "oregon", "portland", "hawthorne")
Virtual:   Geo("cyberspace", "guild-wars", "server-42")
Org:       Geo("organizations", "university", "mit", "csail")
```

The hierarchy is **bottom-up** — neighbors form the base, cities emerge from connected neighborhoods, regions from connected cities. This applies equally to physical and virtual places: you join a game server first, then discover the broader game community, then the gaming umbrella. The pattern is the same — local connections aggregate into larger structures.

### Interest Scopes

Interest scopes describe communities of shared interest that span geography:

```
Dave sets:   Topic("gaming", "pokemon", "competitive")
Eve sets:    Topic("science", "physics", "quantum")
Frank sets:  Topic("music", "jazz")
```

Interest communities are **sparse** — not everyone in Portland cares about Pokemon. A Pokemon community might span Portland, Tokyo, and Berlin with nothing in between. This is the opposite of geographic scopes, which are **dense** (most people are physically somewhere).

### Scope Matching

Subscriptions and queries can match at any level of the hierarchy:

| Pattern | Matches |
|---------|---------|
| `Geo("north-america", "us", "oregon", "portland")` exact | Only Portland |
| `Geo("north-america", "us", "oregon")` prefix | Portland, Eugene, Bend, and everything in Oregon |
| `Geo("north-america", "us")` prefix | All US scopes |
| `Topic("gaming")` prefix | Pokemon, Minecraft, and all gaming sub-topics |
| `Topic("gaming", "pokemon")` exact | Only Pokemon, not gaming broadly |

### Properties

Scopes retain all the properties of `community_label`:

- **Self-assigned** — no one approves your scope claims, no authority enforces them
- **Not authoritative** — scopes carry no protocol-level privileges (cannot grant access, waive fees, or modify trust)
- **Not unique** — multiple disjoint clusters can use the same scope
- **Free-form strings** — all segments are arbitrary strings. Communities converge on naming through social consensus (e.g., "portland" not "pdx"), the same way they do today. No ISO codes, no standardized taxonomy, no gatekeeping.
- **Used by services** — [MHR-Name](../services/mhr-name) scopes names by geographic scope, [MHR-Pub](../services/mhr-pub) supports `Scope(match)` subscriptions, [MHR-DHT](../services/mhr-dht#neighborhood-scoped-dht) uses scopes for content propagation boundaries, and the [Social](../applications/social) layer uses scopes for geographic and interest feeds

### Geo Scope Verification

Geo scopes can optionally be **verified** — see [MHR-ID](../services/mhr-id) for the full verification protocol. Verification methods vary by the kind of place:

| Place Type | Verification Method | Precision |
|-----------|-------------------|-----------|
| **Physical neighborhood** | [RadioRangeProof](../services/mhr-id/verification#radiorangeproof) — if you can hear a node's LoRa beacon, you're within physical range | ~1–15 km |
| **Physical city/region** | Bottom-up aggregation of verified neighborhood claims | Aggregated |
| **Virtual space** | Application-specific (e.g., server-signed attestation, invite-chain, admin vouch) | Varies |
| **Organization** | Peer attestation from existing verified members | Social |

Interest scopes are **never verified** — anyone can declare interest in Pokemon. Verification matters for geo scopes that carry governance weight (see [Voting](../applications/voting)) — a node cannot vote on Portland issues without a verified Portland-area presence claim. Unverified geo scopes are still useful for content routing and feed subscriptions; they just don't carry voting rights.

### Wire Format

Designed for constrained devices:

| Field | Size | Description |
|-------|------|-------------|
| `scope_type` | 1 byte | 0 = Geo, 1 = Topic |
| `segment_count` | 1 byte | Number of path segments (max 8) |
| `segments` | variable | Length-prefixed UTF-8 (1-byte length + content per segment) |

Maximum size per scope: 2 + 8 × 33 = 266 bytes. Total scope data is capped at **1,024 bytes** (1 KB). With max 4 scopes (1 Geo + 3 Topic), typical usage is well under the cap — e.g., `Geo("us", "oregon", "portland")` (15 bytes) + `Topic("gaming", "pokemon")` (18 bytes) + `Topic("music", "jazz")` (16 bytes) = 49 bytes. The cap only binds when using deep hierarchies (8 segments × 32 chars) across multiple scopes.

### Backward Compatibility

The `community_label` field is retained for backward compatibility. New nodes populate both:

```
Migration:
  community_label: "portland-mesh"
    → scopes: [Geo("portland")]

  Old nodes: read community_label, ignore scopes
  New nodes: read scopes, fall back to community_label if scopes is empty
```

### Geo vs. Topic: Two Dimensions of Community

| | Geo Scopes (Places) | Topic Scopes (Interests) |
|---|---|---|
| **Density** | Dense — members are nearby each other | Sparse — members are scattered |
| **Propagation** | Bottom-up through proximity | Wide, across places |
| **Verification** | RadioRangeProof (physical), attestation (virtual), or none | None needed (self-declared) |
| **Content cost** | Cheap locally, expensive globally | Depends on relay distance |
| **Voting** | Enables scoped voting (if verified) | No voting implications |
| **Physical examples** | `Geo("north-america", "us", "oregon", "portland")` | `Topic("gaming", "pokemon")` |
| **Virtual examples** | `Geo("cyberspace", "guild-wars", "server-42")` | `Topic("science", "physics")` |
| **Multiplicity** | One per node/content | Up to 3 (within 1 KB total) |

A single post can have **one** geographic scope and **multiple** interest scopes. A post tagged `Geo("portland") + Topic("gaming", "pokemon")` appears in both the Portland local feed and the global Pokemon feed. Intersection queries ("Portland Pokemon") are resolved client-side by filtering on both scopes.

## Comparison: Explicit Zones vs. Trust Neighborhoods

| Aspect | Explicit Zones | Trust Neighborhoods |
|--------|---------------|---------------------|
| Creation | Someone creates a zone | Emerges from mutual trust |
| Joining | Request + approval | Mark someone as trusted |
| Governance | Admin keys, voting | None needed |
| Boundaries | Hard, declared | Soft, overlapping |
| Free communication | Within zone boundary | Between any trusted peers |
| Naming | `alice@zone-name` | `alice@geo:portland` (hierarchical scopes) |
| Sybil resistance | Admission policy | Trust is social and economic (you absorb their debts) |
| UX complexity | Create, join, configure | Add contacts |

## Sybil Mitigation

The trust graph provides natural Sybil resistance:

1. **Trust has economic cost**: Vouching for a node means absorbing its potential debts. Sybil identities with no real relationships get no credit.
2. **Rate limiting**: Even if a malicious node gains one trust relationship, transitive credit is capped by configurable ratio (default 10%, max 50%) per hop.
3. **Reputation**: A node's usefulness as a relay/service provider is what earns trust over time. Creating many identities dilutes reputation rather than concentrating it.
4. **Local detection**: A node's trust graph is visible to its peers. A node trusting an unusual number of new, unproven identities is itself suspicious.

## Real-World Parallels

| Real World | Mehr Trust |
|-----------|------------|
| Talk to your neighbor for free | Free relay between trusted peers |
| Lend money to a friend | Transitive credit via trust |
| Wouldn't lend to a stranger | No credit without trust chain |
| Communities aren't corporations | Neighborhoods have no admin |
| You belong to multiple groups | Trust graph is continuous, not partitioned |
| Reputation builds over time | Trust earned through reliable service |

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>How do communities actually form if there’s no “create community” button?</summary>

You simply mark other people as trusted peers in your node’s configuration. When a cluster of people mutually trust each other, a neighborhood emerges organically — no one needs to create, name, or administrate it. It’s the same way friend groups form in real life: you start trusting individuals, and the group structure follows.

</details>

<details className="faq-item">
<summary>What if I’m new and don’t trust anyone yet?</summary>

You can still participate — you’ll just pay standard relay fees in MHR for traffic that crosses trust boundaries. As you interact with neighbors and build relationships, you’ll naturally add trusted peers. Gateway operators can also onboard new users by adding them as trusted peers, giving immediate free access within the gateway’s neighborhood.

</details>

<details className="faq-item">
<summary>Can I revoke trust once I’ve granted it?</summary>

Yes, instantly. Removing a node from your `trusted_peers` list takes effect immediately. That node loses free relay through you, and any stored data from them drops to normal priority in garbage collection. Trust is asymmetric and unilateral — you control your own trust list without needing the other party’s permission.

</details>

<details className="faq-item">
<summary>Are my trust relationships visible to everyone on the network?</summary>

Your trust graph is visible to your direct peers (they can see who you relay for free), but it is not broadcast globally. Neighbors observe trust relationships through relay behavior — if you relay someone’s traffic for free, nearby nodes can infer a trust link. There is no public trust directory that lists all relationships.

</details>

<!-- faq-end -->

---
sidebar_position: 4
title: Trust & Neighborhoods
---

# Trust & Neighborhoods

Communities in NEXUS are **emergent, not declared**. There are no admin-created "zones" to join, no governance to negotiate, no artificial boundaries between groups. Instead, communities form naturally from a trust graph — just like in the real world.

## The Trust Graph

Each node maintains a set of trusted peers:

```
TrustConfig {
    // Peers I trust — relay their traffic for free
    trusted_peers: Set<NodeID>,

    // What I charge non-trusted traffic
    default_cost_per_byte: u64,

    // Per-peer cost overrides (discount for friends-of-friends, etc.)
    cost_overrides: Map<NodeID, u64>,

    // Optional self-assigned label (purely informational)
    community_label: Option<String>,    // e.g., "portland-mesh"
}
```

**Adding a trusted peer is the only social action in NEXUS.** Everything else — free local communication, community identity, credit lines — emerges from the trust graph.

## How Communities Emerge

When a cluster of nodes all trust each other, a **neighborhood** forms:

```
  [Alice] ←──trust──→ [Bob] ←──trust──→ [Carol]
     │                  │                   │
     └────trust────→ [Dave] ←───trust──────┘
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
  if sender is trusted OR destination is trusted:
    relay for free (no lottery, no channel update)
  else:
    relay with stochastic reward lottery
```

This means a village mesh where everyone trusts each other operates with **zero economic overhead** — no tokens, no channels, no settlements. The economic layer only activates for traffic crossing trust boundaries.

## Trust-Based Credit

When a node needs NXS (e.g., to reach beyond its trusted neighborhood), its trusted peers can vouch for it:

```
Transitive credit:
  Direct trust:           full credit line (set by trusting peer)
  Friend-of-friend (2 hops): 10% of direct credit line
  3+ hops of trust:        no credit (too diluted)

  If a credited node defaults, the vouching peer absorbs the debt.
  This makes trust economically meaningful — you only trust people
  you'd lend to.
```

The credit line is **rate-limited** for safety:

| Trust Distance | Max Credit Rate |
|---------------|----------------|
| Direct trusted peer | Configurable by trusting node |
| Friend-of-friend | 10% of direct limit |
| Beyond 2 hops | No transitive credit |

## Community Labels

Nodes can optionally self-assign a `community_label` string:

```
Alice sets:  community_label = "portland-mesh"
Bob sets:    community_label = "portland-mesh"
Carol sets:  community_label = "portland-mesh"
```

This label is:
- **Purely informational** — it has no protocol-level authority
- **Self-assigned** — no one approves it
- **Not unique** — multiple disjoint clusters can use the same label
- **Useful for discovery** — "find nodes labeled 'portland-mesh' near me"
- **Useful for naming** — `alice@portland-mesh` resolves to the nearest cluster with that label

Community labels enable human-readable naming and discovery without any of the governance overhead of explicit zones.

## Comparison: Zones vs. Trust Neighborhoods

| Aspect | Explicit Zones (old) | Trust Neighborhoods (current) |
|--------|---------------------|-------------------------------|
| Creation | Someone creates a zone | Emerges from mutual trust |
| Joining | Request + approval | Mark someone as trusted |
| Governance | Admin keys, voting | None needed |
| Boundaries | Hard, declared | Soft, overlapping |
| Free communication | Within zone boundary | Between any trusted peers |
| Naming | `alice@zone-name` | `alice@community-label` |
| Sybil resistance | Admission policy | Trust is social and economic (you absorb their debts) |
| UX complexity | Create, join, configure | Add contacts |

## Sybil Mitigation

The trust graph provides natural Sybil resistance:

1. **Trust has economic cost**: Vouching for a node means absorbing its potential debts. Sybil identities with no real relationships get no credit.
2. **Rate limiting**: Even if a malicious node gains one trust relationship, transitive credit is capped at 10% per hop.
3. **Reputation**: A node's usefulness as a relay/service provider is what earns trust over time. Creating many identities dilutes reputation rather than concentrating it.
4. **Local detection**: A node's trust graph is visible to its peers. A node trusting an unusual number of new, unproven identities is itself suspicious.

## Real-World Parallels

| Real World | NEXUS Trust |
|-----------|------------|
| Talk to your neighbor for free | Free relay between trusted peers |
| Lend money to a friend | Transitive credit via trust |
| Wouldn't lend to a stranger | No credit without trust chain |
| Communities aren't corporations | Neighborhoods have no admin |
| You belong to multiple groups | Trust graph is continuous, not partitioned |
| Reputation builds over time | Trust earned through reliable service |

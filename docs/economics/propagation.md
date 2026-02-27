---
sidebar_position: 6
title: Content Propagation
---

# Content Propagation

Content on Mehr doesn't spread uniformly — it follows economic gravity. Local content is cheap and fast. Global content costs more but reaches more people. Popular content funds its own propagation. Unpopular content stays local or expires. No algorithm decides what lives and what dies — economics does.

## Geographic Propagation

Geographic content follows a **bottom-up, demand-driven** model. Content starts local and bubbles upward as demand increases.

### Cost by Scope Level

| Scope Level | Relay Cost | Cache Density | Typical Latency |
|-------------|-----------|---------------|----------------|
| Neighborhood | ~free (trusted peers) | Very high | Seconds |
| City | Low (short paths, many caches) | High | Seconds to minutes |
| Region | Moderate | Moderate | Minutes |
| Country | Higher | Sparse | Minutes to hours |
| Continent/Global | Highest | Very sparse | Hours (LoRa) to minutes (internet gateway) |

The cost gradient is **natural** — it costs more relay hops to reach distant nodes, so the price is higher. There is no artificial pricing; relay fees accumulate per hop.

### Upward Propagation

Content climbs the scope hierarchy through three mechanisms:

**1. Demand-driven caching**: When readers at a broader scope request content, intermediate nodes cache it. A Portland post requested by 10 Oregon readers gets cached at relay nodes between Portland and the rest of Oregon. Those caches then serve future Oregon requests cheaply.

```
Portland post → requested by Eugene reader
  → relay nodes between Portland and Eugene cache the post
  → next Eugene reader gets it from the cache (cheaper, faster)
  → after N requests, the post is effectively "Oregon-scoped"
```

**2. Speculative caching**: Storage nodes observe demand signals (retrieval frequency) and speculatively cache popular content. A storage node in Seattle might cache a popular Portland post because serving it to Seattle readers is profitable.

```
Storage node decision:
  observed_demand = retrievals_per_epoch for this content
  hosting_cost = storage_cost_per_epoch
  expected_revenue = observed_demand × average_retrieval_fee × (255 - kickback_rate) / 255

  if expected_revenue > hosting_cost:
    cache the content (profitable to serve)
```

**3. Author-funded promotion**: An author can explicitly pay for wider scope by creating storage agreements with providers in broader geographic areas. This is the equivalent of "promoting" a post — paying for reach.

### The Self-Funding Loop

When a post earns more in [kickback](../services/mhr-store#revenue-sharing-kickback) than it costs to store, it becomes **self-sustaining**:

```mermaid
graph TD
    A[Author pays initial cost] --> B[Storage - N epochs]
    B --> C[Readers pay to access]
    C --> D[Kickback to author]
    D --> E[Reinvest]
    E --> F[Extend storage / wider scope]
    F --> B
```

```
Self-funding threshold:
  kickback_per_epoch > cost_per_epoch → content is immortal
  kickback_per_epoch < cost_per_epoch → author subsidizes or content expires
```

**Popular content climbs automatically:**

| Phase | Scope | Funding |
|-------|-------|---------|
| 1. Published | Neighborhood | Author pays |
| 2. Local hit | City | Kickback covers neighborhood; surplus pays for city scope |
| 3. Regional hit | Region | City kickback funds regional storage |
| 4. Viral | Country/Global | Self-funding at all levels; may exceed author's cost |

**Unpopular content follows the opposite trajectory:** kickback doesn't cover costs, author stops paying, storage agreements expire, content is garbage-collected. No moderation needed — economics handles content lifecycle.

## Interest Propagation

Interest communities are **sparse** — they span geography. A `Topic("gaming", "pokemon")` post from Portland might interest readers in Tokyo, Berlin, and Buenos Aires, with nothing in between.

```mermaid
graph TD
    subgraph Geographic["Geographic (dense, local-first)"]
        direction BT
        G_Author[Author] --> G_Nbhd1[Nbhd]
        G_Nbhd1 --> G_City1[City]
        G_Nbhd2[Nbhd] --> G_City1
        G_City1 --> G_Region1[Region]
        G_City2[City] --> G_Region1
        G_City3[City] --> G_Region2[Region]
        G_Region1 --> G_Country[Country]
        G_Region2 --> G_Country
    end

    subgraph Interest["Interest (sparse, validated-then-global)"]
        direction BT
        I_Author[Author] --> I_Validation[Local validation]
        I_Validation --> I_Relay1[Interest relay node]
        I_Validation --> I_Relay2[Interest relay node]
        I_Validation --> I_Relay3[Interest relay node]
        I_Relay1 --> I_Portland[Portland]
        I_Relay2 --> I_Tokyo[Tokyo]
        I_Relay3 --> I_Berlin[Berlin]
    end
```

> **Geographic** bubbles UP with demand. **Interest** spreads OUT after local validation.

### Interest Relay Nodes

Interest communities naturally develop **interest relay nodes** — nodes that subscribe to a topic and bridge between geographic clusters:

```
Portland ──LoRa──▶ [Portland Pokemon fan] ──internet gateway──▶ [Tokyo Pokemon fan] ──LoRa──▶ Tokyo mesh
                   (interest relay)                              (interest relay)
```

Interest relay nodes earn relay fees for bridging communities. They subscribe to a topic via [MHR-Pub Scope subscriptions](../services/mhr-pub#interest-feeds) and forward content to other interested nodes.

### Local-First Interest Propagation

Interest content follows the same demand-driven model as geographic content — **start local, propagate outward only when validated**. An envelope tagged `Topic("gaming", "pokemon")` does not immediately reach every Pokemon subscriber worldwide. Instead:

```
Interest propagation stages:

  1. PUBLISH: Envelope propagates to the author's local geographic cluster
     (same as any post — reaches nearby nodes first)

  2. LOCAL VALIDATION: Interest relay nodes in the author's cluster observe:
     - Did anyone in my cluster boost this envelope?
     - Did N distinct nodes fetch the full post? (default N = 3)
     - Did a curator include it in a feed?
     If none of these: envelope stays local.

  3. OUTBOUND: Once locally validated, interest relay nodes forward the
     envelope to peer interest relay nodes in other geographic clusters.

  4. REMOTE CLUSTERS: Each receiving cluster applies the same validation
     before forwarding further. Content spreads through the interest graph
     one cluster at a time, gated by local traction at each hop.
```

**Why this matters**: Without local validation, a garbage post tagged with a popular topic would reach every subscriber globally — the envelope is free, so there's no economic brake. Local-first propagation ensures that only content validated by the author's community reaches distant clusters. The author's neighbors are the first quality gate.

**Validation thresholds** (configurable per interest relay node):

| Signal | Default Threshold | Rationale |
|--------|------------------|-----------|
| Boost from trusted node | 1 boost | Someone in the local cluster endorsed it |
| Full post retrievals | 3 distinct nodes | Multiple people found it worth paying for |
| Curator inclusion | 1 curator | A human with reputation selected it |

An interest relay node can set its own thresholds — a high-traffic relay might require more validation before forwarding, while a small community relay might forward after a single boost. The thresholds are a local policy, not a protocol constant.

### Interest vs. Geographic Cost

| | Geographic | Interest |
|---|---|---|
| **Propagation pattern** | Dense, local-first | Sparse, local-first then global |
| **Cost driver** | Relay distance (hops) | Relay distance (may cross continents) |
| **Caching** | Many nearby caches (dense) | Few caches, widely spaced (sparse) |
| **Self-funding** | Easy (many local readers) | Harder (fewer readers, higher relay costs) |
| **Typical delivery** | Push/Digest (short paths) | Digest/PullHint (long paths, constrained links) |
| **Quality gate** | Retrieval demand drives scope promotion | Local validation gates outbound relay |

Interest content is generally more expensive to propagate because it crosses more trust boundaries and relay hops. But interest communities can compensate by having dedicated relay infrastructure — nodes that specialize in bridging a specific topic.

## Intersection: Geographic + Interest

A post tagged with both geographic and interest scopes propagates through **both** channels:

```
Post: "Pokemon tournament in Portland this Saturday"
Scopes: Geo("north-america", "us", "oregon", "portland") + Topic("gaming", "pokemon")

Propagation:
  Geographic: Portland neighborhood → Portland city (high priority, local event)
  Interest: Portland → global Pokemon community (relevant to traveling players)

Readers see it via:
  Portland feed subscribers (geographic)
  Pokemon feed subscribers (interest)
  Portland Pokemon intersection (both)
```

The economics naturally prioritize the right audience: local Portland readers get it cheaply (geographic proximity), global Pokemon fans get it at higher cost (interest relay), and Portland Pokemon fans get it through whichever channel is cheaper.

## Content Lifecycle

Every piece of content on Mehr follows an economic lifecycle. Content is born local and either grows through demand or expires through indifference:

```mermaid
graph LR
    Birth["BIRTH\nAuthor pays\nNeighborhood scope"] --> Growth["GROWTH\nKickback rises\nCaches multiply"]
    Growth --> Peak["PEAK\nSelf-funding\nWide caching"]
    Peak --> Decline["DECLINE\nDemand drops\nCaches evict"]
    Decline --> Expiry["EXPIRY\nGC'd or\nreduced scope"]
```

```
Phase 1: BIRTH
  Author creates post, pays for initial storage
  Content exists at neighborhood scope

Phase 2: GROWTH (if popular)
  Readers pay to access → kickback accumulates
  Speculative caching expands effective scope
  Storage nodes compete to host (profitable)

Phase 3: PEAK
  Content widely cached, cheaply accessible
  Kickback may exceed storage cost (self-funding)
  Maximum reach for its popularity level

Phase 4: DECLINE
  Readership drops → kickback drops
  Speculative caches evict (no longer profitable)
  Scope contracts back toward origin

Phase 5: EXPIRY (if not self-funding)
  Kickback below storage cost
  Author stops paying → grace period → garbage collection
  Or: remains self-funding indefinitely at reduced scope
```

### Comparison with Other Models

| | Centralized (Twitter) | Polycentric | Mehr |
|---|---|---|---|
| **What lives** | Platform decides | Server operator decides | Economics decides |
| **Content cost** | Free to post | Free to post | Author pays |
| **Popular content** | Algorithmically boosted | Same treatment as unpopular | Self-funds, propagates wider |
| **Unpopular content** | Shadow-banned or deprioritized | Lives until server drops it | Expires when funding stops |
| **Content lifespan** | Platform's discretion | Until all servers remove it | Until demand or author funding stops |
| **Spam** | ML moderation (arms race) | ML moderation | Economically irrational |

## Protocol Constants

| Constant | Value | Description |
|----------|-------|-------------|
| Kickback rate range | 0–255 | Author's share of retrieval fees (rate/255) |
| Default kickback rate | 128 (~50%) | Balanced split for social posts |
| Speculative cache threshold | Configurable | Retrievals/epoch before speculative caching triggers |
| Scope promotion threshold | Configurable | Kickback surplus that triggers scope expansion |

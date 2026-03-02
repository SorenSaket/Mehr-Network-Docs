---
sidebar_position: 7
title: Content Governance
description: "Distributed content governance where every node independently decides what to store, relay, and display — no central authority."
keywords:
  - content governance
  - moderation
  - censorship resistance
  - node sovereignty
  - filtering
---

# Content Governance

Mehr has no content moderation, no terms of service, and no central authority that decides what is allowed. Content governance is distributed: every node makes its own decisions about what to store, relay, and display. Censorship resistance and content governance are the same mechanism — **node sovereignty**.

## Node Autonomy

Every node has absolute control over three decisions:

```mermaid
flowchart TD
    Node["YOUR NODE"]
    Store["1. What to STORE<br/>Refuse any StorageAgreement"]
    Relay["2. What to RELAY<br/>Refuse to forward any envelope"]
    Display["3. What to DISPLAY<br/>Filter, block, hide anything"]
    Local["These are LOCAL decisions.<br/>The protocol does not enforce them network-wide.<br/>No node can override another node's choices."]

    Node --> Store
    Node --> Relay
    Node --> Display
    Store --> Local
    Relay --> Local
    Display --> Local
```

**Storing**: A storage node can refuse any [StorageAgreement](/docs/L5-services/mhr-store#storage-agreements) for any reason. No node is compelled to host content it objects to. The agreement is bilateral — both parties must consent.

**Relaying**: A relay node can inspect [PostEnvelope](/docs/L6-applications/social#postenvelope-free-layer) metadata and refuse to forward specific content. This is a local routing policy, not protocol enforcement. The node still relays other traffic normally.

**Displaying**: Client software can filter, block, or hide content based on any criteria — author blocklists, content-type filters, community norms, or user preferences. This happens entirely on the reader's device.

## Content Filtering

### Envelope-Based Filtering

PostEnvelopes contain metadata that nodes can use for filtering without fetching paid content:

| Envelope Field | Filtering Use |
|---------------|--------------|
| `scopes` | Block specific topics or geographic areas |
| `author` | Block specific authors (local blocklist) |
| `media_hints.content_type` | Block specific media types (e.g., refuse video) |
| `content_size` | Refuse to relay objects above a size threshold |
| `references` | Block content referencing known-bad posts |

A relay node's filtering policy is expressed as local configuration, not as a protocol message. Other nodes don't know what you filter — they only notice that you don't relay certain content.

### Trust-Based Enforcement

The most powerful governance mechanism is the [trust graph](trust-neighborhoods):

```mermaid
flowchart TD
    Discover["1. Alice discovers Bob is<br/>producing objectionable content"]
    Remove["2. Alice removes Bob<br/>from trusted_peers"]

    Discover --> Remove

    Remove --> LoseRelay["Loses free relay"]
    Remove --> LoseStorage["Loses free storage"]
    Remove --> LoseCredit["Credit line drops to zero"]
    Remove --> LoseRep["Trust distance increases"]

    Social["3. Carol and Dave also<br/>remove Bob (social consensus)"]

    LoseRelay --> Social
    LoseStorage --> Social
    LoseCredit --> Social
    LoseRep --> Social

    Social --> Isolated["Isolated from<br/>neighborhood free tier"]
    Social --> Paying["Paying full relay<br/>and storage costs"]
    Social --> NoCredit["Unable to get credit<br/>(no one vouches)"]
    Social --> MarketOnly["Visible only to nodes<br/>willing to serve at market rate"]
```

This mirrors real-world community enforcement. If your neighbors find your behavior unacceptable, they stop helping you. Nobody passes a law — social consequences are sufficient. The economic impact of trust revocation is real: lost credit lines, lost free relay, lost free storage.

### Community Norms

Communities can establish shared content policies through social consensus:

- "Our trust neighborhood doesn't relay content tagged with X"
- "Nodes that relay Y will be removed from trusted peers"
- "Our curators don't include Z in their feeds"

These are enforced through trust relationships, not protocol rules. A node that violates community norms faces trust revocation — which has economic consequences. No formal governance or voting is needed for communities to establish and enforce norms.

:::tip[Key Insight]
Community moderation in Mehr mirrors real-world social enforcement: trust revocation costs the offender free relay, free storage, and credit lines. No formal governance is needed — a cluster of nodes independently removing someone from `trusted_peers` is economically equivalent to community expulsion.
:::

## Why Illicit Content Is Harder on Mehr

| Factor | Regular Internet | Mehr |
|--------|-----------------|------|
| **Cost to publish** | Free (anonymous upload) | Author pays storage per epoch |
| **Author identity** | Anonymous (VPN, Tor, throwaway accounts) | NodeID attached; author known to local cluster |
| **Hosting** | Bulletproof hosting services exist | Every storage node can independently refuse |
| **Distribution** | Global CDN, unlimited free copies | [Local-first propagation](./propagation#local-first-interest-propagation); global reach requires demand or payment |
| **Amplification** | Algorithms promote engagement | No algorithm — only human curators and boosts |
| **Social consequences** | None (anonymous) | Trust revocation, credit loss, neighborhood isolation |
| **Takedown** | Centralized (platform compliance) | Distributed (each node independently decides) |

### What Economics Limits

```
Economic barriers to abuse:

  Spam:
    Cost to post: N μMHR per epoch
    Revenue from spam: ~0 (nobody reads it)
    Result: economically irrational

  Low-demand illicit content:
    Cost to store: N μMHR per epoch (ongoing)
    Readership: small (niche audience)
    Kickback: below self-funding threshold
    Result: author pays indefinitely or content expires

  Automated distribution (bots):
    Bot needs MHR → must earn through service OR purchase
    Each bot post costs storage
    Local-first propagation means no automatic global reach
    Result: expensive and slow compared to internet-scale abuse

  Mass distribution:
    Local validation gates interest propagation
    Content needs real engagement (boosts, retrievals, curation)
    before reaching distant clusters
    Result: garbage can't go viral without genuine demand
```

### Formal Economic Model

**Spam Unprofitability Proof:**

```mermaid
flowchart LR
    Spammer["Spammer sends<br/>N messages"]
    Cost["Cost = N × C_relay<br/>+ N × C_store × T"]
    Revenue["Revenue = N × R_spam"]
    Result["Cost > Revenue<br/>ALWAYS"]

    Spammer --> Cost
    Spammer --> Revenue
    Cost --> Result
    Revenue --> Result
```

```
Spam profitability:
  Cost_spam = N × C_relay + N × C_store × T
  Revenue_spam = N × R_spam

  Profitable only if: R_spam > C_relay + C_store × T

  In Mehr:
    R_spam → 0 (client-side filtering, no algorithmic amplification)
    C_relay > 0 (paid relay for non-trusted traffic)
    C_store > 0 (ongoing per-epoch storage cost)

  Therefore: Cost > Revenue always. Spam is unprofitable at any scale.
```

**Trust-Flow Sybil Resistance:**

```mermaid
graph LR
    subgraph Honest["Honest Network"]
        A["Alice<br/>100 MHR credit"] <-->|"full trust"| B["Bob<br/>100 MHR credit"]
        B <-->|"full trust"| C["Carol<br/>100 MHR credit"]
        A <-->|"full trust"| C
    end

    subgraph Sybil["Sybil Cluster"]
        S1["Sybil-1<br/>0 MHR credit"]
        S2["Sybil-2<br/>0 MHR credit"]
        S3["Sybil-3<br/>0 MHR credit"]
        S1 <-->|"fake trust"| S2
        S2 <-->|"fake trust"| S3
        S1 <-->|"fake trust"| S3
    end

    B -->|"1 trust edge<br/>10 MHR max credit"| S1

    style Sybil fill:#fdd,stroke:#c00
    style Honest fill:#dfd,stroke:#0a0
```

The honest network has full mutual credit. The Sybil cluster has zero internal credit (no real economic backing). Even with one trust edge from Bob, Sybil-1 gets at most `transitive_credit_ratio × Bob's limit` — and Sybil-2 and Sybil-3 get nothing (3+ hops = no credit). Creating more Sybils doesn't increase available credit.

**Content Lifecycle Economic Model:**

```mermaid
flowchart LR
    Post["Author publishes post<br/>(pays storage)"]
    Propagate["Propagation cost<br/>(relay fees)"]
    Demand["Demand signal<br/>(retrievals + boosts)"]
    Threshold{"Kickback ≥<br/>storage cost?"}
    Sustain["Self-funding:<br/>content persists"]
    Expire["Below threshold:<br/>author pays or<br/>content expires"]

    Post --> Propagate
    Propagate --> Demand
    Demand --> Threshold
    Threshold -->|"Yes"| Sustain
    Threshold -->|"No"| Expire
```

### What Economics Doesn't Limit

A determined, well-funded group willing to pay high storage and relay costs can distribute content through the paid economy. The protocol does not prevent this.

The defense layers for this scenario:

```mermaid
flowchart TD
    Content["Well-funded bad actor<br/>publishes content"]
    L1["Layer 1: NODE REFUSAL<br/>Every storage and relay node<br/>can independently refuse"]
    L2["Layer 2: TRUST REVOCATION<br/>Local community discovers content,<br/>trust revocation isolates author"]
    L3["Layer 3: CURATOR EXCLUSION<br/>No curator includes content →<br/>no organic amplification"]
    L4["Layer 4: LOCAL VALIDATION<br/>Interest relays gate propagation<br/>on local engagement"]
    L5["Layer 5: ECONOMIC ATTRITION<br/>Ongoing storage costs,<br/>no self-funding threshold,<br/>no ad revenue"]

    Content --> L1
    L1 -->|"passes"| L2
    L2 -->|"passes"| L3
    L3 -->|"passes"| L4
    L4 -->|"passes"| L5
    L5 --> Result["Content bleeds MHR<br/>indefinitely with<br/>minimal reach"]
```

This is the same tradeoff every free society makes: some bad actors will misuse freedom. The alternative — giving any central authority the power to decide what's allowed — creates a worse problem. Mehr is more resistant than centralized platforms to censorship, but also more resistant to centralized takedown. Both properties come from the same design: node sovereignty.
:::caution[Trade-off]
A well-funded bad actor can pay full market rates to distribute content — the protocol cannot prevent this. The five defense layers (node refusal, trust revocation, curator exclusion, local validation, economic attrition) limit reach and make it expensive, but they do not guarantee removal. This is the inherent tradeoff of node sovereignty.
:::
## Not Censorship

Refusing to store or relay content is **not censorship** — it is individual autonomy.

```
Censorship:
  A central authority prevents content from existing or
  being accessed ANYWHERE on the network.
  → Impossible on Mehr (no central authority exists)

Node autonomy:
  An individual node chooses not to participate in
  distributing specific content.
  → Always possible on Mehr (every node is sovereign)
```

On Mehr, no single node can prevent content from existing. It can only refuse to help distribute it. If even one node in the network is willing to store and relay the content, it remains accessible to anyone willing to pay the relay costs to reach it. The author's freedom to publish and the node's freedom to refuse coexist without contradiction.

## Comparison With Other Models

| | Centralized Platform | Polycentric (ActivityPub) | Mehr |
|---|---|---|---|
| **Who decides** | Platform moderation team | Server administrator | Each node independently |
| **Enforcement** | Account ban, content removal | Server defederation | Trust revocation, storage/relay refusal |
| **Scope** | Global (platform-wide) | Per-server | Per-node |
| **Appeal** | Platform's discretion | Server operator's discretion | None needed (find a willing node) |
| **Collateral damage** | Affects all users on platform | Affects all users on defederated server | Affects only the specific node |
| **Can content survive?** | No (platform removes it) | Maybe (other servers may host) | Yes (if any node is willing) |
| **Can node refuse?** | N/A (users don't run nodes) | Yes (server operator decides) | Yes (every node operator decides) |

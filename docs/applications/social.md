---
sidebar_position: 2
title: Social
---

# Social

A decentralized content distribution network built on Mehr primitives. No central servers, no algorithmic recommendations, no ads. Authors pay to publish — skin in the game. Readers pay bandwidth to access — infrastructure sustains itself. Popular content self-funds and propagates wider. Unpopular content expires. Economics replaces algorithms.

While "social" implies short text posts, the same architecture handles **any content type**: music albums, scientific papers, video courses, games, software, journalism, podcasts — anything that can be stored as a DataObject. The envelope/post split, kickback economics, and propagation rules are content-agnostic.

| Content Type | Envelope Shows | Paid Content | Typical Kickback |
|-------------|---------------|-------------|-----------------|
| Text post | Full text (under 280 chars) | Full text + links | Low (cheap to read) |
| Photo essay | Summary + blurhash thumbnails | Full-resolution images | Moderate |
| Music album | Track listing + artist + duration | Audio files | High (large files) |
| Video course | Lesson titles + descriptions | Video files | High |
| Scientific paper | Title + abstract + authors | Full PDF | Moderate |
| Game / software | Name + description + screenshots | Binary + assets | High |
| Podcast episode | Title + show notes | Audio file | Moderate |
| Curated collection | Curator notes per item | References to originals | Curator earns on collection; authors earn on items |

## Architecture

Every publication on Mehr has two layers: a **free envelope** that propagates everywhere (browsable at zero cost), and **paid content** that requires retrieval fees. Users browse envelopes to decide what's worth accessing, then pay only for content they actually want.

```mermaid
graph TD
    subgraph FREE["FREE LAYER (PostEnvelope)<br/>Propagates via MHR-Pub to all scope subscribers<br/>~300–500 bytes — fits in a single LoRa frame"]
        Headline
        Summary
        Blurhash
        Scopes["Scopes, metadata"]
    end

    subgraph PAID["PAID LAYER (SocialPost)<br/>Fetched on demand — reader pays relay fees<br/>Size proportional to content"]
        FullText["Full text"]
        Media["Media (images, video, audio)"]
        Links
    end

    Headline -->|post_id| FullText
    Summary -->|post_id| FullText
    Blurhash -->|post_id| FullText
    Scopes -->|post_id| FullText

    FullText -->|Kickback| Author
    Media -->|Kickback| Author
    Links -->|Kickback| Author
```

### PostEnvelope (Free Layer)

The envelope is a lightweight, separate [DataObject](../services/mhr-store) that propagates freely across the mesh. It contains everything a reader needs to decide whether to fetch the full post:

```
PostEnvelope {
    post_id: Option<Blake3Hash>,            // stable ID of the SocialPost (None for boost-only envelopes)
    author: NodeID,
    headline: Option<String>,               // title (~100 chars, author-set)
    summary: Option<String>,                // author-written preview (None for boosts — use the original's)
    media_hints: Vec<MediaHint>,            // lightweight descriptions of attachments
    scopes: Vec<HierarchicalScope>,         // max 1 Geo + up to 3 Topic; total ≤ 1 KB
    reply_to: Option<Blake3Hash>,           // post_id of parent (threading)
    boost_of: Option<Blake3Hash>,           // post_id of boosted post
    references: Vec<Blake3Hash>,            // post_ids of related posts (bidirectional content graph)
    content_size: u32,                      // full post size in bytes (0 for boost-only)
    created: Timestamp,
    sequence: u64,                          // monotonic version counter (incremented on edit)
    kickback_rate: u8,                      // author's desired share of retrieval fees (0-255)
    signature: Ed25519Sig,                  // signed by author (proves authenticity)
}

MediaHint {
    content_type: String,                   // "image/jpeg", "video/mp4", etc.
    size: u32,                              // bytes
    blurhash: Option<String>,               // visual placeholder (~30 bytes)
    alt_text: Option<String>,               // accessibility description
}
```

Envelope size: ~300–500 bytes. Fits in a single LoRa frame with `min_bandwidth: 0`. A reader on a LoRa-only node can browse headlines, summaries, and blurhash thumbnails without paying anything.

### SocialPost (Paid Layer)

The full post is a mutable [DataObject](../services/mhr-store) containing the actual content. Fetching it costs retrieval fees:

```
SocialPost {
    post_id: Blake3Hash,                    // stable ID: Blake3(author ‖ created ‖ nonce)
    author: NodeID,
    content: PostContent {
        text: Option<String>,               // full post body (UTF-8)
        media: Vec<Blake3Hash>,             // references to media DataObjects
        links: Vec<String>,                 // external URLs (for internet-connected nodes)
    },
    sequence: u64,                          // monotonic version counter (0 on first publish)
    edited: Option<Timestamp>,              // None on first publish, Some on edits
    signature: Ed25519Sig,
}
```

The SocialPost is lean — scopes, timestamps, and metadata live on the envelope. The post contains only the content that costs money to retrieve. Both the envelope and the post are mutable DataObjects addressed by `(author, post_id)`. The `post_id` is a stable identifier generated at creation time (`Blake3(author ‖ created ‖ nonce)`) that never changes, even when the content is edited.

### Profile

A mutable DataObject containing identity information. The `claims` list references [IdentityClaims](../services/mhr-id#claims) — including [ProfileField](../services/mhr-id#profile-fields) claims for display name, bio, avatar, and any other key-value data. Each claim has its own [visibility](../services/mhr-id#visibility-controls), so different viewers see different fields depending on their trust relationship with the profile owner.

```
UserProfile {
    node_id: NodeID,
    display_name: String,                   // quick-access copy (also in ProfileField claims)
    bio: Option<String>,                    // quick-access copy
    avatar: Option<Blake3Hash>,             // quick-access copy
    scopes: Vec<HierarchicalScope>,         // from TrustConfig
    claims: Vec<Blake3Hash>,                // references to IdentityClaims (profile fields, geo, links, etc.)
    sequence: u64,                          // monotonic version counter
    signature: Ed25519Sig,
}
```

The `display_name`, `bio`, and `avatar` fields are **quick-access copies** of the corresponding [ProfileField](../services/mhr-id#profile-fields) claims — included directly so clients can render a basic profile without fetching individual claims. The full profile (including visibility-controlled fields, linked accounts, achievements, and verification status) is assembled from the `claims` list. See [Profile Assembly](../services/mhr-id#profile-assembly) for the full resolution flow.

## Feed Types

Mehr social supports five feed types. All feeds are assembled **locally** — no server decides what you see.

```mermaid
graph TD
    Follow["1. FOLLOW<br/>Specific users you choose<br/>Node(alice)"]
    Geographic["2. GEOGRAPHIC<br/>Content from a place:<br/>neighborhood → city → region"]
    Interest["3. INTEREST<br/>Content by topic:<br/>pokemon, physics, jazz"]
    Intersection["4. INTERSECTION<br/>Client-side filter on BOTH:<br/>'Portland Pokemon' = geo ∩ topic"]
    Curated["5. CURATED<br/>Human editor selects best content<br/>Readers subscribe to curator's feed<br/>Two kickback flows: curator + original author"]

    Geographic --> Intersection
    Interest --> Intersection
```

### 1. Direct Follow Feed

Follow specific users. Unchanged from the basic MHR-Pub model.

```
// Follow Alice — see everything she posts
subscribe(Node(alice_node_id), Push);
```

This is the foundation. You follow people you trust, and you see their posts in reverse-chronological order.

### 2. Geographic Feed

Subscribe to content from a geographic area at any level of the [scope hierarchy](../economics/trust-neighborhoods#hierarchical-scopes):

```
// Everything from my neighborhood
subscribe(Scope(Geo("north-america", "us", "oregon", "portland", "hawthorne"), Exact), Push);

// Everything from Portland (all neighborhoods)
subscribe(Scope(Geo("north-america", "us", "oregon", "portland"), Prefix), Digest);

// Everything from Oregon
subscribe(Scope(Geo("north-america", "us", "oregon"), Prefix), PullHint);
```

Geographic feeds are the **local newspaper** — events, news, discussions relevant to where you physically are. Content is cheapest and fastest at the neighborhood level, progressively more expensive at higher scopes.

### 3. Interest Feed

Subscribe to content by topic, independent of geography:

```
// All Pokemon content globally
subscribe(Scope(Topic("gaming", "pokemon"), Prefix), Digest);

// Only competitive Pokemon
subscribe(Scope(Topic("gaming", "pokemon", "competitive"), Exact), Push);

// All science content
subscribe(Scope(Topic("science"), Prefix), PullHint);
```

Interest feeds are **sparse** — they connect people across geography. A Pokemon feed connects Portland, Tokyo, and Berlin. Content propagates through [interest relay nodes](../economics/propagation#interest-relay-nodes) that bridge geographic clusters, but only after [local validation](../economics/propagation#local-first-interest-propagation) — the author's local community must engage with the content (boost, retrieve, or curate) before interest relays forward it globally.

### 4. Intersection Feed

Combine geographic and interest scopes client-side:

```
// Subscribe to Portland AND Pokemon
subscribe(Scope(Geo("...", "portland"), Exact), Push);
subscribe(Scope(Topic("gaming", "pokemon"), Prefix), Push);

// Client-side: show only posts that appear in BOTH feeds
// Result: Portland Pokemon community
```

The protocol delivers by individual scope. The application composes intersection feeds locally by filtering posts that match multiple subscriptions. This keeps the protocol simple while enabling powerful queries.

### 5. Curated Feed

Follow a **curator** — a human who selects the best content from a broader scope:

```
CuratedFeed {
    curator: NodeID,
    name: String,                           // "Portland's Best", "Quantum Physics Weekly"
    description: String,
    entries: Vec<CuratedEntry>,             // max 256 entries per feed page
    scope: HierarchicalScope,               // what this feed covers
    updated: Timestamp,
    sequence: u64,                          // monotonic version counter
    kickback_rate: u8,                      // curator's share of retrieval fees
    signature: Ed25519Sig,
}

CuratedEntry {
    post_id: Blake3Hash,                    // stable ID of original post
    added: Timestamp,
    note: Option<String>,                   // curator's commentary
}
```

A single CuratedFeed holds at most **256 entries**. For larger archives, the curator publishes multiple feed pages as separate DataObjects, each covering a time period or sub-topic. This keeps individual feed objects small enough for constrained devices to fetch and parse.

**How curation works:**

1. Alice follows 200 people and reads the Portland geographic feed daily
2. She publishes a `CuratedFeed` selecting the best posts — "Portland Daily Digest"
3. Bob subscribes to Alice's curated feed instead of following 200 people
4. Bob fetches the CuratedFeed DataObject — Alice earns kickback on it (the curation list has its own `kickback_rate`)
5. Bob's client fetches the **PostEnvelopes** for each curated entry — free, showing headlines + summaries + Alice's curator notes
6. Bob taps posts that interest him — fetches the full SocialPost, and the **original author** earns kickback (the post has its own `kickback_rate`)

These are **two independent kickback flows** on two different DataObjects — the curator's rate and the author's rate don't interact. Bob pays once per DataObject he retrieves, and each DataObject's kickback goes to its respective creator.

**The browsing experience**: Bob sees Alice's curator notes ("Must-read thread on the new bike lanes") alongside each post's envelope (headline, summary, blurhash). He can scroll the entire curated feed for nearly free — only paying when he opens a full post. This makes curated feeds the most bandwidth-efficient way to discover content.

**The curation hierarchy:**

```mermaid
graph TD
    Producers["Producers (authors)<br/>Create content, earn kickback from readers"]
    Curators["Curators (human editors)<br/>Select best content, earn from subscribers"]
    MetaCurators["Meta-curators (curators of curators)<br/>Select best curators, earn from subscribers"]
    Readers["Readers<br/>Pay bandwidth, choose what to subscribe to"]

    Producers --> Curators
    Curators --> MetaCurators
    MetaCurators --> Readers
```

Every level has skin in the game:
- Producers pay to post (anti-spam)
- Curators pay to store their curated feed (anti-spam for curation)
- Readers pay bandwidth (infrastructure sustains itself)
- Kickback flows backward at every level

### Publishing Flow

When an author creates a post, two mutable DataObjects are published:

```
1. Author writes post content + sets headline/summary
2. Client generates a stable post_id: Blake3(author ‖ created ‖ random_nonce)
3. Client creates SocialPost (paid layer):
     → stored as mutable DataObject keyed by (author, post_id)
     → sequence: 0 (first version)
     → only fetched when a reader requests the full content
4. Client creates PostEnvelope (free layer) with same post_id:
     → stored as mutable DataObject with min_bandwidth: 0
     → sequence: 0 (first version)
     → propagates via MHR-Pub to scope subscribers
     → no storage agreement needed within trust network
```

The `post_id` is a stable identifier that never changes — it's the address of both the envelope and the post across all edits. The envelope costs almost nothing to store and propagate (under 500 bytes). The full post costs proportional to its size. Authors pay for content storage, not for letting people know the content exists.

### Editing Posts

Authors can edit their posts by publishing new versions of both the SocialPost and PostEnvelope:

```
Editing flow:
  1. Author modifies content (and optionally headline/summary)
  2. Client publishes updated SocialPost:
       → same post_id, same (author, post_id) key
       → sequence: previous + 1
       → edited: current timestamp
  3. Client publishes updated PostEnvelope (if headline/summary changed):
       → same post_id, same key
       → sequence: previous + 1
  4. MHR-Store propagates the update (highest sequence wins)
  5. MHR-Pub notifies scope subscribers of the updated envelope
```

**Edit properties:**

- **Version history is not preserved** by default. Mutable DataObject semantics: the highest sequence number replaces the previous version. Storage nodes only keep the latest version.
- **Replies, boosts, and references are stable.** They reference the `post_id`, not the content. An edited post doesn't break its reply chains or reference graph.
- **Clients can show edit status.** The `edited` timestamp on SocialPost tells readers the post was modified. Clients may display "edited" alongside the post.
- **No edit limit.** Authors can edit as many times as they want. Each edit increments `sequence` and costs a storage update (negligible).
- **Boosts of edited posts** reflect the latest version. A reader fetching a boosted post always gets the current content.

## Content Economics

```mermaid
graph LR
    Author
    Storage["Storage Node"]
    Reader

    Author -->|"1. Pay storage"| Storage
    Storage -->|"2. Envelope propagates (free)"| Reader
    Reader -->|"3. Browse headlines,<br/>summaries (free)"| Reader
    Reader -->|"4. Fetch full post (paid)<br/>relay fees"| Storage
    Storage -->|"5. Kickback"| Author

    style Author fill:#f9f,stroke:#333
    style Reader fill:#bbf,stroke:#333
    style Storage fill:#bfb,stroke:#333
```

### Browse Before You Pay

Envelopes propagate freely through [MHR-Pub](../services/mhr-pub) notifications. Readers browse without spending:

```
Reader's feed experience:
  1. Receive PostEnvelopes via MHR-Pub subscription (free)
  2. Browse headlines, summaries, blurhash thumbnails (free)
  3. See content_size and estimated retrieval cost (free)
  4. Tap to fetch full SocialPost + media (paid)

LoRa-only node:
  → Sees all envelopes (text headlines + blurhash)
  → Cannot fetch large media (min_bandwidth too low)
  → Can still fetch text-only posts (small enough for LoRa)

WiFi node:
  → Sees all envelopes
  → Fetches full posts + images on demand
  → Fetches video only on high-bandwidth links
```

This solves the "pay before you know what you're getting" problem. The envelope is the shopfront window; the full post is what you pay for inside.

### Author Pays to Post

Every post is a [DataObject](../services/mhr-store) that requires a storage agreement. Posting costs money:

```
Cost to post (neighborhood scope):
    Text-only (~200 bytes):     ~1-5 μMHR per epoch
    With image (~50 KB):        ~50-100 μMHR per epoch
    With video (~5 MB):         ~500-1000 μMHR per epoch

Within trust network: free (no agreement, no payment)
```

This is the **anti-spam mechanism**. Every post costs tokens. Spam is economically irrational because you're paying for content nobody will read. No ML moderation needed — posting costs money, and money is limited.

### Readers Pay for Bandwidth

When someone outside your trust network retrieves your post, they pay relay fees:

```
Reader cost:
    Within trust network:       free
    Cross-trust retrieval:      ~5 μMHR per packet per hop
    Typical 5-hop path:         ~25 μMHR per retrieval

Total reader cost for a text post: ~25-75 μMHR
Total reader cost for an image post: ~250-750 μMHR
```

### Kickback to Author

When readers pay to retrieve content, a portion flows back to the author via the [kickback mechanism](../services/mhr-store#revenue-sharing-kickback):

```
Reader pays 100 μMHR to storage node
    → Storage node keeps (255 - kickback_rate) / 255 of retrieval fee
    → Storage node forwards kickback_rate / 255 to author

At default kickback_rate of 128 (~50%):
    → Storage node keeps ~50 μMHR
    → Author receives ~50 μMHR
```

### Self-Funding Content

Popular content earns more kickback than it costs to store. It becomes **self-sustaining** and [propagates upward](../economics/propagation) through the scope hierarchy automatically:

| Popularity | Scope | Funding Model |
|-----------|-------|--------------|
| Unread | Neighborhood | Author pays entirely |
| Local interest | City | Kickback offsets some storage cost |
| Regional hit | Region | Kickback exceeds storage cost (self-funding) |
| Viral | Country/Global | Self-funding at all levels |

Content that nobody reads expires when the author stops paying. Content that everyone reads lives forever, funded by its own readership. No platform decides — economics decides.

### Why No Likes or Upvotes

Mehr has no reactions, likes, upvotes, or downvotes. This is deliberate.

**The problem with reactions**: Any free reaction can be Sybil-farmed (create 50 accounts, like your own post 50 times). Any paid reaction where the money returns to the sender can be self-tipped in a loop (post → tip own post → kickback returns the tip). Even burn-to-signal (destroy tokens to upvote) creates a vanity metric that people optimize for — the same engagement treadmill that centralized platforms run on.

**Mehr's quality signals are economic, not social:**

| Signal | What It Means | Sybil-Resistant? |
|--------|--------------|-----------------|
| Retrieval count | Real people paid real tokens to read this | Yes — each retrieval costs the reader relay fees that don't return to the author |
| Self-funding threshold | Kickback exceeds storage cost — readership sustains the content | Yes — requires many distinct paying readers |
| Scope promotion | Content bubbled up from neighborhood to city/region | Yes — driven by retrieval demand from geographically distributed nodes |
| Curator inclusion | A human with skin in the game selected this as worth reading | Yes — curator's reputation is on the line |
| Boost count | Multiple people amplified this to their followers | Partially — boosts are free envelopes, but boosting Sybil content wastes your followers' attention |

An author self-retrieving their own post pays relay fees that don't come back via kickback (the storage node keeps its share, and the author is both payer and kickback recipient — net loss). A Sybil cluster retrieving each other's posts bleeds tokens on relay fees with no external demand to sustain it. The economics make fake popularity expensive.

**What readers see instead of like counts**: retrieval-driven propagation scope (neighborhood → city → region tells you how widely read something is), curator endorsements, and boost count from people in their trust graph.

### Clickbait Resistance

The envelope's `headline` and `summary` are author-written and free-form. An author can write a misleading preview. The protocol does not attempt to enforce summary accuracy — there is no way to mechanically verify that a summary "fairly represents" an image, video, or audio post. Instead, clickbait is handled by the same economic and social systems that handle everything else:

**Why clickbait is less profitable on Mehr than on ad-supported platforms:**

| | Ad-Supported Platform | Mehr |
|---|---|---|
| Cost to post | Free | Author pays storage |
| Revenue model | Infinite recurring ad impressions | One-time retrieval fee per reader |
| Amplification | Algorithm promotes high-engagement content | No algorithm — only boosts and curators |
| Second wave | Algorithm keeps serving it to new victims | Zero boosts + zero curation = no second wave |
| Reader cost | Free (attention only) | μMHR per retrieval — small but nonzero |

**Defense layers:**

1. **Local-first propagation** — Content doesn't spread globally on publication. Geographic content starts at neighborhood scope and promotes upward only when retrieval demand justifies it. Interest content starts in the author's local cluster and only propagates to distant clusters when [locally validated](../economics/propagation#local-first-interest-propagation) — at least one boost, multiple distinct retrievals, or curator inclusion. A garbage post tagged with a popular topic never leaves the author's neighborhood because nobody locally endorses it.

2. **Curators are the quality filter** — Raw geographic and interest feeds are unfiltered. Curated feeds are human-verified. For expensive content (video, large media), readers naturally prefer curator-endorsed content over unknown authors. A curator who includes clickbait loses subscribers and kickback revenue.

3. **Client-side author reputation** — After fetching from an author and finding garbage, the client locally downgrades that author. Future envelopes from flagged authors can be marked with a warning or hidden entirely. This is purely local — no protocol change, no centralized blocklist.

4. **Economic self-correction** — Clickbait earns from the first wave of disappointed readers. But with zero boosts, zero curator inclusion, and zero re-reads, the content never self-funds, never promotes to wider scope, and expires when the author stops paying storage. The clickbait author's profit is capped at one wave of retrieval fees minus ongoing storage costs.

5. **Low stakes per read** — A text post retrieval costs ~25–75 μMHR. Being clickbaited once is cheap. Expensive content (video at ~1000+ μMHR) is where the risk is higher — but that's exactly where readers naturally rely on curators rather than browsing raw feeds.

Clickbait on Mehr is a **diminishing-returns attack**: it works once per reader, generates no organic amplification, and the author pays ongoing storage for content that nobody will read a second time.

## Threading and Interaction

### Replies

Replies reference the parent post via `reply_to` on the envelope:

```
Reply to a post:
    PostEnvelope {
        reply_to: Some(parent_post_id),
        summary: "Great point!",
        ...
    }
    SocialPost {
        content: PostContent { text: "Great point! Here's why..." },
        ...
    }
```

Thread assembly is local — each client collects reply envelopes by querying the DHT for envelopes referencing a given hash. Threads are assembled client-side in chronological order. The envelope's summary is enough to display the thread tree — full posts are fetched only when a reader opens a specific reply.

Clients should limit thread traversal depth (recommended: 64 levels). Deeply nested reply chains beyond the limit are still accessible — the client just stops auto-fetching and shows a "load more" prompt. At mesh scale, threads rarely go deep; the economics of reply storage naturally limits chain length.

### Boosts

A boost (repost) references the original via `boost_of` on the envelope:

```
Boost a post:
    PostEnvelope {
        post_id: None,                        // no SocialPost — boost is envelope-only
        boost_of: Some(original_post_id),
        summary: None,                        // original's envelope has the summary
        content_size: 0,
        ...
    }
```

Boosts are envelope-only — `post_id` is None and no SocialPost is created. When a reader fetches the boosted content, the original author receives kickback — not the booster. Boosts are pure amplification without capturing revenue.

### References

References declare that a post is **related to** other posts — without threading (reply) or amplification (boost). They create a queryable content graph: the DHT can answer "what other posts reference this one?", enabling discovery of related discussions, counterarguments, and follow-ups across communities.

```
Reference other posts:
    PostEnvelope {
        references: [post_id_a, post_id_b, post_id_c],
        headline: "Why the bike lane debate misses the point",
        summary: "Alice, Bob, and Carol each analyzed the new bike lanes...",
        ...
    }
```

**What references enable:**

- **Related discussions**: Query the DHT for all envelopes where `references` contains a given hash. A reader viewing a popular post can discover every post that references it — counterarguments, analyses, translations, remixes.
- **Cross-community linking**: A Portland post referenced by a Tokyo post creates a connection between geographic communities. Interest relay nodes can surface cross-references.
- **Knowledge webs**: Scientific papers referencing other papers, course lessons linking to prerequisites, music remixes pointing to originals — any content type benefits from declared relationships.

**How clients render references** is application-dependent. A client might:

1. Show referenced envelopes as linked cards below the post (free — envelope fetch)
2. Show a "referenced by N posts" count with expandable list
3. Build a graph visualization of connected posts
4. Ignore references entirely (minimal client)

When a reader fetches a referenced post's full content, the **referenced author** gets kickback — same as any retrieval.

| | Reply | Boost | Reference |
|---|---|---|---|
| Creates new content | Yes | No (envelope-only) | Yes |
| Relationship | Vertical (parent → child) | Amplification (repost) | Horizontal (related posts) |
| Protocol-level field | `reply_to` on envelope | `boost_of` on envelope | `references` on envelope |
| Queryable via DHT | "What replied to X?" | "Who boosted X?" | "What references X?" |
| Who earns kickback on original | Original author | Original author | Original author |
| Multiple targets | No (one parent) | No (one target) | Yes (any number) |

## Scoped Content

Every post declares its scopes — where it's relevant and how it propagates:

### Local Post (Geographic Only)

```
PostEnvelope {
    scopes: [Geo("north-america", "us", "oregon", "portland")],
    headline: "Hawthorne Farmers Market",
    summary: "Farmers market on Hawthorne this Saturday! Fresh produce, live music...",
    ...
}
```

Envelope appears in Portland geographic feeds. Propagates cheaply within Portland. May bubble up to Oregon if popular.

### Interest Post (Topic Only)

```
PostEnvelope {
    scopes: [Topic("gaming", "pokemon", "competitive")],
    headline: "VGC Meta Analysis",
    summary: "New VGC meta analysis after the latest patch...",
    media_hints: [MediaHint { content_type: "image/png", size: 85000, ... }],
    ...
}
```

Envelope appears in Pokemon interest feeds globally. Readers see the headline and summary for free. The 85KB image is only fetched (and paid for) when a reader opens the full post. Propagates through interest relay nodes. No geographic bias.

### Cross-Scoped Post (Geographic + Interest)

```
PostEnvelope {
    scopes: [
        Geo("north-america", "us", "oregon", "portland"),
        Topic("gaming", "pokemon"),
    ],
    headline: "Portland Pokemon League Meetup",
    summary: "Meetup next Friday at Pioneer Square — all skill levels welcome",
    ...
}
```

Envelope appears in both Portland geographic feeds and Pokemon interest feeds. Portland Pokemon intersection subscribers see it automatically. Note: up to 3 Topic scopes are allowed (e.g., `Topic("gaming", "pokemon") + Topic("events", "meetups")`), but only 1 Geo scope per post, with total scope data capped at 1 KB — see [scope constraints](../economics/trust-neighborhoods#hierarchical-scopes).

### Neighborhood-Only Post (Private)

```
PostEnvelope {
    scopes: [],     // no declared scopes
    summary: "Block party at our place this weekend — neighbors only!",
    ...
}
```

Visible only within trust neighborhood. No propagation beyond trusted peers. The most private form of social posting. Since the audience is trusted peers only, the envelope and full post are both free to access.

Privacy depends on [MHR-Pub](../services/mhr-pub) scope routing: an envelope with no declared scopes matches no `Scope(...)` subscriptions, so it is never forwarded beyond direct MHR-Pub gossip between trusted peers. Nodes only gossip unscoped envelopes to their trusted peer set.

## Media Tiering

The envelope/post split naturally creates a tiered browsing experience. Envelopes carry blurhash thumbnails via `MediaHint`; full media lives in the paid SocialPost as separate DataObjects with `min_bandwidth` constraints:

| Layer | Content | Size | Cost | Available On |
|-------|---------|------|------|-------------|
| Envelope | Headline + summary | ~300-500 bytes | Free | Everywhere, including LoRa |
| Envelope | Blurhash thumbnails (in MediaHint) | ~30-64 bytes each | Free | Everywhere, including LoRa |
| Post | Full text body | ~200 bytes - 10 KB | Retrieval fee | Everywhere |
| Post | Compressed image | ~50 KB | Retrieval fee | WiFi and above |
| Post | Full resolution image | ~500 KB | Retrieval fee | WiFi and above |
| Post | Video | 1+ MB | Retrieval fee | High-bandwidth links only |

The application decides what to fetch based on current link quality:

```
// Envelopes always arrive via MHR-Pub (free)
display(envelope.headline, envelope.summary, envelope.media_hints);

// On user tap — fetch full content
let link = query_link_quality(storage_node);

if link.bandwidth_bps < 1000 {
    // LoRa: text content only
    fetch(post.content.text);
} else if link.bandwidth_bps < 100_000 {
    // Moderate: text + compressed images
    fetch(post.content.text);
    fetch(post.content.media, max_size: 50_000);
} else {
    // High bandwidth: everything
    fetch(post.content.text);
    fetch(post.content.media);
}
```

## Privacy

- **Public posts** (scoped): Propagate per declared scopes and [propagation economics](../economics/propagation). Anyone can pay to read them.
- **Neighborhood-only posts** (unscoped): Visible only within trust neighborhood. Gossip only between trusted peers. The most private social posting.
- **Interest-only posts**: No geographic scope. Propagate through interest graph only — no geographic trail.
- **No social graph leakage**: Following is a local [MHR-Pub](../services/mhr-pub) subscription. No central server has a copy of the social graph. Only the subscriber and the publisher know about the subscription.
- **Unfollowing is silent**: Stop subscribing. No notification, no record.

## Comparison: Economics vs. Algorithms

| | Centralized Social | Mehr Social |
|---|---|---|
| **Spam prevention** | AI moderation (arms race) | Posting costs tokens (economically irrational) |
| **Content ranking** | Opaque algorithm optimizing engagement | Economic signal (what people pay to read) |
| **Content lifespan** | Platform decides | Funded by readership |
| **Monetization** | Ads; platform takes 100% | Direct author-reader kickback; no middleman |
| **Censorship** | Platform discretion | No central point of control |
| **Feed curation** | Algorithmic, engagement-optimized | Human curators with skin in the game |
| **Cost to read** | "Free" (you're the product) | μMHR for strangers; free for friends |
| **Infrastructure** | Company-owned data centers | Self-sustaining through service fees |

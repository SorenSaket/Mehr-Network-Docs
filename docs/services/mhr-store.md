---
sidebar_position: 1
title: "MHR-Store: Content-Addressed Storage"
description: MHR-Store distributed content-addressed storage — BLAKE3 hashing, erasure coding, pinning incentives, and garbage collection on the Mehr mesh.
keywords: [storage, content-addressed, distributed storage, BLAKE3, erasure coding]
---

# MHR-Store: Content-Addressed Storage

MHR-Store is the storage layer of Mehr. Every piece of data is addressed by its content hash — if you know the hash, you can retrieve the data from anywhere in the network. Storage is maintained through bilateral agreements, verified through lightweight challenge-response proofs, and protected against data loss through erasure coding.

## Data Objects

```
DataObject {
    hash: Blake3Hash,               // content hash = address
    content_type: enum { Immutable, Mutable, Ephemeral },
    owner: Option<NodeID>,          // for mutable objects
    created: Timestamp,
    ttl: Option<Duration>,          // for ephemeral objects
    size: u32,
    priority: enum { Critical, Normal, Lazy },
    min_bandwidth: u32,             // don't attempt transfer below this bps

    // Merkle tree root over 4 KB chunks (for verification)
    merkle_root: Blake3Hash,

    payload: enum {
        Inline(Vec<u8>),            // small objects (under 4 KB)
        Chunked([ChunkHash]),       // large objects (4 KB chunks)
    },
}
```

## Content Types

### Immutable

Once created, the content never changes. The hash is the permanent address. Used for: messages, posts, media files, contract code.

### Mutable

The owner can publish updated versions, signed with their key. The highest sequence number wins. Any node can verify the signature. Used for: profiles, status updates, configuration.

**Versioning rules**:
- Sequence numbers must be **strictly monotonic** — each update must have a higher sequence number than the previous one
- Updates are only valid when signed by the owner's Ed25519 key
- **Fork detection**: If two updates with the same sequence number but different content are observed (both validly signed), this is treated as evidence of key compromise or device cloning

**Fork handling**:

```
When a fork is detected (sequence N, two different content hashes, both validly signed):
  1. Record: store (object_key, sequence, both content hashes, detection_time)
  2. Block: reject new updates to this object from this owner for 24 hours
     or until a KeyCompromiseAdvisory with SignedByBoth evidence is received
  3. Gossip: include the fork evidence in the next gossip round as advisory
     metadata (both conflicting hashes + sequence). This is informational —
     receiving nodes independently verify and may apply their own block
  4. Dedup: fork records are retained for 7 days to prevent re-reporting
  5. Resolution: a KeyCompromiseAdvisory with SignedByBoth clears the block
     and allows the new key's updates to proceed. SignedByOldOnly does NOT
     clear the block (could be the attacker)
```

### Ephemeral

Data with a time-to-live (TTL). Automatically garbage-collected after expiration. Used for: presence information, temporary caches, session data.

## Storage Agreements

Storage on Mehr is maintained through **bilateral agreements** between data owners and storage nodes. This is how data stays alive on the network.

```
StorageAgreement {
    data_hash: Blake3Hash,          // what's being stored
    data_size: u32,                 // bytes
    provider: NodeID,               // who stores it
    consumer: NodeID,               // who pays for it
    payment_channel: ChannelID,     // bilateral channel
    cost_per_epoch: u64,            // MHR per epoch
    duration_epochs: u32,           // how long
    challenge_interval: u32,        // how often to verify (in gossip rounds)
    erasure_role: Option<ShardInfo>,// if part of an erasure-coded set

    // Revenue sharing — for content that earns from reader access
    kickback_recipient: Option<NodeID>,  // original author (receives share of retrieval fees)
    kickback_rate: u8,                   // 0-255: author's share of retrieval fee (rate/255)

    signatures: (Sig_Provider, Sig_Consumer),
}
```

### Payment Model

Storage is **pay-per-duration** — like rent, not like purchase. The data owner pays the storage node a recurring fee via their bilateral [payment channel](../economics/payment-channels).

| Duration | Billing | Use Case |
|----------|---------|----------|
| Short-term (hours) | Per-epoch micro-payments | Temporary caches, session data |
| Medium-term (weeks) | Prepaid for N epochs | Messages, posts, media |
| Long-term (months+) | Recurring per-epoch | Persistent data, profiles, hosted content |

When payment stops, the storage node garbage-collects the data after a grace period (1 epoch). The data owner is responsible for maintaining payment — there is no "permanent storage" guarantee.

### Free Storage Between Trusted Peers

Just like [relay traffic](../economics/trust-neighborhoods), storage between trusted peers is **free**:

```
Storage decision:
  if data owner is trusted:
    store for free (no agreement needed, no payment)
  else:
    require a StorageAgreement with payment
```

A trust neighborhood where members store each other's data operates with zero economic overhead — no tokens, no agreements, no challenges. This is how a community mesh handles local content naturally.

## Revenue Sharing (Kickback)

When content is published for public consumption (social posts, media, curated feeds), the **original author** can earn a share of retrieval fees through the kickback mechanism.

### How It Works

```
Author publishes post → creates StorageAgreement with kickback fields:
    kickback_recipient = Author's NodeID
    kickback_rate = 128  (roughly 50% of retrieval fees go to author)

Reader pays storage node to retrieve post:
    Retrieval fee: 100 μMHR
    Storage node keeps: 100 × (255 - 128) / 255 ≈ 50 μMHR
    Storage node forwards: 100 × 128 / 255 ≈ 50 μMHR → Author

Settlement: via the existing payment channel between storage node and author
```

### Incentive Alignment

- **Storage nodes** are incentivized to host popular content because they earn the non-kickback portion of every retrieval fee
- **Authors** are incentivized to create content people want to read because they earn kickback from every reader
- **Readers** pay the same retrieval fee regardless — the kickback split is between author and storage node
- **Curators** who reference posts in [curated feeds](../applications/social#5-curated-feed) drive traffic to original authors, earning kickback on their own curation feed while generating kickback for the original authors too

### Kickback Rate

The `kickback_rate` field is a `u8` (0–255):

| Rate | Author Share | Storage Node Share | Typical Use |
|------|-------------|-------------------|-------------|
| 0 | 0% | 100% | No kickback (pure storage) |
| 64 | ~25% | ~75% | Low author share, high storage incentive |
| 128 | ~50% | ~50% | Balanced split |
| 192 | ~75% | ~25% | High author share |
| 255 | 100% | 0% | Maximum author share (storage node earns only per-epoch fee) |

If `kickback_recipient` is `None`, there is no kickback — the storage node keeps all retrieval fees. This is the default for non-social content (private data, infrastructure objects, etc.).

### Self-Funding Content

When kickback revenue exceeds storage cost, content becomes **self-funding**. The author can reinvest kickback to extend storage agreements, or an automated [RepairAgent](#automated-repair) can do it:

```
Self-funding threshold:
    If kickback_per_epoch > cost_per_epoch:
        Content is self-sustaining — it lives as long as people read it
    If kickback_per_epoch < cost_per_epoch:
        Author must subsidize — content expires if author stops paying
```

Popular content that crosses the self-funding threshold climbs the [propagation hierarchy](../economics/propagation) automatically. Unpopular content stays local or expires. No algorithm decides what lives and what dies — economics does.

## Proof of Storage

How does a data owner know a storage node actually has their data? Through **lightweight challenge-response proofs** that run on any hardware, including ESP32.

### Challenge-Response Protocol

```
Proof of Storage:
  1. Data owner builds a Merkle tree over 4 KB chunks at storage time
     (stores only the merkle_root — not the full tree)

  2. Periodically, owner sends:
     Challenge {
         data_hash: Blake3Hash,
         chunk_index: u32,          // random chunk to verify
         nonce: [u8; 16],           // prevents pre-computation
     }

  3. Storage node responds:
     Proof {
         chunk_hash: Blake3(chunk_data || nonce),
         merkle_proof: [sibling hashes from chunk to root],
     }

  4. Owner verifies:
     a. Recompute merkle root from chunk_hash + merkle_proof
     b. Compare against stored merkle_root
     c. If match: storage verified
     d. If mismatch: node is lying or lost the data
```

### Why This Works on Constrained Devices

| Operation | Compute Cost | RAM Required |
|-----------|-------------|-------------|
| Generate challenge | 16 random bytes | Negligible |
| Compute chunk hash (storage node) | 1 Blake3 hash of 4 KB | 4 KB |
| Verify Merkle proof (owner) | ~10 Blake3 hashes (for 1 MB file) | ~320 bytes |

An ESP32 can verify a storage proof in under 10ms. No GPU needed, no heavy cryptography, no sealing. This is intentionally simpler than Filecoin's Proof of Replication — we trade the ability to detect deduplicated storage for something that actually runs on mesh hardware.

### Challenge Frequency

| Data Priority | Challenge Interval |
|--------------|-------------------|
| Critical | Every gossip round (60 seconds) |
| Normal | Every 10 gossip rounds (~10 minutes) |
| Lazy | Every 100 gossip rounds (~100 minutes) |

Challenges are staggered across stored objects so a storage node never faces a burst of challenges at once.

### What If a Challenge Fails?

```
Challenge failure handling:
  1. First failure: retry after 1 gossip round (could be transient)
  2. Second consecutive failure: flag the storage node
  3. Third consecutive failure: consider data lost on this node
     → trigger repair (see Erasure Coding below)
     → reduce node's storage reputation
     → terminate the StorageAgreement
```

## Erasure Coding

Full replication is wasteful. Storing 3 complete copies of a file costs 3x the storage. **Erasure coding** achieves the same durability with far less overhead.

### Reed-Solomon Coding

Mehr uses Reed-Solomon erasure coding to split data into **k data shards + m parity shards**, where any k of (k + m) shards can reconstruct the original:

```
Erasure coding example (4, 2):
  Original file: 1 MB
  → Split into 4 data shards (256 KB each)
  → Generate 2 parity shards (256 KB each)
  → 6 shards total, stored on 6 different nodes
  → Any 4 of 6 shards can reconstruct the original
  → Total storage: 1.5 MB (1.5x overhead)

Compare with 3x replication:
  → 3 full copies = 3 MB (3x overhead)
  → Tolerates 2 node failures (same as erasure coding)
  → But uses 2x more storage
```

### Default Erasure Parameters

| Data Size | Scheme | Shards | Overhead | Tolerates |
|-----------|--------|--------|----------|-----------|
| Under 4 KB | No erasure (inline) | 1 | 1x | Replication only |
| 4 KB – 1 MB | (2, 1) | 3 shards | 1.5x | 1 node loss |
| 1 MB – 100 MB | (4, 2) | 6 shards | 1.5x | 2 node losses |
| Over 100 MB | (8, 4) | 12 shards | 1.5x | 4 node losses |

The data owner chooses the scheme based on durability requirements and willingness to pay. Higher redundancy = more shards = more storage agreements = higher cost.

### Shard Distribution

Shards are distributed across nodes in **different trust neighborhoods** to maximize independence:

```
Shard placement strategy:
  1. Prefer nodes in different trust neighborhoods
  2. Prefer nodes with different transport types (LoRa, WiFi, cellular)
  3. Prefer nodes with proven uptime (high storage reputation)
  4. Never place two shards of the same object on the same node
```

This ensures that a single neighborhood going offline (power outage, network split) doesn't lose more shards than the erasure code can tolerate.

## Repair

When a storage node fails challenges or goes offline, the data owner must **repair** — reconstruct the lost shard and store it on a new node.

```
Repair flow:
  1. Detect: storage node fails 3 consecutive challenges
  2. Assess: how many shards are still healthy?
     - If >= k shards remain: reconstruction is possible
     - If fewer than k: data is lost (this is why shard distribution matters)
  3. Reconstruct: download k healthy shards, regenerate the lost shard
  4. Re-store: form a new StorageAgreement with a different node
  5. Upload the reconstructed shard
```

### Automated Repair

For users who can't be online to monitor their data, repair can be delegated:

```
RepairAgent {
    data_hash: Blake3Hash,
    shard_map: Map<ShardIndex, NodeID>,
    merkle_root: Blake3Hash,
    authorized_spender: NodeID,     // can spend from owner's channel
    max_repair_cost: u64,           // budget cap
}
```

A RepairAgent is an [MHR-Compute contract](mhr-compute) that periodically challenges storage nodes on behalf of the data owner. If a shard is lost, it handles reconstruction and re-storage automatically, spending from the owner's pre-authorized budget.

## Bandwidth Adaptation

The `min_bandwidth` field controls how data propagates across links of different speeds:

```
Example:
  A 500 KB image declares min_bandwidth: 10000 (10 kbps)

  LoRa node (1 kbps):
    → Propagates hash and metadata only
    → Never attempts to transfer the full image

  WiFi node (100 Mbps):
    → Transfers normally
```

This is a property of the data object that the storage and routing layers respect. Applications set `min_bandwidth` based on the nature of the data, and the network handles the rest.

## Garbage Collection

Storage nodes manage their disk space through a priority-based garbage collection system:

```
Garbage collection priority (lowest priority deleted first):
  1. Expired TTL + no active agreement → immediate deletion
  2. Unpaid (agreement expired, no renewal) → delete after 1 epoch grace
  3. Cached content (no agreement, just opportunistic) → LRU eviction
  4. Low-priority paid data → delete only under extreme space pressure
  5. Normal paid data → never delete while agreement is active
  6. Critical paid data → never delete while agreement is active
  7. Trusted peer data → never delete while trust relationship exists
```

A storage node never deletes data that has an active, paid agreement. Data whose agreement expires is kept for a 1-epoch grace period (to allow renewal), then garbage-collected.

## Chunking

Large objects are split into 4 KB chunks, each independently addressed by hash:

```
Large file (1 MB):
  → Split into 256 chunks of 4 KB each
  → Each chunk has its own Blake3 hash
  → Merkle tree built over all chunk hashes
  → The DataObject stores the chunk hash list and merkle_root
  → Chunks can be retrieved from different nodes in parallel
  → Missing chunks can be re-requested individually
```

Chunking enables:
- Parallel downloads from multiple peers
- Efficient deduplication (identical chunks across objects are stored once)
- Resumable transfers on unreliable links
- Fine-grained storage proofs (challenge any individual chunk)
- Erasure coding at the chunk level for large objects

### Reassembly

```
Fragment reassembly protocol:
  Per-chunk timeout: 30 seconds (configurable per StorageAgreement)
  Retry policy: exponential backoff (2s, 4s, 8s, max 30s), up to 3 retries
  After 3 retries: mark chunk provider as unreliable, try alternate via DHT
  Overall timeout: 5 minutes (all chunks must arrive within this window)

  Resumable downloads:
    Consumer tracks received chunk indices. To resume, send:
      ChunkRequest { data_hash: Blake3Hash, chunk_indices: Vec<u32> }
    Provider responds with only the requested chunks, avoiding
    retransmission of already-received data.
```

## Comparison with Other Storage Protocols

| Aspect | Filecoin | Arweave | Mehr (MHR-Store) |
|--------|----------|---------|-------------------|
| **Payment** | Per-deal, on-chain | One-time endowment | Per-duration, bilateral channels |
| **Proof** | PoRep + PoSt (GPU-heavy, minutes to seal) | SPoRA (mining-integrated) | Challenge-response (milliseconds, runs on ESP32) |
| **Durability** | Slashing for failures (requires blockchain) | Incentivized mining of historical data | Erasure coding + repair agents |
| **Permanent storage** | No (deals expire) | Yes (pay once) | No (pay per duration, data owner's responsibility) |
| **Blockchain** | Required (proof submission on-chain) | Required (block weave) | Not needed (bilateral agreements) |
| **Minimum hardware** | GPU for sealing | Standard PC | ESP32 for verification, Pi for storage |
| **Partition tolerance** | No (needs chain access) | No (needs chain access) | Yes (bilateral proofs work offline) |
| **Free tier** | No | No | Yes (trusted peer storage) |

Mehr deliberately chooses lightweight proofs over heavy cryptographic guarantees. The tradeoff: a storage node could store the same data once and claim to store it twice (unlike Filecoin's Proof of Replication). This is acceptable because:

1. The economic incentive is weak — the node earns the same fee either way
2. The data owner doesn't care *how* the node stores the data, only that it can return it on demand
3. Erasure coding across multiple nodes provides real redundancy regardless

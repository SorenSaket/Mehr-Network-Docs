---
sidebar_position: 2
title: "Layer 1: Network Protocol"
---

# Layer 1: Network Protocol

The network protocol handles identity, addressing, routing, and state propagation across the mesh. It uses [Reticulum](physical-transport) as the transport foundation and extends it with cost-aware routing and economic state gossip.

## Identity and Addressing

Mehr uses Reticulum's identity model. Every node has a cryptographic identity generated locally with no registrar:

```
NodeIdentity {
    keypair: Ed25519Keypair,            // 256-bit, generated locally
    public_key: Ed25519PublicKey,        // 32 bytes
    destination_hash: [u8; 16],         // truncated hash of public key
    x25519_public: X25519PublicKey,      // derived via RFC 7748 birational map
}
```

### Destination Hash

The destination hash is the node's address — 16 bytes (128 bits), derived from the public key. This provides:

- **Flat address space**: No hierarchy, no subnets, no allocation authority
- **Self-assigned**: Any node can generate an address without asking permission
- **Negligible collision probability**: 2^128 possible addresses
- **Pseudonymous**: The hash is not linked to a real-world identity unless the owner publishes that association

A single node can generate **multiple destination hashes** for different purposes (personal identity, service endpoints, anonymous identities). Each is derived from a separate Ed25519 keypair.

## Packet Format

Mehr uses the [Reticulum packet format](https://reticulum.network/manual/understanding.html):

```
[HEADER 2 bytes] [ADDRESSES 16/32 bytes] [CONTEXT 1 byte] [DATA 0-465 bytes]
```

Header flags encode: propagation type (broadcast/transport), destination type (single/group/plain/link), and packet type (data/announce/link request/proof). Maximum overhead per packet: 35 bytes.

**Critical property** (inherited from Reticulum): The source address is **NOT** in the header. Packets carry only the destination. Sender anonymity is structural.

### Mehr Extension: Compact Path Cost

Mehr extends announces with a constant-size cost summary that each relay updates in-place as it forwards the announce:

```
CompactPathCost {
    cumulative_cost: u16,    // log₂-encoded μMHR/byte (2 bytes)
    worst_latency_ms: u16,   // max latency on any hop in path (2 bytes)
    bottleneck_bps: u8,      // log₂-encoded min bandwidth on path (1 byte)
    hop_count: u8,           // number of relays traversed (1 byte)
}
// Total: 6 bytes (constant, regardless of path length)
```

Each relay updates the running totals as it forwards:
- `cumulative_cost += my_cost_per_byte` (re-encoded to log scale)
- `worst_latency_ms = max(existing, my_measured_latency)`
- `bottleneck_bps = min(existing, my_bandwidth)`
- `hop_count += 1`

**Log encoding for cost**: `encoded = round(16 × log₂(value + 1))`. A u16 covers the full practical cost range with ~6% precision per step.

**Log encoding for bandwidth**: `encoded = round(8 × log₂(bps))`. A u8 covers 1 bps to ~10 Tbps with ~9% precision.

The CompactPathCost is carried in the announce DATA field using a TLV envelope:

```
MehrExtension {
    magic: u8 = 0x4E,           // 'N' — identifies Mehr extension presence
    version: u8,                 // extension format version
    path_cost: CompactPathCost,  // 6 bytes
    extensions: [{               // future extensions via TLV pairs
        type: u8,
        length: u8,
        data: [u8; length],
    }],
}
// Minimum size: 8 bytes (magic + version + path_cost)
```

Nodes that don't understand the `0x4E` magic byte forward the DATA field as opaque payload. Mehr-aware nodes parse and update it.

#### Why No Per-Relay Signatures

Earlier designs signed each relay's cost annotation individually (~84 bytes per relay hop). This is unnecessary for three reasons:

1. **Routing decisions are local.** You select a next-hop neighbor. You only need to trust your neighbor's cost claim — and your neighbor is already authenticated by the link-layer encryption.
2. **Trust is transitive at each hop.** Your neighbor trusts *their* neighbor (link-authenticated), who trusts *their* neighbor, and so on. No node needs to verify claims from relays it has never communicated with.
3. **The market enforces honesty.** A relay that inflates path costs gets routed around. A relay that deflates costs loses money on every packet. Economic incentives are a cheaper and more robust enforcement mechanism than cryptographic proofs for cost claims.

The announce itself remains signed by the destination node (proving authenticity of the route). The path cost summary is trusted transitively through link-layer authentication at each hop — analogous to how BGP trusts direct peers, not every AS along the path.

## Routing

Routing is destination-based with cost annotations, formalized as **greedy forwarding on a small-world graph**. Each node maintains a routing table:

```
RoutingEntry {
    destination: DestinationHash,
    next_hop: InterfaceID + LinkAddress, // which interface, which neighbor

    // From CompactPathCost (6 bytes in announce)
    cumulative_cost: u16,                // log₂-encoded μMHR/byte
    worst_latency_ms: u16,              // max latency on path
    bottleneck_bps: u8,                 // log₂-encoded min bandwidth
    hop_count: u8,                      // relay count

    // Locally computed
    reliability: u8,                     // 0-255 (0=unknown, 255=perfect) — avoids FP on ESP32

    last_updated: Timestamp,
    expires: Timestamp,
}
```

### Small-World Routing Model

Mehr routing is based on the **Kleinberg small-world model**, adapted for a physical mesh with heterogeneous transports. This provides a formal basis for routing scalability.

#### The Network as a Small-World Graph

The destination hash space `[0, 2^128)` forms a **ring**. The circular distance between two addresses is:

```
ring_distance(a, b) = min(|a - b|, 2^128 - |a - b|)
```

The physical mesh naturally provides two types of links, matching Kleinberg's model:

- **Short-range links** (lattice edges): LoRa, WiFi ad-hoc, BLE — these connect geographically nearby nodes, forming an approximate 2D lattice determined by physical proximity.
- **Long-range links** (Kleinberg contacts): Directional WiFi, cellular, internet gateways, fiber — these connect distant nodes, providing shortcuts across the ring.

Kleinberg's result proves that greedy forwarding achieves **O(log² N) expected hops** when long-range link probability follows `P(u→v) ∝ 1/d(u,v)^r` with clustering exponent `r` equal to the network dimension. The distribution of real-world backbone links (many local WiFi, fewer city-to-city, even fewer intercontinental) naturally approximates this harmonic distribution.

#### Greedy Forwarding with Cost Weighting

At each hop, the current node selects the neighbor that minimizes a scoring function:

```
score(neighbor) = α · norm_ring_distance(neighbor, destination)
                + β · norm_cumulative_cost(neighbor)
                + γ · norm_worst_latency(neighbor)
```

Where `norm_*` normalizes each metric to `[0, 1]` across the candidate set. Normalization is performed on **decoded** values (not the log-encoded wire representation):

```
Decoding (for normalization):
  decoded_cost = (2 ^ (encoded / 16.0)) - 1    // inverse of log₂ encoding
  decoded_bw   = 2 ^ (encoded / 8.0)           // inverse of bandwidth encoding

  norm_cumulative_cost = decoded_cost(neighbor) / max_decoded_cost_in_candidate_set
  norm_worst_latency   = neighbor.worst_latency_ms / max_latency_in_candidate_set
```

This preserves the true cost ratios. Log-encoded values compress dynamic range for wire efficiency but must not be used directly in scoring — otherwise a 1000x cost difference would appear as only ~2x.

The weights α, β, γ are derived from the per-packet `PathPolicy`:

```
PathPolicy: enum {
    Cheapest,                           // α=0.1, β=0.8, γ=0.1
    Fastest,                            // α=0.1, β=0.1, γ=0.8
    MostReliable,                       // maximize delivery probability
    Balanced(cost_weight, latency_weight, reliability_weight),
}
```

Pure greedy routing (α=1, β=0, γ=0) guarantees **O(log² N) expected hops**. Cost and latency weighting trades path length for economic efficiency — a path may take more hops if each hop is cheaper or faster.

Applications specify their preferred policy:
- **Voice traffic** uses `Fastest` — latency matters most
- **Bulk storage replication** uses `Cheapest` — cost efficiency matters most
- **Default** is `Balanced` — a weighted combination of all factors

With N nodes where each has O(1) long-range links (typical for relay nodes), expected path length is **O(log² N)**. Backbone nodes with O(log N) connections reduce this to **O(log N)**.

#### Why Mehr Does Not Need Location Swapping

Unlike Freenet/Hyphanet, which uses location swapping to arrange nodes into a navigable topology, Mehr does not need this mechanism:

1. **Destination hashes are self-assigned** — each node's position on the ring is fixed by its Ed25519 keypair.
2. **Announcements build routing tables** — when a node announces itself, it creates routing table entries across the mesh that function as navigable links.
3. **Multi-transport bridges are natural long-range contacts** — a node bridging LoRa to WiFi to internet inherently provides the long-range shortcuts that make the graph navigable.

The announcement propagation itself creates the navigable topology. Each announcement that reaches a distant node via a backbone link creates exactly the kind of long-range routing table entry that Kleinberg's model requires.

### Path Discovery

Path discovery works via announcements:

1. A node announces its destination hash to the network, signed with its Ed25519 key
2. The announcement propagates through the mesh via greedy forwarding, with each relay updating the [CompactPathCost](#mehr-extension-compact-path-cost) running totals in-place (no per-relay signatures — link-layer authentication is sufficient)
3. Receiving nodes record the path (or multiple paths) and select based on the scoring function above
4. Multiple paths are retained and scored — the best path per policy is used, with fallback to alternatives on failure

### Announce Propagation Rules

Announces are **event-driven with periodic refresh**, not purely periodic:

```
Announce triggers:
  - First boot / new identity: immediate announce
  - Interface change: announce on new interface within 1 gossip round
  - Cost change > 25%: re-announce with updated CompactPathCost
  - Periodic refresh: every 30 minutes (1,800 seconds)
  - Forced refresh: on peer request (pull-based for constrained links)
```

**Hop limit**: Announces carry a `max_hops` field (u8, default 128). Each relay decrements by 1; announces at 0 are not forwarded. This prevents unbounded propagation in large meshes while ensuring O(log² N) reachability.

**Expiry**: Routing entries expire at `last_updated + announce_interval × 3` (default 90 minutes). If no refresh is received, the entry is marked stale (still usable at lower priority) for one additional interval, then evicted. On memory pressure, LRU eviction removes the least-recently-used stale entries first, then lowest-reliability active entries.

**Link failure detection**: If a direct neighbor misses 3 consecutive gossip rounds (3 minutes) without response, the link is marked down. All routing entries using that neighbor as next-hop are immediately marked stale (not deleted — the neighbor may return). After 10 missed rounds, entries are evicted.

## Gossip Protocol

All protocol-level state propagation uses a common gossip mechanism:

```
GossipRound (every 60 seconds with each neighbor):

1. Exchange state summaries (bloom filters of known state)
2. Identify deltas (what I have that you don't, and vice versa)
3. Exchange deltas (compact, only what's new)
4. Apply received state via CRDT merge rules
```

### Gossip Bloom Filter

State summaries use a compact bloom filter to identify deltas without exchanging full state:

```
GossipFilter {
    bits: [u8; N],          // N scales with known state entries
    hash_count: 3,          // 3 independent hash functions (Blake3-derived)
    target_fpr: 1%,         // 1% false positive rate (tolerant — FP only causes redundant delta)
}
```

| Known state entries | Filter size | FPR |
|-------------------|-------------|-----|
| 100 | 120 bytes | ~1% |
| 1,000 | 1.2 KB | ~1% |
| 10,000 | 12 KB | ~1% |

On constrained links (below 10 kbps), the filter is capped at 256 bytes — entries beyond the filter capacity are omitted (pull-only mode for Tiers 3-4 handles this). False positives are harmless: they cause a delta item to not be requested, but the item will be caught in the next round when the bloom filter is regenerated.

**New node joining**: A node with empty state sends an all-zeros bloom filter. The neighbor detects maximum divergence and sends a prioritized subset of state (Tier 1 first, then Tier 2, etc.) spread across multiple gossip rounds to avoid link saturation.

A single gossip round multiplexes all protocol state:
- Routing announcements (with cost annotations)
- Ledger state (settlements, balances)
- Trust graph updates
- Capability advertisements
- DHT metadata
- Pub/sub notifications

### Bandwidth Budget

Total protocol overhead targets **≤10% of available link bandwidth**, allocated by priority tier:

```
Gossip Bandwidth Budget (per link):

  Tier 1 (critical):  Routing announcements         — up to 3%
  Tier 2 (economic):  Payment + settlement state     — up to 3%
  Tier 3 (services):  Capabilities, DHT, pub/sub     — up to 2%
  Tier 4 (social):    Trust graph, names               — up to 2%
```

**On constrained links (< 10 kbps)**, the budget adapts automatically:

- Tiers 3–4 switch to **pull-only** (no proactive gossip — only respond to requests)
- Payment batching interval increases from 60 seconds to **5 minutes**
- Capability advertisements limited to **Ring 0 only** (direct neighbors)

| Link type | Routing | Payment | Services | Trust/Social | Total |
|---|---|---|---|---|---|
| 1 kbps LoRa | ~1.5% | ~0.5% | pull-only | pull-only | ~2% |
| 50 kbps LoRa | ~2% | ~2% | ~1% | ~1% | ~6% |
| 10+ Mbps WiFi | ~1% | ~1% | ~2% | ~2% | ~6% |

This tiered model ensures constrained links are never overwhelmed by protocol overhead, while higher-bandwidth links gossip more aggressively for faster convergence.

## Congestion Control

User data has three layers of congestion control. Protocol gossip is handled separately by the [bandwidth budget](#bandwidth-budget).

### Link-Level Collision Avoidance (CSMA/CA)

On half-duplex links (LoRa, packet radio), mandatory listen-before-talk:

```
LinkTransmit(packet):
  1. CAD scan (LoRa Channel Activity Detection, ~5ms)
  2. If channel busy:
       backoff = random(1, 2^attempt) × slot_time
       slot_time = max_packet_airtime for this link
                   (~200ms at 1 kbps for 500-byte MTU)
  3. Max 7 backoff attempts → drop packet, signal congestion upstream
  4. If channel clear → transmit
```

On full-duplex links (WiFi, Ethernet), the transport handles collision avoidance natively — this layer is a no-op.

### Per-Neighbor Token Bucket

Each outbound link enforces fair sharing across neighbors:

```
LinkBucket {
    link_id: InterfaceID,
    capacity_tokens: u32,        // link_bandwidth_bps × window_sec / 8
    tokens: u32,                 // current available (1 token = 1 byte)
    refill_rate: u32,            // bytes/sec = measured_bandwidth × (1 - protocol_overhead)
    per_neighbor_share: Map<NodeID, u32>,
}

Bandwidth measurement:
  measured_bandwidth = exponential moving average of successfully-transmitted bytes/sec
  Half-life: 60 seconds (adapts within ~3 half-lives = 3 minutes)
  On transport change (e.g., LoRa → WiFi): reset EMA to the new link's nominal rate,
    then converge from there
  refill_rate = measured_bandwidth × 0.90  (10% reserved for protocol overhead)
  per_neighbor_share = refill_rate / num_active_neighbors  (user data only;
    protocol gossip has its own budget per the bandwidth tiers above)
```

Fair share is `refill_rate / num_active_neighbors` by default. Neighbors with active payment channels get share weighted proportionally to channel balance — paying for bandwidth earns proportional priority.

When a neighbor exceeds its share, packets are queued (not dropped). If the queue exceeds a depth threshold, a backpressure signal is sent.

### Priority Queuing

Four priority levels for user data, scheduled with strict priority and starvation prevention (P3 guaranteed at least 10% of user bandwidth):

| Priority | Traffic Type | Examples | Queue Policy |
|----------|-------------|----------|--------------|
| P0 | Real-time | Voice (Codec2), interactive control | Tail-drop at 500ms deadline |
| P1 | Interactive | Messaging, DHT lookups, link establishment | FIFO, 5s max queue time |
| P2 | Standard | Social posts, pub/sub, MHR-Name | FIFO, 30s max queue time |
| P3 | Bulk | Storage replication, large file transfer | FIFO, unbounded patience |

Within a priority level, round-robin across neighbors. On half-duplex links, preemption occurs at packet boundaries only.

### Backpressure Signaling

When an outbound queue exceeds 50% capacity, a 1-hop signal is sent to upstream neighbors:

```
CongestionSignal {
    severity: enum {          // 2 bits
        Moderate,             // reduce sending rate by 25%
        Severe,               // reduce by 50%, reroute P2/P3 traffic
        Saturated,            // stop P2/P3, throttle P1, P0 only
    },
    scope: enum {             // 2 bits
        ThisLink,             // only the link to the signaling neighbor is congested
        AllOutbound,          // all outbound links on this node are congested
    },
    estimated_drain_ms: u16,  // estimated time until queue drains
}
// Byte 0: [severity (2 bits) | scope (2 bits) | reserved (4 bits)]
// Bytes 1-2: estimated_drain_ms (u16, little-endian)
// Total: 3 bytes
```

The signal does not identify which internal interface is congested — upstream peers only need to know whether to reduce traffic through this node (`ThisLink` for targeted rerouting, `AllOutbound` if the node itself is overloaded). Internal link topology is not exposed.
```

### Dynamic Cost Response

Congestion increases the effective cost of a link. When queue depth exceeds 50%:

```
effective_cost = base_cost × (1 + (queue_depth / queue_capacity)²)
```

The quadratic term ensures gentle increase at moderate load and sharp increase near saturation. The updated cost propagates in the next gossip round's CompactPathCost, causing upstream nodes to naturally reroute traffic to less-congested paths. This is a local decision — no protocol extension beyond normal cost updates.

## Time Model

Mehr does not require global clock synchronization. Time is handled through three mechanisms:

### Logical Clocks

Packet headers carry a **Lamport timestamp** incremented at each hop. Used for ordering events and detecting stale routing entries. If a node receives a routing announcement with a lower logical timestamp than one already in its table for the same destination, the older announcement is discarded.

### Neighbor-Relative Time

During link establishment, nodes exchange their local monotonic clock values. Each node maintains a `clock_offset` per neighbor. Relative time between any two direct neighbors is accurate to within RTT/2.

Used for: agreement expiry, routing entry TTL, payment channel batching intervals.

### Epoch-Relative Time

Epochs define coarse time boundaries. "Weekly" means approximately **10,000 settlement batches after the previous epoch** — not wall-clock weeks. The epoch trigger is settlement count, not elapsed time.

The "30-day grace period" for epoch finalization is defined as **4 epochs after activation**, tolerating clock drift of up to 50% without protocol failure.

All protocol `Timestamp` fields are `u64` values representing milliseconds on the node's local monotonic clock (not wall-clock). Conversion to neighbor-relative or epoch-relative time is performed at the protocol layer.

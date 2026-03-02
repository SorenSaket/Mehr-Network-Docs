---
sidebar_position: 2
title: "Network Protocol"
description: Network protocol layer for the Mehr mesh — addressing, routing, packet format, and multi-hop relay with incentivized forwarding.
keywords: [network protocol, routing, mesh routing, packet format, addressing]
---

# MHR-Net: Network Protocol

The network protocol handles identity, addressing, routing, and state propagation across the mesh. It builds on the [transport layer](../L0-physical/physical-transport) and extends it with cost-aware routing and economic state gossip.

## Identity and Addressing

:::info[Specification]

Every node has a cryptographic identity generated locally with no registrar:

```
NodeIdentity {
    keypair: Ed25519Keypair,            // 256-bit, generated locally
    public_key: Ed25519PublicKey,        // 32 bytes
    destination_hash: [u8; 16],         // truncated hash of public key
    x25519_public: X25519PublicKey,      // derived via RFC 7748 birational map
}
```

:::

### Destination Hash

The destination hash is the node's address — 16 bytes (128 bits), derived from the public key. This provides:

- **Flat address space**: No hierarchy, no subnets, no allocation authority
- **Self-assigned**: Any node can generate an address without asking permission
- **Negligible collision probability**: 2^128 possible addresses
- **Pseudonymous**: The hash is not linked to a real-world identity unless the owner publishes that association

A single node can generate **multiple destination hashes** for different purposes (personal identity, service endpoints, anonymous identities). Each is derived from a separate Ed25519 keypair.

## Packet Format

Mehr uses the following packet format:

```
[HEADER 2 bytes] [ADDRESSES 16/32 bytes] [CONTEXT 1 byte] [DATA 0-465 bytes]
```

Header flags encode: propagation type (broadcast/transport), destination type (single/group/plain/link), and packet type (data/announce/link request/proof). Maximum overhead per packet: 35 bytes.

**Critical property**: The source address is **NOT** in the header. Packets carry only the destination. Sender anonymity is structural.

### Mehr Extension: Compact Path Cost

Mehr extends announces with a constant-size cost summary that each relay updates in-place as it forwards the announce:

```
CompactPathCost {
    cumulative_cost: u16,    // log₂-encoded μMHR/byte (2 bytes)
    worst_latency_ms: u16,   // max latency on any hop in path (2 bytes)
    bottleneck_bps: u8,      // log₂-encoded min bandwidth on path (1 byte)
    hop_count: u8,           // number of relays traversed (1 byte)
    bottleneck_mtu: u8,      // log₂-encoded min MTU on path (1 byte)
}
// Total: 7 bytes (constant, regardless of path length)
```

Each relay updates the running totals as it forwards:
- `cumulative_cost += my_cost_per_byte` (re-encoded to log scale)
- `worst_latency_ms = max(existing, my_measured_latency)`
- `bottleneck_bps = min(existing, my_bandwidth)`
- `bottleneck_mtu = min(existing, my_interface_mtu)`
- `hop_count += 1`

**Log encoding for cost**: `encoded = round(16 × log₂(value + 1))`. A u16 covers the full practical cost range with ~6% precision per step.

**Log encoding for bandwidth**: `encoded = round(8 × log₂(bps))`. A u8 covers 1 bps to ~10 Tbps with ~9% precision.

**Log encoding for MTU**: `encoded = round(4 × log₂(mtu_bytes))`. A u8 covers 1 byte to ~16 MB with ~19% precision per step.

| MTU | Encoded |
|-----|--------|
| 228 bytes (Meshtastic) | 31 |
| 484 bytes (Constrained) | 35 |
| 1,500 bytes (Ethernet) | 43 |
| 4,096 bytes (bulk) | 48 |
| 9,000 bytes (jumbo) | 51 |

The CompactPathCost is carried in the announce DATA field using a TLV envelope:

```
MehrExtension {
    magic: u8 = 0x4E,           // 'N' — identifies Mehr extension presence
    version: u8,                 // extension format version
    path_cost: CompactPathCost,  // 7 bytes
    extensions: [{               // future extensions via TLV pairs
        type: u8,
        length: u8,
        data: [u8; length],
    }],
}
// Minimum size: 9 bytes (magic + version + path_cost)
```

Nodes that don't understand the `0x4E` magic byte forward the DATA field as opaque payload. Mehr-aware nodes parse and update it.

#### Why No Per-Relay Signatures

:::tip[Key Insight]

Earlier designs signed each relay's cost annotation individually (~84 bytes per relay hop). This is unnecessary for three reasons:

1. **Routing decisions are local.** You select a next-hop neighbor. You only need to trust your neighbor's cost claim — and your neighbor is already authenticated by the link-layer encryption.
2. **Trust is transitive at each hop.** Your neighbor trusts *their* neighbor (link-authenticated), who trusts *their* neighbor, and so on. No node needs to verify claims from relays it has never communicated with.
3. **The market enforces honesty.** A relay that inflates path costs gets routed around. A relay that deflates costs loses money on every packet. Economic incentives are a cheaper and more robust enforcement mechanism than cryptographic proofs for cost claims.

The announce itself remains signed by the destination node (proving authenticity of the route). The path cost summary is trusted transitively through link-layer authentication at each hop — analogous to how BGP trusts direct peers, not every AS along the path.

:::

## Routing

Routing is destination-based with cost annotations, formalized as **greedy forwarding on a small-world graph**. Each node maintains a routing table:

```
RoutingEntry {
    destination: DestinationHash,
    next_hop: InterfaceID + LinkAddress, // which interface, which neighbor

    // From CompactPathCost (7 bytes in announce)
    cumulative_cost: u16,                // log₂-encoded μMHR/byte
    worst_latency_ms: u16,              // max latency on path
    bottleneck_bps: u8,                 // log₂-encoded min bandwidth
    hop_count: u8,                      // relay count
    bottleneck_mtu: u8,                 // log₂-encoded min MTU on path

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
    LargestMTU,                         // α=0.1, β=0.1, γ=0.1 — prefer paths with largest bottleneck_mtu
}
```

Pure greedy routing (α=1, β=0, γ=0) guarantees **O(log² N) expected hops**. Cost and latency weighting trades path length for economic efficiency — a path may take more hops if each hop is cheaper or faster.

Applications specify their preferred policy:
- **Voice traffic** uses `Fastest` — latency matters most
- **Bulk storage replication** uses `Cheapest` — cost efficiency matters most
- **Large file transfer** uses `LargestMTU` — prefer paths that support larger packets to reduce per-packet overhead
- **Default** is `Balanced` — a weighted combination of all factors

#### MTU-Aware Path Selection

When the `PathPolicy` is `LargestMTU` or when the application specifies a `min_mtu` requirement, paths are **pre-filtered** before scoring:

```
MTU-aware path selection:

  1. Pre-filter: discard routes where decoded_mtu(bottleneck_mtu) < required_mtu
  2. Among remaining routes, prefer higher bottleneck_mtu as a tiebreaker:
       mtu_bonus(neighbor) = (decoded_mtu(neighbor) - min_required) /
                             (max_decoded_mtu_in_set - min_required)
       adjusted_score = base_score - 0.1 × mtu_bonus
  3. If no route meets min_mtu: fall back to best available route
     (application is notified via PathConstraintViolation callback)

  Decoding:
    decoded_mtu = 2 ^ (encoded / 4.0)   // inverse of MTU log₂ encoding
```

This ensures that bulk transfers and large-payload applications are routed through high-MTU paths when available, without affecting routing for small-payload traffic (messaging, voice) that fits in any MTU.

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

### Route Probing

The `bottleneck_mtu` and `bottleneck_bps` fields in CompactPathCost give **passive** path characterization from announces. For applications that need **real-time** measurements before starting a session (e.g., before a voice call or large file transfer), an active probe mechanism is available.

:::info[Specification]

Route probing is **opt-in** — applications request it explicitly. It is never triggered automatically by the protocol.

```
ProbeRequest {
    probe_id: u16,              // correlates request/response
    payload_size: u16,          // total probe packet size in bytes (including this header)
    padding: [u8; N],           // zero-filled to reach payload_size
    timestamp: u64,             // sender's monotonic clock (for RTT calculation)
}

ProbeResponse {
    probe_id: u16,              // echo from request
    received_size: u16,         // actual bytes received (detects truncation or fragmentation)
    timestamp_echo: u64,        // echo sender's timestamp
    responder_mtu: u16,        // this node's outbound MTU toward the destination
    measured_bps: u32,          // responder's current outbound bandwidth estimate
}
```

:::

**Binary search for path MTU**: Send probes at doubling sizes (256, 512, 1024, 2048...), then binary-search the failure boundary. Converges in **4–5 probes**.

**Constraints**:

| Rule | Value | Rationale |
|------|-------|-----------|
| Rate limit | 1 probe/minute per destination | Prevents probe flooding |
| Minimum link bandwidth | 10 kbps | Never probe on constrained LoRa links |
| Relay rewards | Probes are **exempt** from VRF lottery | Prevents artificial traffic generation for profit |
| Priority | P2 (Standard) | Probes yield to voice and interactive traffic |
| Timeout | `3 × worst_latency_ms` from routing table | Adapts to path characteristics |

**RTT measurement**: `RTT = local_time_now - timestamp_echo`. Combined with `received_size`, the sender calculates actual path throughput: `throughput = received_size / (RTT / 2)`.

Probe data is cached per-destination with the same expiry as routing entries (90 minutes default, refreshed on new announce). Applications query the cache via a local API — they never send probes directly.

### Probe Response Routing

ProbeResponse routing uses the transport layer's **reverse-path forwarding** mechanism. The destination node generates the ProbeResponse addressed to the original request's implicit return path. No source address or explicit return route is embedded in the ProbeRequest.

Each relay on the forward path maintains a **probe forwarding entry** (keyed by `destination_hash + probe_id`) for `3 × worst_latency_ms` from the routing table. This entry records only the incoming interface — not the originator — preserving the same anonymity properties as regular packet forwarding.

## Bandwidth Reservation

For large transfers (over 1 MB), per-packet stochastic VRF lottery overhead becomes significant. Bandwidth reservation allows a sender to negotiate an entire transfer upfront: agree on cost and bandwidth with each relay along the path, escrow the payment, and stream data with zero per-packet economic overhead.

### Core Principle: Hop-by-Hop Propagation

The sender NEVER learns or specifies the full path. Instead, the reservation propagates hop-by-hop, exactly like packet forwarding:

```
Reservation propagation (hop-by-hop):

  Sender → Neighbor A:
    "I want to send ~1 GB toward destination X.
     My max cost: 50 μMHR/byte. Duration: ~1 hour."

  Neighbor A → Neighbor B:
    "I need to relay ~1 GB toward X.
     My max cost: 44 μMHR/byte (50 minus my 6 μMHR/byte fee)."

  Neighbor B → Neighbor C:
    "I need to relay ~1 GB toward X.
     My max cost: 38 μMHR/byte."

  ... propagates until reaching destination or cost exhaustion ...

  Commitment propagation (reverse path):
    Destination → C → B → A → Sender:
    "Path reserved. Total cost: 42 μMHR/byte. Committed bandwidth: 500 kbps."
```

**Each relay only knows its immediate neighbors** — identical to regular packet routing. The sender knows the total path cost but not which relays are on the path or how many hops exist. `hop_count` is deliberately excluded from `ReservationCommitment` to avoid leaking path length.

### Wire Format

:::info[Specification]

```
ReservationRequest {
    reservation_id: u16,            // correlates with response
    destination: DestinationHash,   // where the data is going
    estimated_bytes: u64,           // total transfer size estimate
    min_throughput_bps: u32,        // minimum acceptable sustained bandwidth
    max_cost_per_byte: u64,         // sender's maximum per-byte cost (μMHR)
    valid_for_seconds: u32,         // reservation lifetime
    flags: u8,                      // bit 0: require_onion, bit 1: allow_reroute
}
// Size: 2 + 16 + 8 + 4 + 8 + 4 + 1 = 43 bytes

ReservationCommitment {
    reservation_id: u16,            // echo from request
    status: enum {
        Accepted,                   // path fully reserved
        PartialAccepted,            // reserved to intermediate relay (partial path)
        CostExceeded,               // path exists but exceeds max_cost
        NoRoute,                    // no path to destination
        BandwidthInsufficient,      // path exists but below min_throughput
    },
    committed_bps: u32,             // actual committed bandwidth
    actual_cost_per_byte: u64,      // actual total per-byte cost
    valid_until: Timestamp,         // when the reservation expires
}
// Size: 2 + 1 + 4 + 8 + 8 = 23 bytes

ReservationRelease {
    reservation_id: u16,
    bytes_transferred: u64,         // actual bytes sent (for settlement)
    reason: enum {
        Complete,                   // transfer finished normally
        PathFailure,                // a relay went down
        Timeout,                    // reservation expired before transfer completed
        SenderCancel,               // sender aborted
    },
}
// Size: 2 + 8 + 1 = 11 bytes
```

:::

### Routing and Path Changes

A reservation follows the routing table path at reservation time. If the path changes mid-transfer:

1. **Link failure**: The relay at the break generates a `ReservationRelease` with `reason: PathFailure`, which propagates back to the sender
2. **Better path appears**: By default, reservations are **sticky** (don't migrate). The `allow_reroute` flag enables relay-initiated renegotiation if a significantly better path appears (over 25% cost reduction or over 50% bandwidth improvement)
3. **Sender recovery**: On `PathFailure`, the sender negotiates a new reservation for the remaining `estimated_bytes - bytes_transferred`. The new reservation may follow a different path

### Capability Agreement Mapping

A `ReservationRequest` is syntactic sugar over the existing [CapabilityAgreement](/docs/L4-marketplace/agreements) framework:

```
Mapping to existing CapabilityAgreement:

  ReservationRequest → CapabilityRequest {
      capability: Relay,
      cost: PerByte { cost_per_byte: max_cost_per_byte },
      desired_duration: valid_for_seconds,
      proof_preference: DeliveryReceipt,
  }

  + Additional fields: estimated_bytes, min_throughput_bps, destination
  + Propagation behavior: auto-forward to next hop (new)
```

The key difference from a regular `CapabilityAgreement` is the **propagation** — the reservation cascades hop-by-hop toward the destination rather than being a single bilateral agreement.

### Onion Routing Interaction

Reservations can be combined with onion routing. When `flags.require_onion` is set:

1. The `ReservationRequest` is onion-encrypted (each hop only sees its layer)
2. Each relay decrypts its layer, learns only: "reserve X bytes toward destination Y at cost Z for my next hop"
3. The commitment propagates back through the same onion layers
4. Data transfer uses per-packet onion encryption with the reserved relays as the circuit

This provides **maximum privacy** but adds 96 bytes overhead per packet and constrains the circuit to the onion-selected relays.

### When to Use Reservations

| Scenario | Recommended | Rationale |
|----------|-------------|-----------|
| Single message / small file (under 100 KB) | Stochastic (default) | Reservation overhead exceeds benefit |
| Voice call | Stochastic + Fastest policy | Low latency matters more than cost predictability |
| File transfer (1 MB to 100 MB) | Either | Reservation is beneficial but not essential |
| Large transfer (over 100 MB) | Reservation | Significant VRF + channel update savings |
| Bulk replication (over 1 GB) | Reservation + LargestMTU | Maximum throughput optimization |
| High-privacy transfer | Reservation + onion | Consistent traffic pattern harder to analyze than bursty stochastic |

**Heuristic**: Applications should default to stochastic relay and switch to reservation when `estimated_transfer_bytes` exceeds 1 MB.

## Gossip Protocol

:::info[Specification]

All protocol-level state propagation uses a common gossip mechanism:

```
GossipRound (every 60 seconds with each neighbor):

1. Exchange state summaries (bloom filters of known state)
2. Identify deltas (what I have that you don't, and vice versa)
3. Exchange deltas (compact, only what's new)
4. Apply received state via CRDT merge rules
```

:::

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

:::caution[Trade-off]

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

:::

### Gossip Congestion Handling

When data traffic consumes most of the available bandwidth, gossip must be protected from starvation while not overwhelming the link:

```
Gossip under congestion — enforcement rules:

  Budget enforcement mechanism:
    Each link maintains a gossip token bucket (separate from user data):
      gossip_bucket {
          capacity: link_bandwidth × 0.10 × window_sec,  // 10% of link BW
          tokens: current available,
          refill_rate: link_bandwidth × 0.10 / 8,         // bytes/sec
          min_guaranteed_rate: max(link_bandwidth × 0.02, 10),  // 2% floor, min 10 bytes/sec
      }

  When gossip exceeds 10% budget:
    1. THROTTLE (not drop): Gossip messages are queued in a dedicated
       gossip queue, separate from user data queues.
    2. Priority within gossip queue:
       Tier 1 (routing) > Tier 2 (economic) > Tier 3 (services) > Tier 4 (social)
       Lower-priority gossip is delayed, not dropped.
    3. If gossip queue exceeds 50 messages: lowest-priority messages
       are dropped (Tier 4 first, then Tier 3).
    4. Tier 1 and Tier 2 gossip are NEVER dropped — only delayed.

  Minimum guaranteed gossip rate:
    Even at 100% data utilization, gossip receives a guaranteed minimum:
      min_gossip_rate = max(link_bandwidth × 0.02, 10 bytes/sec)

    At 1 kbps LoRa: min = 2.5 bytes/sec → ~150 bytes/minute
      Enough for: 1 routing announce per minute (sufficient to maintain
      direct-neighbor routes) + 1 settlement per 2 minutes

    At 50 kbps LoRa: min = 125 bytes/sec → ~7.5 KB/minute
      Enough for: full Tier 1 + Tier 2 gossip

    The minimum is enforced by PREEMPTING user data packets:
      If gossip has been starved for > 3 gossip intervals (3 minutes),
      the next packet slot is reserved for gossip regardless of user
      data queue depth. This prevents gossip starvation indefinitely.

  Starvation detection and recovery:
    If a node receives no gossip updates (DHT, discovery, ledger) for
    > 10 gossip intervals (10 minutes):
      1. Node enters GOSSIP_RECOVERY mode
      2. Gossip budget temporarily increased to 20% of link bandwidth
      3. User data throttled to 80% until gossip state converges
      4. Recovery mode exits after 5 consecutive gossip rounds with
         successful delta exchange

  Priority queue scheduling (gossip vs. user data):
    Gossip and user data share the link via weighted fair queuing:
      gossip_weight = 10 (10% of bandwidth)
      user_data_weight = 90 (90% of bandwidth)
    Under congestion, both are served proportionally.
    The min_guaranteed_rate acts as a strict floor — if weighted fair
    queuing would starve gossip below the floor, gossip preempts.
```

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
                   (~200ms at 1 kbps for negotiated_mtu-byte packets)
  3. Max 7 backoff attempts → drop packet, signal congestion upstream
  4. If channel clear → transmit

  Note: slot_time scales with the link's negotiated MTU — constrained-class
  links (484B) have shorter slot times than standard-class (1,500B) or
  bulk-class (4,096B) links. This is computed automatically from the
  link's bandwidth and negotiated_mtu.
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

<!-- faq-start -->

## Security Considerations

<details className="security-item">
<summary>CompactPathCost Manipulation (Cost Lying)</summary>

**Vulnerability:** A malicious relay inflates or deflates the `cumulative_cost`, `bottleneck_bps`, or `bottleneck_mtu` fields in CompactPathCost when forwarding announces, attracting or repelling traffic.

**Mitigation:** CompactPathCost fields are not individually signed — they rely on link-layer authentication and transitive trust at each hop. The market enforces honesty: relays that inflate costs get routed around (losing revenue), relays that deflate costs attract traffic but lose money on every forwarded packet (revenue below actual relay cost). Persistent misbehavior causes reputation degradation at the next-hop neighbor, which eventually drops the link. This is a trade-off: cryptographic enforcement (per-relay signatures) would cost ~84 bytes per hop — impractical on constrained links.

</details>

<details className="security-item">
<summary>Route Probing and Sender Deanonymization</summary>

**Vulnerability:** A `ProbeRequest` followed shortly by a data transfer to the same destination could allow a relay to infer the sender is the same entity (timing correlation). The `probe_id` field also confirms bidirectional use of the relay chain, reducing the anonymity set.

**Mitigation:** ProbeResponse uses the transport layer's reverse-path routing — each relay only knows its immediate neighbors, not the probe originator. The structural anonymity (no source address) applies equally to probes. For high-threat environments, probes can be wrapped in `PathPolicy.ONION_ROUTE`.

</details>

<details className="security-item">
<summary>Gossip Flooding / State Injection</summary>

**Vulnerability:** A malicious node floods the gossip channel with fabricated announces, routing state, or economic data, consuming bandwidth and potentially corrupting routing tables.

**Mitigation:** Announces are signed by the destination node's Ed25519 key — forgery is impossible. Gossip bandwidth is enforced by the per-link token bucket (10% ceiling) with priority tiers. Fabricated routing state for fake destination hashes wastes routing table entries but not bandwidth beyond the 10% budget. Reputation scoring penalizes peers whose forwarded gossip is consistently invalid. Bloom filter exchange ensures only deltas are transmitted — a node re-sending known state wastes its own gossip budget, not the receiver's.

</details>

<details className="security-item">
<summary>Backpressure Amplification</summary>

**Vulnerability:** A node sends false `CongestionSignal` messages claiming severe congestion, causing upstream peers to reroute traffic. Repeated across multiple honest nodes, this could create traffic oscillations or deny service to a targeted destination.

**Mitigation:** Congestion signals are 1-hop only — they cannot propagate transitively. A lying node only affects its direct neighbors' routing decisions. Persistent false congestion claims cause the neighbor to mark the link as unreliable (reputation penalty) and prefer alternative next-hops permanently. The quadratic cost response (`effective_cost = base_cost × (1 + (queue_depth / queue_capacity)²)`) is based on the relay's own queue measurement, not the peer's claim — the claim only tells neighbors to reduce sending while the cost update propagates via gossip.

</details>

<details className="security-item">
<summary>Announce Replay Attack</summary>

**Vulnerability:** An attacker replays old announces to inject stale routing entries, potentially directing traffic through links that no longer exist or have degraded.

**Mitigation:** Announces carry Lamport timestamps that must be strictly increasing per destination hash. Routing entries expire at `last_updated + announce_interval × 3` (default 90 minutes). An old announce with a lower Lamport timestamp is rejected. An announce with a plausible but stale Lamport timestamp will expire naturally. Link failure detection (3 missed gossip rounds = 3 minutes) quickly marks stale next-hops as down, limiting the impact window.

</details>

<details className="security-item">
<summary>Path MTU Black Hole</summary>

**Vulnerability:** A relay accepts large packets during route probing but silently drops them during actual data transfer, creating a black hole that wastes sender bandwidth and delays delivery.

**Mitigation:** The `PacketTooBig` signal (18 bytes) is the protocol-level response for oversized packets. A relay that drops packets without sending `PacketTooBig` will be detected by the sender when delivery receipts fail. Reputation scoring penalizes drop-without-signal behavior. For reserved traffic, per-chunk `DeliveryReceipt` confirms each megabyte, detecting black holes within one chunk interval.

</details>

<details className="security-item">
<summary>Reservation DoS (Bandwidth Squatting)</summary>

**Vulnerability:** An attacker sends `ReservationRequest` messages to reserve bandwidth along multiple paths, never actually transferring data. This locks up relay capacity and escrow capital, denying service to legitimate users.

**Mitigation:** The 10% escrow floor is **non-refundable** if no data transfers within the first 60 seconds. For a 1 GB reservation at 42 μMHR/byte, the escrow floor is ~4.2 MHR — a meaningful financial cost per attack. Additionally, reservations expire at `valid_until`, and relays track reservation utilization in their reputation scoring. A node that repeatedly reserves but never sends data will have its future reservation requests deprioritized or rejected by relays with experience.

</details>

<details className="security-item">
<summary>Reservation Commitment Deanonymization</summary>

**Vulnerability:** If `ReservationCommitment` included `hop_count`, it would leak path length to the sender, partially deanonymizing the route by revealing how many relays sit between sender and destination.

**Mitigation:** `hop_count` is deliberately excluded from `ReservationCommitment`. The sender learns only the total cost and committed bandwidth — not the path structure. Each relay knows only its immediate upstream and downstream neighbors, consistent with the protocol's sender anonymity guarantees.

</details>

<details className="security-item">
<summary>Relay Underperformance After Reservation</summary>

**Vulnerability:** A relay accepts a reservation (collecting escrow), then deliberately underperforms — delivering packets at a fraction of the committed bandwidth.

**Mitigation:** Per-chunk `DeliveryReceipt` proves delivery of each 1 MB chunk with a timestamp. If chunk delivery rate drops below 50% of `committed_bps` for 3 consecutive chunks, the sender can unilaterally trigger a `ReservationRelease` with `reason: PathFailure`. The underperforming relay's reputation score is penalized, and the sender renegotiates a new reservation for the remaining data. The `allow_reroute` flag, if set, allows a relay on the path to proactively renegotiate through a better route.

</details>

<details className="security-item">
<summary>Probe-to-Reservation Timing Correlation</summary>

**Vulnerability:** A relay observing a `ProbeRequest` immediately followed by a `ReservationRequest` to the same destination can correlate the two and infer the sender is planning a large transfer.

**Mitigation:** Probes and reservations are independent protocol messages. For typical use, the timing correlation adds no new information — the relay already forwards both messages and knows traffic is flowing toward the destination. For high-threat environments: (1) use `ONION_ROUTE` for both probes and reservations, (2) insert a random delay (30–300s) between probe completion and reservation initiation, or (3) skip active probing entirely and rely on passive `bottleneck_mtu`/`bottleneck_bps` from announces.

</details>

<details className="security-item">
<summary>Progressive Escrow Race Condition</summary>

**Vulnerability:** A relay delivers several chunks then goes offline mid-transfer. The sender has paid for chunks already delivered but the relay at the break holds escrow for chunks not yet forwarded downstream. Settlement may be delayed, causing disagreement about how much was actually transferred.

**Mitigation:** Each hop settles independently via its own bilateral payment channel. When a relay goes down, it generates a `ReservationRelease` with `reason: PathFailure` and `bytes_transferred` set to the last confirmed chunk boundary. Upstream and downstream settlements are independent — the sender settles with Neighbor A for bytes actually handed off, and Neighbor A settles with Neighbor B for bytes A forwarded to B. The standard two-phase settlement protocol with 120-gossip-round timeout handles offline counterparties. Unused escrow is refunded during settlement.

</details>

<details className="security-item">
<summary>Escrow Capital Exhaustion</summary>

**Vulnerability:** An attacker with moderate capital opens many small reservations across the network, locking counterparty capital in escrow. Since the 10% escrow is bilateral (each hop escrows with its next hop), the capital lockup cascades through the relay chain.

**Mitigation:** Each relay independently decides whether to accept a reservation based on its available channel balance and current reservation load. A relay at capacity (e.g., 80% of channel balance already escrowed) rejects new reservations, returning `BandwidthInsufficient`. The 60-second inactivity rule (non-refundable escrow if no data within 60s) ensures dormant reservations are expensive. Relays can also set a minimum reservation size to prevent micro-reservation flooding.

</details>

## Frequently Asked Questions

<details className="faq-item">
<summary>How does Mehr addressing work without a central authority?</summary>

Every node generates its own Ed25519 keypair locally and derives a 16-byte destination hash from the public key. This gives each node a self-assigned, pseudonymous address with negligible collision probability across the 2^128 address space. No registrar, DNS, or allocation authority is involved — any device can create an identity and start participating immediately.

</details>

<details className="faq-item">
<summary>Why doesn't the packet header include the sender's address?</summary>

Sender anonymity is structural in Mehr. Packets carry only the destination hash, never the source address. A relay node knows which direct neighbor handed it a packet but cannot determine whether that neighbor originated it or is forwarding it from someone else. This prevents passive traffic analysis from identifying message senders.

</details>

<details className="faq-item">
<summary>How does cost-aware routing scale to large networks?</summary>

Mehr routing is based on the Kleinberg small-world model. Each announce carries a constant 7-byte CompactPathCost summary that relays update in-place as they forward. With O(1) long-range links per node, expected path length is O(log² N) hops. Backbone nodes with O(log N) connections reduce this to O(log N). The scoring function lets applications trade off between cost, latency, reliability, and path MTU using a per-packet PathPolicy.

</details>

<details className="faq-item">
<summary>Why are per-relay signatures on cost annotations unnecessary?</summary>

Routing decisions are local — you only trust your direct neighbor's cost claim, and that neighbor is already authenticated by link-layer encryption. Trust is transitive at each hop (analogous to BGP trusting direct peers), and the market enforces honesty: relays that inflate costs get routed around, while relays that deflate costs lose money on every forwarded packet. This avoids ~84 bytes of signature overhead per relay hop.

</details>

<details className="faq-item">
<summary>Can a node have multiple identities on the network?</summary>

Yes. A single node can generate multiple Ed25519 keypairs, each producing a separate destination hash. This allows a node to maintain distinct identities for different purposes — personal communication, service endpoints, or anonymous identities. Each identity operates independently with its own routing announcements, reputation, and payment channels.

</details>

<details className="faq-item">
<summary>How does gossip avoid overwhelming low-bandwidth LoRa links?</summary>

The protocol automatically adapts to constrained links (below 10 kbps). Tiers 3–4 (services, trust/social) switch to pull-only mode, payment batching intervals increase from 60 seconds to 5 minutes, and capability advertisements are limited to direct neighbors only. Total protocol overhead on a 1 kbps LoRa link is approximately 2% of bandwidth — well below the 10% ceiling.

</details>

<details className="faq-item">
<summary>What happens if gossip is starved by heavy user data traffic?</summary>

A minimum guaranteed gossip rate is enforced: at least 2% of link bandwidth (or 10 bytes/sec, whichever is greater) is reserved for gossip. If gossip has been starved for more than 3 gossip intervals (3 minutes), the next packet slot is preemptively reserved for gossip. If starvation persists beyond 10 minutes, the node enters GOSSIP_RECOVERY mode, temporarily increasing the gossip budget to 20% until state converges.

</details>

<details className="faq-item">
<summary>How does congestion on one link affect routing across the mesh?</summary>

When a link's queue depth exceeds 50%, the effective cost increases quadratically: `effective_cost = base_cost × (1 + (queue_depth / queue_capacity)²)`. This updated cost propagates in the next gossip round's CompactPathCost, causing upstream nodes to naturally reroute traffic to less-congested paths. Additionally, a 3-byte backpressure signal is sent to direct upstream neighbors, telling them to reduce sending rate.

</details>

<details className="faq-item">
<summary>Does Mehr require synchronized clocks across the network?</summary>

No. Mehr uses three time mechanisms that avoid global clock synchronization: Lamport timestamps (logical clocks) for event ordering, neighbor-relative time (clock offsets exchanged during link establishment) for local agreement expiry, and epoch-relative time where "weekly" epochs are defined by settlement count (~10,000 batches), not wall-clock time. All timestamp fields use each node's local monotonic clock.

</details>

<details className="faq-item">
<summary>How does the priority queuing system prevent voice traffic from being delayed?</summary>

Voice traffic is assigned priority P0 (real-time), the highest level, with a strict 500ms tail-drop deadline. The scheduler uses strict priority ordering — P0 packets are always sent before P1/P2/P3 traffic. To prevent starvation of lower priorities, P3 (bulk) is guaranteed at least 10% of user bandwidth. On half-duplex links, preemption occurs only at packet boundaries.

</details>

<details className="faq-item">
<summary>How do variable packet sizes work across different transports?</summary>

Mehr defines three transport classes: Constrained (484 bytes, for LoRa/NB-IoT), Standard (1,500 bytes, for WiFi/BLE/cellular), and Bulk (4,096 bytes, for Ethernet/fiber/TCP). During link establishment, both nodes exchange their interface MTU and negotiate the link's maximum packet size. The `bottleneck_mtu` field in CompactPathCost (carried in every announce) reports the minimum MTU across the entire path. Senders size packets to match the path MTU — no change for paths with a LoRa hop (still 484 bytes), but 3× improvement on pure WiFi paths and 8.5× on Ethernet/fiber. Applications can also request MTU-aware routing via the `LargestMTU` PathPolicy or specify a `min_mtu` requirement to filter routes.

</details>

<details className="faq-item">
<summary>Can I probe a route to check its bandwidth and maximum packet size?</summary>

Yes. Path bandwidth (`bottleneck_bps`) and MTU (`bottleneck_mtu`) are available passively from routing announces — every node knows these for every known destination with zero additional overhead. For real-time measurements (actual RTT and throughput), applications can send opt-in ProbeRequest packets that measure round-trip time and verify the actual path MTU. Active probing is rate-limited to 1 probe/minute per destination and only available on links above 10 kbps to avoid wasting LoRa airtime.

</details>

<details className="faq-item">
<summary>Does the sender need to know the full path to make a bandwidth reservation?</summary>

No. Reservations propagate hop-by-hop — the sender negotiates only with its direct neighbor, who independently negotiates with the next hop, and so on. The sender never learns which relays are on the path or how many hops exist. This preserves the same sender anonymity as regular packet forwarding.

</details>

<details className="faq-item">
<summary>What happens if a relay on the reserved path goes offline mid-transfer?</summary>

The relay at the break generates a `ReservationRelease` with `reason: PathFailure`. This propagates back to the sender via reverse-path routing. The sender settles with its neighbor for bytes actually transferred, then negotiates a new reservation for the remaining data. Each hop settles independently — no multi-hop coordination needed.

</details>

<details className="faq-item">
<summary>Why not just prepay the full amount upfront for a reservation?</summary>

Full prepayment creates a bad incentive: a relay that has already been paid has no financial motivation to prioritize the sender's traffic. Progressive escrow (10% upfront, per-chunk payment) aligns incentives throughout the transfer. If the relay underperforms or goes offline, the sender has only paid for data actually delivered plus a small escrow floor.

</details>

<details className="faq-item">
<summary>Can bandwidth reservations work over LoRa?</summary>

The reservation overhead itself is small (43 bytes for `ReservationRequest`), so the negotiation fits on LoRa. However, bulk transfers over LoRa are impractical — a 1 GB transfer at 1 kbps would take ~93 days. In practice, reservations are useful when the data path crosses Standard or Bulk transport classes (WiFi, Ethernet, fiber). If the path includes a LoRa hop, the `bottleneck_mtu` and `bottleneck_bps` from announces already indicate the constraint, and applications should use standard stochastic relay for small payloads sized to the path.

</details>

<details className="faq-item">
<summary>How do bandwidth reservations interact with onion routing?</summary>

When `flags.require_onion` is set on the `ReservationRequest`, the reservation and all subsequent data transfer use per-packet onion encryption. Each relay decrypts only its layer and learns only "reserve/transfer X bytes toward destination Y for my next hop." The reservation commitment propagates back through the same onion layers. This provides maximum privacy but adds 96 bytes overhead per data packet and constrains the circuit to the onion-selected relays.

</details>

<details className="faq-item">
<summary>Do relays still earn the 2% service burn during reservations?</summary>

Yes. The 2% service burn applies uniformly to all funded-channel payments — including per-chunk deterministic payments during a reservation. For example, a 1 MB chunk at 42 μMHR/byte costs 42 MHR per chunk, of which 0.84 MHR is burned and 41.16 MHR goes to the relay. The deflationary mechanism works identically to stochastic relay rewards.

</details>

<!-- faq-end -->

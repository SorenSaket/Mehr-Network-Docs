---
sidebar_position: 3
title: Open Questions
---

# Open Questions

These are known unsolved problems in the NEXUS design. Each requires further research, prototyping, or real-world testing to resolve.

## 1. Handoff Protocol

**Problem**: When a mobile node moves between areas, its capability agreements with local nodes become invalid. The node needs to quickly establish new agreements with nodes in its new location.

**Analogous to**: Cellular network handoff, but decentralized.

**Considerations**:
- Pre-negotiation with nodes in adjacent areas (if movement is predictable)
- Grace periods on existing agreements
- Fast capability discovery for mobile nodes
- Payment channel migration or rapid new channel establishment

**Priority**: Required before mobile phone use case ships.

## 2. Price Discovery

**Problem**: How does a new node determine fair prices for capabilities?

**Possible approaches**:
- Observing neighbor pricing through gossip (most natural approach)
- Historical price tracking in the DHT
- Community-label-scoped price indices (nodes with the same label share reference prices)
- Pure market discovery through trial and error

**Tension**: Decentralized price discovery is robust but slow for new participants. Neighborhood gossip provides a natural middle ground — you learn prices from trusted peers.

## 3. Recursive Delegation Depth

**Problem**: Capability chains (A → B → C → D) increase latency with each hop. Long chains also increase the total cost.

**Considerations**:
- Hard depth limit (e.g., max 3 delegation hops)
- Short-circuit mechanism (A discovers D directly and forms a direct agreement)
- Cost transparency (each delegation adds visible cost, so the market naturally limits depth)
- Latency budgets (applications specify maximum acceptable latency)

## 4. CRDT Ledger Size at Scale

**Problem**: With 1M+ nodes, the epoch `account_snapshot` is a flat `Map<NodeID, (total_earned, total_spent)>` — at ~32 bytes per entry, this is ~32 MB for 1M nodes. Unworkable for constrained devices.

**Possible solutions**:
- Neighborhood-level summarization (trust neighborhoods produce local snapshots that compose into global state)
- Sparse representation (only store balances for nodes you interact with)
- Sharded epochs (different nodes responsible for different balance ranges)
- Pruning inactive accounts after extended inactivity

**Priority**: Not blocking for initial deployment (< 100K nodes), but must be solved before scaling beyond that.

## 5. Radio Regulatory Compliance

**Problem**: LoRa operates in ISM bands (unlicensed), but many jurisdictions prohibit encryption on amateur radio bands. NEXUS requires encryption.

**Constraint**: NEXUS must use ISM-band LoRa (lower power, shorter range than amateur allocations).

**Critical implication**: EU ISM bands impose a **1% duty cycle** on some sub-bands. At 1 kbps raw, this limits effective throughput to ~10 bps average. This severely undercuts gossip and payment overhead calculations. Possible mitigations:
- Use EU bands without duty cycle restrictions (e.g., 869.4–869.65 MHz at 10% duty cycle)
- Adaptive duty cycle management per jurisdiction
- Accept that EU LoRa nodes operate in a reduced-capability mode

**Priority**: Must be resolved before European deployment.

## 6. Stochastic Reward Variance

**Problem**: With low-traffic links, the variance between expected and actual relay income can be high. A relay handling only 5 packets/hour with 1/100 win probability may go days without a reward.

**Mitigations under consideration**:
- Adaptive difficulty (already specified — low-traffic links use 1/10 probability with smaller rewards)
- Reward smoothing across longer time windows
- Minimum guaranteed income thresholds for committed relays
- Is the current adaptive difficulty sufficient, or do we need additional mechanisms?

**Priority**: Needs simulation data from real-world traffic patterns.

## 7. Popular Content Economics

**Problem**: A viral post causes storage and bandwidth costs on relay nodes that didn't create or request the content. Who pays?

**Possible mechanisms**:
- Author-funded replication (author pays for N copies)
- Consumer-funded (each consumer pays for their own retrieval)
- Neighborhood-subsidized (trusted peers fund storage of popular local content)
- Natural caching reduces cost over time (popular content ends up cached everywhere)

## 8. Light Client Trust

**Problem**: A phone delegating DHT lookups to a nearby node trusts that node's responses. A malicious node could return false results.

**Possible mitigations**:
- Merkle proofs (verifiable subset of DHT state)
- SPV-style verification (verify against known state roots)
- Multi-node queries (ask multiple nodes, compare responses)
- Reputation-weighted trust (prefer responses from high-reputation nodes)

**Priority**: Required before mobile phone use case ships — phones are inherently light clients.

## 9. DHT Algorithm Formalization

**Problem**: The DHT is described as "proximity-weighted gossip considering both XOR distance and actual network cost" but no weighting formula, routing algorithm, or replication factor is specified. Not implementable as written.

**Needed**:
- Formal weighting function for XOR distance vs. network cost
- Replication factor and storage responsibility assignment
- Rebalancing behavior as nodes join/leave
- Cache TTL interaction with object TTL

## 10. NXS-Byte Instruction Set

**Problem**: NXS-Byte is a core protocol primitive ("~50 KB interpreter") but no instruction set, opcode table, or operational semantics are defined.

**Needed**:
- Complete ISA specification
- Cycle counting model (for cost_per_cycle pricing)
- Determinism guarantees
- Security sandbox boundaries

**Priority**: Required before Phase 3 (NXS-Compute).

## 11. Trust Graph Privacy

**Problem**: A node's trust list is used for relay decisions (free vs. paid), which means relay nodes can infer trust relationships by observing which traffic is relayed for free. This leaks social graph information.

**Possible mitigations**:
- Encrypt trust decisions (relay node knows "relay for free" but not "because sender is trusted")
- Batch free and paid traffic together with delayed settlement
- Probabilistic trust relay (sometimes charge trusted peers, sometimes don't, to add noise)

**Priority**: Important for high-threat environments. Acceptable tradeoff for community meshes.

## 12. Reticulum Interoperability Boundary

**Problem**: NEXUS builds on Reticulum's transport and identity layers but adds economic extensions (cost annotations, payment channels). Where exactly is the boundary? Can a pure Reticulum node participate in a NEXUS mesh?

**Considerations**:
- Pure Reticulum nodes could relay NEXUS packets without understanding economic extensions
- Economic metadata could be carried as opaque annotations that Reticulum ignores
- Risk of fragmentation if the two communities diverge
- Reticulum's planned Rust implementation may affect NEXUS's implementation strategy

**Priority**: Architectural decision needed before Phase 1 implementation.

## 13. Private Compute Overhead on Mesh

**Status**: Design direction established — [private compute](../services/nxs-compute#private-compute-optional) is opt-in with four tiers (None, Split Inference, Secret Shared, TEE).

**Remaining questions**:
- What is the practical overhead of Tier 2 (secret-shared computation via 3-node quorum) on Gateway-tier hardware? Needs benchmarking.
- For split inference (Tier 1): what are optimal cut points for common models (Whisper, LLaMA, Stable Diffusion) on Raspberry Pi + GPU node topology?
- How does the differential privacy noise budget accumulate across multiple queries to the same compute provider? A consumer making repeated queries to the same Inference node leaks progressively more information through the aggregate of DP-noised activations.
- Can MPC be practical for any real workload on a mesh with >50ms inter-node latency? Multiplication gates require communication rounds — deep circuits may be prohibitively slow.

**Priority**: Benchmarking needed during Phase 3. The tiered opt-in design means this doesn't block deployment — consumers use Tier 0 (no privacy) by default and opt into higher tiers as they become practical.

## 14. Congestion Control

**Problem**: The spec has no congestion control mechanism for user data. On a shared LoRa link with multiple nodes, what prevents saturation? The [gossip bandwidth budget](../protocol/network-protocol#bandwidth-budget) provides static allocations for protocol overhead, but user data has no admission control, backpressure, or fairness mechanism. This is especially critical on half-duplex LoRa links where collisions waste the entire transmission time.

**Considerations**:
- CSMA/CA-style collision avoidance at the link layer (LoRa already has CAD — Channel Activity Detection)
- Per-neighbor token bucket or leaky bucket rate limiting
- Priority queuing (voice > messaging > bulk transfer) with preemption
- Backpressure signals propagated upstream when a link is congested
- Interaction with the economic layer — congested links should increase cost_per_byte dynamically to signal scarcity

**Priority**: Required before Phase 1. Without this, a LoRa mesh with >5 active nodes will experience frequent collisions and degraded throughput.

## 15. Gossip Honesty Incentive

**Problem**: A relay node that learns of a cheaper route through its neighbor has an incentive to **withhold** that routing announcement from gossip, keeping traffic flowing through itself to earn more relay fees. There is no mechanism to ensure nodes forward routing announcements honestly.

**Possible mitigations**:
- Redundant announcement propagation — announcements flood via multiple paths, making suppression by a single node ineffective
- Cross-checking — if a node consistently advertises itself as the best route to a destination that other nodes can reach more cheaply, this is detectable by neighbors
- Reputation penalty for nodes whose cost claims diverge significantly from empirically measured costs
- Accept as an inherent limitation — Reticulum's announce flooding already provides redundancy, and cost-weighted routing routes around overpriced nodes naturally

**Priority**: Needs analysis. May be acceptable if Reticulum's existing announce propagation provides sufficient redundancy.

## 16. Epoch Timing in Small Partitions

**Problem**: Epochs trigger at ~10,000 settlement batches. A small partition (e.g., a 20-node village on LoRa) with low transaction volume might take **months** to reach 10,000 settlements. During this time, the settlement GSet grows without bound. Constrained devices (ESP32) will run out of memory long before an epoch triggers.

**Possible solutions**:
- **Secondary trigger**: Add a GSet size threshold (e.g., compact when the GSet exceeds 500 KB regardless of settlement count)
- **Minimum epoch frequency**: Force an epoch after N gossip rounds even with fewer than 10,000 settlements, with reduced acknowledgment requirements for small partitions
- **Partition-aware compaction**: Small partitions (< 50 known nodes) use a lower settlement threshold (e.g., 500 settlements)
- **LoRa node delegation**: LoRa nodes already delegate epoch participation to high-bandwidth peers; ensure this covers GSet storage too

**Priority**: Required before Phase 2. Any deployment with constrained devices will encounter this within weeks.

## 17. Community Label Spoofing

**Problem**: Community labels are self-assigned and non-unique. [NXS-Name](../applications/naming) resolution finds the "nearest" cluster with a given label. An attacker could set `community_label = "portland-mesh"` on nodes physically near a target, becoming the "nearest" resolver and hijacking name resolution for that community.

**Possible mitigations**:
- Trust-weighted name resolution — prefer responses from nodes in your trust graph over random nearby nodes
- Multi-source verification — resolve names against multiple clusters with the same label and flag divergence
- Signed community label attestation — existing members of a community sign each other's label claims, creating a web of trust around the label
- Accept as inherent limitation — petnames as fallback, and users learn their community's real nodes through out-of-band channels

**Priority**: Should be addressed before Phase 3 (NXS-Name deployment). Not a Phase 1 blocker since naming isn't needed for basic mesh operation.

## 18. Gossip Budget Feasibility on LoRa

**Problem**: On a 1 kbps LoRa link, Tier 1 routing gets 3% = 30 bps = ~3.75 bytes/sec. A single `CostAnnotation` is ~40+ bytes (u64 + u32 + u64 + 64-byte signature). That allows roughly **1 routing announcement per 10+ seconds**. For a mesh with 50+ destinations, route convergence could take 10+ minutes after any topology change.

**Needed**:
- Back-of-envelope validation that the budget works for realistic mesh sizes (20, 50, 100, 500 nodes)
- Worst-case convergence time analysis after a topology change
- Whether the constrained-link adaptations (pull-only for Tiers 3-4) are sufficient, or whether Tier 1 also needs pull-only mode on the most constrained links
- Compact announcement encoding — can CostAnnotations be compressed below 40 bytes?

**Priority**: Required before Phase 1. If the budget doesn't work at realistic mesh sizes, the gossip protocol needs fundamental redesign for constrained links.

## 19. NXS-Byte Floating-Point Determinism

**Problem**: [NXS-Compute](../services/nxs-compute) claims "pure deterministic computation" — given the same inputs, any node produces the same output. If NXS-Byte includes any floating-point operations, this is extremely difficult to guarantee across different hardware (ESP32 FPU, ARM, x86). Different FPUs handle rounding, denormals, NaN propagation, and fused multiply-add differently.

**Options**:
- **Exclude floating-point entirely** — NXS-Byte uses only integer and fixed-point arithmetic. Simplest and most reliable for determinism.
- **Software floating-point** — Specify exact soft-float semantics (e.g., IEEE 754 with round-to-nearest-even, no FMA). Slower but deterministic.
- **Restricted floating-point** — Allow hardware FP but constrain to a deterministic subset (e.g., no denormals, strict ordering). Fragile across architectures.

**Priority**: Must be decided before the NXS-Byte ISA is specified (Open Question #10). Integer-only is the safe default.

## 20. Erasure Coding Coordination Overhead

**Problem**: Distributing erasure-coded shards requires finding and negotiating with 3-12 storage nodes across different trust neighborhoods. For a constrained device (phone, ESP32), this is a significant coordination burden — each shard requires capability discovery, agreement negotiation, and channel establishment with a separate node.

**Considerations**:
- The [RepairAgent](../services/nxs-store#automated-repair) helps but is itself an NXS-Compute contract requiring a capable host node — chicken-and-egg for initial storage
- A "storage broker" capability could bundle shard distribution as a service — you give one node the data and payment, it handles distribution and maintenance
- Simplified schemes for constrained devices: just replicate to 2-3 trusted peers (no erasure coding) and upgrade to erasure coding when a capable node is available
- Default to simple replication within trust neighborhoods; erasure coding is an optimization for cross-neighborhood durability

**Priority**: Phase 2. The protocol works with simple replication; erasure coding is an optimization that can be added later.

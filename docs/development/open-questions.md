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

---
sidebar_position: 4
title: Verification
description: "Verification methods for marketplace capabilities including delivery receipts, Merkle proofs, and challenge-response protocols."
keywords:
  - verification
  - delivery receipts
  - Merkle proof
  - storage proof
  - challenge-response
---

# Verification

The capability marketplace requires that consumers can verify providers are actually delivering the agreed service. Mehr uses different verification methods depending on the type of capability.

## Relay / Bandwidth Verification

**Method**: Cryptographic delivery receipts

The destination node signs a receipt proving the packet arrived. The relay chain can prove it delivered. This creates an unforgeable chain of evidence:

```
Packet sent by Alice → relayed by Bob → relayed by Carol → received by Dave

Dave signs: Receipt(packet_hash, timestamp)
Carol proves: "I forwarded to Dave, here's Dave's receipt"
Bob proves: "I forwarded to Carol, here's the chain"
```

A relay node can only earn routing fees by actually delivering packets to their destination.

:::danger[Threat]
Delivery receipts prove delivery, not legitimacy. A Sybil attacker can fabricate traffic between colluding nodes and produce valid receipts. Economic defenses (demand-backed minting, revenue-capped minting) make this self-dealing structurally unprofitable.
:::

**Note**: Delivery receipts prove that packets were delivered, not that the traffic represents legitimate demand. A Sybil attacker can fabricate traffic between colluding nodes and produce valid delivery receipts. The economic defense against this is [demand-backed minting](/docs/L3-economics/payment-channels#demand-backed-minting-eligibility) — VRF wins only count for minting if the packet traversed a funded payment channel, and [revenue-capped minting](/docs/L3-economics/payment-channels#revenue-capped-minting) ensures self-dealing is always unprofitable.

## Storage Verification

**Method**: Merkle-proof challenge-response (see [MHR-Store](/docs/L5-services/mhr-store#proof-of-storage) for full details)

The consumer challenges a random chunk and the provider returns a Blake3 hash plus a Merkle proof:

```
Challenge-Response Protocol:
1. At storage time, consumer builds a Merkle tree over 4 KB chunks
   and stores only the merkle_root locally
2. Periodically, consumer sends:
   Challenge(data_hash, random_chunk_index, nonce)
3. Provider responds:
   Proof(Blake3(chunk_data || nonce), merkle_siblings)
4. Consumer recomputes merkle root from proof — if it matches, data is verified
```

This is:
- **Lightweight**: Runs on ESP32 in under 10ms — no GPU, no heavy crypto
- **Nonce-protected**: The random nonce prevents pre-computation of responses
- **Merkle-verified**: Consumer only stores the root hash, not the full data
- **Bandwidth-efficient**: ~320 bytes per proof (for a 1 MB file)
- **Partition-safe**: Works between any two directly connected nodes, no chain needed

Three consecutive failed challenges trigger [repair](/docs/L5-services/mhr-store#repair) — the consumer reconstructs the lost shard from erasure-coded replicas and stores it on a replacement node.

## Compute Verification

Compute verification uses three tiers, scaled to the stakes involved:

### Tier 1: Reputation Trust (Cheapest)

Accept the result. The provider has no incentive to lie — getting caught destroys their reputation and all future income.

**Use for**: Low-stakes operations where the cost of a wrong answer is low.

### Tier 2: Optimistic Verification (Moderate)

Accept the result but randomly re-execute 1-in-N requests on a different node. Divergent results flag the provider for investigation.

```
Optimistic Verification:
1. Send compute request to Provider A
2. Accept result immediately
3. With probability 1/N, also send same request to Provider B
4. Compare results
5. If divergent: flag Provider A, reduce reputation
```

**Use for**: Medium-stakes operations. The random audit probability can be tuned — higher for newer/less-trusted providers, lower for established ones.

### Tier 3: Redundant Execution (Expensive)

Send the same request to K independent nodes. The majority result wins.

```
Redundant Execution:
1. Send compute request to K nodes (e.g., K=3)
2. Collect results
3. Majority wins (2 of 3 agree)
4. Dissenting node is flagged
```

**Use for**: High-stakes operations where the result affects payments or irreversible state changes.

:::tip[Key Insight]
Compute verification is tiered by stakes, not by capability. Most operations use optimistic verification (accept then spot-check), keeping costs near 1x while maintaining deterrence through random audits. Only payment-affecting computation requires expensive redundant execution.
:::

## Verification Cost Tradeoffs

| Tier | Cost | Latency | Trust Required | Use Case |
|------|------|---------|---------------|----------|
| Reputation | 1x | 1x | High | Cheap, frequent ops |
| Optimistic | ~1.1x | 1x | Moderate | Default for most compute |
| Redundant | Kx | ~1x (parallel) | Minimal | Payment-affecting compute |

## Heartbeat Verification

For ongoing services (internet gateway, persistent connections), a simple heartbeat mechanism verifies continued availability:

```
Heartbeat Protocol:
1. Consumer sends periodic ping (every N seconds)
2. Provider responds with signed pong
3. If M consecutive heartbeats are missed: agreement terminated
4. Payment stops when heartbeats stop
```

This is suitable for services where the consumer can directly observe whether the service is working (e.g., "I can reach the internet through this gateway").

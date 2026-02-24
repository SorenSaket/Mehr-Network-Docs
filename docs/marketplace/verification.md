---
sidebar_position: 4
title: Verification
---

# Verification

The capability marketplace requires that consumers can verify providers are actually delivering the agreed service. NEXUS uses different verification methods depending on the type of capability.

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

## Storage Verification

**Method**: Periodic challenge-response

The consumer picks a random offset in the stored data and asks the provider to return the hash of bytes at that offset:

```
Challenge-Response Protocol:
1. Consumer stores data with provider
2. Periodically, consumer sends: Challenge(random_offset, chunk_size)
3. Provider responds: Response(hash_of_bytes_at_offset)
4. Consumer verifies against their local record of the data
```

This is:
- **Pre-computable**: Consumer can pre-compute expected hashes at multiple offsets
- **Cheap to verify**: Only a hash comparison
- **Hard to fake**: Provider must actually have the data to produce correct hashes
- **Bandwidth-efficient**: Only hashes are exchanged, not the actual data

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

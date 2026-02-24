---
sidebar_position: 2
title: Stochastic Relay Rewards
---

# Stochastic Relay Rewards

Relay nodes are compensated through **probabilistic micropayments** rather than per-packet accounting. This dramatically reduces payment overhead on constrained radio links while providing the same expected income over time.

## Why Not Per-Packet Payment?

Per-packet payment requires a channel state update for every batch of relayed packets. Even batched, this consumes significant bandwidth on LoRa links. The insight: relay rewards don't need to be deterministic — they can be probabilistic, like mining, achieving the same expected value with far less overhead.

## How Stochastic Rewards Work

Each relayed packet is checked against a **VRF-based lottery**. The relay computes a Verifiable Random Function output over the packet, producing a deterministic but unpredictable result that anyone can verify:

```
Relay reward lottery (VRF-based):
  1. Relay computes: (vrf_output, vrf_proof) = VRF_prove(relay_private_key, packet_hash)
  2. Check: vrf_output < difficulty_target
  3. If win: reward = per_packet_cost × (1 / win_probability)
  4. Expected value per packet = reward × probability = per_packet_cost ✓
  5. Verification: VRF_verify(relay_public_key, packet_hash, vrf_output, vrf_proof)
```

**Why VRF, not a random nonce?** If the relay chose its own nonce, it could grind through values until it found a winner for every packet, extracting the maximum reward every time. The VRF produces exactly **one valid output** per (relay key, packet) pair — the relay cannot influence the lottery outcome. The proof lets any party verify the result without the relay's private key.

The VRF used is **ECVRF-ED25519-SHA512-TAI** ([RFC 9381](https://www.rfc-editor.org/rfc/rfc9381)), which reuses the relay's existing Ed25519 keypair. VRF proof size is 80 bytes, included only in winning lottery claims (not in every packet).

### Example

| Parameter | Value |
|-----------|-------|
| Per-packet relay cost | 5 μNXS |
| Win probability | 1/100 |
| Reward per win | 500 μNXS |
| Expected value per packet | 5 μNXS (same) |
| Channel updates needed | 1 per ~100 packets (vs. every batch) |

A relay handling 10 packets/minute triggers a channel update approximately once every 10 minutes — a **10x reduction** in payment overhead compared to per-minute batching.

### Adaptive Difficulty

The win probability adjusts based on traffic volume:

```
Difficulty adjustment:
  High-traffic links (>100 packets/min):   1/1000 probability, larger rewards
  Medium-traffic links (10-100 packets/min): 1/100 probability
  Low-traffic links (<10 packets/min):     1/10 probability, smaller rewards

  Adjusted so channel updates happen roughly every 5-15 minutes
  regardless of traffic level.
```

Low-traffic links use higher win probability to reduce variance — a relay handling only a few packets per hour will still receive rewards regularly.

## Bilateral Payment Channels

Rewards are settled through bilateral channels between direct neighbors. Unlike Lightning-style multi-hop payment routing, NEXUS uses simple per-hop channels:

- Only two parties need to coordinate
- Both parties are direct neighbors (by definition)
- No global coordination needed

### Channel State

```
ChannelState {
    channel_id: [u8; 16],       // truncated Blake3 hash (16 bytes)
    party_a: [u8; 16],          // destination hash (16 bytes)
    party_b: [u8; 16],          // destination hash (16 bytes)
    balance_a: u64,             // party A's current balance (8 bytes)
    balance_b: u64,             // party B's current balance (8 bytes)
    sequence: u64,              // monotonically increasing (8 bytes)
    sig_a: Ed25519Signature,    // party A's signature (64 bytes)
    sig_b: Ed25519Signature,    // party B's signature (64 bytes)
}
// Total: 16 + 16 + 16 + 8 + 8 + 8 + 64 + 64 = 200 bytes
```

### Channel Lifecycle

1. **Open**: Both parties agree on initial balances. Both sign the opening state.
2. **Update**: On each lottery win, the balance shifts by the reward amount. Channel updates are infrequent — only triggered by wins.
3. **Settle**: Either party can request settlement. Both sign a `SettlementRecord` that is gossiped to the network and applied to the [CRDT ledger](crdt-ledger).
4. **Dispute**: If one party submits an old state, the counterparty can submit a higher-sequence state within a **48-hour challenge window** (~7 settlement batches). The higher sequence always wins.
5. **Abandonment**: If a channel has no updates for **4 epochs** (~30 days), either party can unilaterally close with the last mutually-signed state. This prevents permanent fund lockup.

## Multi-Hop Payment

When Alice sends a packet through Bob → Carol → Dave, each relay independently runs the VRF lottery:

```
Alice ──→ Bob ──→ Carol ──→ Dave
           │        │
        lottery?  lottery?
```

A lottery win triggers compensation through one or both mechanisms:

1. **Channel debit** (if a channel exists with the upstream sender): Bob's win debits Alice's channel with Bob; Carol's win debits Bob's channel with Carol. This is the steady-state mechanism once NXS is circulating.
2. **Mining proof** (always): The VRF proof is accumulated as a service proof entitling the relay to a share of the epoch's [minting reward](nxs-token#proof-of-service-mining-nxs-genesis). This is the dominant income source during bootstrap and provides a baseline subsidy that decays over time.

Most packets trigger no channel update at all. Each hop is independent — no end-to-end payment coordination.

## Efficiency on Constrained Links

| Metric | Value |
|--------|-------|
| State update size | 200 bytes |
| Average updates per hour (1/100 prob, 10 pkts/min) | ~6 |
| Bandwidth overhead at 1 kbps LoRa | ~0.3% |
| Compared to per-minute batching | **~8x reduction** |

The stochastic model fits within [Tier 2 (economic)](../protocol/network-protocol#bandwidth-budget) of the gossip bandwidth budget even on the most constrained links.

## Trusted Peers: Free Relay

Nodes relay traffic for [trusted peers](community-zones) for free — no lottery, no channel updates. The stochastic reward system only activates for traffic between non-trusted nodes. This mirrors the real world: you help your neighbors for free, but charge strangers for using your infrastructure.

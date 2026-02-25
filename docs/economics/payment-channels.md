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
| Per-packet relay cost | 5 μMHR |
| Win probability | 1/100 |
| Reward per win | 500 μMHR |
| Expected value per packet | 5 μMHR (same) |
| Channel updates needed | 1 per ~100 packets (vs. every batch) |

A relay handling 10 packets/minute triggers a channel update approximately once every 10 minutes — a **10x reduction** in payment overhead compared to per-minute batching.

### Adaptive Difficulty

The win probability adjusts based on traffic volume. Each relay computes its own difficulty locally based on its observed traffic rate — no global synchronization needed:

```
Difficulty adjustment:
  target_updates_per_minute = 0.1  (one channel update per ~10 minutes)
  observed_packets_per_minute = trailing 5-minute moving average

  win_probability = target_updates_per_minute / observed_packets_per_minute
  win_probability = clamp(win_probability, 1/10000, 1/5)  // bounds

  difficulty_target = MAX_VRF_OUTPUT × win_probability

Traffic tiers (approximate):
  High-traffic links (>100 packets/min):   ~1/1000 probability, larger rewards
  Medium-traffic links (10-100 packets/min): ~1/100 probability
  Low-traffic links (<10 packets/min):     ~1/10 probability, smaller rewards

  Reward on win = per_packet_cost × (1 / win_probability)
  Expected value per packet = per_packet_cost (always, regardless of difficulty)
```

Low-traffic links use higher win probability to reduce variance — a relay handling only a few packets per hour will still receive rewards regularly. The difficulty is computed independently by each relay per-link, so different links on the same node may have different difficulties.

## Bilateral Payment Channels

Rewards are settled through bilateral channels between direct neighbors. Unlike Lightning-style multi-hop payment routing, Mehr uses simple per-hop channels:

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

1. **Open**: Both parties agree on initial balances. Both sign the opening state (`sequence = 0`).
2. **Update**: On each lottery win, the balance shifts by the reward amount and `sequence` increments by 1. Both parties sign the updated state. Channel updates are infrequent — only triggered by wins.
3. **Settle**: Either party can request settlement. Both sign a `SettlementRecord` whose `final_sequence` matches the current channel `sequence`. The record is gossiped to the network and applied to the [CRDT ledger](crdt-ledger). The channel remains open after settlement — subsequent lottery wins continue from the settled point.
4. **Dispute**: If one party submits an old state, the counterparty can submit a higher-sequence state within a **2,880 gossip round challenge window** (~48 hours at 60-second rounds). The higher sequence always wins.
5. **Abandonment**: If a channel has no updates for **4 epochs**, either party can unilaterally close with the last mutually-signed state. This prevents permanent fund lockup.

### Settlement Timing

Lottery wins accumulate as local channel state updates (balance shifts + sequence increments). Settlements to the CRDT ledger are **not** created per-win — they are created when either party decides to finalize:

```
Settlement triggers:
  - Either party requests cooperative settlement
  - Channel dispute (one party publishes an old state)
  - Channel abandonment (4 epochs of inactivity)
  - Periodic finalization (recommended: once per epoch)

Between settlements, interim balances are NOT gossiped.
Only the two parties track the current ChannelState locally.
```

This preserves the stochastic lottery's bandwidth savings: a relay handling 10 packets/minute triggers ~6 local channel updates per hour, but settlements to the CRDT ledger happen much less frequently.

### Sequence Number Semantics

The `sequence` field is a monotonically increasing version number:

- Each update increments `sequence` by 1; both parties must sign the same sequence
- A `SettlementRecord` references `final_sequence` — the sequence of the state being settled
- After settlement, the channel continues with `sequence > final_sequence`
- Dispute resolution: higher `sequence` always wins, regardless of settlement history
- Replay protection: the CRDT ledger rejects settlements where `final_sequence` is not greater than the last settled sequence for the same `channel_id`

## Multi-Hop Payment

When Alice sends a packet through Bob → Carol → Dave, each relay independently runs the VRF lottery:

```
Alice ──→ Bob ──→ Carol ──→ Dave
           │        │
        lottery?  lottery?
```

A lottery win triggers compensation through one or both mechanisms:

1. **Channel debit** (if a channel exists with the upstream sender): Bob's win debits Alice's channel with Bob; Carol's win debits Bob's channel with Carol. This is the steady-state mechanism once MHR is circulating.
2. **Mining proof** (always): The VRF proof is accumulated as a service proof entitling the relay to a share of the epoch's [minting reward](mhr-token#proof-of-service-mining-mhr-genesis). This is the dominant income source during bootstrap and provides a baseline subsidy that decays over time.

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

Nodes relay traffic for [trusted peers](trust-neighborhoods) for free — no lottery, no channel updates. The stochastic reward system only activates for traffic between non-trusted nodes. This mirrors the real world: you help your neighbors for free, but charge strangers for using your infrastructure.

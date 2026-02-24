---
sidebar_position: 1
title: NXS Token
---

# NXS Token

NXS is the unit of account for the NEXUS network. It is not a speculative asset — it is the internal currency for purchasing capabilities from nodes outside your trust network.

## Properties

```
NXS Properties:
  Smallest unit: 1 μNXS (micro-NXS)
  Initial distribution: Proof-of-service mining only (no ICO, no pre-mine)
  Total supply cap: 2^64 μNXS (~18.4 × 10^18 μNXS)
```

### Supply Model

NXS has a **hard supply cap** with **decaying emission**:

| Phase | Period | Emission Rate |
|-------|--------|--------------|
| Bootstrap | Years 0–2 | Fixed reward per epoch, ~1% of cap per year |
| Maturity | Years 2+ | Reward halves every 2 years (geometric decay) |
| Tail | Indefinite | Floor of 0.1% annual inflation relative to circulating supply |

The tail emission ensures ongoing proof-of-service rewards exist indefinitely, funding relay and storage operators. The cap is a hard ceiling — tail emission asymptotically approaches but never reaches it. In practice, lost keys (estimated 1–2% of supply annually) offset tail emission, keeping effective circulating supply roughly stable after year ~10.

### Typical Costs

| Operation | Cost |
|-----------|------|
| Stochastic relay reward (per win) | ~500 μNXS (1/100 prob × 5 μNXS/pkt) |
| Expected cost: 1 KB message, 5 hops | ~10 μNXS |
| 1 hour of storage (1 MB) | ~50 μNXS |
| 1 minute of compute (contract execution) | ~30-100 μNXS |

## Economic Architecture

NEXUS has a simple economic model: **free between friends, paid between strangers.**

### Free Tier (Trust-Based)

- Traffic between [trusted peers](community-zones) is **always free**
- No tokens, no channels, no settlements needed
- A local mesh where everyone trusts each other has **zero economic overhead**

### Paid Tier (NXS)

- Traffic crossing trust boundaries triggers [stochastic relay rewards](payment-channels)
- Relay nodes earn NXS probabilistically — same expected income, far less overhead
- Settled via [CRDT ledger](crdt-ledger)

## Genesis and Bootstrapping

The bootstrapping problem — needing NXS to use services, but needing to provide services to earn NXS — is solved by separating free-tier operation from the paid economy:

### Free-Tier Operation (No NXS Required)

- **Trusted peer communication is always free** — no tokens needed
- **A local mesh works with zero tokens in circulation**
- The protocol is fully functional without any NXS — just limited to your trust network

### Proof-of-Service Mining (NXS Genesis)

When a node wins a [stochastic relay reward](payment-channels) for non-trusted traffic, the protocol **mints new NXS** as the reward. This is how NXS enters existence:

```
Mining reward per epoch:
  reward = base_reward_schedule(epoch_number) / active_relays_in_epoch
  Verified via: lottery win proofs aggregated at epoch boundaries
  Minting: new supply created (not transferred from a pool)
```

### Bootstrap Sequence

1. Nodes form local meshes (free between trusted peers, no tokens)
2. Gateway nodes bridge to wider network
3. Non-trusted traffic triggers stochastic relay rewards (NXS minting)
4. Relay nodes accumulate NXS from mining
5. NXS enters circulation as relay nodes spend on services
6. Market pricing emerges from supply/demand

### Trust-Based Credit

Trusted peers can [vouch for each other](community-zones#trust-based-credit) by extending transitive credit. A friend-of-a-friend gets a credit line (capped at 10% of direct credit), backed by the vouching peer's NXS balance. This provides an on-ramp for new users without any explicit "zone" to join.

**Free direct communication works immediately** with no tokens at all. NXS is only needed when your packets traverse untrusted infrastructure.

## Economic Design Goals

- **No speculation**: NXS is for purchasing services, not for trading
- **No pre-mine**: All NXS enters circulation through proof-of-service
- **Partition-safe**: The economic layer works correctly during network partitions and converges when they heal
- **Minimal overhead**: [Stochastic rewards](payment-channels) reduce economic bandwidth overhead by ~10x compared to per-packet payment
- **Communities first**: Trusted peer communication is free. The economic layer only activates at trust boundaries.

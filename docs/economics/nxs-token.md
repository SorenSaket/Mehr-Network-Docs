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
  Supply ceiling: 2^64 μNXS (~18.4 × 10^18 μNXS, asymptotic — never reached)
```

### Supply Model

NXS has an **asymptotic supply ceiling** with **decaying emission**:

| Phase | Epoch Range | Emission Per Epoch |
|-------|-------------|-------------------|
| Bootstrap | 0–99,999 | 10^12 μNXS (1,000,000 NXS) |
| Halving 1 | 100,000–199,999 | 5 × 10^11 μNXS |
| Halving 2 | 200,000–299,999 | 2.5 × 10^11 μNXS |
| Halving N | N × 100,000 – (N+1) × 100,000 − 1 | 10^12 × 2^(−N) μNXS |
| Tail | When halved reward is below floor | 0.1% of circulating supply / estimated epochs per year |

```
Emission formula:
  epoch_reward(e) = max(
    10^12 >> (e / 100_000),              // discrete halving (bit-shift)
    circulating_supply * 0.001 / E_year  // tail floor
  )

  E_year = trailing 1,000-epoch moving average of epoch frequency
  Halving is epoch-counted, not wall-clock (partition-safe)
  At ~1 epoch per 10 minutes: 100,000 epochs ≈ 1.9 years
```

The theoretical ceiling is 2^64 μNXS, but it is never reached — tail emission asymptotically approaches it. The initial reward of 10^12 μNXS/epoch yields ~1.5% of the supply ceiling minted in the first halving period, providing strong bootstrap incentive. Discrete halving every 100,000 epochs is epoch-counted (no clock synchronization needed) and trivially computable via bit-shift on integer-only hardware.

The tail ensures ongoing proof-of-service rewards exist indefinitely, funding relay and storage operators. In practice, lost keys (estimated 1–2% of supply annually) offset tail emission, keeping effective circulating supply roughly stable after year ~10.

### Typical Costs

| Operation | Cost |
|-----------|------|
| Expected relay cost per packet | ~5 μNXS |
| Relay lottery payout (on win) | ~500 μNXS (5 μNXS ÷ 1/100 win probability) |
| Expected cost: 1 KB message, 5 hops | ~75 μNXS (~3 packets × 5 μNXS × 5 hops) |
| 1 hour of storage (1 MB) | ~50 μNXS |
| 1 minute of compute (contract execution) | ~30–100 μNXS |

The relay lottery pays out infrequently but in larger amounts. Expected value per packet is the same: `500 μNXS × 1/100 = 5 μNXS`. See [Stochastic Relay Rewards](payment-channels) for the full mechanism.

## Economic Architecture

NEXUS has a simple economic model: **free between friends, paid between strangers.**

### Free Tier (Trust-Based)

- Traffic between [trusted peers](trust-neighborhoods) is **always free**
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

The [stochastic relay lottery](payment-channels) serves a dual purpose: it determines who earns and how much, while the **funding source** depends on the economic context:

1. **Minting (subsidy)**: Each epoch, the emission schedule determines how much new NXS is minted. This is distributed proportionally to relay nodes based on their accumulated VRF lottery wins during that epoch — proof that they actually forwarded packets. Minting dominates during bootstrap and decays over time per the emission schedule.

2. **Channel debit (market)**: When a relay wins the lottery and has an open [payment channel](payment-channels) with the upstream sender, the reward is debited from that channel. The sender pays directly for routing. This becomes the dominant mechanism as NXS enters circulation and channels become widespread.

Both mechanisms coexist. As the economy matures, channel-funded relay payments naturally replace minting as the primary income source for relays, while the decaying emission schedule ensures the transition is smooth.

```
Relay compensation per epoch:
  Epoch mint pool: max(10^12 >> (epoch / 100_000), tail_floor)
    → new supply created (not transferred from a pool)
    → halves every 100,000 epochs; floors at 0.1% annual inflation

  Relay R's mint share: epoch_mint_pool × (R_wins / total_wins_in_epoch)
    → proportional to verified VRF lottery wins
    → a relay with 10% of the epoch's wins gets 10% of the mint pool

  Channel revenue: sum of lottery wins debited from sender channels
    → direct payment, no new supply created

  Total relay income = mint share + channel revenue
```

### Bootstrap Sequence

1. Nodes form local meshes (free between trusted peers, no tokens)
2. Gateway nodes bridge to wider network
3. Non-trusted traffic triggers stochastic relay lottery (VRF-based)
4. Lottery wins accumulate as service proofs; epoch minting distributes NXS to relays
5. Relay nodes open payment channels and begin spending NXS on services
6. Senders with NXS fund relay costs via channel debits; minting share decreases
7. Market pricing emerges from supply/demand

### Trust-Based Credit

Trusted peers can [vouch for each other](trust-neighborhoods#trust-based-credit) by extending transitive credit. Each node configures the credit line it extends to its direct trusted peers (e.g., "I'll cover up to 1000 μNXS for Alice"). A friend-of-a-friend gets 10% of that direct limit — backed by the vouching peer's NXS balance. If a credited node defaults, the voucher absorbs the debt. This provides an on-ramp for new users without needing to earn NXS first.

**Free direct communication works immediately** with no tokens at all. NXS is only needed when your packets traverse untrusted infrastructure.

## Why One Global Currency

NXS is a single global unit of account, not a per-community token. This is a deliberate design choice.

### The Alternative: Per-Community Currencies

If each isolated community minted its own token, connecting two communities would require a currency exchange — someone to set an exchange rate, provide liquidity, and settle trades. On a mesh network of 50–500 nodes, there is not enough trading volume to sustain a functioning exchange market. The complexity (order books, matching, dispute resolution) vastly exceeds what constrained devices can support.

### How One Currency Works Across Partitions

When two communities operate in isolation:

1. **Internally**: Both communities communicate free between trusted peers — no NXS needed
2. **Independently**: Each community mints NXS via proof-of-service, proportional to actual relay work. The [CRDT ledger](crdt-ledger) tracks balances independently on each side
3. **On reconnection**: The CRDT ledger merges automatically (CRDTs guarantee convergence). Both communities' NXS is valid because it was earned through real work, not printed arbitrarily

NXS derives its value from **labor** (relaying, storage, compute), not from community membership. One hour of relaying in Community A is roughly equivalent to one hour in Community B. Different hardware costs are reflected in **market pricing** — nodes set their own per-byte charges — not in separate currencies.

### Price Discovery Without Fiat

NXS has no fiat exchange rate by design. Its "purchasing power" floats based on supply and demand for services:

```
Abundant relay capacity + low demand → relay prices drop (in μNXS)
Scarce relay capacity + high demand  → relay prices rise (in μNXS)
```

Users don't need to know what 1 μNXS is worth in dollars. They only need to know: "Can I afford this service?" — and the answer is usually yes, because they earn NXS by providing services to others. The economy is circular, not pegged to an external reference.

## Economic Design Goals

- **No speculation**: NXS is for purchasing services, not for trading. There is no fiat exchange rate by design.
- **No pre-mine**: All NXS enters circulation through proof-of-service
- **Hoarding-resistant**: NXS has no external exchange value, so accumulating it has no purpose beyond purchasing network services. Tail emission (0.1% annual) mildly dilutes idle holdings. Lost keys (~1–2% annually) permanently remove supply. The economic incentive is to spend NXS on services, not to sit on it.
- **Partition-safe**: The economic layer works correctly during network partitions and converges when they heal
- **Minimal overhead**: [Stochastic rewards](payment-channels) reduce economic bandwidth overhead by ~10x compared to per-packet payment
- **Communities first**: Trusted peer communication is free. The economic layer only activates at trust boundaries.

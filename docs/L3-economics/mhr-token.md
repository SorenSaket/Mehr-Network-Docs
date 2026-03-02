---
sidebar_position: 1
title: MHR Token
description: MHR token economics — Proof of Service minting, supply dynamics, anti-inflation mechanisms, and token utility in the Mehr Network.
keywords: [MHR token, proof of service, tokenomics, cryptocurrency, minting]
---

# MHR Token

MHR is the unit of account for the Mehr network. It is not a speculative asset — it is the internal currency for purchasing capabilities from nodes outside your trust network.

## Properties

```
MHR Properties:
  Smallest unit: 1 μMHR (micro-MHR)
  Initial distribution: Genesis service allocation + demand-backed proof-of-service mining (no ICO)
  Genesis allocation: Disclosed amount to genesis gateway operator (see Genesis below)
  Supply ceiling: 2^64 μMHR (~18.4 × 10^18 μMHR, asymptotic — never reached)
```

### Supply Model

MHR has an **asymptotic supply ceiling** with **decaying emission**:

| Phase | Epoch Range | Emission Per Epoch |
|-------|-------------|-------------------|
| Bootstrap | 0–99,999 | 10^12 μMHR (1,000,000 MHR) |
| Halving 1 | 100,000–199,999 | 5 × 10^11 μMHR |
| Halving 2 | 200,000–299,999 | 2.5 × 10^11 μMHR |
| Halving N | N × 100,000 – (N+1) × 100,000 − 1 | 10^12 × 2^(−N) μMHR |
| Tail | When halved reward is below floor | 0.1% of circulating supply / estimated epochs per year |

```
Emission formula:
  halving_shift = min(e / 100_000, 63)   // clamp to prevent undefined behavior
  epoch_reward(e) = max(
    10^12 >> halving_shift,              // discrete halving (bit-shift)
    circulating_supply * 0.001 / E_year  // tail floor
  )

  E_year = trailing 1,000-epoch moving average of epoch frequency
  Halving is epoch-counted, not wall-clock (partition-safe)
  At ~1 epoch per 10 minutes: 100,000 epochs ≈ 1.9 years

  Implementation note: the shift operand MUST be clamped to 63 (max
  for u64). At epoch 6,400,000 (~year 1218), unclamped shift = 64
  which is undefined behavior on most platforms. Clamping to 63 yields
  0 (10^12 >> 63 = 0), so the tail floor takes over — correct behavior.
```

:::info[Specification]
Emission halves every 100,000 epochs via bit-shift (`10^12 >> halving_shift`). Tail floor at 0.1% of circulating supply per year ensures perpetual service rewards. Shift operand clamped to 63 for u64 safety.
:::

The theoretical ceiling is 2^64 μMHR, but it is never reached — tail emission asymptotically approaches it. The initial reward of 10^12 μMHR/epoch yields ~1.5% of the supply ceiling minted in the first halving period, providing strong bootstrap incentive. Discrete halving every 100,000 epochs is epoch-counted (no clock synchronization needed) and trivially computable via bit-shift on integer-only hardware.

The tail ensures ongoing proof-of-service rewards exist indefinitely, funding all service operators (relay, storage, compute). In practice, lost keys (estimated 1–2% of supply annually) offset tail emission, keeping effective circulating supply roughly stable after year ~10.

### Typical Costs

| Operation | Cost |
|-----------|------|
| Expected relay cost per packet | ~5 μMHR |
| Relay lottery payout (on win) | ~500 μMHR (5 μMHR ÷ 1/100 win probability) |
| Expected cost: 1 KB message, 5 hops | ~75 μMHR (~3 packets × 5 μMHR × 5 hops) |
| 1 hour of storage (1 MB) | ~50 μMHR |
| 1 minute of compute (contract execution) | ~30–100 μMHR |

The relay lottery pays out infrequently but in larger amounts. Expected value per packet is the same: `500 μMHR × 1/100 = 5 μMHR`. See [Stochastic Relay Rewards](payment-channels) for the full mechanism.

## All-Service Minting

All services — relay, storage, and compute — earn minting rewards. Minting is proportional to real economic activity (channel debits) and capped at a fraction of that activity, making self-dealing structurally unprofitable. A 2% service burn on every funded-channel payment creates a deflationary force that bounds supply even in isolated partitions.

### Why All Services Mint

The anti-gaming defense is **not** service-specific proofs. It is three mechanisms that work uniformly across all services:

1. **Non-deterministic assignment** — the client cannot choose who serves the request
2. **Net-income revenue cap** — total minting cannot exceed 50% of net economic activity
3. **Service burn + active-set scaling** — 2% burn on all funded-channel payments + emission scaled by partition size bounds isolated partition supply growth to at most `E_s` per epoch

Together, these guarantee that self-dealing in a connected network is **never profitable**, and that isolated partition minting is bounded by scaled emission per epoch (convergent over time due to halving). See the [Security Analysis](./token-security#security-analysis) for the complete threat model.

### Non-Deterministic Assignment

Each service type has a natural mechanism that prevents the client from choosing the server:

```
Service assignment:

  Relay:    Mesh routing (Kleinberg greedy forwarding)
            Path determined by network topology, not client choice.
            Multi-hop paths include honest relays with high probability.
            Probability of ALL hops being attacker-controlled: X^hops
            (vanishingly small for typical path lengths).

  Storage:  DHT ring assignment
            responsible_node = DHT(hash(content_id || epoch_hash))
            The epoch_hash is unpredictable at request time, preventing
            the client from grinding content IDs to influence assignment.
            Replicas assigned to multiple DHT-ring positions for durability.

  Compute:  DHT ring assignment
            responsible_node = DHT(hash(job_spec || epoch_hash))
            Same mechanism as storage. The compute node is determined by
            the DHT ring, not by client choice.
```

The DHT ring is the same Kleinberg small-world ring used for routing. No new mechanism — storage and compute assignment reuse the existing topology.

### Unified Minting Formula

All service income contributes to one minting pool. The revenue cap uses **net income** (income minus spending per provider), not gross channel debits, to prevent [cycling attacks](./token-security#attack-channel-cycling). Emission is scaled by the active set size to limit small-partition minting:

```
Minting formula (all services):

  For each provider P this epoch:
    P_income  = relay_income + storage_income + compute_income  (payments received)
    P_spending = total payments sent across all channels
    P_net     = max(0, P_income - P_spending)

  Active-set-scaled emission:
    active_nodes = number of nodes in epoch's active set
    reference_size = 100  (configurable protocol parameter)
    scale_factor = min(active_nodes, reference_size) / reference_size
    scaled_emission = emission(epoch) × scale_factor
      → 3-node partition: 3/100 × E = 0.03E
      → 100+ node partition: full E

  Revenue cap (net-income based):
    minting_eligible = Σ P_net for all providers P
    epoch_minting = min(scaled_emission, 0.5 × minting_eligible)

  Service burn:
    burn_rate = 0.02  (2% of every funded-channel payment)
    Burned amount is permanently destroyed before minting calculation.
    Provider receives 98% of channel payment; 2% is removed from supply.

  Distribution (gross-income based):
    provider_mint_share = (P_income / Σ all_income) × epoch_minting

  The cap uses net income (prevents cycling). Distribution uses gross
  income (rewards all service provision fairly). A relay earning 1000 μMHR
  and a storage node earning 1000 μMHR get the same distribution share.

  Why net income for the cap:
    In a round-trip cycle (A→B→A), every provider's income = spending → net = 0.
    Cycling produces zero minting, regardless of how many times MHR circulates.
    One-directional spending (real demand) produces positive net income.

  Why active-set scaling:
    Without scaling, a 3-node partition mints the same as a 10,000-node network.
    With scaling, the 3-node partition mints 3% of full emission — proportional
    to its size. The 2% burn provides additional friction (~4% reduction in
    attacker growth rate) and absorbs excess supply after partition merge.
```

### Service-Specific Payment Mechanics

The VRF stochastic lottery remains relay-specific — it is a bandwidth optimization, not a minting mechanism:

```
Payment mechanics by service:

  Relay:    VRF stochastic lottery per-packet (existing)
            Channel debit on lottery win (~1/100 packets)
            High-frequency, low-value: lottery reduces overhead by ~10x

  Storage:  Direct channel debit per-epoch per-agreement
            Low-frequency: one payment per storage agreement per epoch
            No lottery needed — per-event channel updates are affordable

  Compute:  Direct channel debit per-job
            Medium-frequency: one payment per computation
            No lottery needed — per-event channel updates are affordable
```

### Proof: Self-Dealing Is Unprofitable

```
Self-dealing with non-deterministic assignment + net-income cap:

  Attacker has X fraction of network economic capacity.
  Attacker generates Y MHR in fake service demand.

  Non-deterministic assignment routes:
    X × Y  → attacker's own nodes (internal transfer, net cost 0)
    (1-X) × Y → honest nodes (REAL cost to attacker)

  Net income (for revenue cap):
    Honest providers: net = (1-X)Y (received payment, didn't spend back to attacker)
    Attacker providers: net = max(0, XY - Y) = 0 (income < spending for X < 1)
    minting_eligible = (1-X)Y  (only honest providers contribute)

  Minting earned by attacker:
    attacker_share = XY / Y = X  (gross income share)
    attacker_minting = X × min(E, 0.5 × (1-X)Y)

  Attacker's net profit (assuming 0.5(1-X)Y < E):
    -(1-X)Y + X × 0.5 × (1-X)Y = (1-X)Y × (0.5X - 1)

  This is ALWAYS negative for any X < 1:
    X = 10%: net = -0.45Y × 0.9 = -0.855Y  (85.5% loss)
    X = 30%: net = -0.35Y × 0.7 = -0.49Y   (49% loss)
    X = 50%: net = -0.25Y × 0.5 = -0.375Y  (37.5% loss)
    X = 90%: net = -0.05Y × 0.1 = -0.045Y  (4.5% loss)
    X = 99%: net = -0.005Y × 0.01 = -0.005Y (0.5% loss)

  Self-dealing is NEVER profitable in a connected network.
  The net-income cap ensures the attacker's own internal transfers
  don't count toward minting eligibility.
```

Non-deterministic assignment forces the attacker to pay honest nodes. The net-income cap ensures the attacker's internal transfers (paying their own nodes) produce zero minting eligibility. Together, self-dealing in a connected network always loses money — the attacker spends real MHR on honest nodes and earns nothing from their internal circulation.

:::tip[Key Insight]
Self-dealing is **never profitable** for any attacker fraction X < 1. The net-income cap zeroes out internal transfers, while non-deterministic assignment forces irrecoverable payment to honest nodes. Net profit = `(1-X)Y × (0.5X - 1)` — always negative.
:::

:::note[Design Note]
This "never profitable" result requires that the network is connected and non-deterministic assignment is operational. In an [isolated partition](./token-security#attack-isolated-partition) where the attacker controls all nodes, non-deterministic assignment is nullified — but the [trust-gated active set](./token-security#trust-gated-active-set) + [merge-time trust audit](./token-security#merge-time-trust-audit) (rejects untrusted partition minting on reconnection), active-set-scaled emission, and 2% service burn bound supply growth. See the [Security Analysis](./token-security#security-analysis) for the full threat model.
:::

### What We Don't Need

The three-mechanism defense (non-deterministic assignment + net-income cap + burn/scaling) makes several commonly proposed anti-gaming mechanisms unnecessary:

| Mechanism | Why not needed |
|-----------|----------------|
| Numerical trust scores | Binary trust neighborhoods handle free/paid boundary |
| Staking | Channel funding provides implicit Sybil cost |
| Slashing | Attacks are structurally unprofitable — punishment is redundant |
| Service-specific proof protocols | DHT assignment + bilateral verification sufficient |
| Dynamic pool rebalancing | Single pool, proportional distribution, market adjusts prices |

Three mechanisms. One formula. Zero trust assumptions.

### Bootstrap by Service Type

```
Bootstrap sequence:

  Phase 0: FREE TIER
    ├── Relay:   Trusted peers relay for free (works immediately)
    ├── Storage: Trusted peers store each other's data for free
    └── Compute: Nodes run their own contracts locally

  Phase 0.5: GENESIS SERVICE GATEWAY
    ├── Genesis gateway receives transparent MHR allocation
    ├── Gateway offers real services for fiat (relay, storage, compute)
    ├── Consumer fiat → MHR credit extensions → funded channels
    └── Real service demand enters the network for the first time

  Phase 1: DEMAND-BACKED SERVICE MINTING
    ├── Funded-channel traffic triggers relay VRF lottery
    ├── Storage/compute agreements generate direct channel debits
    ├── ALL channel debits (relay + storage + compute) earn minting
    ├── Revenue-capped minting prevents self-dealing (see above)
    └── MHR enters circulation backed by real demand across all services

  Phase 2: MARKET ECONOMY
    ├── Service providers spend MHR on other services
    ├── Competition drives prices toward marginal cost
    └── All service types have mature bilateral payment markets

  Phase 3: MATURE ECONOMY
    ├── Bilateral payments dominate all services
    ├── Minting becomes residual (decaying emission)
    └── Service prices emerge from supply/demand
```

Every service type earns minting from Phase 1. A $30 solar relay earns minting by forwarding packets. A node with spare disk earns minting by storing data. A node with a GPU earns minting by running compute jobs. The minting subsidy is proportional to economic contribution, not service type.

**Storage is a particularly low-barrier entry point.** Any device with spare disk space can offer [cloud storage](/docs/L6-applications/cloud-storage#earning-mhr-through-storage) and earn MHR through both bilateral payments and minting rewards. The marginal cost is near zero (idle disk space), so even modest demand generates income. For users who want to participate in the economy without running relay infrastructure, storage is the simplest starting point.

### Genesis-Anchored Minting

During bootstrap (before the first halving at epoch 100,000), minting eligibility requires a **GenesisAttestation** — a signed proof of recent connectivity to a genesis node. This completely eliminates the [isolated partition attack](./token-security#attack-isolated-partition) during the most vulnerable period (high emission, low total supply).

```
GenesisAttestation {
    epoch_number: u64,              // epoch this attestation was issued
    attestor_id: NodeID,            // genesis node or attested peer
    attestor_sig: Ed25519Signature, // signature over (epoch_number || subject_id)
    chain_length: u8,               // 0 = genesis node itself, 1 = direct peer, etc.
    max_chain_length: u8,           // protocol parameter (default: 5)
}

How attestations propagate:
  1. Genesis nodes sign attestations for directly connected peers each epoch
     (chain_length = 1)
  2. Any node with a valid attestation (chain_length < max) can vouch for
     its own direct peers (chain_length + 1)
  3. Attestations propagate one hop per epoch via gossip
  4. TTL: attestations expire after 10 epochs — a node that loses genesis
     connectivity for >10 epochs can no longer mint
  5. Minting eligibility check:
     IF epoch_number < 100,000:  // bootstrap phase
       provider must have a valid GenesisAttestation (not expired, chain verified)
     ELSE:
       GenesisAttestation sunsets — trust-gated active set + merge-time audit take over

Why this works:
  - An isolated partition with no path to a genesis node gets ZERO minting
  - The attacker cannot forge attestations (Ed25519 signatures)
  - The attacker cannot relay attestations without actual connectivity
  - Legitimate isolated communities (natural partitions) also cannot mint
    during bootstrap — this is acceptable because the bootstrap period is
    when the genesis gateway is the primary MHR source anyway
```

**Post-bootstrap defense**: At epoch 100,000 (first halving), GenesisAttestation is retired. Post-bootstrap partition defense is provided by the [trust-gated active set](./token-security#trust-gated-active-set) (minting requires ≥1 mutual trust link) and the [merge-time trust audit](./token-security#merge-time-trust-audit) (rejects untrusted partition minting on reconnection). No attestation chains, no central authority, no expiring certificates. See [Partition Defense](./token-security#partition-defense) for the complete design.

### Service Burn

A **2% burn** is applied to every funded-channel payment, permanently destroying the burned amount. This creates a deflationary force that provides friction in isolated partitions and absorbs excess supply after partition merge.

```
Service burn mechanics:

  On every funded-channel payment (relay lottery win, storage debit, compute debit):
    burn_amount = payment × 0.02
    provider_receives = payment × 0.98
    burn_amount is permanently destroyed (removed from circulating supply)

  Applies to:
    ✓ Relay VRF lottery wins (burn 2% of the payout)
    ✓ Storage per-epoch debits (burn 2% of the payment)
    ✓ Compute per-job debits (burn 2% of the payment)
    ✗ Free-tier trusted traffic (no payment = nothing to burn)
    ✗ Minting rewards (new supply, not a payment)

  Burn tracking:
    Each ServiceDebitSummary includes a burn_total field
    Epoch snapshot includes epoch_burn_total (sum of all burns)
    Burns are reflected in the CRDT ledger as reduced delta_earned
    (provider's delta_earned increases by 98% of payment, not 100%)

Burn role in isolated partitions:
  In an isolated partition, the attacker spends the minimum needed to
  saturate the minting cap (~2.04 × E_s per epoch). The burn on this
  activity is ~0.04 × E_s per epoch — a ~4% reduction in the attacker's
  supply growth rate (see Supply Dynamics Proof in Security Analysis).
  After reconnection, the 2% burn on the entire network's economic
  activity gradually absorbs the excess supply.

Effect on connected networks:
  In the normal (connected) network, burns reduce effective circulating supply.
  Combined with lost keys (~1-2% annual), the deflationary pressure is mild
  but creates a tighter long-term equilibrium. Tail emission (0.1% annual)
  compensates — the steady state is: tail_emission ≈ burns + lost_keys.
```

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>How is MHR different from typical cryptocurrencies?</summary>

MHR is not a speculative asset — it is the internal currency for purchasing services (relay, storage, compute) from nodes outside your trust network. There is no ICO, no pre-mine, and no exchange mechanism built into the protocol. Supply is minted only through demand-backed proof-of-service: you earn MHR by providing real services through funded payment channels. The 2% service burn on every payment creates a deflationary counterforce.

</details>

<details className="faq-item">
<summary>What prevents someone from gaming the minting system by creating fake traffic?</summary>

Three mechanisms work together: non-deterministic assignment routes most service requests to honest nodes (the attacker cannot choose the server), the net-income revenue cap ensures internal transfers between the attacker's own nodes produce zero minting eligibility, and the 2% service burn imposes friction on every payment. Self-dealing in a connected network is mathematically proven to be unprofitable for any attacker controlling less than 100% of the network.

</details>

<details className="faq-item">
<summary>How does the emission schedule work and when does supply stop growing?</summary>

Emission starts at 1,000,000 MHR per epoch and halves every 100,000 epochs (approximately every 1.9 years). When the halved reward falls below a floor, tail emission kicks in at 0.1% of circulating supply per year, ensuring service providers always have a minting incentive. The theoretical supply ceiling of 2^64 μMHR is never reached — tail emission approaches it asymptotically. In practice, lost keys (1–2% annually) and the 2% service burn offset tail emission, keeping effective circulating supply stable.

</details>

<details className="faq-item">
<summary>Can storage and compute providers earn minting rewards, or only relay nodes?</summary>

All service types earn minting rewards equally. Relay, storage, and compute income all contribute to a single minting pool. Distribution is proportional to each provider's gross income share — a storage node earning 10% of total income gets 10% of epoch minting. The VRF stochastic lottery is relay-specific (a bandwidth optimization), but storage and compute use direct channel debits that count identically toward minting.

</details>

<details className="faq-item">
<summary>What is the genesis-anchored minting requirement during bootstrap?</summary>

During bootstrap (epoch 0–99,999), minting requires a GenesisAttestation — a signed proof of recent connectivity to a genesis node. These attestations propagate one hop per epoch via gossip, expire after 10 epochs, and form chains up to 5 hops. This completely eliminates isolated partition attacks during the most vulnerable period. After epoch 100,000, genesis attestation sunsets and the trust-gated active set with merge-time audit takes over.

</details>

<!-- faq-end -->

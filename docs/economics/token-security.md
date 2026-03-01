---
sidebar_position: 3
title: Token Security
description: Partition tolerance, comprehensive security analysis of all economic attack vectors, and long-term sustainability of the MHR token.
keywords: [security analysis, partition tolerance, isolated partition, trust audit, self-dealing]
---

# Token Security

## Partition Tolerance

The economic layer is designed to operate correctly during network partitions and converge automatically when they heal. This section describes how all-service minting interacts with partitions.

### Per-Partition Minting

Each partition operates as a self-contained economy with its own minting. Emission is **scaled by the partition's active set size** and reduced by the **2% service burn**:

```
Partition minting (with active-set scaling and burn):

  Partition A (60 nodes):
    scaled_emission_A = emission(epoch) × min(60, 100) / 100 = 0.6E
    local_debits_A = relay + storage + compute debits within partition A
    local_minting_A = min(scaled_emission_A, 0.5 × net_income_A)
    burns_A = 0.02 × total_funded_payments_A

  Partition B (40 nodes):
    scaled_emission_B = emission(epoch) × min(40, 100) / 100 = 0.4E
    local_debits_B = relay + storage + compute debits within partition B
    local_minting_B = min(scaled_emission_B, 0.5 × net_income_B)
    burns_B = 0.02 × total_funded_payments_B

  Each partition independently applies scaled emission, revenue cap, and burns.
  No cross-partition knowledge needed — each side sees only local activity.
```

On merge, total minted supply may exceed what a single-network emission would have produced. However, with active-set scaling, the overminting is **bounded by the sum of scale factors** (e.g., 60-node + 40-node = 0.6E + 0.4E = 1.0E, no overminting at all when the two partitions together equal the reference size). The 2% burn during partition operation further reduces the net supply impact. This is the same [partition minting tradeoff](crdt-ledger#partition-minting-and-supply-convergence) — the alternative (coordinated minting) requires global consensus, which contradicts partition tolerance.

### DHT Assignment During Partitions

Storage and compute use DHT ring assignment. During a partition:

```
DHT assignment in partitioned network:

  Before partition:
    Full ring: nodes A, B, C, D, E, F, G, H
    storage_key = hash(content || epoch_hash) → assigned to node D

  During partition (A,B,C,D | E,F,G,H):
    Left partition ring: A, B, C, D
    Right partition ring: E, F, G, H

    New storage requests in left partition use left-ring DHT
    New storage requests in right partition use right-ring DHT
    Existing agreements continue on whichever side their node is in

  After merge:
    Full ring restored
    New requests use full ring
    Existing agreements are unaffected (provider stays the same)
```

Existing storage agreements survive partitions because the payment channel persists between client and provider. If the provider is on the other side of the partition, the client cannot verify or pay — the agreement is effectively paused. On merge, the channel resumes (CRDT convergence restores both parties' balances).

### Revenue Cap During Partitions

Each partition's revenue cap uses only local net income, scaled by its active set size:

- No cross-partition knowledge needed
- Each partition independently caps minting at `min(scaled_emission, 0.5 × net_income)`
- Active-set scaling limits small partitions: 3-node partition gets 3% of full emission
- 2% service burn creates deflationary counterforce within each partition
- The net-income cap prevents [cycling attacks](#attack-channel-cycling) even within isolated partitions
- On merge, the CRDT ledger handles balance convergence
- During bootstrap (epoch < 100,000): [genesis-anchored minting](mhr-token#genesis-anchored-minting) prevents isolated partitions from minting at all
- Post-bootstrap: [trust-gated active set](#trust-gated-active-set) requires mutual trust links for minting eligibility; [merge-time trust audit](#merge-time-trust-audit) rejects untrusted minting on reconnection

For detailed analysis of attacks that exploit partitions — including fully-controlled partitions, cycling, and compounding — see the [Security Analysis](#security-analysis).

## Security Analysis

This section catalogs all known economic attack vectors and their defenses. The economic layer relies on five mechanisms — **non-deterministic assignment**, **net-income revenue cap**, **service burn + active-set scaling**, **[trust-gated active set](#trust-gated-active-set)**, and **[merge-time trust audit](#merge-time-trust-audit)** — to defend against minting abuse. During bootstrap, [genesis-anchored minting](mhr-token#genesis-anchored-minting) provides the initial layer by requiring provable connectivity to genesis nodes. Post-bootstrap, the trust-gated active set requires mutual trust links for minting eligibility, and the merge-time trust audit validates partition minting on reconnection. No staking, slashing, or hardware attestation is required.

### Attack: Self-Dealing (Connected Network)

**Description**: Attacker controls X fraction of network economic capacity. Generates Y MHR in fake service demand through funded channels to earn minting rewards.

**Defense**: Non-deterministic assignment routes (1-X)×Y to honest nodes (real, irrecoverable cost). The net-income revenue cap ensures the attacker's own internal transfers produce zero minting eligibility. Result: self-dealing in a connected network is **never profitable** for any X < 1.

**Residual risk**: None in connected networks. See [Proof: Self-Dealing Is Unprofitable](mhr-token#proof-self-dealing-is-unprofitable) for the full analysis.

### Attack: Channel Cycling

**Description**: Two colluding nodes cycle M MHR back and forth on the same channel K times per epoch. With gross debits, each round-trip adds 2M to total debits — after K cycles, total debits = 2KM. The attacker reaches the emission ceiling immediately, regardless of actual economic activity. This also works across channels (triangle cycling: A→B→C→A) and through settlement-mediated cycling (settle, refund, repeat).

**Defense**: The revenue cap uses **net income per provider** (income minus spending), not gross channel debits.

```
Cycling prevention (net-income cap):

  Same-channel cycling: A→B then B→A, repeated K times
    A: income = KM, spending = KM → net = 0
    B: income = KM, spending = KM → net = 0
    minting_eligible = 0 → epoch_minting = 0 ✓

  Cross-channel cycling (triangle): A→B→C→A, repeated K times
    A: income = KM (from C), spending = KM (to B) → net = 0
    B: income = KM (from A), spending = KM (to C) → net = 0
    C: income = KM (from B), spending = KM (to A) → net = 0
    minting_eligible = 0 → epoch_minting = 0 ✓

  Settlement-mediated cycling: settle channel, refund, repeat
    Same result — net income is tracked per-provider across ALL
    channels and settlements within the epoch. A provider who
    receives M via settlement and spends M via new channel debits
    has net income = 0 regardless of settlement timing.

  Key property: any CLOSED CYCLE produces zero net income for
  every participant, because every provider's income equals their
  spending. Only one-directional flows (real demand) produce
  positive net income.
```

**Residual risk**: None. Cycling is completely neutralized by the net-income cap.

### Attack: Sybil DHT Positioning

**Description**: Attacker creates many node identities to occupy more DHT ring space. With more ring positions, a larger fraction of storage/compute assignments are directed to attacker nodes, increasing their minting share.

**Defense**: This is equivalent to increasing X (attacker's network fraction) in the self-dealing proof. More identities capture more assignments, but:

```
Sybil analysis:

  Attacker creates N identities, captures N/total_nodes of DHT ring.
  Equivalent to having X = N/total_nodes network fraction.

  In connected network: self-dealing proof applies.
    Attacker's net income = 0 (internal transfers don't count).
    Never profitable for any X < 1.

  Additional defenses:
    - DHT assignment uses hash(content_id || epoch_hash)
      → epoch_hash changes every epoch, so ring positions are ephemeral
      → attacker can't grind permanent strategic positions
    - Each identity needs funded channels (real MHR) to earn minting
    - Creating identities is cheap but funding channels requires capital
```

**Residual risk**: Same as self-dealing — none in connected networks.

### Attack: Content/Job ID Grinding

**Description**: Client generates content IDs or job specifications designed so that `hash(content_id || epoch_hash)` maps to an attacker-controlled node on the DHT ring.

**Defense**: The `epoch_hash` is determined at epoch proposal time and is unpredictable at content creation time. To pre-grind assignments, the attacker would need to predict future epoch hashes — computationally infeasible (hash space is 2^256). Even grinding after the epoch hash is known is impractical: the client must use the content_id it actually wants to store, not an arbitrary one.

**Residual risk**: None (computationally infeasible).

### Attack: Relay Without Forwarding

**Description**: Relay node claims VRF lottery wins without actually forwarding packets, collecting payment for non-service.

**Defense**: The VRF lottery requires the actual packet hash as input — the relay must have received the real packet to compute a valid VRF proof. If the relay doesn't forward the packet:

- The sender detects non-delivery (no acknowledgment from destination)
- The sender routes around the dishonest relay in future
- Persistent non-forwarding is detectable via delivery rate monitoring

**Residual risk**: Individual packet drops are hard to attribute (could be normal link loss). But the economic impact is bounded to individual lottery wins, and persistent dishonesty leads to route abandonment.

### Attack: Storage/Compute Fabrication

**Description**: Provider claims to store data or execute computations without actually doing so, collecting channel payments for non-service.

**Defense**: Bilateral verification by the client:

- **Storage**: Client issues periodic challenge-response queries on stored data (e.g., "return bytes 1024-2048 of block X"). Failure to respond correctly means the data is not stored.
- **Compute**: Client verifies computation results against expected output or spot-checks. Incorrect results are immediately detectable.

No protocol-level proof mechanism is needed. The economic incentive (continued payment) ensures honest service. Dishonest providers lose the client's business immediately.

**Residual risk**: Brief period of undetected non-service before the client verifies. Bounded by a single epoch's payment for storage, or a single job's payment for compute.

### Attack: Isolated Partition

**Description**: Attacker creates a network partition they fully or majority control. Within this partition, the attacker controls enough of the economic capacity to profit from self-dealing. At 100% control, non-deterministic assignment is nullified — all service requests go to attacker nodes. Creating an isolated partition is trivial — a few VMs on a laptop suffice.

This is the most significant economic attack vector. Seven defense layers bound the damage to a finite, predictable amount:

**Defense layers**:

1. **Genesis-anchored minting (bootstrap defense)**: During bootstrap (epoch < 100,000), minting requires a valid [GenesisAttestation](mhr-token#genesis-anchored-minting) — a signed proof of recent connectivity to a genesis node. An isolated partition with no path to a genesis node gets **zero minting**. This completely eliminates the attack during the most vulnerable period (high emission, low total supply).

2. **[Trust-gated active set](#trust-gated-active-set) (post-bootstrap identity defense)**: After bootstrap, minting requires ≥1 mutual trust link with another active-set member. This prevents nodes with zero social ties from entering the minting-eligible set in connected networks. During isolation, attacker nodes trivially satisfy this (they trust each other) — the defense activates at merge time.

3. **[Merge-time trust audit](#merge-time-trust-audit) (reconnection defense)**: When a partition reconnects, minting from untrusted nodes is rejected. Cross-partition trust scoring ensures that only minting from nodes with real trust relationships is accepted into the main network supply. Fresh-identity attacks → 0% dilution on merge.

4. **Active-set-scaled emission (size defense)**: Emission is scaled by the partition's active set size: `scaled_emission = emission × min(active_nodes, 100) / 100`. A 3-node partition gets 3% of full emission. This eliminates the linear scaling advantage of small partitions.

5. **Service burn (friction defense)**: 2% of every funded-channel payment is permanently destroyed. This imposes ongoing friction on the attacker and, after reconnection, the burn on the entire network's economic activity gradually absorbs excess supply.

6. **Cycling prevention**: The net-income cap prevents the attacker from inflating debits by cycling MHR between their own nodes. Only net one-directional flows count toward minting eligibility.

7. **Self-correcting on merge**: Excess supply dilutes ALL holders equally, including the attacker's own holdings. The emission schedule decays geometrically, so any supply shock becomes negligible over time.

#### Supply Dynamics Proof

The attacker's supply growth per epoch depends on their spending strategy. Let `S_k` = supply at epoch k, `E_s` = scaled emission, `b` = burn rate (0.02), and `A_k` = economic activity (total one-directional payments):

```
Supply recurrence:
  S_{k+1} = S_k - b × A_k + min(E_s, 0.5 × 0.98 × A_k)

  Minting requires positive net income. A rational attacker structures
  one-directional payments (no cycling within an epoch) to maximize
  net income. Each epoch, the sender alternates (A→B in epoch k,
  B→A in epoch k+1) to avoid same-epoch cycling.

  The attacker chooses A_k to maximize S_{k+1}:
    If 0.49 × A_k < E_s (revenue cap binds):
      gain = 0.49 × A_k - 0.02 × A_k = 0.47 × A_k
      → maximized by A_k = S_k (spend everything)
    If 0.49 × A_k ≥ E_s (emission cap binds):
      gain = E_s - 0.02 × A_k
      → maximized by A_k = E_s / 0.49 ≈ 2.04 × E_s (spend minimum)

  Phase 1 (S_k < 2.04 × E_s): attacker spends everything
    S_{k+1} = S_k + 0.47 × S_k = 1.47 × S_k  (exponential growth)

  Phase 2 (S_k ≥ 2.04 × E_s): attacker spends only 2.04 × E_s
    S_{k+1} = S_k + E_s - 0.02 × 2.04 × E_s = S_k + 0.959 × E_s
    (linear growth at ~0.96 × E_s per epoch, no equilibrium)
```

The attacker reaches Phase 2 quickly (about `log(2.04 × E_s / M_0) / log(1.47)` epochs from initial capital `M_0`). After that, supply grows linearly:

```
Worst-case supply bound (optimal attacker, post-Phase 1):
  S_K ≈ 2.04 × E_s + 0.959 × E_s × K  (after K epochs in Phase 2)

  Simpler upper bound (per epoch):
    Supply growth ≤ E_s per epoch  (emission is the hard ceiling)

  Example (3-node partition, after first halving, 1000 epochs ≈ 1 week):
    E_s = 15,000 MHR/epoch
    Max excess after 1000 epochs: ~15,000 × 1000 = 15M MHR
    Total network supply at epoch 100,000: ~10^11 MHR
    Impact: 0.015% of supply  → negligible

  Example (3-node partition, after 5 halvings, 1000 epochs):
    E_s = 937.5 MHR/epoch
    Max excess after 1000 epochs: ~937,500 MHR  → negligible

  Total lifetime excess (infinite-duration partition, all halvings):
    Σ E_s per halving period = (N/100) × Σ_{h=1}^{∞} E_h × 100,000
    = (N/100) × 10^11 MHR (convergent geometric sum)
    For N=3: 3 × 10^9 MHR
    Total actual supply: ~2 × 10^11 MHR
    Dilution: 3 × 10^9 / 2 × 10^11 = 1.5%
    → Even an infinitely long 3-node partition produces ~1.5% dilution
    → For realistic durations (weeks-months), dilution is < 0.1%
```

:::tip[Key Insight]
Worst-case supply growth is bounded at ≤ E_s (scaled emission) per epoch. A 3-node partition running indefinitely produces ~1.5% lifetime dilution. With merge-time trust audit, fresh-identity attacks produce **0% dilution** on reconnection.
:::

**Note on the `E_s / burn_rate` formula**: Under 100% money velocity (attacker circulates ALL supply every epoch), a true equilibrium exists at `S* = E_s / burn_rate`. This is because `S_{k+1} = 0.98 × S_k + E_s`, which converges to `E_s / 0.02`. However, a rational attacker avoids this by spending only the minimum needed to saturate the minting cap, keeping a reserve that is never burned. The per-epoch growth bound (`≤ E_s`) and the convergent halving sum are the correct worst-case bounds.

#### Attacker Economics: Cost vs. Damage

The isolated partition attack requires running node processes and maintaining them. The attacker's return on investment determines whether the attack is practical at scale.

**Critical note on hardware costs**: A "node" in Mehr is an Ed25519 keypair plus a lightweight process. Active set membership requires only that a node appears in a `SettlementRecord` within the last 2 epochs — there is no hardware attestation, proof-of-work, or unique device requirement. An attacker can run 100 node identities as 100 processes on a single machine (localhost). The processes settle with each other over loopback, generating the required `SettlementRecord` entries for active set membership. This means the real hardware cost for a 100-node partition is **one machine** (~$60/year for a cheap VPS), not 100 separate VMs.

```
Cost-damage analysis (post-bootstrap, first halving period):

  N = virtual attacker nodes (Ed25519 identities, all on one machine)
  E_s = (N/100) × 500,000 MHR/epoch  (capped at 500,000 for N ≥ 100)
  Annual excess = E_s × 52,600 epochs/year
  Total supply at epoch 100,000: ~10^11 MHR
  Hardware cost: ONE machine for any N (processes on localhost)

  N     E_s/epoch   Annual excess    Annual dilution   Lifetime dilution   Real cost/year
  ---   ---------   ------------     ---------------   -----------------   ---------------
    3      15,000       789M MHR     0.8% of supply          1.5%              ~$60
   10      50,000     2,630M MHR     2.6% of supply          5.0%              ~$60
   50     250,000    13,150M MHR    13.2% of supply         25.0%              ~$60
  100     500,000    26,300M MHR    26.3% of supply         50.0%              ~$60
  200     500,000    26,300M MHR    26.3% of supply         50.0%              ~$60

  Notes:
    - "Annual dilution" is the first year only; subsequent years are halved
    - "Lifetime dilution" assumes infinite duration (convergent halving sum)
    - Active-set cap at 100 means nodes beyond 100 add no damage
    - All N identities run on one machine: cost is FLAT, not per-node
    - These are upper bounds: actual dilution decreases as emission halves
```

#### Localhost Attack: Why Hardware Cost Is Not the Defense {#localhost-attack}

The previous cost table assumed $5/month per VM per node. This is wrong. Nothing in the protocol prevents running N identities on one machine:

```
Localhost attack setup:
  1. Generate 100 Ed25519 keypairs                    (free, instant)
  2. Start 100 processes on one $5/month VPS           (~$60/year)
  3. Open funded channels between them on loopback     (needs initial MHR)
  4. Settle channels → 100 nodes appear in active set  (100/100 = full scaling)
  5. Self-deal: one-directional payments between nodes  (net income > 0)
  6. Mint at full emission rate                         (500,000 MHR/epoch)

Bootstrap from minimal capital:
  Phase 1: exponential growth at 1.47x per epoch (spend everything)
  Phase 2: linear growth at ~0.96 × E_s per epoch (saturate minting cap)

  Starting capital    Epochs to Phase 2    Wall-clock time
  ----------------    -----------------    ---------------
  1 MHR                     ~36 epochs       ~6 hours
  100 MHR                   ~24 epochs       ~4 hours
  10,000 MHR                ~12 epochs       ~2 hours

  Even 1 MHR of initial capital reaches full emission rate in ~6 hours.
  Initial capital is a speed bump, not a wall.

Per-MACHINE return comparison (the correct metric):
  An attacker's "nodes" are lightweight processes on one machine.
  An honest node is a real device. The correct comparison is per-machine.

  Network size    Honest return/machine    Attack return/machine    Ratio
  ------------    ---------------------    ---------------------    -----
       100         5,000 MHR/epoch          500,000 MHR/epoch       100x
     1,000           500 MHR/epoch          500,000 MHR/epoch     1,000x
    10,000            50 MHR/epoch          500,000 MHR/epoch    10,000x

  The per-NODE comparison ("honest participation earns the same") is
  misleading because it equates a virtual process with a physical device.
```

**What the real defenses are** (honest assessment):

| Defense layer | Strength | Why |
|---|---|---|
| **GenesisAttestation** (bootstrap, epoch < 100,000) | **Complete** | No connectivity to genesis node → zero minting. ~1.9 years of total protection. |
| **Halving schedule** | **Strong** | Annual dilution halves every ~1.9 years: 26.3% → 13.2% → 6.6% → ... |
| **Active-set cap at 100** | **Strong** | No benefit from running > 100 identities |
| **Lifetime dilution cap** | **Strong** | 50% maximum (convergent halving sum) regardless of attacker persistence |
| Hardware cost | **Weak** | ~$60/year for one machine, not $6,000/year. Not a deterrent. |
| Per-node return parity | **Misleading** | Per-machine, attacker wins by 100x–10,000x |
| Token value destruction | **Partial** | Attacker's minted tokens lose value from dilution, but this is a circular argument and doesn't prevent the attack |

**Key observations**:

1. **The attack is cheap post-bootstrap.** A 100-node localhost partition costs ~$60/year for a $5/month VPS and produces 26.3% annual dilution (first year). Hardware cost is not the defense — mathematical bounds are.

2. **Attack yields dilution, not theft.** Minted MHR dilutes ALL holders including the attacker. If the attacker holds fraction F of pre-attack supply, they lose F × dilution from their existing holdings. The net gain is `minted_amount - F × dilution × total_supply`, which decreases as the attacker's share of the network grows. An attacker who already holds significant MHR damages their own position by inflating supply.

3. **Repeated attacks offer no compounding advantage.** An attacker who merges and re-partitions continues at the same emission rate (epoch-counted, not wall-clock). The total damage over T epochs is ≤ E_s × T regardless of how many merge/split cycles occur. There is no "compound interest" — the attack is strictly linear per epoch, and the halving schedule steadily reduces E_s.

4. **CRDT merge is permissionless — but minting is audited.** CRDT merge rules adopt data automatically (settlements, counters, bloom filters converge). However, the [merge-time trust audit](#merge-time-trust-audit) validates the *minting component* separately — rejecting minting from partition nodes that lack cross-partition trust. Fresh-identity attacks produce 0% dilution; pre-planned attacks are discounted proportional to untrusted nodes.

5. **The protocol can distinguish trusted from untrusted nodes — not localhost from real devices.** 100 localhost processes are indistinguishable from 100 real devices during isolation. But on reconnection, the merge-time trust audit exposes them: zero cross-partition trust → 100% minting rejection. The defense works at merge time, not during isolation.

**Why these layers matter**: Each defense targets a different phase of the attack:
- Genesis attestation prevents the attack during bootstrap (when damage is maximal) — this is the only **complete** defense
- Active-set scaling limits emission rate regardless of economic activity — this is the primary quantitative defense
- Service burn imposes ~4% friction during isolation and, more importantly, absorbs excess supply after merge via ongoing 2% deflation on the entire network's economic activity

#### Solution: Trust-Gated Active Set + Merge-Time Trust Audit {#partition-defense}

The localhost attack exposes a gap: post-bootstrap, there is no mechanism that makes running virtual nodes on one machine more expensive than running one honest node. Two defense layers close this gap without introducing any centralized dependency.

##### Layer 1: Trust-Gated Active Set {#trust-gated-active-set}

Post-bootstrap, minting eligibility requires **mutual trust**: a node must have at least one **mutual trust link** with another active-set member to be minting-eligible. "Mutual" means both nodes have each other in their `trusted_peers` configuration.

```
Trust-gated minting eligibility:

  A node N is minting-eligible in epoch E if ALL of:
    1. N appears in ≥1 SettlementRecord in the last 2 epochs (active set)
    2. ∃ at least one node M such that:
       - M is also in the active set
       - N is in M.trusted_peers
       - M is in N.trusted_peers
       (i.e., N and M have a mutual trust link)

  Emission scaling (updated):
    trust_gated_active = number of active set nodes WITH ≥1 mutual trust link
    scaled_emission = emission(epoch) × min(trust_gated_active, 100) / 100

    Nodes without mutual trust links can still transact (channels,
    settlements) but do NOT contribute to the minting-eligible active set.

  Why mutual trust is expensive:
    Adding a node to your trusted_peers means:
      - You absorb their debts if they default
      - You relay their traffic for free
      - Your reputation is linked to theirs
    This economic cost makes mass trust fabrication expensive.
    An attacker needs real people to willingly vouch for fake nodes —
    each vouch exposes the voucher to economic loss.
```

**Why the trust gate does NOT prevent partition attacks during isolation:**

The trust gate is not the partition defense — the merge-time trust audit (Layer 2) is. Here's why:

```
During isolation:
  Attacker's 100 localhost nodes all trust each other.
  They satisfy the mutual-trust requirement trivially.
  They generate SettlementRecords among themselves.
  → Trust gate does NOT block minting during the partition.

The trust gate's value is structural:
  - It establishes trust relationships as a protocol-level concept
  - These relationships become the basis for merge-time auditing
  - It prevents nodes with zero social ties from entering the active set
    in the connected network (e.g., drive-by Sybil nodes)
```

**Impact on legitimate communities:**

| Scenario | Outcome |
|---|---|
| Village mesh, connected | Mutual trust between neighbors — mints normally |
| Village mesh, isolated | Mutual trust still valid — mints normally for any duration |
| New node joining | Gets mutual trust link with any existing trusted peer; can mint immediately |
| Nomadic node (no local trust) | Cannot mint until establishing mutual trust; can still transact via channels |

Unlike time-limited attestations, the trust gate never expires. Legitimate isolated communities mint indefinitely — the defense activates only at merge time.

##### Layer 2: Merge-Time Trust Audit {#merge-time-trust-audit}

The trust gate establishes trust relationships; the merge-time audit **uses those relationships to validate minting on reconnection**. This is the primary partition defense.

The key insight: **separate CRDT convergence from economic validation**. The CRDT merge is automatic and conflict-free (settlements, counters, bloom filters converge as designed). The *minting component* is audited separately.

```
Merge-time trust audit:

  When partition P reconnects to main network M:

  Step 1: CRDT merge (unchanged, automatic)
    Settlements, GCounters, epoch snapshots merge per existing rules.
    This is non-negotiable — CRDT convergence is preserved.

  Step 2: Identify divergent epoch range
    E_split = last common epoch between P and M
    divergent_epochs = P's epochs after E_split

  Step 3: Cross-partition trust scoring
    For each node N in P's active set during divergent epochs:
      cross_trust(N) = number of nodes in M's active set (at E_split)
                       that have N in their trusted_peers

    partition_trust_score = Σ min(1, cross_trust(N)) / |P.active_set|
      → 1.0 if every partition node is trusted by someone in the main network
      → 0.0 if no partition node has any external trust

  Step 4: Minting discount
    For each divergent epoch E in P's chain:
      accepted_minting(E) = P.epoch_minting(E) × partition_trust_score
      rejected_minting(E) = P.epoch_minting(E) × (1 - partition_trust_score)

  Step 5: Balance rebase
    For each node in P's active set:
      epoch_balance is adjusted to reflect only accepted minting
      This is applied as a rebase during the merge verification window
      (extends the existing 4-epoch grace period to 8 epochs for
      cross-partition merges)

  Step 6: Quarantine window
    Rejected minting enters a Q = 10 epoch quarantine.
    During quarantine, partition nodes can submit trust proofs:
      - Signed trust configs from M-side nodes that trust P-side nodes
      - Pre-partition channel histories showing real economic relationships
    If proofs are validated, quarantined minting is released.
    After Q epochs with no proofs: minting is permanently rejected
    (balance rebase becomes final).

Attack outcomes (with trust gate + merge audit combined):

  Fresh localhost (0 cross-trust):
    During isolation: mints freely (nodes trust each other)
    On merge: partition_trust_score = 0.0 → 100% rejected → 0% dilution ✓

  Pre-planned, 1 real trust link out of 100 nodes:
    During isolation: mints freely
    On merge: 1/100 nodes trusted → partition_trust_score = 0.01
    99% rejected → ~0.26% dilution per cycle ✓

  Pre-planned, deep infiltration (50 of 100 nodes trusted):
    During isolation: mints freely
    On merge: 50/100 trusted → partition_trust_score = 0.50
    50% accepted → ~33.3% dilution (one-shot, flagged after merge)
    Requires 50 real people to vouch for attacker nodes ⚠

  Legitimate village (all nodes trusted by external peers):
    partition_trust_score = 1.0 → 0% rejection → full minting accepted ✓
```

**Why this doesn't break CRDTs**: The CRDT merge (Step 1) is unconditional — data converges. The trust audit (Steps 3-6) operates on the *economic layer on top of the CRDT*. It adjusts `epoch_balance` during the verification window, which is an existing mechanism (settlement proofs already modify balances during the grace period). The audit extends this same mechanism to minting validation.

##### Combined Defense Summary

:::info[Specification]
Five defense layers — trust-gated active set, merge-time trust audit, active-set-scaled emission, 2% service burn, and halving schedule — combine to bound isolated partition damage. Fresh-identity attacks achieve 0% dilution on merge.
:::

| Attack variant | Trust gate alone | Trust gate + merge audit | Notes |
|---|---|---|---|
| Fresh localhost (100 virtual nodes) | Mints during isolation | **0% dilution on merge** | 100% minting rejected — no cross-partition trust |
| Pre-planned, no trust infiltration | Mints during isolation | **~0% dilution** | All nodes untrusted → 100% rejection |
| Pre-planned, 1 trust link | Mints during isolation | **~0.26% dilution** | 99 untrusted → 99% rejection |
| Pre-planned, deep infiltration (50%) | Mints during isolation | **~33.3% dilution** | One-shot; requires 50 real vouchers |
| Legitimate village | Full minting | Full minting | All nodes trusted → 0% rejection |

**Note on neighborhood-scoped minting**: An alternative structural defense — each trust neighborhood minting its own denomination with market-set exchange rates — would achieve 0% dilution even against deep infiltration. However, it introduces ~10x implementation complexity, destroys the single global currency, creates new attack surfaces (exchange rate manipulation), and hurts legitimate nomadic users. See [Partition Defense Comparison](../development/partition-defense-comparison) for the full analysis.

#### Can This Attack Ruin the Network?

No. With the [trust-gated active set](#trust-gated-active-set) + [merge-time trust audit](#merge-time-trust-audit), the most common attack variants are eliminated entirely:

1. **Fresh-identity attacks produce zero dilution.** 100 virtual nodes on localhost with no external trust connections → merge-time trust audit rejects 100% of their minting on reconnection (zero cross-partition trust). Result: 0% dilution.

2. **Pre-planned attacks with minimal infiltration produce negligible dilution.** Attacker pre-positions nodes, establishes 1 real trust link, then isolates. On reconnection, merge-time trust audit rejects ~99% of minting. With 1 out of 100 nodes trusted → ~0.26% dilution per cycle.

3. **Damage rate decreases over time.** Each halving period (≈ 1.9 years), the attacker's per-epoch minting is halved. Combined with merge audit rejection, effective damage is a small fraction of an already-decaying emission schedule.

4. **Network value grows faster than attacker damage.** A healthy network's total economic value (real services transacted) grows with adoption, while the attacker's dilution rate shrinks with each halving and each audit rejection. The ratio of attack damage to network value decreases over time.

The fundamental tradeoff: Mehr chooses **partition tolerance over inflation resistance**. A globally-consistent ledger (blockchain) can prevent this attack entirely, but at the cost of requiring global consensus — which fails during partitions. Mehr accepts bounded, audited, decreasing inflation from isolated partitions in exchange for partition tolerance. The trust-gated active set + merge-time trust audit make this tradeoff far more favorable than pure mathematical bounds alone.

**Residual risk**: The remaining exposure is **deep trust infiltration** — an attacker who gets ≥50% of their partition nodes trusted by main-network peers before isolating. In this worst case, ~33.3% dilution passes the merge audit (one-shot). This scenario requires sustained social engineering — convincing 50 real people to add attacker nodes to their `trusted_peers`, each person accepting economic liability for the attacker's debts. This is visible, one-shot (flagged after the first merge), and bounded by the halving schedule. See the [Partition Defense Comparison](../development/partition-defense-comparison) for the design rationale and analysis of neighborhood-scoped minting as an alternative.

### Attack: Artificial Partition Creation

**Description**: Attacker deliberately creates multiple isolated partitions they control, maximizing total minting across all partitions.

**Defense**:

```
Multi-partition attack economics (with active-set scaling + burn):

  K partitions, each with N_k nodes fully controlled by attacker
  Total attacker nodes: Σ N_k

  Per-partition max growth: (N_k / 100) × E per epoch
  Per-partition max over T epochs: (N_k / 100) × E × T

  Total attacker max growth: Σ (N_k / 100) × E per epoch
                            = (Σ N_k / 100) × E per epoch

  Key insight: splitting nodes across K partitions gives the SAME total
  growth rate as one partition with Σ N_k nodes. There is no advantage
  to fragmenting into multiple partitions.

  During bootstrap: genesis-anchored minting prevents all isolated
  partitions from minting regardless of K.

  Cost:
    - K sets of hardware (real physical devices)
    - Initial MHR capital in each partition
    - No scaling advantage over a single partition of the same total size
```

**Residual risk**: No advantage over single-partition attack. Same per-epoch growth bound applies. During bootstrap, completely prevented by genesis attestation.

### Attack: Channel Balance Inflation

**Description**: Attacker creates payment channels with inflated balances not backed by actual MHR holdings on the CRDT ledger.

**Defense**: Settlement validation is performed by **every receiving node**, which checks that neither party's derived balance goes negative after applying the settlement. Derived balance = `epoch_balance + delta_earned - delta_spent`, which is deterministic from the CRDT state. A node cannot claim more MHR than the ledger attributes to it.

Channel opening requires both parties to sign the initial state. The balances must be backed by ledger holdings. Creating MHR from nothing requires forging the CRDT state, which requires forging settlement records (dual Ed25519 signatures) or corrupting epoch snapshots (67% acknowledgment threshold).

**Residual risk**: None under normal operation. In a fully attacker-controlled partition, the attacker can corrupt the local CRDT state — but this reduces to the [Isolated Partition](#attack-isolated-partition) attack, defended by [trust-gated active set + merge-time trust audit](#partition-defense).

### Attack: Double-Spend via Old Channel State

**Description**: One party publishes an old channel state (lower sequence number, more favorable balance) to claim funds already spent.

**Defense**: The dispute resolution window (2,880 gossip rounds, ~48 hours) allows the counterparty to submit a higher-sequence state, which always wins. After the window, the latest submitted state is final. Channel abandonment (4 epochs of inactivity) allows unilateral close with the last mutually-signed state. See [Bilateral Payment Channels](payment-channels#channel-lifecycle).

**Residual risk**: If the honest counterparty is offline for >48 hours during a dispute, they cannot submit the newer state. Mitigated by the probabilistic double-spend detection in the CRDT ledger and by economic disincentive (blacklisting makes the one-time gain smaller than the cost of losing network identity).

### Attack: Settlement Forgery

**Description**: Forge settlement records to credit attacker with unearned balance on the CRDT ledger.

**Defense**: Settlement records require Ed25519 signatures from BOTH parties. Forging requires compromising both private keys. Every receiving node validates both signatures independently against the settlement hash. Invalid settlements are silently dropped and not gossiped.

**Residual risk**: None without private key compromise.

### Attack: CRDT Counter Manipulation

**Description**: Inflate GCounter entries in the CRDT ledger to increase balance without corresponding economic activity.

**Defense**: GCounter entries are per-node — each processing node writes only to its own entry. Merge takes pointwise maximum. Increases must correspond to valid settlement records, which require dual Ed25519 signatures. A node that inflates its own entry without corresponding settlements is detectable by any peer that compares the claimed delta against available settlement records during the epoch verification window.

**Residual risk**: In a partition where all verifiers are attacker nodes, inflation goes undetected locally. On merge, this reduces to the [Isolated Partition](#attack-isolated-partition) attack — defended by [trust-gated active set + merge-time trust audit](#partition-defense), and corrected during epoch reconciliation.

### Attack: VRF Lottery Manipulation

**Description**: Relay node tries to influence the VRF output to win the lottery more frequently.

**Defense**: The VRF (ECVRF-ED25519-SHA512-TAI, RFC 9381) produces exactly **one valid output** per (private_key, packet_hash) pair. The relay cannot "grind" through values — there is only one valid output for each packet. The VRF proof is verifiable by any party using the relay's public key. Changing the relay key changes the node identity (and forfeits accumulated reputation).

**Residual risk**: None (cryptographic guarantee).

### Attack: Trust/Credit Exploitation

**Description**: Attacker gains trust from peers, extracts maximum credit, then defaults on the debt.

**Defense**: Credit limits are per-peer, per-epoch, configurable by the vouching node. The voucher absorbs the debt (economic skin in the game — you only trust people you'd lend to). Transitive credit decays (10% per hop, max 2 hops). Trust is revocable at any time. See [Trust & Neighborhoods](trust-neighborhoods).

**Residual risk**: One-time loss up to the extended credit limit. Mitigated by conservative credit settings and the social cost of defaulting (loss of all trust relationships in the network).

### Defense Summary

| Attack Vector | Primary Defense | Residual Risk |
|---|---|---|
| Self-dealing (connected) | Non-deterministic assignment + net-income cap | None |
| Channel cycling | Net-income revenue cap | None |
| Sybil DHT positioning | Reduces to self-dealing proof | None (connected) |
| Content/Job ID grinding | Unpredictable epoch_hash | None |
| Relay non-forwarding | VRF requires real packet + sender detection | Individual packet drops |
| Storage/compute fabrication | Bilateral client verification | Brief undetected period |
| **Isolated partition** | **Trust-gated active set + merge-time trust audit + burn + scaled emission** | **Fresh IDs: 0% dilution on merge. Pre-planned: audit-discounted on merge** |
| Artificial partition creation | Same as isolated partition; no advantage to splitting | Same per-epoch growth bound |
| Channel balance inflation | CRDT ledger validation | None (connected) |
| Double-spend (old state) | 48-hour dispute window | Offline counterparty |
| Settlement forgery | Dual Ed25519 signatures | None |
| CRDT counter manipulation | Per-node entries + settlement proof | Reduces to partition attack |
| VRF lottery manipulation | Cryptographic (one output per input) | None |
| Trust/credit exploitation | Credit limits + voucher absorbs debt | One-time credit loss |

**All attack vectors are bounded.** The isolated partition — the only vector with material residual risk — is defended by five layers:

1. **Trust-gated active set** ([details](#trust-gated-active-set)): Post-bootstrap, minting requires ≥1 mutual trust link. Prevents zero-social-tie nodes from minting in connected networks. During isolation, attacker nodes satisfy this trivially — the defense activates at merge time.
2. **Merge-time trust audit** ([details](#merge-time-trust-audit)): On reconnection, minting from untrusted partition nodes is rejected. Fresh-identity attacks → 0% dilution. Pre-planned with minimal infiltration → ~0.26% dilution.
3. **Active-set-scaled emission**: Limits small-partition minting rate — the primary quantitative defense.
4. **2% service burn**: Provides ~4% friction during isolation and absorbs excess supply after merge.
5. **Halving schedule**: Cumulative excess converges — the exponentially decaying emission bounds lifetime dilution.

**Hardware cost is not a meaningful defense** — 100 virtual nodes can run on a single $5/month machine ([localhost attack](#localhost-attack)), ~$60/year. The defense rests on merge-time trust audit (rejects minting from untrusted nodes on reconnection) and mathematical bounds (halving, active-set cap). See [Attacker Economics](#attacker-economics-cost-vs-damage), [Localhost Attack](#localhost-attack), and [Partition Defense](#partition-defense) for the full analysis.

For the worst-case residual scenario (attacker deeply infiltrates the trust graph with 50% of partition nodes trusted by main-network peers), dilution is ~33.3% one-shot — still bounded by halving and flagged after the first merge. See the [Partition Defense Comparison](../development/partition-defense-comparison) for the design rationale and analysis of neighborhood-scoped minting as an alternative.

## Long-Term Sustainability

Does MHR stay functional for 100 years?

### Economic Equilibrium

```
Supply dynamics over time:

  Year 0-10:   High minting emission, rapid supply growth
               2% service burn provides continuous deflationary pressure
               Lost keys: ~1-2% annually (negligible vs. emission)
               Economy bootstraps; genesis attestation prevents partition exploits

  Year 10-30:  Minting decays significantly (many halvings)
               Burns + lost keys accumulate (~10-40% of early supply permanently gone)
               Effective circulating supply stabilizes faster than without burns
               Genesis attestation sunsets at first halving; burns + scaling take over

  Year 30+:    Tail emission ≈ burns + lost keys
               Tighter equilibrium than lost keys alone
               All income is from bilateral payments + residual minting
```

The tail emission exists specifically for this: it ensures service providers always have a minting incentive, even centuries from now. Lost keys, service burns, and tail emission create a tight equilibrium — new supply enters through service, old supply exits through burns and lost keys. Neither grows without bound. The 2% service burn accelerates the approach to equilibrium compared to relying on lost keys alone.

### Technology Evolution

| Challenge | Mehr's Answer |
|-----------|--------------|
| **New radio technologies** | Transport-agnostic — any medium that moves bytes works |
| **Post-quantum cryptography** | [KeyRotation](../services/mhr-id) claims enable key migration; new algorithms plug into existing identity framework |
| **Hardware evolution** | Capability marketplace adapts — nodes advertise what they can do, not what they are |
| **Protocol upgrades** | [MEP governance](../protocol/versioning#governance) — trust-weighted version signaling via announces, ≥67% acceptance threshold. Communities can fork; gateway bridges maintain connectivity across versions |

### What Doesn't Change

The fundamental economic model — free between trusted peers, paid between strangers — is as old as human commerce. It doesn't depend on any specific technology, cryptographic primitive, or hardware platform. As long as people want to communicate and are willing to help their neighbors, the model works.

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>Can an attacker inflate the token supply by running virtual nodes on a single machine?</summary>

During bootstrap (first ~1.9 years), genesis-anchored minting completely prevents this — isolated partitions without genesis connectivity get zero minting. Post-bootstrap, an attacker can mint during isolation, but the merge-time trust audit rejects 100% of minting from nodes with zero cross-partition trust on reconnection. Fresh-identity localhost attacks produce 0% dilution. Even deep infiltration (50% of nodes trusted) is bounded to ~33.3% one-shot dilution, flagged after the first merge.

</details>

<details className="faq-item">
<summary>What is the worst-case supply dilution from a partition attack?</summary>

Lifetime dilution from a 3-node isolated partition running indefinitely is approximately 1.5% of total supply — and this assumes 100% minting acceptance on merge, ignoring the trust audit. With the merge-time trust audit, fresh-identity attacks produce 0% dilution. Active-set-scaled emission limits a 3-node partition to just 3% of full emission per epoch. The halving schedule ensures cumulative excess converges geometrically, and the 2% service burn provides additional friction.

</details>

<details className="faq-item">
<summary>How does the channel cycling attack work and why is it fully neutralized?</summary>

In a cycling attack, two colluding nodes pass MHR back and forth to inflate gross channel debits and reach the minting ceiling. The defense is the net-income revenue cap: minting eligibility uses net income (income minus spending per provider), not gross debits. In any closed cycle — same-channel, cross-channel triangle, or settlement-mediated — every participant's income equals their spending, producing net income of zero. Only one-directional flows (real demand) generate positive net income.

</details>

<details className="faq-item">
<summary>What prevents an attacker from forging settlement records or VRF lottery outcomes?</summary>

Settlement records require valid Ed25519 signatures from both parties — forging requires compromising both private keys. Every receiving node independently validates both signatures before accepting. For VRF lottery manipulation, the ECVRF-ED25519-SHA512-TAI function produces exactly one valid output per (relay key, packet hash) pair. The relay cannot grind through values since there is only one valid output per packet — this is a cryptographic guarantee.

</details>

<details className="faq-item">
<summary>How does the trust-gated active set differ from traditional staking?</summary>

Unlike staking (which requires locking up tokens as collateral), the trust-gated active set requires mutual trust relationships — another active-set member must have you in their trusted_peers, and you must have them in yours. Adding someone to your trusted_peers means absorbing their debts if they default and relaying their traffic for free, making mass trust fabrication economically expensive. This social-economic cost replaces financial collateral without requiring locked capital.

</details>

<!-- faq-end -->

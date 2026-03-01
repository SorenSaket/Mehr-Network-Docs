---
sidebar_position: 7
title: Voting
description: "Sybil-resistant voting using trust-flow analysis instead of one-person-one-vote, with secret ballot support."
keywords:
  - voting
  - Sybil resistance
  - trust flow
  - secret ballot
  - governance
  - PageRank
---

# Voting

Voting on a decentralized mesh has a fundamental problem: **how do you tell 1 person with 50 keys apart from 50 people with 1 key each?** You can't. So instead of trying to count people, Mehr counts **trust flow** — how much trust the honest network places in you. Creating 50 fake accounts doesn't increase the trust flowing into you. It just divides it thinner.

:::info[App Manifest]
Voting is packaged as a **Headless** (compute only) [AppManifest](../services/mhr-app). It composes MHR-Compute contracts for trust-flow analysis, vote tallying, and secret ballot commit/reveal logic; MHR-Store for signed ballot storage and election configuration DataObjects; and MHR-DHT for voter eligibility lookups. No UI bundle is included — front-end rendering is handled by the host application that triggers the voting contract.
:::

## The Attack

Before designing defenses, understand the attack:

```
The Sybil Cluster:
  1. Attacker creates 50 NodeIDs
  2. All 50 claim GeoPresence for "portland"
  3. All 50 vouch for each other's geographic claims
  4. Attacker establishes 2-3 trust links from fake nodes to real Portland nodes
  5. Under naive "one verified node, one vote": attacker gets 50 votes

  The 50 fake nodes look internally healthy:
    - They all have vouches ✓
    - They all have RadioRangeProof (attacker has radios) ✓
    - They all trust each other ✓
    - They have outbound trust links to real nodes ✓
```

Every defense below targets a different property of this attack.

## Defense Layer 1: Trust Flow Voting

The core anti-Sybil mechanism. Instead of counting votes, Mehr computes **how much trust flows from the broader honest network into each voter**.

### How It Works

Think of trust like water flowing through pipes. Each honest node is a faucet that produces 1.0 units of trust. Trust flows along trust edges, splitting equally among outbound connections. After many iterations, each node's accumulated trust is its **vote weight**.

```
TrustFlow algorithm (per voting scope):

  1. Initialize: every node in scope gets trust_balance = 1.0
  2. For each iteration (converge after ~10 rounds):
     For each node N:
       outflow = trust_balance(N) / count(N.trusted_peers_in_scope)
       For each trusted peer P of N:
         trust_balance(P) += outflow × damping_factor
     Normalize so total trust in system = number of nodes
  3. Node's vote weight = final trust_balance

  damping_factor = 0.85 (same as PageRank — prevents trust cycling)
```

### Why This Kills Sybil Clusters

```
Honest network (48 real Portland nodes):
  Each real node receives trust from multiple independent real nodes
  Total trust flowing into honest network ≈ 48.0

Sybil cluster (50 fake nodes, 2 outbound trust links):
  Trust enters the cluster ONLY through those 2 edges
  Total trust flowing into entire cluster ≈ 2.0 × damping_factor ≈ 1.7
  Per-Sybil vote weight ≈ 1.7 / 50 = 0.034

  Real node vote weight ≈ 1.0
  50 Sybils × 0.034 = 1.7 total Sybil voting power
  vs. 48 real nodes × ~1.0 = ~48.0 honest voting power
```

**Creating more Sybil nodes makes each one weaker.** The attacker's total voting power is bounded by their inbound trust edges, not their node count. To get 10 votes worth of power, you need 10 real trust relationships — which means convincing 10 real people to trust you, which is expensive and slow.

### Properties

- **Bottleneck principle**: A cluster's total vote weight is bounded by its inbound trust from outside the cluster
- **Dilution**: Adding more Sybil nodes divides the limited inbound trust thinner
- **Locally computable**: Each node runs TrustFlow from its own perspective on its known trust graph. No global consensus needed.
- **Converges quickly**: ~10 iterations on a neighborhood-sized graph (~100 nodes). Feasible on Raspberry Pi class hardware.

## Defense Layer 2: Personhood Vouching

Trust flow handles the math, but there's a social layer too. A **PersonhoodVouch** is a stronger assertion than a regular vouch:

```
PersonhoodVouch {
    voucher: NodeID,
    subject: NodeID,               // "I attest this is a unique human being"
    scope: HierarchicalScope,      // "...in Portland"
    epoch: u64,                    // when issued
    signature: Ed25519Sig,
}
```

### Scarcity Rules

| Rule | Value | Rationale |
|------|-------|-----------|
| Max personhood vouches per node per scope | 5 per epoch | You can't personally know 500 people well enough to vouch for them |
| Vouch expiry | 10 epochs | Forces periodic re-confirmation (people move, leave) |
| Revocable | Immediately | If you discover a Sybil, revoke instantly |

### Economic Liability

If a node you personhood-vouched for is later identified as a Sybil (via trust flow analysis or liveness challenge failure):

```
Sybil detection penalty:
  1. Your PersonhoodVouches for the flagged node are invalidated
  2. Your own vote weight multiplier decreases by 10% per bad vouch
  3. If you vouched for 3+ identified Sybils: you lose voting eligibility
     for the current vote (suspicious — either complicit or negligent)
  4. Penalty decays over 5 epochs (recoverable mistake, not permanent ban)
```

This makes personhood vouching **costly to get wrong** — you're putting your own voting power on the line.

### Personhood vs. Geographic Vouches

| | Geographic Vouch | Personhood Vouch |
|---|---|---|
| Asserts | "This node is in Portland" | "This node is a unique human in Portland" |
| Limit | Unlimited per epoch | 5 per scope per epoch |
| Economic penalty | None (information only) | Vote weight reduction if subject is Sybil |
| Required for voting | Yes | Yes (minimum 2 from distinct vouchers) |
| Can be automated | Yes (RadioRangeProof bots) | No (must be a conscious human decision) |

## Defense Layer 3: Hardware Liveness Challenge

For high-stakes votes, the protocol can require voters to prove they control **distinct physical hardware** simultaneously.

### Challenge Protocol

```
Liveness challenge (triggered by vote initiator for high-stakes votes):

  1. ANNOUNCE: Vote coordinator broadcasts challenge_nonce on LoRa
     Challenge {
         vote_id: Blake3Hash,
         nonce: [u8; 16],
         response_window: Duration,     // e.g., 30 seconds
     }

  2. RESPOND: Each voter must broadcast a signed response via LoRa
     ChallengeResponse {
         voter: NodeID,
         vote_id: Blake3Hash,
         nonce: [u8; 16],
         response_nonce: [u8; 16],      // voter's own random nonce
         signature: Ed25519Sig,
     }

  3. VERIFY: Witnesses observe LoRa responses
     - Each response must arrive as a distinct radio transmission
     - Responses from the same radio (same signal fingerprint, same antenna)
       within the response window indicate a single physical device
     - Witnesses sign attestations of which NodeIDs they observed
       as distinct transmissions

  4. RESULT: Voters who failed the liveness challenge have their
     vote weight zeroed for this vote
```

### Why This Works

An attacker with 50 NodeIDs but 3 LoRa radios:
- Can only transmit 3 distinct responses within the window
- The other 47 NodeIDs either don't respond (weight = 0) or respond from the same radio (detected by witnesses, weight = 0)
- Net result: 3 votes, not 50

### Radio Fingerprinting Algorithm

Witnesses distinguish distinct radios using a **multi-feature classifier** based on physical-layer characteristics:

```
Radio fingerprinting features:

  1. RSSI Pattern (primary):
     Multiple witnesses at known positions measure RSSI of each response.
     The RSSI vector (e.g., [-80, -65, -92] across 3 witnesses) forms
     a spatial signature. Two responses from the same antenna produce
     similar RSSI vectors; different antennas at different locations
     produce different vectors.

     Similarity metric:
       rssi_distance(a, b) = euclidean_distance(a.rssi_vector, b.rssi_vector)
       same_radio_threshold = 6 dB (total across all witnesses)
       Responses with rssi_distance < threshold → flagged as same radio

  2. Clock Drift (secondary):
     LoRa transmitters have slightly different crystal oscillator frequencies.
     Carrier frequency offset (CFO) measured by witnesses provides a
     per-radio fingerprint. CFO is stable over short time windows (minutes)
     but varies between different hardware units.

     Precision: ±50 Hz resolution on typical LoRa receivers
     Discrimination: most LoRa modules differ by >200 Hz CFO

  3. Timing Offset (tertiary):
     The exact arrival time of each response (measured in LoRa symbol
     periods) varies by radio — crystal accuracy affects transmission
     start time. With 30-second response windows, timing alone is weak
     but provides corroborating evidence.

  Combined classifier:
    fingerprint_score(a, b) = w1 × rssi_similarity(a, b)
                            + w2 × cfo_similarity(a, b)
                            + w3 × timing_similarity(a, b)
    Weights: w1=0.5, w2=0.35, w3=0.15

    same_radio if fingerprint_score > 0.75
```

### Error Rates

```
Estimated error rates (based on LoRa fingerprinting literature):

  False positive (two DIFFERENT radios classified as same):
    Urban (high interference):   ~3-5%
    Suburban (moderate):          ~1-2%
    Rural (low interference):    <1%

  False negative (SAME radio classified as different):
    With antenna/location change: ~5-10%
    Static position:              <1%

  Discrimination capacity:
    Typical LoRa deployment: 15-30 distinct radios reliably distinguished
    in a ~1 km² area with 3+ witnesses.
    Above ~50 radios: RSSI vectors become crowded; CFO becomes primary
    discriminant. Practical limit: ~100 radios per geographic cluster
    (bounded by witness processing, not physics).

  Known limitations:
    - Identical hardware from the same batch may have similar CFO
      (mitigated by RSSI spatial diversity)
    - An attacker can use directional antennas to manipulate RSSI
      (mitigated by requiring 3+ geographically distributed witnesses)
    - Environmental changes (temperature, humidity) shift CFO over hours
      (mitigated by the 30-second challenge window being much shorter)
```

### Remote Voter Sybil Resistance

Hardware liveness only works for LoRa-reachable voters. For internet-connected remote voters, Sybil resistance relies on the other defense layers:

```
Remote voter anti-Sybil (no hardware liveness):

  Layer 1: Trust Flow — still the primary defense. Remote Sybils need
           real inbound trust edges from the honest network.

  Layer 2: Personhood Vouching — remote voters still need 2 personhood
           vouches from distinct vouchers who know them personally.

  Layer 3: Temporal Requirements — 10+ epoch account age, service history.

  Layer 4 (remote-specific): IP/Transport Diversity Check
    Remote voters submit votes via internet gateways. Gateways record
    the transport metadata (not stored, just checked in real-time):
      - Multiple votes from the same gateway within the response window
        are flagged for additional scrutiny
      - Witnesses at gateways sign attestations of transport-layer diversity
      - NOT a hard block — just a weight reduction (0.8x multiplier)
        for same-gateway submissions

  Net effect:
    Remote voters have LOWER maximum vote weight than locally-present voters
    (they cannot earn the StronglyVerified geo multiplier of 1.2x).
    Their vote weight is capped at:
      trust_flow × 1.0 (Verified geo, not StronglyVerified) × age × service
    This naturally preferences local, physically-present voters for
    geo-scoped decisions — which is the correct behavior.
```

### Limitations

- Only works for LoRa-reachable voters (not internet-connected nodes voting remotely)
- Radio fingerprinting is imperfect — different radios may have similar characteristics
- Adds latency (30-second challenge window)
- Requires honest witnesses (but witnesses are selected from the trust graph, so Sybil witnesses are low-weight)

Liveness challenges are **optional** — the vote initiator decides whether the stakes warrant them. For a neighborhood potluck vote: probably not. For a community resource allocation: yes.

## Defense Layer 4: Temporal Requirements

You can't create accounts and vote immediately. Voting eligibility requires sustained presence:

```
VotingEligibility {
    voter: NodeID,
    scope: HierarchicalScope,

    // Identity requirements
    geo_verification: GeoVerificationLevel,  // from IdentityClaim
    personhood_vouches: u8,                  // minimum 2, from distinct vouchers
    account_age_epochs: u64,                 // minimum 10 epochs in scope

    // Trust flow (fixed-point: raw_value / 65536 = actual weight)
    trust_flow_weight: u32,                  // from TrustFlow algorithm, fixed-point Q16.16

    // Service history (optional, increases weight)
    service_reputation: u16,                 // from PeerReputation
    epochs_of_service: u64,                  // epochs providing relay/storage/compute in scope
}
```

### Minimum Thresholds

| Requirement | Minimum | Rationale |
|-------------|---------|-----------|
| Account age in scope | 10 epochs | Can't create accounts the day of a vote |
| Personhood vouches | 2 from distinct vouchers | At least 2 real people know you |
| Geographic verification | WeaklyVerified or above | At least some evidence of presence |
| Trust flow weight | greater than 0 | Must have at least one inbound trust edge from outside your immediate cluster |

### GeoVerificationLevel

```
GeoVerificationLevel: enum {
    Unverified,         // self-declared only, no vouches (cannot vote)
    WeaklyVerified,     // 1-2 peer vouches (limited voting weight)
    Verified,           // 3+ peer vouches OR RadioRangeProof (full voting weight)
    StronglyVerified,   // RadioRangeProof + 3+ peer vouches (maximum weight)
}
```

### Time Cost of Sybil Attack

To create a voting-eligible Sybil identity, an attacker must:

1. Create a NodeID (instant, free)
2. Wait 10 epochs (days to weeks — can't rush)
3. Get 2 personhood vouches from real people (social engineering required)
4. Establish trust links to honest nodes (requires providing real service)
5. Maintain presence throughout (continuous hardware operation)

**Per-identity cost**: significant time + hardware + social engineering. And after all that, the trust flow algorithm still limits the cluster's total voting power to its inbound trust edges.

## Vote Weight Formula

A voter's weight combines trust flow with eligibility multipliers:

```
vote_weight(node) = trust_flow_weight
                    × geo_multiplier
                    × age_multiplier
                    × service_multiplier

Where:
  trust_flow_weight:  from TrustFlow algorithm (the primary anti-Sybil signal)

  geo_multiplier:
    Unverified:          0.0  (cannot vote)
    WeaklyVerified:      0.5
    Verified:            1.0
    StronglyVerified:    1.2

  age_multiplier:
    min(account_age_epochs / 100, 1.5)
    (linear growth, capped at 1.5x after 100 epochs)

  service_multiplier:
    1.0 + min(epochs_of_service / 200, 0.5)
    (bonus for service providers, capped at 1.5x)
```

### Attack Scenarios

| Scenario | Attacker's Total Voting Power | Why |
|----------|-------------------------------|-----|
| 50 Sybils, 2 outbound trust edges | ~1.7 votes | Trust flow bottleneck |
| 50 Sybils, 10 outbound trust edges | ~8.5 votes | More edges help, but 10 real trust relationships is expensive |
| 50 Sybils, 0 outbound trust edges | 0 votes | No trust flows into the cluster at all |
| 1 real node, bribes 5 nodes to delegate | ~6 votes | Possible, but the bribed nodes risk their own weight if caught |
| 50 Sybils, all with service history | ~1.7 votes | Service multiplier helps, but trust flow is the dominant factor |

## Voting Mechanisms

### Simple Majority (Trust-Weighted)

```
Vote {
    voter: NodeID,
    vote_id: Blake3Hash,           // identifies the proposal
    choice: enum { Yes, No, Abstain },
    signature: Ed25519Sig,
}

Tally:
    yes_weight  = sum(vote_weight(v) for v where v.choice == Yes)
    no_weight   = sum(vote_weight(v) for v where v.choice == No)
    total_weight = yes_weight + no_weight

    Result: Yes wins if yes_weight / total_weight > 0.5
```

Suitable for binary decisions. Each voter's influence is proportional to their trust flow weight.

### Quadratic Voting

Voters spend MHR tokens to express preference intensity:

```
QuadraticVote {
    voter: NodeID,
    vote_id: Blake3Hash,
    choice: enum { Yes, No },
    tokens_spent: u64,            // μMHR committed to this vote
    signature: Ed25519Sig,
}

Vote power = sqrt(tokens_spent) × trust_flow_weight

Cost for N units of influence = N² μMHR
```

Properties:
- Splitting tokens across Sybil identities doesn't help: `sqrt(100) = 10` but `10 × sqrt(1) = 10` — same result whether one identity spends 100 or ten identities each spend 1
- Trust flow weight still applies — Sybils with low trust flow get reduced power even with tokens
- Allows expressing "I care a lot about this" vs. "I have a mild preference"
- Tokens are burned (not redistributed) to prevent vote-buying markets

### Liquid Democracy

Delegate your vote to someone you trust:

```
VoteDelegation {
    delegator: NodeID,
    delegate: NodeID,              // who receives my voting power
    scope: HierarchicalScope,      // delegation scope (can be narrow)
    vote_id: Option<Blake3Hash>,   // None = standing delegation, Some = per-vote
    signature: Ed25519Sig,
}

Rules:
    - Delegation chains: A delegates to B, B delegates to C
      → C votes with weight(A) + weight(B) + weight(C)
    - Max chain length: 3 hops (prevents unbounded accumulation)
    - Override: delegator can vote directly at any time, revoking delegation
    - Circular delegation: detected and broken (the delegation with the latest
      timestamp in the cycle is dropped; if timestamps tie, highest NodeID breaks it)
    - Delegation is public (necessary for tally verification)
```

Natural fit for Mehr's trust graph — you delegate to people you've already marked as trusted. Combines the convenience of representative democracy with the option of direct participation.

## Vote Lifecycle

```
1. PROPOSE: Any eligible node publishes a Proposal
   Proposal {
       proposer: NodeID,
       scope: HierarchicalScope,          // who can vote
       title: String,
       description: String,
       mechanism: enum { SimpleMajority, Quadratic, Liquid },
       liveness_challenge: bool,          // require hardware liveness?
       voting_period: u32,                // epochs
       quorum: f32,                       // minimum participation (0.0-1.0)
       signature: Ed25519Sig,
   }

2. ELIGIBILITY: Each node locally computes voter eligibility
   - Run TrustFlow on known trust graph within scope
   - Check personhood vouches, account age, geo verification
   - Nodes that don't meet thresholds cannot submit votes

3. CHALLENGE (optional): If liveness_challenge is true
   - Coordinator broadcasts LoRa challenge
   - Voters respond within window
   - Witnesses attest to distinct transmissions

4. VOTE: Eligible nodes submit votes during voting_period
   - Votes are immutable DataObjects stored via MHR-Store
   - Votes propagate via MHR-Pub within the proposal's scope
   - Each node can submit one vote per proposal (latest wins if resubmitted)

5. TALLY: Each node computes the result locally
   - Collect all Vote DataObjects for this proposal
   - Verify signatures and eligibility for each voter
   - Compute trust_flow_weight for each voter from local trust graph
   - Apply vote weight formula
   - Sum weighted votes per choice
   - Check quorum: total participating weight must meet threshold

6. RESULT: Local tally is the result from each node's perspective
   - In a well-connected community, all honest nodes converge on the same result
   - In a partitioned network, different partitions may see different results
     (consistent with Mehr's eventual consistency — reconcile when partition heals)
```

## Quorum and Validity

| Community Size (eligible voters) | Default Quorum | Rationale |
|----------------------------------|---------------|-----------|
| Fewer than 10 nodes | 60% | Small community, high participation needed |
| 10–50 nodes | 40% | Medium community |
| 50–200 nodes | 25% | Larger community |
| More than 200 nodes | 15% | Large community, representative participation |

Quorum is measured by **trust flow weight**, not node count. A quorum of 25% means "voters representing 25% of total trust flow weight in the scope participated" — not "25% of NodeIDs voted."

## Privacy Considerations

Votes on Mehr are **public by default** — every vote is a signed DataObject visible to anyone in scope. This enables:
- Full auditability (anyone can verify the tally)
- Accountability (voters stand behind their choices)
- Delegation transparency (you can see who your delegate voted for)

The tradeoff is no ballot secrecy, which enables social pressure and coercion. For communities that need secret ballots, Mehr provides a **commitment-scheme secret ballot** mechanism designed for partition-prone meshes.

### Secret Ballot Protocol

```
Secret ballot specification:

  1. COMMIT PHASE (during voting_period):
     Voter publishes:
       VoteCommitment {
           voter: NodeID,
           vote_id: Blake3Hash,
           commitment: Blake3(choice || random_nonce || voter_id),
           commit_epoch: u64,
           signature: Ed25519Sig,
       }
     The commitment hides the vote choice. The voter_id in the hash
     prevents two voters with the same choice+nonce from producing
     identical commitments.

  2. REVEAL PHASE (reveal_period epochs after voting_period ends):
     Voter publishes:
       VoteReveal {
           voter: NodeID,
           vote_id: Blake3Hash,
           choice: enum { Yes, No, Abstain, ... },
           nonce: [u8; 32],
           signature: Ed25519Sig,
       }
     Verifier checks: Blake3(choice || nonce || voter_id) == commitment

  3. TALLY PHASE (after reveal_period ends):
     Count all valid reveals. Unrevealed commits are counted as abstentions.
```

### Partition-During-Reveal Handling

A voter who commits but is partitioned during reveal has their vote lost (counted as abstention). This is unavoidable without global consensus. Mehr mitigates the impact:

```
Partition-safe reveal rules:

  Reveal extension window:
    reveal_period = voting_period × 2  (default)
    The reveal window is deliberately long to tolerate temporary partitions.
    A voter who reconnects within the reveal period can still reveal.

  Quorum adjustment for unrevealed commits:
    unrevealed_count = commits - reveals
    If unrevealed_count / total_commits > 0.20:
      The vote is marked INCONCLUSIVE — too many voters were unable to reveal.
      The proposer may re-run the vote with a longer reveal_period.

  Partial reveal acceptance threshold:
    A tally is valid if reveals >= max(quorum_threshold, 0.80 × total_commits).
    Below 80% reveal rate: vote is INCONCLUSIVE.
    Above 80% reveal rate: tally proceeds normally.

  Rationale: 80% threshold ensures that a partition affecting up to 20%
  of voters does not invalidate the vote, while a larger partition
  (which could change the outcome) triggers re-vote.
```

### Partition Reconciliation

If two partitions each tally independently during a partition:

```
Partition reconciliation for secret ballots:

  Each partition tallies only its local reveals.
  On merge:
    1. Merge all VoteCommitment DataObjects (CRDT union)
    2. Merge all VoteReveal DataObjects (CRDT union)
    3. Late reveals (commits from partition A, revealed in partition B)
       are accepted if received within reveal_period of the ORIGINAL
       commit_epoch (not the merge time)
    4. Re-tally with the merged reveal set
    5. If merged reveal rate >= 80% of merged commits: final tally
       If merged reveal rate < 80%: vote remains INCONCLUSIVE

  The merged tally supersedes both partition-local tallies.
  This is consistent with Mehr's eventual consistency model —
  the pre-merge tallies were preliminary, not authoritative.
```

### Deliberate Withhold Attack

A malicious voter who commits but deliberately withholds reveal to manipulate outcomes:

```
Anti-withhold defenses:

  1. Withhold = abstention: A withheld reveal counts as abstention,
     not as a spoiled ballot. The attacker gains nothing unless the
     abstention itself changes the outcome (which requires the vote
     to be extremely close AND the attacker to have significant weight).

  2. Withhold penalty: If a voter commits but does not reveal in 3
     consecutive secret ballots, their future commitments receive a
     0.5x weight multiplier for 10 epochs (decaying penalty).
     Rationale: occasional non-reveal is normal (genuine partitions);
     repeated non-reveal is suspicious.

  3. Quorum absorbs: The 80% reveal threshold means an attacker must
     withhold >20% of total commit weight to force an INCONCLUSIVE
     result — requiring either massive trust flow weight or many
     colluding voters, both expensive.

  4. Economic cost: A voter spends reputation to participate.
     Repeated withholding triggers the penalty, reducing their
     influence in future votes without any benefit from the current one.
```

## Summary of Anti-Sybil Defenses

| Defense | What It Prevents | Cost to Attacker |
|---------|-----------------|------------------|
| **Trust Flow** | Sybil clusters gaining proportional voting power | Must gain real trust edges from honest nodes |
| **Personhood Vouching** | Anonymous/puppet accounts voting | Must convince real humans to vouch (limit 5/epoch) |
| **Hardware Liveness** | Software-only Sybil farming | Must buy physical radios per identity |
| **Temporal Requirements** | Last-minute account creation | Must maintain presence for 10+ epochs |
| **Economic Liability** | Reckless vouching for Sybils | Vouchers lose vote weight if caught |
| **Service History Bonus** | Pure-consumer Sybils | Must provide real relay/storage/compute service |

No single defense is sufficient. The combination makes Sybil attacks expensive across multiple dimensions — hardware, time, social capital, and economic risk — simultaneously.

---
sidebar_position: 4
title: Epoch Compaction
description: Epoch checkpoint protocol, GCounter rebase, partition-safe merge rules, merge-time supply audit, bloom filter sizing, and snapshot scaling for the Mehr CRDT ledger.
keywords: [epoch compaction, CRDT merge, partition merge, bloom filter, settlement proof, Merkle tree]
---

# Epoch Compaction

The settlement GSet grows without bound. The Epoch Checkpoint Protocol solves this by periodically snapshotting the ledger state.

```
Epoch {
    epoch_number: u64,
    timestamp: u64,

    // Frozen account balances at this epoch (see GCounter Rebase)
    account_snapshot: Map<NodeID, epoch_balance>,

    // Bloom filter of ALL settlement hashes included
    included_settlements: BloomFilter,

    // Active set: defines the 67% threshold denominator
    active_set_hash: Blake3Hash,    // hash of sorted NodeIDs active in last 2 epochs
    active_set_size: u32,           // number of nodes in the active set

    // Genesis-anchored minting (bootstrap only, before epoch 100,000)
    genesis_attestations: GSet<GenesisAttestationHash>,  // valid attestations this epoch

    // Service burn tracking
    epoch_burn_total: u64,          // total μMHR burned this epoch across all providers

    // Acknowledgment tracking
    ack_count: u32,
    ack_threshold: u32,             // 67% of active_set_size
    status: enum { Proposed, Active, Finalized, Archived },
}
```

:::info[Specification]
The Epoch struct snapshots frozen account balances, a bloom filter of included settlements, the active set hash defining the 67% threshold, and cumulative burn totals. Constrained devices discard individual settlement records after epoch activation.
:::

## Epoch Triggers

An epoch is triggered when **any** of these conditions is met:

| Trigger | Threshold | Purpose |
|---------|-----------|---------|
| **Settlement count** | ≥ 10,000 batches | Standard trigger for large meshes |
| **GSet memory** | ≥ 500 KB | Protects constrained devices (ESP32 has ~520 KB usable RAM) |
| **Small partition** | ≥ max(200, active_set_size × 10) settlements AND ≥ 1,000 gossip rounds since last epoch | Prevents stagnation in small partitions |

The small-partition trigger ensures a 20-node village doesn't wait months for an epoch. At 200 settlements (the minimum), the GSet is ~6.4 KB — well within ESP32 capacity. The 1,000 gossip round floor (roughly 17 hours at 60-second intervals) prevents epochs from firing too rapidly in tiny partitions with bursty activity.

## Epoch Proposer Selection

Eligibility requirements adapt to partition size:

1. The node has processed ≥ min(10,000, current epoch trigger threshold) settlement batches since the last epoch
2. The node has direct links to ≥ min(3, active_set_size / 2) active nodes
3. No other epoch proposal for this `epoch_number` has been seen

In a 20-node partition, a node needs only 3 direct links (not 10) and 200 processed settlements (not 10,000) to propose.

**Conflict resolution**: If multiple proposals for the same `epoch_number` arrive, nodes ACK the one with the **highest settlement count** (most complete state). Ties broken by lowest proposer `destination_hash`.

**Active set divergence** (post-partition): Two partitions may propose epochs with different `active_set_hash` values because they've seen different settlement participants. Resolution:

```
Active set conflict handling:
  1. If your local settlement count is within 5% of the proposal's count:
     ACK the proposal's active_set_hash (defer to proposer — close enough)
  2. If your local settlement count exceeds the proposal's by >5%:
     NAK the proposal. Wait 3 gossip rounds for further convergence,
     then propose your own epoch if no better proposal arrives
  3. After partition merge: the epoch with the highest settlement count
     is accepted by all nodes. The losing partition's active set members
     that were missing from the winning proposal are included in the
     NEXT epoch's active set (no settlements are lost — they are applied
     on top of the winning snapshot during the verification window)
```

Epoch proposals are rate-limited to one per node per epoch period. Proposals that don't meet eligibility are silently ignored.

## Epoch Lifecycle

1. **Propose**: An eligible node proposes a new epoch with a snapshot of current state. The proposal includes an `active_set_hash` — a Blake3 hash of the sorted list of NodeIDs in the active set, as observed by the proposer. This fixes the denominator for the 67% threshold.

**Active set definition**: A node is in the active set if it appears as `party_a` or `party_b` in at least one `SettlementRecord` within the last 2 epochs. Relay-only nodes (that relay packets but never settle channels) are not in the active set — they participate in the economy via mining proofs, not via epoch consensus. This keeps the active set small and the 67% threshold meaningful.
2. **Acknowledge**: Nodes compare against their local state. If they've seen the same or more settlements, they ACK. If they have unseen settlements, they gossip those first. A node ACKs the proposal's `active_set_hash` — even if its own view differs slightly, it agrees to use the proposer's set as the threshold denominator for this epoch.
3. **Activate**: At 67% acknowledgment (of the active set defined in the proposal), the epoch becomes active. Nodes can discard individual settlement records and use only the bloom filter for dedup. If a significant fraction of nodes reject the active set (NAK), the proposer must re-propose with an updated set after further gossip convergence.
4. **Verification window**: During the grace period (4 epochs after activation), any node can submit a **settlement proof** — the full `SettlementRecord` — for any settlement it believes was missed. If the settlement is valid (signatures check) and NOT in the epoch's bloom filter, it is applied on top of the snapshot.
5. **Finalize**: After the grace period, previous epoch data is fully discarded. The bloom filter is the final word.

## GCounter Rebase

GCounter `delta_earned` and `delta_spent` grow monotonically between epochs. Over very long timescales (centuries), high-throughput nodes could approach the u64 maximum (1.84 × 10^19) due to money velocity: the same tokens are earned, spent, earned again, each cycle growing both delta counters.

Epoch compaction solves this. At each epoch, the snapshot freezes the balance and resets the deltas:

```
GCounter rebase at epoch compaction:

  Before epoch:
    Alice: epoch_balance = 200,000    delta_earned = {Y: 3,000,000, Z: 1,800,000}
    delta_spent = {W: 4,600,000, V: 200,000}
    Balance = 200,000 + 4,800,000 - 4,800,000 = 200,000

  After epoch snapshot (rebased):
    Alice: epoch_balance = 200,000    epoch_number incremented
    delta_earned = {}  (zeroed)
    delta_spent = {}   (zeroed)
    Balance = 200,000 (unchanged)

  Post-epoch settlements apply on top:
    Alice earns 50,000 (processed by node Y) → delta_earned = {Y: 50,000}
    Alice spends 30,000 (processed by node Z) → delta_spent = {Z: 30,000}
    Balance = 200,000 + 50,000 - 30,000 = 220,000 ✓
```

Without rebase, a node processing 10^10 μMHR/epoch of throughput would overflow u64 after ~1.84 × 10^9 epochs (~35,000 years). With rebase, delta counters never exceed one epoch's worth of activity — the protocol runs indefinitely.

## Partition-Safe Merge Rules

The separation of `epoch_balance` from delta GCounters is critical for correctness during partition merges. When two copies of the same account are merged:

```
CASE 1: Same epoch_number, same epoch_balance (normal operation)
  Standard CRDT merge:
    epoch_balance: unchanged (identical on both sides)
    delta_earned: GCounter pointwise max
    delta_spent:  GCounter pointwise max
    settlements:  GSet union

  This is the common case — both nodes are in the same partition
  or have received the same epoch snapshot.

CASE 2: Same epoch_number, DIFFERENT epoch_balance (concurrent partition compaction)
  Two partitions independently compacted to the same epoch number
  but processed different pre-rebase settlements, producing different
  epoch_balance values.

  Resolution:
    1. The epoch with the higher settlement count wins (existing rule)
    2. Winning epoch's account_snapshot provides epoch_balance for ALL accounts
    3. Winning partition's delta GCounters are kept as-is
    4. Losing partition's delta GCounters are discarded
    5. Losing partition's post-epoch settlements that are NOT in the winning
       epoch's bloom filter are submitted as settlement proofs during the
       verification window, which re-applies them to the delta GCounters
    6. Losing partition's PRE-epoch settlements that are NOT in the winning
       epoch's bloom filter are ALSO submitted as settlement proofs —
       these add the amounts that were absorbed into the losing partition's
       epoch_balance but lost when the winning partition's higher/lower
       epoch_balance was adopted

CASE 3: DIFFERENT epoch_numbers (one partition is ahead)
  The higher epoch_number wins entirely.
    epoch_number: higher value
    epoch_balance: from the higher-epoch partition
    delta_earned: from the higher-epoch partition
    delta_spent:  from the higher-epoch partition
  The lower-epoch partition's settlements are recovered via
  settlement proofs against the winning epoch's bloom filter.
```

**Why this is safe**: The delta GCounters use per-node entries (each processing node writes only to its own entry). Within a single partition, standard CRDT merge (pointwise max) is always correct. Across partitions with conflicting epochs, the settlement proof mechanism — which checks against the winning epoch's bloom filter, NOT the GSet — recovers any settlements that were lost during epoch_balance adoption. The bloom filter check is critical: a settlement may be in the merged GSet (from the losing partition's contribution) but NOT reflected in the winning epoch's delta GCounters, so the GSet must not be used for dedup during settlement proof processing.

**Settlement proof dedup rule**: During the verification window, settlement proofs are checked against the **winning epoch's bloom filter only**. The live GSet is NOT consulted. After successful re-application, the settlement hash is added to the GSet to prevent future re-processing during normal (non-verification-window) operation.

## Merge-Time Supply Audit {#merge-time-supply-audit}

When two partitions reconnect, the CRDT merge (above) handles data convergence automatically. The **supply audit** is an additional economic layer that validates minting produced during the partition. This prevents an isolated attacker from injecting unbounded supply into the main network.

**Key principle**: CRDT convergence is unconditional — settlements, GCounters, epoch snapshots, and bloom filters all merge per the rules above. The supply audit operates *on top of* the merged data, adjusting only the minting component.

:::tip[Key Insight]
CRDT convergence and economic validation are cleanly separated. The merge is unconditional (data always converges); the supply audit adjusts only minting via cross-partition trust scoring — preserving CRDT guarantees while validating economic integrity.
:::

```
Merge-time supply audit:

  Trigger: a node receives epoch data from a partition it has been
  disconnected from for ≥ 1 epoch

  Step 1: Identify divergent epoch range
    E_split = last common epoch number between the two partitions
    divergent_range = epochs in the reconnecting partition after E_split

  Step 2: Cross-partition trust scoring
    For each node N that was in the reconnecting partition's active set
    during the divergent range:

      cross_trust(N) = |{ M_node ∈ main_active_set(E_split) :
                          N ∈ M_node.trusted_peers }|

    This counts how many main-network active nodes had N in their
    trusted_peers at the time of the split. The trust graph is a
    CRDT (GSet of signed trust configs), so both sides have the
    pre-split state.

    partition_trust_score = Σ min(1, cross_trust(N)) / |partition_active_set|
      → 1.0 if every partition node was trusted by ≥1 main-network node
      → 0.0 if no partition node had any cross-partition trust

  Step 3: Minting discount
    For each divergent epoch E in the reconnecting partition:
      accepted_minting(E) = partition_epoch_minting(E) × partition_trust_score
      rejected_minting(E) = partition_epoch_minting(E) × (1 - partition_trust_score)

    accepted_minting merges into the main supply normally.
    rejected_minting enters quarantine (Step 4).

  Step 4: Quarantine window (Q = 10 epochs)
    Rejected minting is held in a pending state for Q = 10 epochs.

    During quarantine, partition nodes can submit trust proofs:
      - Signed trust configs from main-network nodes dated after E_split
        that trust partition nodes (proves trust was established during,
        not before, the partition — weaker but still counts)
      - Pre-partition settlement records showing real bilateral economic
        activity between partition nodes and main-network nodes
      - Channel close proofs from before the split showing funded channels

    Trust proofs increase partition_trust_score retroactively.
    Recalculated score applies to all divergent epochs.

    After Q epochs with no proofs: rejected minting is permanently
    discarded. Affected nodes' epoch_balances are rebased:
      rebased_balance = epoch_balance - (rejected_minting / partition_size)

    This rebase uses the same mechanism as the existing settlement proof
    verification window — it adjusts epoch_balance during the grace period.

  Step 5: Normal operation resumes
    After quarantine closes, all nodes (main + reconnected partition)
    have a consistent view. CRDT state has converged. Supply reflects
    only accepted minting.
```

**Why this doesn't break CRDTs**: The CRDT merge (Cases 1-3 above) is unconditional — `epoch_balance`, `delta_earned`, `delta_spent` GCounters, and the settlement GSet converge without modification. The supply audit adjusts `epoch_balance` *during* the verification window through the same mechanism that settlement proofs already use (re-applying missed settlements adjusts deltas, which affects derived balances). The quarantine and rebase are *economic policy* applied on top of convergent data, not modifications to convergence itself.

**Interaction with settlement proofs**: During the quarantine window, settlement proofs and trust proofs are processed in parallel. Settlement proofs recover lost transactions (existing mechanism); trust proofs validate minting (new mechanism). Both modify the same `epoch_balance` through their respective adjustments. The extended verification window (8 epochs for cross-partition merges, up from 4) ensures both processes complete before epoch finalization.

**Extended verification window**: Cross-partition merges extend the standard 4-epoch verification window to 8 epochs. The first 4 epochs handle settlement proof recovery (existing). Epochs 5-8 overlap with the quarantine window for trust proof submission. The supply audit quarantine (Q = 10 epochs) extends beyond the verification window — any balance rebase from rejected minting in epochs 9-10 is applied as a separate adjustment to the already-finalized epoch, similar to how late-arriving settlement proofs are handled after the standard window closes.

For the full economic analysis and attack outcomes, see [Partition Defense](token-security#partition-defense) in the token economics specification.

## Late Arrivals After Compaction

When a node reconnects after an epoch has been compacted, it checks its unprocessed settlements against the epoch's bloom filter:
- **Present in filter**: Already counted in epoch_balance, discard
- **Absent from filter**: New settlement, apply to delta GCounters on top of epoch_balance. If within the verification window, submit as a settlement proof.

**Important**: During the verification window after a partition merge, settlement proofs are checked against the **winning epoch's bloom filter only** — NOT the merged GSet. This is because a settlement may exist in the merged GSet (contributed by the losing partition) but not be reflected in the delta GCounters (because the losing partition's deltas were discarded during conflict resolution). The bloom-filter-only check ensures such settlements are correctly re-applied.

## Bloom Filter Sizing

| Data | Size |
|------|------|
| 1M settlement hashes (raw) | ~32 MB |
| Bloom filter (0.01% false positive rate) | ~2.4 MB |
| Target epoch frequency | ~10,000 settlement batches |
| Per-node storage target | Under 5 MB |

The false positive rate is set to **0.01% (1 in 10,000)** rather than 1%, because false positives cause legitimate settlements to be silently treated as duplicates. At 0.01%, the expected loss is negligible (~1 settlement per 10,000), and the verification window provides a recovery mechanism for any that are caught.

**Construction**: The bloom filter uses `k = 13` hash functions derived from Blake3:

```
Bloom filter hash construction:
  For each settlement_hash and index i in [0, k):
    h_i = Blake3(settlement_hash || i as u8) truncated to 32 bits
    bit_position = h_i mod m  (where m = total bits in filter)

  Bits per element: m/n = -ln(p) / (ln2)² ≈ 19.2 bits at p = 0.0001
  k = -log₂(p) ≈ 13.3, rounded to 13

  For 10,000 settlements: m = 192,000 bits = 24 KB
  For 1M settlements: m = 19.2M bits ≈ 2.4 MB
```

The Merkle tree over the account snapshot also uses Blake3 (consistent with all content hashing in Mehr). Leaf nodes are `Blake3(NodeID || epoch_balance)`, and internal nodes are `Blake3(left_child || right_child)`.

**Critical retention rule**: Both parties to a settlement **must retain the full `SettlementRecord`** until the epoch's verification window closes (4 epochs after activation). If both parties discard the record after epoch activation (believing it was included) and a bloom filter false positive caused it to be missed, the settlement would be permanently lost. During the verification window, each party independently checks that its settlements are reflected in the snapshot; if any are missing, it submits a settlement proof. Only after the window closes may the full record be discarded.

## Snapshot Scaling

At 1M+ nodes, the flat `account_snapshot` is ~32 MB — too large for constrained devices. The solution is a **Merkle-tree snapshot** with sparse views.

**Full snapshot** (backbone/gateway nodes only): The account snapshot is stored as a sorted Merkle tree keyed by NodeID. Only nodes that participate in epoch consensus need the full tree. At 1M nodes and 24 bytes per entry (16-byte NodeID + 8-byte epoch_balance), this is ~24 MB — feasible for nodes with SSDs.

**Sparse snapshot** (everyone else): Constrained devices store only:
- Their own balance
- Balances of direct channel partners
- Balances of trust graph neighbors (Ring 0-2)
- The Merkle root of the full snapshot

For a typical node with ~50 relevant accounts: 50 × 24 bytes = 1.2 KB.

**On-demand balance verification**: When a constrained node needs a balance it doesn't have locally (e.g., to extend credit to a new node), it requests a Merkle proof from any capable peer:

```
BalanceProof {
    node_id: NodeID,
    epoch_balance: u64,
    merkle_siblings: Vec<Blake3Hash>,  // path from leaf to root
    epoch_number: u64,
}
// Size: ~640 bytes for 1M nodes (20 tree levels × 32-byte hashes)
```

The constrained node verifies the proof against the Merkle root it already has. This proves the balance is in the snapshot without storing the full 32 MB.

## Constrained Node Epoch Summary

LoRa nodes and other constrained devices don't participate in epoch consensus. They receive a compact summary from their nearest capable peer:

```
EpochSummary {
    epoch_number: u64,
    merkle_root: Blake3Hash,               // root of full account snapshot
    proposer_id: NodeID,                   // who proposed this epoch
    proposer_sig: Ed25519Signature,        // signature over (epoch_number || merkle_root)
    my_epoch_balance: u64,                     // frozen balance at this epoch
    partner_epoch_balances: Vec<(NodeID, u64)>, // channel partners + trust neighbors
    bloom_segment: BloomFilter,            // relevant portion of settlement bloom
}
```

Typical size: under 5 KB for a node with 20-30 channel partners.

## Merkle Root Trust

The `merkle_root` is the anchor for all balance verification on constrained nodes. To prevent a malicious relay from feeding a fake root:

```
Merkle root acceptance:
  - If the source is a trusted peer (in trust graph): accept immediately
    (trusted peers have economic skin in the game)
  - If the source is untrusted: verify proposer_sig against proposer_id,
    then confirm with at least 1 additional independent peer in Ring 0/1
    (2-source quorum, same as DHT mutable object verification)
  - Cold start (no prior epoch): query 2+ peers and accept majority agreement
  - Retention: keep roots for the last 4 epochs (grace period for balance proofs)
```

The proposer's signature prevents trivial forgery — an attacker must either compromise the proposer's key or control the majority of a node's Ring 0 peers.

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>Why is epoch compaction necessary for the CRDT ledger?</summary>

The settlement GSet (grow-only set) grows without bound as more settlements are processed. Without compaction, memory usage would eventually exceed device capacity — especially on constrained devices like ESP32 with ~520 KB usable RAM. Epoch compaction periodically snapshots the ledger state, freezes account balances, and replaces the full settlement history with a compact bloom filter. GCounter deltas are rebased to zero, preventing overflow even over centuries of operation.

</details>

<details className="faq-item">
<summary>How are epochs triggered in small mesh networks?</summary>

Small partitions use an adaptive trigger: an epoch fires after at least max(200, active_set_size × 10) settlements AND 1,000 gossip rounds (~17 hours) since the last epoch. This prevents a 20-node village from waiting months for the standard 10,000-settlement threshold. The 1,000-round floor also prevents epochs from firing too rapidly during bursty activity. Proposer eligibility requirements similarly adapt — a node needs only 3 direct links (not 10) in a small partition.

</details>

<details className="faq-item">
<summary>What happens if a settlement is missed during epoch compaction?</summary>

The verification window (4 epochs after activation) provides a recovery mechanism. Any node can submit a settlement proof — the full SettlementRecord — for any settlement not in the epoch's bloom filter. The bloom filter uses a 0.01% false positive rate (1 in 10,000) to minimize silent losses. Both parties to a settlement must retain the full record until the verification window closes. For cross-partition merges, the window extends to 8 epochs.

</details>

<details className="faq-item">
<summary>How do constrained devices like ESP32 nodes handle epoch data?</summary>

Constrained devices do not participate in epoch consensus. Instead, they receive a compact EpochSummary (typically under 5 KB) from their nearest capable peer, containing the Merkle root, their own frozen balance, channel partner balances, and a relevant bloom filter segment. When they need a balance they don't have locally, they request a Merkle proof (~640 bytes for 1M nodes) and verify it against the stored Merkle root.

</details>

<details className="faq-item">
<summary>How does the merge-time supply audit prevent inflation from partition attacks?</summary>

When partitions reconnect, the CRDT data merges unconditionally, but the minting component is audited separately. A cross-partition trust score is computed: each partition node is checked for trust relationships with main-network nodes at the time of the split. Minting from untrusted nodes is discounted or rejected entirely. Rejected minting enters a 10-epoch quarantine where partition nodes can submit trust proofs. Unclaimed minting is permanently discarded and balances are rebased.

</details>

<!-- faq-end -->

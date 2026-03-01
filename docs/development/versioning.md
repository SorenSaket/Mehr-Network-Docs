---
sidebar_position: 4
title: Protocol Versioning
description: "Version negotiation strategy for a decentralized mesh where nodes may be offline for months or never updated."
keywords:
  - versioning
  - protocol upgrades
  - compatibility
  - MEP
  - migration
  - governance
---

# Protocol Versioning

Mehr has no central authority to push upgrades. Nodes can be offline for months. ESP32 nodes may never be updated. Partitioned networks may run different versions simultaneously. The versioning strategy must work under all these conditions.

## Version Field

Every Mehr announce carries a version byte in the [MehrExtension](../protocol/network-protocol#mehr-extension-compact-path-cost):

```
MehrExtension:
  [MAGIC 0x4E] [VERSION 1B] [CompactPathCost 6B] [TLV extensions...]

VERSION encoding:
  Bits 7-4: major version (0-15)
  Bits 3-0: minor version (0-15)

  Current: 0x10 = major 1, minor 0 (v1.0)

Reserved value:
  Major = 15 (0xF_): EXTENDED VERSION
    When major = 15, the actual version is read from a TLV extension
    in the MehrExtension payload:
      Type: 0x01 (ExtendedVersion)
      Length: 4 bytes
      Data: [major u16 LE] [minor u16 LE]

    This allows up to 65,535 major versions — sufficient for any
    foreseeable protocol lifetime. Old nodes that don't understand
    extended versioning see major=15 and treat it as "unknown future
    version" (the correct behavior for any unrecognized major).
```

Nodes advertise their version in every announce. A node can see what versions its neighbors run without any explicit version query. The extended version escape hatch ensures the 4-bit version field never becomes a hard limit — major 15 bootstraps into an arbitrarily large version space via TLV.

## Change Categories

Not all changes are equal. Mehr classifies protocol changes into three categories based on their impact on the network:

### Soft Extensions (Minor Version Bump)

New features that old nodes can safely ignore:

```
Examples:
  - New TLV extension types in MehrExtension
  - New optional fields in DataObject (old nodes skip unknown fields)
  - New capability bits (bits 8-15 in presence beacon, currently reserved)
  - New scope types beyond Geo and Topic
  - New delivery modes in MHR-Pub
  - New claim types in IdentityClaim

Old node behavior:
  - Ignores unknown TLV types, unknown capability bits, unknown fields
  - Continues operating normally
  - Can still communicate with new nodes
  - No action required by operator
```

Soft extensions are the primary upgrade mechanism. The protocol is designed with reserved fields, TLV extensibility, and optional fields specifically to enable this.

### Hard Changes (Major Version Bump)

Incompatible changes that require nodes to understand the new format:

```
Examples:
  - Changing wire format of existing fields (e.g., CompactPathCost layout)
  - Changing cryptographic primitives (e.g., Ed25519 → post-quantum)
  - Changing CRDT merge semantics
  - Changing VRF algorithm for relay lottery
  - Changing settlement record format

Network impact:
  - Old nodes cannot process new-format messages
  - New nodes must handle both old and new formats during transition
  - Requires coordinated transition period
```

Hard changes should be extremely rare. The protocol is designed to avoid them through extensibility.

### Cryptographic Migration (Special Case)

Cryptographic algorithm replacement is the most likely hard change and gets its own process:

```
Crypto migration timeline:

  Phase 1: DUAL SUPPORT (soft extension)
    New nodes support both old and new algorithms.
    New nodes advertise new algorithm support via TLV extension.
    All communication uses old algorithms (backward compatible).
    Duration: until >80% of active nodes support new algorithms.

  Phase 2: PREFER NEW (soft extension)
    New-capable nodes prefer new algorithms for new channels/agreements.
    Old nodes still work — they just use old algorithms.
    KeyRotation claims allow nodes to migrate identity keys.
    Duration: until <5% of active traffic uses old algorithms.

  Phase 3: DEPRECATE OLD (major version bump)
    New nodes stop accepting old algorithm traffic.
    Old nodes are effectively partitioned (can still talk to each other).
    Operators must upgrade to rejoin the main network.
    Duration: permanent.
```

The [KeyRotation](../services/mhr-id) identity claim is designed specifically for this: a node signs a statement with its old key saying "my new key is X", then the network recognizes the new key. This works even if the old algorithm is weakened — as long as the rotation happens before the old key is compromised.

## Transition Mechanics

### How Nodes Learn About New Versions

```
Version discovery:

  1. PASSIVE: Node sees announces with higher version numbers
     from neighbors. No action needed — just awareness.

  2. GOSSIP: Epoch proposals include a version histogram
     (count of nodes per version in the active set).
     Every node knows the version distribution.

  3. LOCAL DECISION: The node operator decides when to upgrade.
     The protocol never forces an upgrade.
```

### Compatibility Rules

```
Compatibility matrix:

  Same major, any minor:
    ✓ Full interoperability
    Old nodes ignore new extensions
    New nodes include backward-compatible fallbacks

  Different major, during transition:
    ✓ Partial interoperability via bridge behavior
    New nodes accept both old and new format
    Old nodes work within their version cluster

  Different major, after transition:
    ✗ No interoperability
    Old nodes form a separate network
    Upgrade required to rejoin
```

### Partition-Safe Upgrades

Version transitions must be partition-safe. A partition that misses the transition window must still be able to rejoin:

```
Partition rejoining after version transition:

  Scenario: Partition P was isolated during v1 → v2 transition.
  P runs v1. Main network runs v2.

  On reconnection:
    1. P's nodes see v2 announces from main network.
    2. P's nodes cannot process v2-only traffic.
    3. P's v1 traffic is still accepted by main network
       (during transition period: main nodes accept both).
    4. P's operators upgrade to v2.
    5. P's CRDT ledger merges normally (GCounter/GSet merge
       is version-independent — balances are just numbers).
    6. P fully rejoins.

  If P reconnects AFTER the transition period:
    1. Main network no longer accepts v1 traffic.
    2. P's nodes are effectively still partitioned.
    3. P's operators must upgrade before traffic can flow.
    4. CRDT merge still works once P upgrades — no balance loss.
```

## What Doesn't Need Versioning

Several aspects of Mehr are upgradeable without any version mechanism:

| Component | Why No Version Needed |
|-----------|----------------------|
| **Service pricing** | Market-set per node — just change your config |
| **Trust policies** | Local per node — change trusted_peers, credit limits |
| **Content filtering** | Local per node — change relay/storage policies |
| **Application layer** | PostEnvelope, SocialPost, CuratedFeed are DataObjects — new formats are just new DataObject types |
| **Scope naming** | Free-form strings — communities evolve naming conventions socially |
| **Capability types** | New capabilities advertised via reserved beacon bits or TLV extensions |

The layered architecture means most changes happen above the protocol layer and don't require protocol versioning at all.

## Post-Quantum Cryptography

The most likely cryptographic migration is from Ed25519/X25519 to post-quantum algorithms. Current timeline estimates suggest this may be needed within 10-20 years.

```
PQC migration plan:

  Current primitives:
    Identity/Signing:  Ed25519 (32-byte public key)
    Key Exchange:      X25519 (32 bytes)
    VRF:               ECVRF-ED25519-SHA512-TAI

  Candidate replacements:
    Identity/Signing:  ML-DSA (FIPS 204) or SLH-DSA (FIPS 205)
    Key Exchange:      ML-KEM (FIPS 203)
    VRF:               Post-quantum VRF (research area — no standard yet)

  Constraints:
    ML-DSA-44 public key:  1,312 bytes (vs 32 for Ed25519)
    ML-DSA-44 signature:   2,420 bytes (vs 64 for Ed25519)
    ML-KEM-512 ciphertext: 768 bytes (vs 32 for X25519)

    These sizes are challenging for LoRa (484-byte max packet).
    Solutions:
      - Fragment announces across multiple packets
      - Use hash-based short identifiers on LoRa, full keys on WiFi+
      - Hybrid schemes (Ed25519 + PQC) during transition
```

### Post-Quantum VRF Strategy

Post-quantum VRF is an active research area with no production standard. Mehr's strategy is a **two-track approach**: adopt a PQ VRF candidate when one matures, with a hash-based fallback ready if needed.

```
PQ VRF candidates (ranked by viability):

  1. Lattice-based VRF (XVRF, based on Module-LWE)
     Pros: Compact proofs (~1.5 KB), fast verification
     Cons: No NIST standard yet, ongoing cryptanalysis
     Timeline: Likely standardized by 2030-2035

  2. Hash-based VRF (using SLH-DSA / SPHINCS+ signatures)
     Pros: Conservative security assumptions, NIST-standardized base
     Cons: Large proofs (~8-17 KB), requires multi-packet fragmentation
     Timeline: Constructible today from existing standards

  3. Isogeny-based VRF
     Pros: Small key/proof sizes
     Cons: SIDH broken in 2022; remaining schemes immature
     Timeline: Uncertain

Fallback: Hash-chain lottery (no VRF)
  If no PQ VRF standard emerges before quantum threat materializes:

    HashChainLottery {
        relay_id: NodeID,
        packet_hash: Blake3Hash,
        epoch_hash: Blake3Hash,
        chain_link: Blake3(relay_secret || packet_hash || epoch_hash),
        // Deterministic per (relay, packet, epoch) — no grinding
        // relay_secret committed at epoch start via hash(relay_secret)
        // Revealed per-epoch, verified by checking commitment
    }

    Commitment protocol:
      1. At epoch start: relay publishes commitment = Blake3(relay_secret)
      2. Per packet: chain_link = Blake3(relay_secret || packet_hash || epoch_hash)
      3. Win check: chain_link < difficulty_target
      4. At epoch end: relay reveals relay_secret for verification
      5. All wins verified retroactively against the commitment

    Properties:
      - No wasted work (single hash per packet, not proof-of-work)
      - Deterministic (relay cannot grind — secret is committed)
      - Retroactive verification (cheating detected at epoch boundary)
      - Penalty for non-reveal: forfeit all epoch earnings

  This is NOT proof-of-work — it's a committed hash lottery.
  Expected compute: 1 Blake3 hash per packet (~1 μs). No grinding.
```

**Migration path**: The VRF algorithm is negotiated per-link via the [cryptographic migration](#cryptographic-migration-special-case) three-phase process. During Phase 1 (dual support), both the current Ed25519 VRF and the new PQ VRF are accepted. During Phase 2, new channels prefer PQ VRF. Phase 3 deprecates the old VRF. Because VRF verification only involves the two channel parties (relay and sender), migration is per-channel, not network-wide — far simpler than migrating identity keys.

## Protocol Longevity

Can the protocol run for 1000 years without hitting a numerical wall? Every field in the protocol has been audited for overflow at millennial timescales.

### Numerical Overflow Audit

Assumptions: 1 epoch per 10 minutes, 52,560 epochs/year, 1000 years = 52.56 million epochs.

| Field | Type | Capacity | 1000-Year Usage | Headroom |
|-------|------|----------|-----------------|----------|
| `epoch_number` | u64 | 1.84 × 10^19 | 5.26 × 10^7 | Safe for 3.5 × 10^11 years |
| Timestamps | u64 | 5.8 × 10^11 years | 1000 years | Safe for 10^11 years |
| MHR supply ceiling | u64 | 1.84 × 10^19 μMHR | Asymptotic by design | Never reached |
| Channel `sequence` | u64 | 1.84 × 10^19 | ~5.3 × 10^7 per channel (if never closed) | Safe |
| `active_set_size` | u32 | 4.3 × 10^9 | Up to millions | Safe |
| `win_count` | u32 | 4.3 × 10^9 | Per-epoch, resets | Safe |
| Version byte | 4-bit major | 16 versions | ~1 per 50 years = 20 | **Overflow at year ~800** |
| GCounters | u64 | 1.84 × 10^19 | Grows with money velocity | **Theoretical overflow** |
| Emission bit-shift | u64 >> N | N must be 0–63 | At epoch 6.4M (year ~1218): N = 64 | **Undefined behavior** |

### Mitigations

**Version byte (solved)**: Major version 15 is reserved as an escape hatch into [extended versioning](#version-field). When major = 15, the actual version is read from a TLV extension as a u16 pair — supporting 65,535 major versions. At one major version per 50 years, this covers 3.2 million years.

**GCounters (solved)**: [Epoch compaction](../economics/epoch-compaction#gcounter-rebase) rebases GCounters to net balance at each epoch. Instead of tracking cumulative lifetime earnings (which grows with money velocity), the snapshot stores only current balance. Counters never exceed current circulating supply — the protocol runs indefinitely.

**Emission bit-shift (solved)**: The halving formula `10^12 >> (e / 100_000)` overflows when the shift operand reaches 64 at epoch 6.4 million (~year 1218). Implementations must [clamp the shift to 63](../economics/mhr-token#supply-model). At shift = 63, the halved reward is 0, so the tail emission floor takes over — which is the correct behavior.

### What Fundamentally Cannot Overflow

The economic model — free between trusted peers, paid between strangers — doesn't depend on any numerical field. Even if every counter were reset to zero, the trust graph and bilateral relationships would reconstruct the economy. Numbers track accounting; the trust graph *is* the network.

## Governance

Mehr has no central authority for protocol changes. Governance uses a **Mehr Enhancement Proposal (MEP)** process with trust-weighted version signaling — lightweight enough to avoid creating a political attack surface, structured enough to coordinate upgrades across a decentralized mesh.

### Mehr Enhancement Proposals (MEPs)

Any node operator can propose a protocol change by publishing a MEP as a DataObject in MHR-Store:

```
MEP {
    mep_number: u32,                    // sequential, claimed by publisher
    title: String,                       // short description
    author: NodeID,                      // proposer's identity
    status: enum {
        Draft,                           // under discussion
        Proposed,                        // ready for signaling
        Accepted,                        // ≥67% signal weight in target scope
        Implemented,                     // reference implementation available
        Active,                          // ≥80% of active nodes running it
        Rejected,                        // failed to reach acceptance threshold
        Withdrawn,                       // author withdrew
    },
    category: enum {
        SoftExtension,                   // minor version bump
        HardChange,                      // major version bump
        CryptoMigration,                 // cryptographic algorithm change
        Process,                         // governance process change
    },
    target_version: (u16, u16),          // proposed (major, minor)
    spec_hash: Blake3Hash,               // hash of full specification document
    reference_impl_hash: Option<Blake3Hash>, // hash of reference implementation
    created: u64,                        // epoch
    signature: Ed25519Signature,
}
```

MEPs are registered via MHR-Name under `topic:mehr/meps` and propagate through normal gossip.

### Trust-Weighted Version Signaling

Nodes signal support for MEPs via a TLV extension in their announces:

```
VersionSignal TLV (type 0x03):
    mep_count: u8,                       // number of MEPs signaled (max 8)
    signals: [{
        mep_number: u32,                 // which MEP
        support: enum { Support, Oppose, Neutral },  // 1 byte
    }],
```

The epoch proposer aggregates signals into a **version histogram** included in epoch proposals:

```
Version histogram (per epoch):
    For each signaled MEP:
        support_weight  = Σ trust_flow_weight(node) for all Supporting nodes
        oppose_weight   = Σ trust_flow_weight(node) for all Opposing nodes
        neutral_weight  = Σ trust_flow_weight(node) for all Neutral nodes
        total_weight    = support_weight + oppose_weight + neutral_weight

    Acceptance threshold: support_weight / total_weight ≥ 0.67
    Rejection threshold:  oppose_weight / total_weight ≥ 0.34
```

Signaling uses trust flow weight (from the [voting](../applications/voting) TrustFlow algorithm), not node count. This prevents Sybil manipulation of governance — 50 fake nodes with 2 inbound trust edges get ~1.7 total signal weight, not 50.

### Cross-Fork Compatibility

When different communities run different versions:

```
Cross-fork interaction rules:

    Same major version, different minor:
        Full interoperability. Old nodes ignore new TLV extensions.

    Different major versions:
        Gateway nodes that support both versions act as bridges.
        Bridge behavior:
            1. Accept packets in either format
            2. Translate between formats where possible
            3. For untranslatable features: drop gracefully
        Bridge nodes advertise multi-version support via capability bits.

    Permanent fragmentation prevention:
        A fork that loses >90% of trust-weighted signal is considered abandoned.
        MEPs include a sunset_epoch — if acceptance threshold is not reached
        within 50,000 epochs (~1 year), the MEP automatically moves to Rejected.
        This prevents indefinite version limbo.
```

### Why This Works

- **No political attack surface**: No elected committee, no foundation, no voting token. Signal weight comes from the same trust graph used for everything else.
- **Fork-friendly**: Communities can disagree and fork. Gateway bridges maintain connectivity. The trust graph, not the protocol version, defines the real network.
- **Partition-safe**: Version signaling is carried in announces and aggregated in epochs — both are partition-tolerant mechanisms.
- **Lightweight**: The entire governance mechanism is a TLV extension (≤41 bytes) and a DataObject (MEP). No new protocol primitives.

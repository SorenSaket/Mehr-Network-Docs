---
sidebar_position: 3
title: "Design Decision: Partition Defense"
description: "Comparison of trust-gated minting vs. neighborhood-scoped currencies for defending against isolated partition attacks."
keywords:
  - partition defense
  - Sybil attack
  - trust graph
  - minting
  - CRDT ledger
  - security
---

# Distributed Exchange vs Trust Graph: Partition Defense Comparison

The [isolated partition attack](../economics/token-security#attack-isolated-partition) is the most significant economic threat to Mehr's CRDT-based ledger. An attacker runs 100 virtual nodes on a single machine (~$60/year), isolates them in a partition, and mints MHR uncontested. Post-bootstrap (epoch > 100,000), [GenesisAttestation](../economics/mhr-token#genesis-anchored-minting) sunsets and the network needs a **fully distributed** defense — no genesis root, no central authority.

Two architectures address this:

| | **A: Trust-Gated Active Set + Merge-Time Audit** | **B: Neighborhood-Scoped Minting** |
|---|---|---|
| **One-liner** | One global MHR. Minting requires trust links. Untrusted minting rejected on merge. | Local currencies per neighborhood. Cross-neighborhood exchange at market rates. |
| **Defense type** | Retroactive — minting audited when partitions reconnect | Structural — attacker tokens are a different currency |
| **Status** | **Current design** | Not adopted — see [rationale](#rationale) |

## The Problem

During bootstrap (epoch 0–100,000), [GenesisAttestation](../economics/mhr-token#genesis-anchored-minting) prevents all isolated partition minting by requiring a signed proof of connectivity to a genesis node. This works but is centralized — every attestation chain traces back to one root.

Post-bootstrap, three approaches are possible:

1. **Make GenesisAttestation permanent** — Not viable. This is "centralization with extra steps." Every attestation chain forever traces back to genesis. A community that forms after bootstrap and has never connected to the genesis graph can never mint. Not distributed.

2. **Trust-gated active set + merge-time audit** — Current design. Uses the existing trust graph as a minting gate. Merge-time audit rejects untrusted partition minting on reconnection. Fully distributed post-bootstrap.

3. **Neighborhood-scoped minting** — Not adopted. Each neighborhood mints its own denomination with cross-neighborhood exchange. Structurally eliminates the attack but creates massive new complexity.

## Approach A: Trust-Gated Active Set + Merge-Time Audit

### Design

**Continuous gate** (connected network):
- A node is **minting-eligible** if it is in the [active set](../economics/epoch-compaction#epoch-lifecycle) AND has ≥1 mutual trust link with another active-set member
- "Mutual trust link" = both nodes have each other in `trusted_peers`
- This is a soft Sybil gate — it doesn't prevent the partition attack (attacker nodes trust each other) but provides basic hygiene in the connected network

**Merge-time defense** (partition reconnection):
- When a partition reconnects, CRDT data merges normally (unconditional convergence)
- The **minting component** is audited: cross-partition trust scoring determines what fraction of partition minting is accepted
- `partition_trust_score = (nodes trusted by main-network peers) / (total partition nodes)`
- Untrusted minting enters quarantine (10 epochs), then is permanently rejected if unproven
- See [merge-time trust audit](../economics/token-security#merge-time-trust-audit) for full spec

### Attack Outcomes

| Scenario | Dilution |
|---|---|
| Fresh localhost (100 virtual nodes, 0 trust) | **0.00%** |
| Pre-planned, 1/100 nodes trusted by main network | **0.99%** |
| Pre-planned, 10/100 trusted | 9.09% |
| Deep infiltration, 50/100 trusted | 33.33% |
| Extreme infiltration, 90/100 trusted | 47.37% |

### Properties

- **Fully distributed**: No genesis dependency post-bootstrap. Trust graph is the only authority.
- **One global currency**: MHR is MHR everywhere. Zero exchange friction.
- **Backward compatible**: Nodes that haven't implemented the audit yet degrade gracefully.
- **CRDT-safe**: Audit is an economic overlay on convergent data, not a modification to CRDT merge.
- **~500 lines of new code**: Trust-link check on active set + merge-time audit logic.

## Approach B: Neighborhood-Scoped Minting

### Design

**Local currencies**:
- Each trust neighborhood mints its own denomination: MHR-Portland, MHR-Tehran, MHR-Attacker
- A `neighborhood_tag` (trust anchor hash) tags every minted unit
- Cross-neighborhood payments use bilateral exchange channels at market-negotiated rates
- Exchange rate = supply/demand at boundary nodes (nodes in multiple neighborhoods)

**Structural defense**:
- Attacker creates "MHR-Attacker" in their isolated partition
- Zero real services → zero demand for MHR-Attacker → zero exchange rate
- No impact on any other neighborhood's economy
- The market IS the proof: tokens backed by nothing have no value

### Attack Outcomes

| Scenario | Dilution on honest neighborhoods |
|---|---|
| Fresh localhost (any number of nodes) | **0.00%** (different currency) |
| Pre-planned, any trust level | **0.00%** (different currency) |
| Deep infiltration, any level | **0.00%** (different currency) |
| Attacker provides 10% real services | ~9.09% (exchange rate reflects real services) |
| Attacker provides 50% real services | ~33.33% (exchange rate reflects real services) |

### Properties

- **Fully distributed**: Each neighborhood is self-sovereign. No external dependency.
- **Structurally immune**: Attack produces worthless tokens by definition.
- **Perfect partition tolerance**: Each partition IS its own economy. No merge conflict ever.
- **~5,000+ lines of new code**: Cross-denomination channels, exchange rate protocol, wallet UX.

## Head-to-Head Comparison

### Security

| Attack | A: Trust-Gated+Audit | B: Neighborhood-Scoped |
|---|---|---|
| Fresh identities (the real threat) | **0%** | **0%** |
| 1% trust infiltration | 0.99% | 0% |
| 50% trust infiltration | 33.3% | 0% |
| Attacker provides 50% real services | N/A (one currency) | 33.3% |

**Verdict**: Tied for realistic attacks (fresh IDs). B wins on deep infiltration. But if the attacker in B provides real services (the only way to get exchange value), dilution converges to the same numbers — B just shifts the attack surface from "trust infiltration" to "exchange rate manipulation."

### User Experience

| Scenario | A | B |
|---|---|---|
| Pay for service in your city | Send MHR | Send MHR-Portland |
| Pay for service in another city | Send MHR (same currency) | Exchange MHR-Portland → MHR-Tehran, then send |
| Move to a new city | Nothing changes | Must exchange all tokens |
| Check your balance | "1,000 MHR" | "800 MHR-Portland + 150 MHR-Tehran + 50 MHR-Guild" |
| New node joining | Add a contact, start minting | Join neighborhood, get local denomination |

**Verdict**: A wins decisively. B imposes foreign exchange friction on every cross-community interaction.

### Implementation Complexity

| Component | A | B |
|---|---|---|
| Active set | Add trust-link check (~20 lines) | Add `neighborhood_tag` to active set |
| CRDT ledger | Merge-time audit (already spec'd) | `epoch_balance` becomes per-denomination. GCounter entries tagged. Major rework. |
| Payment channels | No change | Cross-denomination channels: new type, exchange negotiation, dual-currency settlement. Major rework. |
| Emission schedule | No change | Per-neighborhood emission with neighborhood size tracking |
| New protocol | Trust proofs at merge (~200 bytes) | Exchange rate gossip, cross-denom channel ops (~5 new message types) |
| Wallet UX | No change | Multi-denomination display, exchange interface |
| **Total** | **~500 lines** | **~5,000+ lines** |

**Verdict**: A is 10x simpler. B requires changes to nearly every economic subsystem.

### Architecture

| Concern | A | B |
|---|---|---|
| Single global currency | **Preserved** | Destroyed — MHR becomes a token family |
| CRDT properties | Preserved entirely (audit is economic overlay) | GCounter merge becomes denomination-aware |
| Existing spec changes | Moderate (mhr-token.md, crdt-ledger.md) | Massive (every economic doc) |
| Backward compatible | Yes (graceful degradation) | No (breaking change) |

**Verdict**: A is a surgical addition. B is a fundamental architecture change.

### Philosophy

| Principle | A | B |
|---|---|---|
| Distributed? | Yes — trust graph is sole authority | Yes — each neighborhood self-sovereign |
| Communities first? | Communities share one economy. Free local, paid global. | Communities own their economy. Free local, exchange at boundary. |
| Partition tolerance? | Good — minting works during isolation, audited on merge | Perfect — each partition is its own economy |
| Simplicity? | High — one currency, one wallet | Low — multi-currency management |
| Real-world parallel | One country, one dollar (with post-partition audit) | Multi-country with forex markets |

**Verdict**: Philosophical tie. A favors cohesion ("one MHR for everyone"). B favors sovereignty ("each community controls its money"). Both are valid readings of "communities first."

### Edge Cases

| Edge Case | A | B |
|---|---|---|
| 1-node neighborhood | Works — gets trust from any peer, mints global MHR | Mints into local denomination with zero liquidity |
| Nomadic user | MHR works everywhere | Must exchange on every move |
| Bridge node (2 neighborhoods) | Normal node | Must hold 2 denominations, provides liquidity |
| Adversarial exchange rate manipulation | N/A (one currency) | **New attack surface** — attacker manipulates rates between neighborhoods |
| New neighborhood forming | Any trusted peer → in | Must create new denomination. Who accepts your new token? (Chicken-and-egg) |

**Verdict**: A handles edge cases naturally. B creates new problems for single-node communities, nomadic users, and new neighborhoods.

## Design Rationale {#rationale}

1. **Security is equivalent for practical attacks.** Both produce 0% dilution for fresh-identity localhost attacks — the realistic, cheap threat. The gap is deep trust infiltration (50%+ of attacker nodes pre-trusted by real people). This requires sustained social engineering, is slow, visible, and doesn't scale. It's also bounded by the halving schedule.

2. **Approach B solves one problem by creating three.** Exchange rate manipulation, liquidity bootstrapping, and cross-denomination UX are each individually harder unsolved problems than the partition attack itself.

3. **10x simpler.** ~500 lines vs ~5,000+. Zero changes to payment channels, wallet UX, or protocol messages. The merge-time audit is already specified in [crdt-ledger.md](../economics/epoch-compaction#merge-time-supply-audit).

4. **B hurts legitimate users more than attackers.** Users moving between cities, paying for cross-community services, or running multi-region applications all face exchange friction. The attacker pays zero (their tokens are worthless either way).

5. **A is more "communities first."** Communities share a global commons (one MHR), communicate freely within trust boundaries, and pay at the boundary. This matches Mehr's ethos better than fragmenting the economy into sovereign micro-currencies.

### Residual Risk

The remaining exposure in Approach A is **deep trust infiltration** — an attacker who gets ≥50% of their partition nodes trusted by main-network peers before isolating. This worst case produces ~33% dilution per cycle.

Mitigations:
- This requires **sustained social engineering** — building real trust relationships with real people who will absorb your debts. This is the hardest, slowest, most visible form of attack in any system.
- The **halving schedule** bounds cumulative damage. Each halving period (~1.9 years), attacker per-epoch minting halves.
- **Per-cycle visibility**: The attacker must reconnect to spend the minted MHR, making each cycle observable.
- If deep infiltration proves to be a **practical** problem (observed in the wild, not just theoretical), neighborhood-scoped minting can be introduced as a network evolution: A → A+B (dual-mode) → B (if needed). This should be a response to observed attacks, not a pre-emptive architectural bet.

### Key Insight

The partition attack is about **minting**. Neighborhood-scoped minting solves it by making minting local. But the merge-time trust audit solves it just as well for all realistic attacks, without fragmenting the economy. The ~33% worst case requires social engineering at scale — which is already the hardest attack vector in any distributed system.

## Quantitative Model

The full analysis with dilution calculations across all scenarios is in the [defense comparison script](https://github.com/mehr-network/mehr-docs/blob/main/scripts/defense_comparison.py). The [localhost partition analysis](https://github.com/mehr-network/mehr-docs/blob/main/scripts/localhost_partition_analysis.py) demonstrates the cost gap that motivates this defense.

"""
Mehr Network -- Localhost Partition Attack Analysis

Evaluates the REAL cost of the isolated partition attack when the attacker
runs N node identities as processes on a single machine (localhost), not
N separate VMs.

Key insight: The existing cost-damage table uses $5/month per cloud VM per
node. But nothing in the protocol prevents running 100 Ed25519 identities
on one machine. This script computes the TRUE attack economics.

Attack setup:
  1. Attacker generates N Ed25519 keypairs (free)
  2. Runs N processes on one machine (localhost)
  3. Opens funded channels between them (needs initial MHR)
  4. Creates settlement records → all N nodes join active set
  5. Isolated partition: attacker controls 100% → self-dealing works
  6. Active-set scaling: min(N, 100) / 100 of full emission

Questions addressed:
  - How fast does the attacker bootstrap from minimal capital?
  - What is the REAL hardware cost (1 machine, not N VMs)?
  - What is the annual dilution at realistic costs?
  - What defenses actually matter?

All constants from the Mehr protocol specification.
"""

import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── PROTOCOL CONSTANTS (from spec) ──────────────────────────────────────────

INITIAL_EPOCH_REWARD = 10**6       # MHR per epoch (= 10^12 μMHR)
HALVING_INTERVAL     = 100_000     # epochs per halving period
BURN_RATE            = 0.02        # 2% service burn
MINTING_CAP          = 0.5         # minting ≤ 50% of net income
REFERENCE_SIZE       = 100         # active-set scaling denominator
EPOCHS_PER_YEAR      = 52_600      # ~1 epoch per 10 minutes


def epoch_reward(epoch_number):
    """Emission at a given epoch (MHR)."""
    shift = min(epoch_number // HALVING_INTERVAL, 63)
    return INITIAL_EPOCH_REWARD / (2 ** shift)


def scaled_emission(N, epoch_number):
    """Emission scaled by partition's active set size."""
    return (min(N, REFERENCE_SIZE) / REFERENCE_SIZE) * epoch_reward(epoch_number)


def cumulative_supply_at(epoch):
    """Approximate total circulating supply at a given epoch."""
    supply, current = 0.0, 0
    while current < epoch:
        reward = epoch_reward(current)
        next_halving = ((current // HALVING_INTERVAL) + 1) * HALVING_INTERVAL
        epochs_at_rate = min(next_halving, epoch) - current
        supply += reward * epochs_at_rate
        current += epochs_at_rate
    return supply


# ── SUPPLY DYNAMICS (from isolated_partition_analysis.py) ────────────────────

def simulate_partition(N, M_0, epochs, start_epoch=100_000):
    """Simulate optimal-attacker supply growth in an isolated N-node partition.
    Returns (supply_history, phase1_end_epoch)."""
    S = M_0
    history = [S]
    phase1_end = None
    for k in range(epochs):
        E_s = scaled_emission(N, start_epoch + k)
        min_spend = E_s / (MINTING_CAP * (1 - BURN_RATE))  # ~2.04 × E_s
        if S < min_spend:
            # Phase 1: spend everything, exponential growth (1.47x/epoch)
            A = S
        else:
            # Phase 2: spend minimum, linear growth (~0.96 × E_s/epoch)
            A = min_spend
            if phase1_end is None:
                phase1_end = k
        burns = BURN_RATE * A
        income = (1 - BURN_RATE) * A
        minting = min(E_s, MINTING_CAP * income)
        S = S - burns + minting
        history.append(S)
    return history, phase1_end


# ── LOCALHOST COST MODEL ────────────────────────────────────────────────────

# Realistic single-machine costs for running 100 lightweight processes
LOCALHOST_COSTS = {
    "free_hardware": {
        "label": "Existing PC/laptop",
        "monthly_hw": 0,        # already owned
        "monthly_elec": 5,      # ~$5/month marginal electricity
        "monthly_inet": 0,      # already have internet (not needed for localhost)
    },
    "cheap_vps": {
        "label": "Cheapest VPS ($5/mo)",
        "monthly_hw": 5,
        "monthly_elec": 0,      # included in VPS
        "monthly_inet": 0,      # included
    },
    "midrange_vps": {
        "label": "Mid-range VPS ($20/mo)",
        "monthly_hw": 20,
        "monthly_elec": 0,
        "monthly_inet": 0,
    },
}

# What the existing docs CLAIM (per-VM model, obviously wrong for localhost):
EXISTING_CLAIM_PER_NODE_MONTHLY = 5  # $5/month per node


# ── MAIN ANALYSIS ───────────────────────────────────────────────────────────

def main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    START_EPOCH = 100_000  # post-bootstrap (first halving)
    supply_at_start = cumulative_supply_at(START_EPOCH)

    print("=" * 74)
    print("LOCALHOST PARTITION ATTACK -- HONEST COST ANALYSIS")
    print("=" * 74)

    # ── 1. The per-VM cost model is wrong ───────────────────────────────────
    print("\n1. WHY THE $5/VM MODEL IS WRONG")
    print("=" * 74)
    print("""
   The existing analysis assumes each attacker node needs a separate cloud
   VM at $5/month. This gives 100-node attack = $6,000/year.

   Reality: a "node" is an Ed25519 keypair + a lightweight process.
   Nothing in the protocol prevents running 100 on one machine.

   Active set membership requires:
     - Appear as party_a or party_b in a SettlementRecord (last 2 epochs)
     - That's it. No hardware attestation, no PoW, no unique device check.

   100 processes on localhost can all settle with each other and all
   appear in the active set as 100 distinct nodes.
""")

    print(f"   {'Scenario':<28s}  {'Nodes':>6s}  {'Existing claim':>16s}  {'Real cost':>12s}")
    print(f"   {'-'*28}  {'-'*6}  {'-'*16}  {'-'*12}")
    for N in [3, 10, 50, 100]:
        existing_annual = N * EXISTING_CLAIM_PER_NODE_MONTHLY * 12
        real_annual = 5 * 12  # $5/month cheapest VPS
        print(f"   {'Cheap VPS, N=' + str(N):<28s}  {N:>6d}  ${existing_annual:>14,d}  ${real_annual:>10,d}")

    # ── 2. Bootstrap from minimal capital ───────────────────────────────────
    print(f"\n2. BOOTSTRAP FROM MINIMAL CAPITAL (N=100, start_epoch={START_EPOCH})")
    print("=" * 74)

    N = 100
    E_s = scaled_emission(N, START_EPOCH)
    min_spend_phase2 = E_s / (MINTING_CAP * (1 - BURN_RATE))

    print(f"   E_s = {E_s:,.0f} MHR/epoch (full emission, N≥100)")
    print(f"   Phase 2 threshold = 2.04 × E_s = {min_spend_phase2:,.0f} MHR")
    print(f"   Phase 1 growth factor = 1.47x per epoch")
    print()

    for M_0_label, M_0 in [("1 MHR", 1), ("100 MHR", 100), ("10,000 MHR", 10_000)]:
        epochs_to_phase2 = math.ceil(
            math.log(min_spend_phase2 / M_0) / math.log(1.47)
        ) if M_0 < min_spend_phase2 else 0
        hours = epochs_to_phase2 * 10 / 60
        print(f"   Starting capital: {M_0_label:<12s} → Phase 2 in {epochs_to_phase2:>4d} epochs"
              f" (~{hours:.1f} hours)")

    print(f"\n   Even 1 MHR bootstraps to full linear growth in ~36 epochs (~6 hours).")
    print(f"   Initial capital is NOT a meaningful barrier.")

    # ── 3. True cost-damage table ───────────────────────────────────────────
    print(f"\n3. CORRECTED COST-DAMAGE TABLE (localhost, post-bootstrap)")
    print("=" * 74)

    header = (f"   {'N':>5s}  {'E_s/epoch':>12s}  {'Annual excess':>16s}  "
              f"{'Ann dilution':>12s}  {'Real $/yr':>10s}  {'Old $/yr':>10s}  "
              f"{'Cost reduction':>15s}")
    print(header)
    print(f"   {'-'*5}  {'-'*12}  {'-'*16}  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*15}")

    for N in [3, 10, 50, 100, 200, 500]:
        e_s = scaled_emission(N, START_EPOCH)
        annual_excess = e_s * EPOCHS_PER_YEAR
        annual_pct = annual_excess / supply_at_start * 100
        real_cost = 60  # $5/month × 12 (one machine for ANY N)
        old_cost = N * EXISTING_CLAIM_PER_NODE_MONTHLY * 12
        reduction = f"{old_cost / real_cost:.0f}x cheaper" if real_cost > 0 else "∞"
        print(f"   {N:>5d}  {e_s:>12,.0f}  {annual_excess:>16,.0f}  "
              f"{annual_pct:>11.1f}%  ${real_cost:>8,d}  ${old_cost:>8,d}  {reduction:>15s}")

    print(f"\n   Key: N > 100 adds cost but NO additional damage (active-set cap).")
    print(f"   At N=100, attacker gets FULL emission for ~$60/year.")
    print(f"   The old table claimed $6,000/year — a 100x overestimate of cost.")

    # ── 4. Per-machine comparison: attacker vs honest ───────────────────────
    print(f"\n4. PER-MACHINE RETURN: ATTACKER vs HONEST")
    print("=" * 74)
    print("""
   The existing docs compare per-NODE returns: "honest participation earns
   the same per-node return." But the attacker's "nodes" are lightweight
   processes, not separate machines. The correct comparison is per-MACHINE.
""")

    for M_honest in [100, 1_000, 10_000]:
        honest_per_machine = epoch_reward(START_EPOCH) / M_honest
        attacker_per_machine = scaled_emission(100, START_EPOCH)  # 100 virtual nodes
        ratio = attacker_per_machine / honest_per_machine if honest_per_machine > 0 else float('inf')
        print(f"   Network size M={M_honest:>6,d}:")
        print(f"     Honest: {honest_per_machine:>12,.1f} MHR/epoch/machine")
        print(f"     Attack: {attacker_per_machine:>12,.1f} MHR/epoch/machine (100 virtual nodes)")
        print(f"     Ratio:  {ratio:>12,.0f}x advantage for attacker")
        print()

    # ── 5. What ACTUALLY defends against this? ──────────────────────────────
    print(f"5. REAL DEFENSES (honest assessment)")
    print("=" * 74)
    print("""
   STRONG defenses:
   ✓ Bootstrap phase (epoch < 100,000, ~1.9 years): GenesisAttestation
     completely prevents the attack. This is the ONLY complete defense.
   ✓ Halving schedule: Annual dilution halves every ~1.9 years.
     Year 1: 26.3% → Year 3: 13.2% → Year 5: 6.6% → ...
   ✓ Active-set cap at 100: Running >100 nodes adds zero benefit.
   ✓ Lifetime dilution cap: 50% maximum (convergent halving sum).

   WEAK defenses:
   ✗ Hardware cost: ~$60/year, not $6,000/year. NOT a deterrent.
   ✗ Per-node return parity: Misleading. Per-MACHINE, attacker wins by
     100x-10,000x depending on honest network size.
   ✗ Token value destruction: Circular argument ("attack reduces value of
     what you're attacking"). Does not prevent the attack.

   MEDIUM defenses:
   ~ Initial capital: Attacker needs SOME MHR. But even 1 MHR bootstraps
     to full emission in ~6 hours. This is a speed bump, not a wall.
   ~ Detection on merge: Excess supply is visible. But the CRDT merge
     rules are permissionless — the network MUST accept the excess.
     Social response (hard fork) is possible but outside the protocol.

   MISSING defenses:
   ! No proof-of-unique-device or hardware attestation
   ! No proof-of-work or computational cost per identity
   ! No mechanism to distinguish 100 localhost processes from 100 real
     devices in different locations
   ! No post-bootstrap defense that makes the attack MORE expensive
     than honest participation on a per-machine basis
""")

    # ── 6. Concrete attack scenario ─────────────────────────────────────────
    print(f"6. CONCRETE ATTACK SCENARIO")
    print("=" * 74)

    N = 100
    M_0 = 1.0  # 1 MHR initial capital
    years_to_sim = 5
    epochs_to_sim = years_to_sim * EPOCHS_PER_YEAR

    history, phase1_end = simulate_partition(N, M_0, epochs_to_sim, START_EPOCH)

    print(f"   Setup: 100 Ed25519 identities on one $5/month VPS")
    print(f"   Initial capital: 1 MHR (purchased or earned)")
    print(f"   Start: epoch {START_EPOCH} (post-bootstrap)")
    print()

    print(f"   {'Time':>16s}  {'Epochs':>8s}  {'Attacker supply':>18s}  "
          f"{'Network supply':>18s}  {'Dilution':>10s}")
    print(f"   {'-'*16}  {'-'*8}  {'-'*18}  {'-'*18}  {'-'*10}")

    for label, ep in [("6 hours", 36), ("1 day", 144), ("1 week", 1008),
                      ("1 month", 4320), ("6 months", 26300),
                      ("1 year", 52600), ("2 years", 105200),
                      ("5 years", 263000)]:
        if ep <= epochs_to_sim:
            atk_supply = history[ep]
            net_supply = cumulative_supply_at(START_EPOCH + ep)
            dilution = atk_supply / net_supply * 100 if net_supply > 0 else 0
            print(f"   {label:>16s}  {ep:>8,d}  {atk_supply:>18,.0f}  "
                  f"{net_supply:>18,.0f}  {dilution:>9.4f}%")

    print(f"\n   Phase 1 (exponential) ends at epoch {phase1_end} ({phase1_end * 10 / 60:.1f} hours)")
    print(f"   After that: linear growth at ~{0.959 * E_s:,.0f} MHR/epoch")

    # ── 7. What would make this defense credible? ───────────────────────────
    print(f"\n7. POTENTIAL MITIGATIONS (not currently in protocol)")
    print("=" * 74)
    print("""
   Options to make the localhost attack genuinely uneconomical:

   a) Proof-of-unique-hardware (TEE attestation):
      Require AMD SEV-SNP / ARM CCA attestation that each node runs on
      distinct physical hardware. Prevents virtual node multiplication.
      Downside: excludes devices without TEE support.

   b) Proof-of-bandwidth (challenge-response):
      Active set membership requires proof of REAL bandwidth to external
      peers (not just localhost). E.g., periodic latency/throughput
      challenges from random honest nodes.
      Downside: complex, requires connected honest nodes for verification.

   c) Social/trust-gated active set:
      Active set membership requires vouching from existing trusted nodes.
      Sybil nodes with no real trust relationships can't join.
      Downside: creates gatekeeping, hurts permissionless nature.

   d) Proof-of-storage/bandwidth-as-work:
      Each active set slot requires periodic proof of storing real data
      or relaying real traffic (verified by external challenge).
      Integrates Sybil cost into the service layer.

   e) Extended bootstrap period:
      Keep GenesisAttestation requirement beyond epoch 100,000.
      Simple but centralizing (genesis nodes become permanent gatekeepers).

   f) Graduated active-set scaling:
      Instead of linear scaling to 100, use sqrt(N) or log(N).
      Reduces benefit of adding virtual nodes beyond a small number.
      E.g., sqrt scaling: 100 virtual nodes → sqrt(100)/sqrt(100) = same,
      but 10 nodes → sqrt(10)/sqrt(100) = 31.6% (vs current 10%).

   g) IP/network diversity requirements:
      Require active set nodes to demonstrate distinct IP ranges or
      network paths. Localhost nodes would all share one IP.
      Downside: easy to circumvent with multiple IPs/VPNs.

   h) Minimum channel duration + diversity:
      Require settlement records to span multiple epochs AND involve
      channels with nodes outside the immediate partition (checked
      retroactively on merge).
""")

    # ── Plot ────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: localhost attack timeline
    ax = axes[0]
    epochs_plot = min(EPOCHS_PER_YEAR * 3, epochs_to_sim)  # 3 years
    x = np.arange(epochs_plot + 1) / EPOCHS_PER_YEAR  # in years
    ax.plot(x, [history[i] for i in range(epochs_plot + 1)],
            color="#F44336", linewidth=2, label="Attacker supply (100 virtual nodes)")
    ax.axhline(y=E_s / BURN_RATE, color="#4CAF50", linestyle="--", linewidth=1,
               label=f"Full-velocity equilibrium ({E_s/BURN_RATE:,.0f})")
    ax.set_xlabel("Years since attack start")
    ax.set_ylabel("Attacker MHR supply")
    ax.set_title("Localhost 100-Node Attack (1 MHR initial, $60/yr)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.ticklabel_format(style="plain", axis="y")

    # Right: cost comparison — old vs real
    ax = axes[1]
    nodes = [3, 10, 20, 50, 100, 200]
    old_costs = [n * 60 for n in nodes]
    real_costs = [60] * len(nodes)
    annual_dilutions = [scaled_emission(n, START_EPOCH) * EPOCHS_PER_YEAR
                        / supply_at_start * 100 for n in nodes]

    ax2 = ax.twinx()
    w = 0.35
    x_pos = np.arange(len(nodes))
    bars1 = ax.bar(x_pos - w/2, old_costs, w, color="#2196F3", alpha=0.7,
                   label="Old claim (N × $60/yr)")
    bars2 = ax.bar(x_pos + w/2, real_costs, w, color="#F44336", alpha=0.7,
                   label="Real cost ($60/yr flat)")
    ax2.plot(x_pos, annual_dilutions, "o-", color="#4CAF50", linewidth=2,
             label="Annual dilution %", markersize=6)

    ax.set_xlabel("Number of virtual nodes")
    ax.set_ylabel("Annual cost ($)")
    ax2.set_ylabel("Annual dilution (%)")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(n) for n in nodes])
    ax.set_title("Attack Cost: Old Claim vs Reality")
    ax.legend(loc="upper left", fontsize=9)
    ax2.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "localhost_partition_analysis.png"), dpi=150)
    plt.close(fig)

    # ── Save summary ────────────────────────────────────────────────────────
    summary_path = os.path.join(output_dir, "localhost_partition_table.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=" * 74 + "\n")
        f.write("LOCALHOST PARTITION ATTACK -- COST ANALYSIS SUMMARY\n")
        f.write("=" * 74 + "\n\n")

        f.write("THE PROBLEM:\n")
        f.write("  The existing cost table assumes 1 VM per node ($5/month each).\n")
        f.write("  Nothing prevents running 100 nodes on one machine.\n")
        f.write("  100-node attack real cost: ~$60/year (not $6,000/year).\n\n")

        f.write("CORRECTED COST TABLE (post-bootstrap, first halving period):\n")
        f.write(f"  {'N':>5s}  {'E_s/epoch':>12s}  {'Annual dilution':>16s}"
                f"  {'Real $/yr':>10s}  {'Old $/yr':>10s}\n")
        f.write(f"  {'-'*5}  {'-'*12}  {'-'*16}  {'-'*10}  {'-'*10}\n")
        for n in [3, 10, 50, 100, 200]:
            e_s = scaled_emission(n, START_EPOCH)
            ann_pct = e_s * EPOCHS_PER_YEAR / supply_at_start * 100
            real = 60
            old = n * 60
            f.write(f"  {n:>5d}  {e_s:>12,.0f}  {ann_pct:>15.1f}%"
                    f"  ${real:>8,d}  ${old:>8,d}\n")

        f.write("\nBOOTSTRAP FROM 1 MHR:\n")
        f.write(f"  Phase 1 → Phase 2 in ~36 epochs (~6 hours)\n")
        f.write(f"  Initial capital is NOT a meaningful barrier.\n\n")

        f.write("REAL DEFENSES:\n")
        f.write("  1. Bootstrap GenesisAttestation (epoch < 100,000): COMPLETE block\n")
        f.write("  2. Halving schedule: damage halves every ~1.9 years\n")
        f.write("  3. Active-set cap at 100: no benefit from >100 nodes\n")
        f.write("  4. Lifetime dilution cap: 50% (convergent sum)\n\n")

        f.write("WEAK/INVALID DEFENSES:\n")
        f.write("  - Hardware cost ($6,000/yr): Actually $60/yr\n")
        f.write("  - Per-node return parity: Per-MACHINE, attacker wins 100-10,000x\n")
        f.write("  - Token value destruction: Circular argument\n\n")

        f.write("OPEN QUESTION:\n")
        f.write("  Post-bootstrap, what makes this attack more expensive than\n")
        f.write("  honest participation on a per-hardware-dollar basis?\n")
        f.write("  Current answer: nothing in the protocol.\n")
        f.write("  The defense relies on halving (time) and dilution (self-harm),\n")
        f.write("  not on making the attack genuinely costly.\n")

    print(f"\nOutput saved to {output_dir}/")
    print(f"  - localhost_partition_analysis.png")
    print(f"  - localhost_partition_table.txt")

    # ── Final verdict ───────────────────────────────────────────────────────
    print(f"\n{'='*74}")
    print("VERDICT")
    print(f"{'='*74}")
    print("""
The claim that the isolated partition attack is "uneconomical" is WRONG
for the localhost case. The real defenses are:

  1. Bootstrap phase (~1.9 years of complete protection)
  2. Halving (damage decreases over time, but slowly)
  3. Mathematical cap (50% lifetime dilution max)

These are REAL but they are not "the attack is too expensive." The attack
costs ~$60/year for 26.3% first-year dilution. That's extremely cheap.

The protocol needs either:
  (a) An honest acknowledgment that this is the inherent cost of partition
      tolerance without hardware attestation, OR
  (b) A new mechanism to make virtual node multiplication expensive
      (TEE attestation, proof-of-bandwidth, trust-gated active set, etc.)
""")


if __name__ == "__main__":
    main()

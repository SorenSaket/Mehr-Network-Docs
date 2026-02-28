"""
Mehr Network -- Isolated Partition Supply Dynamics Analysis

Models the supply growth in an attacker-controlled isolated partition
under two strategies:
  1. Full velocity:    attacker spends ALL supply each epoch (converges)
  2. Minimum spending: attacker spends only enough to max minting (linear growth)

Demonstrates that the equilibrium formula E_s/burn_rate only holds under
strategy 1. The correct worst-case bound (strategy 2) is linear growth
at ~0.96×E_s per epoch, but the cumulative excess converges because
the emission schedule halves geometrically.

All constants are drawn directly from the Mehr protocol specification.
"""

import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --- PROTOCOL CONSTANTS (from spec) -----------------------------------------

INITIAL_EPOCH_REWARD = 10**6       # MHR per epoch (bootstrap, = 10^12 μMHR)
HALVING_INTERVAL = 100_000         # epochs per halving period
BURN_RATE = 0.02                   # 2% service burn
MINTING_CAP = 0.5                  # minting ≤ 50% of net income
REFERENCE_SIZE = 100               # active-set scaling denominator
SUPPLY_CEILING_uMHR = 2**64        # theoretical μMHR ceiling


def epoch_reward(epoch_number):
    """Exact emission formula from mhr-token.md (in MHR, not μMHR)."""
    shift = min(epoch_number // HALVING_INTERVAL, 63)
    return INITIAL_EPOCH_REWARD / (2 ** shift)


def scaled_emission(N, epoch_number):
    """Scaled emission for an N-node partition."""
    return (min(N, REFERENCE_SIZE) / REFERENCE_SIZE) * epoch_reward(epoch_number)


# --- SUPPLY DYNAMICS MODEL --------------------------------------------------

def simulate_partition(N, M_0, epochs, strategy="optimal", start_epoch=100_000):
    """Simulate supply dynamics in an isolated N-node partition.

    Args:
        N: number of attacker nodes
        M_0: initial MHR capital
        epochs: number of epochs to simulate
        strategy: "full_velocity" or "optimal" (minimum spending)
        start_epoch: starting epoch number (affects emission schedule)

    Returns:
        supply_history: list of supply values per epoch
    """
    S = M_0
    history = [S]
    for k in range(epochs):
        E_s = scaled_emission(N, start_epoch + k)
        # Minimum spend to saturate minting cap: 0.5 * 0.98 * A = E_s → A = E_s / 0.49
        min_spend = E_s / (MINTING_CAP * (1 - BURN_RATE))

        if strategy == "full_velocity":
            A = S
        else:  # optimal: minimize spending to maximize supply growth
            if S < min_spend:
                A = S  # must spend everything (not enough for minimum)
            else:
                A = min_spend

        burns = BURN_RATE * A
        income = (1 - BURN_RATE) * A
        minting = min(E_s, MINTING_CAP * income)
        S = S - burns + minting
        history.append(S)
    return history


def cumulative_excess(N, start_epoch=100_000, num_halvings=20):
    """Total lifetime excess from an infinite-duration partition.

    Sums E_s per epoch over all halving periods from start_epoch onward.
    Under optimal attacker strategy, supply grows at most E_s per epoch,
    so this is the upper bound on total excess.
    """
    total = 0.0
    for h in range(num_halvings):
        epoch = start_epoch + h * HALVING_INTERVAL
        E_s = scaled_emission(N, epoch)
        total += E_s * HALVING_INTERVAL
    return total


def cumulative_supply_at(epoch):
    """Approximate total circulating supply at given epoch."""
    supply = 0.0
    current = 0
    while current < epoch:
        reward = epoch_reward(current)
        next_halving = ((current // HALVING_INTERVAL) + 1) * HALVING_INTERVAL
        epochs_at_rate = min(next_halving, epoch) - current
        supply += reward * epochs_at_rate
        current += epochs_at_rate
    return supply


# --- MAIN ANALYSIS ----------------------------------------------------------

def main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("MEHR NETWORK -- ISOLATED PARTITION SUPPLY DYNAMICS")
    print("=" * 70)

    # --- 1. Compare strategies for a 3-node partition ---
    N = 3
    M_0 = 100.0  # initial capital
    epochs = 1000
    start_epoch = 100_000  # post-bootstrap (first halving)
    E_s = scaled_emission(N, start_epoch)

    print(f"\n1. STRATEGY COMPARISON (N={N}, M_0={M_0}, start_epoch={start_epoch})")
    print(f"   Scaled emission E_s = {E_s:,.1f} MHR/epoch")
    print(f"   Claimed equilibrium (E_s/burn_rate) = {E_s/BURN_RATE:,.1f} MHR")

    full_vel = simulate_partition(N, M_0, epochs, "full_velocity", start_epoch)
    optimal = simulate_partition(N, M_0, epochs, "optimal", start_epoch)

    print(f"\n   {'Epoch':>8s}  {'Full Velocity':>16s}  {'Optimal (Min Spend)':>20s}")
    print(f"   {'-'*8}  {'-'*16}  {'-'*20}")
    for k in [0, 10, 50, 100, 200, 500, 999]:
        print(f"   {k:>8d}  {full_vel[k]:>16,.1f}  {optimal[k]:>20,.1f}")

    print(f"\n   Full velocity converges to: {full_vel[-1]:>14,.1f} MHR")
    print(f"   Optimal after {epochs} epochs:  {optimal[-1]:>14,.1f} MHR")
    print(f"   Ratio (optimal/equilibrium): {optimal[-1]/(E_s/BURN_RATE):.1f}x")

    # --- 2. Correct worst-case bounds ---
    print(f"\n2. WORST-CASE BOUNDS (optimal attacker strategy)")
    print(f"\n   Per-epoch bound: ≤ E_s = {E_s:,.1f} MHR/epoch")
    print(f"   Actual per-epoch growth (Phase 2): ~{0.959*E_s:,.1f} MHR/epoch")
    print(f"   Burn friction: {(1 - 0.959)*100:.1f}% reduction vs no-burn")

    for duration, label in [(100, "~17 hours"), (1000, "~1 week"),
                            (4300, "~1 month"), (52600, "~1 year")]:
        excess = optimal[min(duration, epochs)] if duration <= epochs else M_0 + 0.959 * E_s * duration
        supply = cumulative_supply_at(start_epoch)
        pct = excess / supply * 100
        print(f"\n   After {duration:>6d} epochs ({label:>10s}):")
        print(f"     Max excess:  {excess:>14,.1f} MHR")
        print(f"     Network supply: {supply:>14,.1f} MHR")
        print(f"     Dilution:    {pct:>14.6f}%")

    # --- 3. Total lifetime excess (convergent halving sum) ---
    print(f"\n3. TOTAL LIFETIME EXCESS (infinite-duration partition)")
    for n in [3, 5, 10, 50, 100]:
        total = cumulative_excess(n, start_epoch)
        supply = cumulative_supply_at(start_epoch + 20 * HALVING_INTERVAL)
        pct = total / supply * 100 if supply > 0 else 0
        print(f"   N={n:>3d}: total excess = {total:>16,.1f} MHR"
              f"  ({pct:.4f}% of mature supply)")

    # --- 4. Comparison across partition sizes ---
    print(f"\n4. PARTITION SIZE COMPARISON (1000 epochs, optimal attacker)")
    print(f"   {'N':>5s}  {'E_s':>12s}  {'After 1000':>14s}  {'% of supply':>12s}")
    print(f"   {'-'*5}  {'-'*12}  {'-'*14}  {'-'*12}")
    supply = cumulative_supply_at(start_epoch)
    for n in [3, 5, 10, 20, 50, 100]:
        hist = simulate_partition(n, M_0, 1000, "optimal", start_epoch)
        e_s = scaled_emission(n, start_epoch)
        pct = hist[-1] / supply * 100
        print(f"   {n:>5d}  {e_s:>12,.1f}  {hist[-1]:>14,.1f}  {pct:>12.6f}%")

    # --- 5. Cost-damage analysis ---
    EPOCHS_PER_YEAR = 52_600
    VM_COST_MONTHLY = 5  # $5/month per cloud VM (low estimate)
    print(f"\n5. ATTACKER ECONOMICS: COST vs. DAMAGE")
    print(f"   {'N':>5s}  {'E_s/epoch':>12s}  {'Annual excess':>16s}  {'Annual %':>10s}"
          f"  {'Lifetime %':>12s}  {'VM $/yr':>10s}")
    print(f"   {'-'*5}  {'-'*12}  {'-'*16}  {'-'*10}  {'-'*12}  {'-'*10}")
    for n in [3, 5, 10, 20, 50, 100, 200]:
        e_s = scaled_emission(n, start_epoch)
        annual = e_s * EPOCHS_PER_YEAR
        annual_pct = annual / supply * 100
        lifetime = cumulative_excess(n, start_epoch)
        mature_supply = cumulative_supply_at(start_epoch + 20 * HALVING_INTERVAL)
        lifetime_pct = lifetime / mature_supply * 100 if mature_supply > 0 else 0
        cost = n * VM_COST_MONTHLY * 12
        print(f"   {n:>5d}  {e_s:>12,.1f}  {annual:>16,.0f}  {annual_pct:>10.3f}"
              f"  {lifetime_pct:>12.1f}  ${cost:>9,d}")

    # --- Plot ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: strategy comparison
    ax = axes[0]
    x = range(len(full_vel))
    ax.plot(x, full_vel, label="Full velocity (spends all)", color="#2196F3", linewidth=1.5)
    ax.plot(x, optimal, label="Optimal (minimum spending)", color="#F44336", linewidth=1.5)
    ax.axhline(y=E_s / BURN_RATE, color="#4CAF50", linestyle="--", linewidth=1,
               label=f"Claimed equilibrium ({E_s/BURN_RATE:,.0f})")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Supply (MHR)")
    ax.set_title(f"Isolated Partition Supply ({N}-node, post-bootstrap)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.ticklabel_format(style="plain")

    # Right: partition size comparison
    ax = axes[1]
    for n, color in [(3, "#F44336"), (5, "#FF9800"), (10, "#4CAF50"),
                     (50, "#2196F3"), (100, "#9C27B0")]:
        hist = simulate_partition(n, M_0, 1000, "optimal", start_epoch)
        ax.plot(range(len(hist)), hist, label=f"N={n}", color=color, linewidth=1.5)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Supply (MHR)")
    ax.set_title("Optimal Attacker: Supply vs Partition Size")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.ticklabel_format(style="plain")

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "isolated_partition_analysis.png"), dpi=150)
    plt.close(fig)

    # --- Summary ---
    print(f"\n{'='*70}")
    print("KEY FINDINGS")
    print(f"{'='*70}")
    print("""
1. EQUILIBRIUM CLAIM:
   - The formula equilibrium = E_s / burn_rate is ONLY valid when the
     attacker circulates ALL supply every epoch (100% money velocity).
   - A rational attacker spends the minimum needed to saturate the
     minting cap (~2.04 × E_s per epoch), keeping a growing reserve
     that is never burned.
   - Under optimal strategy, supply grows linearly at ~0.96 × E_s
     per epoch with NO convergence.

2. CORRECT WORST-CASE BOUND:
   - Per epoch: supply growth ≤ E_s (scaled emission is the hard ceiling)
   - The 2% burn provides ~4% friction (0.96 × E_s vs E_s)
   - Total lifetime excess converges because emission halves:
     Σ E_s × halving_period = (N/100) × E × 100,000 × 2 (geometric sum)

3. ATTACKER ECONOMICS:
   - A 3-node attack costs $180/year for 0.8% annual dilution (first year)
   - A 100-node attack costs $6,000/year for 26% annual dilution (first year)
   - Annual dilution halves every ~1.9 years (emission halving)
   - Active-set cap at 100: no benefit from running > 100 nodes
   - Repeated attacks (merge/split) offer no compounding advantage
   - Honest participation earns similar per-node return

4. CAN ATTACKERS RUIN THE NETWORK?
   - No. Lifetime dilution is bounded: N/200 of supply (max 50% for N ≥ 100)
   - Damage rate decreases over time (halving schedule)
   - Small partitions (N ≤ 10): < 5% lifetime dilution → negligible
   - Large partitions (N = 100): 50% lifetime → significant but requires
     $6,000+/year indefinitely, decreasing return each halving period
   - This is the inherent cost of partition tolerance without global consensus
""")

    # Save summary table
    with open(os.path.join(output_dir, "isolated_partition_table.txt"), "w") as f:
        f.write("=" * 70 + "\n")
        f.write("MEHR NETWORK -- ISOLATED PARTITION SUPPLY DYNAMICS\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Protocol constants:\n")
        f.write(f"  Burn rate: {BURN_RATE*100}%\n")
        f.write(f"  Minting cap: {MINTING_CAP*100}% of net income\n")
        f.write(f"  Reference size: {REFERENCE_SIZE} nodes\n\n")

        f.write("Strategy comparison (N=3, start_epoch=100,000):\n")
        f.write(f"  E_s = {E_s:,.1f} MHR/epoch\n")
        f.write(f"  Claimed equilibrium = {E_s/BURN_RATE:,.1f} MHR\n\n")
        f.write(f"  {'Epoch':>8s}  {'Full Velocity':>16s}  {'Optimal':>16s}\n")
        f.write(f"  {'-'*8}  {'-'*16}  {'-'*16}\n")
        for k in [0, 10, 50, 100, 200, 500, 999]:
            f.write(f"  {k:>8d}  {full_vel[k]:>16,.1f}  {optimal[k]:>16,.1f}\n")
        f.write(f"\n  Full velocity final:  {full_vel[-1]:>14,.1f} MHR (converges)\n")
        f.write(f"  Optimal final:        {optimal[-1]:>14,.1f} MHR (linear growth)\n")
        f.write(f"  Ratio:                {optimal[-1]/(E_s/BURN_RATE):.1f}x claimed equilibrium\n\n")

        f.write("Correct worst-case bounds:\n")
        f.write(f"  Per-epoch: ≤ {E_s:,.1f} MHR (actual ~{0.959*E_s:,.1f} with burn)\n")
        f.write(f"  1 week (1000 epochs):  {optimal[-1]:>14,.1f} MHR\n")

        total_3 = cumulative_excess(3, start_epoch)
        mature_supply = cumulative_supply_at(start_epoch + 20 * HALVING_INTERVAL)
        lifetime_pct = total_3 / mature_supply * 100 if mature_supply > 0 else 0
        f.write(f"  Infinite duration:     {total_3:>14,.1f} MHR (convergent sum)\n")
        f.write(f"  As % of mature supply: {lifetime_pct:.1f}%\n\n")

        f.write("Cost-damage analysis (first halving period, $5/mo per VM):\n")
        f.write(f"  {'N':>5s}  {'E_s/epoch':>12s}  {'Annual dilution':>16s}"
                f"  {'Lifetime':>10s}  {'VM $/yr':>10s}\n")
        f.write(f"  {'-'*5}  {'-'*12}  {'-'*16}  {'-'*10}  {'-'*10}\n")
        for n in [3, 5, 10, 20, 50, 100, 200]:
            e_s = scaled_emission(n, start_epoch)
            annual_pct = e_s * 52_600 / supply * 100
            lt = cumulative_excess(n, start_epoch)
            lt_pct = lt / mature_supply * 100 if mature_supply > 0 else 0
            cost = n * 5 * 12
            f.write(f"  {n:>5d}  {e_s:>12,.1f}  {annual_pct:>15.1f}%"
                    f"  {lt_pct:>9.1f}%  ${cost:>9,d}\n")

    print(f"\nOutput saved to {output_dir}/")


if __name__ == "__main__":
    main()

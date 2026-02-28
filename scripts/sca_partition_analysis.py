"""
Mehr Network -- Partition Defense Analysis (Trust-Gated + Merge Audit)

Models the TWO-LAYER defense against the localhost partition attack:

  Layer 1: Trust-gated active set
    - Post-bootstrap, minting requires ≥1 mutual trust link
    - Does NOT prevent minting during isolation (attacker nodes trust each other)
    - Establishes trust as protocol-level concept for merge-time auditing

  Layer 2: Merge-time trust audit
    - On rejoin, partition's minted supply is validated against trust graph
    - Nodes with zero cross-partition trust have minting quarantined
    - CRDT data merges normally; only minting is audited

Compares:
  - Baseline (no defense post-bootstrap)
  - Trust-gated + merge audit (combined defense, various trust infiltration levels)

All constants from the Mehr protocol specification.
"""

import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -- PROTOCOL CONSTANTS -------------------------------------------------------

INITIAL_EPOCH_REWARD = 10**6       # MHR per epoch
HALVING_INTERVAL     = 100_000     # epochs per halving period
BURN_RATE            = 0.02        # 2% service burn
MINTING_CAP          = 0.5         # minting <= 50% of net income
REFERENCE_SIZE       = 100         # active-set scaling denominator
EPOCHS_PER_YEAR      = 52_600      # ~1 epoch per 10 minutes


def epoch_reward(epoch_number):
    shift = min(epoch_number // HALVING_INTERVAL, 63)
    return INITIAL_EPOCH_REWARD / (2 ** shift)


def scaled_emission(N, epoch_number):
    return (min(N, REFERENCE_SIZE) / REFERENCE_SIZE) * epoch_reward(epoch_number)


def cumulative_supply_at(epoch):
    supply, current = 0.0, 0
    while current < epoch:
        reward = epoch_reward(current)
        next_h = ((current // HALVING_INTERVAL) + 1) * HALVING_INTERVAL
        epochs_at_rate = min(next_h, epoch) - current
        supply += reward * epochs_at_rate
        current += epochs_at_rate
    return supply


def simulate_partition(N, M_0, epochs, start_epoch=100_000):
    """Optimal-attacker supply growth. Returns supply history."""
    S = M_0
    history = [S]
    for k in range(epochs):
        E_s = scaled_emission(N, start_epoch + k)
        min_spend = E_s / (MINTING_CAP * (1 - BURN_RATE))
        if S < min_spend:
            A = S
        else:
            A = min_spend
        burns = BURN_RATE * A
        income = (1 - BURN_RATE) * A
        minting = min(E_s, MINTING_CAP * income)
        S = S - burns + minting
        history.append(S)
    return history


# -- SCA MODEL ----------------------------------------------------------------

def simulate_sca_attack(N, M_0, K_sca, total_epochs, start_epoch=100_000,
                        reconnect_cost_epochs=10):
    """Simulate attack with Service Continuity Attestation.

    The attacker gets K_sca epochs of minting per isolation cycle.
    To restart, they must reconnect for reconnect_cost_epochs (during
    which the excess is visible and merge audit runs).

    Args:
        N: virtual nodes
        M_0: initial capital
        K_sca: SCA attestation lifetime (epochs)
        total_epochs: total simulation duration
        start_epoch: starting epoch number
        reconnect_cost_epochs: epochs spent reconnected between cycles

    Returns:
        dict with attack metrics
    """
    S = M_0
    total_minted = 0.0
    cycles = 0
    epoch = 0

    while epoch < total_epochs:
        # Isolation phase: mint for K_sca epochs
        mint_epochs = min(K_sca, total_epochs - epoch)
        for k in range(mint_epochs):
            E_s = scaled_emission(N, start_epoch + epoch + k)
            min_spend = E_s / (MINTING_CAP * (1 - BURN_RATE))
            if S < min_spend:
                A = S
            else:
                A = min_spend
            burns = BURN_RATE * A
            income = (1 - BURN_RATE) * A
            minting = min(E_s, MINTING_CAP * income)
            S = S - burns + minting
            total_minted += minting
        epoch += mint_epochs
        cycles += 1

        # Reconnection phase: no minting, visible to network
        epoch += reconnect_cost_epochs

    net_supply = cumulative_supply_at(start_epoch + total_epochs)
    return {
        "total_minted": total_minted,
        "final_supply": S,
        "cycles": cycles,
        "dilution_pct": S / net_supply * 100 if net_supply > 0 else 0,
    }


def simulate_sca_with_merge_audit(N, M_0, K_sca, total_epochs, start_epoch=100_000,
                                  audit_discount=1.0, reconnect_cost_epochs=10):
    """Simulate attack with SCA + merge-time audit.

    audit_discount: fraction of minting rejected at merge (0.0 = no audit, 1.0 = all rejected)
    For fresh identities: audit_discount = 1.0 (no cross-trust -> all minting rejected)
    For pre-planned with some trust: audit_discount < 1.0
    """
    S = M_0
    total_accepted = 0.0
    total_rejected = 0.0
    cycles = 0
    epoch = 0

    while epoch < total_epochs:
        # Isolation phase
        cycle_minted = 0.0
        mint_epochs = min(K_sca, total_epochs - epoch)
        for k in range(mint_epochs):
            E_s = scaled_emission(N, start_epoch + epoch + k)
            min_spend = E_s / (MINTING_CAP * (1 - BURN_RATE))
            if S < min_spend:
                A = S
            else:
                A = min_spend
            burns = BURN_RATE * A
            income = (1 - BURN_RATE) * A
            minting = min(E_s, MINTING_CAP * income)
            S = S - burns + minting
            cycle_minted += minting
        epoch += mint_epochs
        cycles += 1

        # Merge audit: discount the minting
        rejected = cycle_minted * audit_discount
        accepted = cycle_minted - rejected
        S -= rejected  # balance rebased
        S = max(S, M_0)  # floor at initial capital (can't go below what you started with)
        total_accepted += accepted
        total_rejected += rejected

        # Reconnection phase
        epoch += reconnect_cost_epochs

    net_supply = cumulative_supply_at(start_epoch + total_epochs)
    return {
        "total_accepted": total_accepted,
        "total_rejected": total_rejected,
        "final_supply": S,
        "cycles": cycles,
        "dilution_pct": S / net_supply * 100 if net_supply > 0 else 0,
    }


# -- MAIN ANALYSIS ------------------------------------------------------------

def main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    START = 100_000
    N = 100
    M_0 = 1.0
    supply_at_start = cumulative_supply_at(START)

    print("=" * 74)
    print("SERVICE CONTINUITY ATTESTATION (SCA) -- PARTITION DEFENSE ANALYSIS")
    print("=" * 74)

    # -- 1. Current design (no SCA post-bootstrap) --
    print("\n1. BASELINE: CURRENT DESIGN (no SCA after epoch 100K)")
    print("=" * 74)

    for label, ep in [("1 year", EPOCHS_PER_YEAR), ("5 years", 5 * EPOCHS_PER_YEAR)]:
        hist = simulate_partition(N, M_0, ep, START)
        supply = cumulative_supply_at(START + ep)
        pct = hist[-1] / supply * 100
        print(f"   {label}: {hist[-1]:>16,.0f} MHR minted, {pct:.2f}% dilution")

    # -- 2. SCA with various K values --
    print(f"\n2. WITH SCA: ATTESTATION EXPIRES AFTER K EPOCHS")
    print("=" * 74)
    print(f"   Attack: 100 virtual nodes, pre-planned (get SCAs, then isolate)")
    print(f"   Reconnection cost: 10 epochs between cycles (merge audit window)")
    print()

    header = (f"   {'K (epochs)':>12s}  {'K (days)':>10s}  {'1yr dilution':>14s}  "
              f"{'5yr dilution':>14s}  {'Cycles/yr':>10s}")
    print(header)
    print(f"   {'-'*12}  {'-'*10}  {'-'*14}  {'-'*14}  {'-'*10}")

    for K in [1000, 2500, 5000, 10000, 25000, 50000, 100000]:
        days = K * 10 / 60 / 24
        r1 = simulate_sca_attack(N, M_0, K, EPOCHS_PER_YEAR, START)
        r5 = simulate_sca_attack(N, M_0, K, 5 * EPOCHS_PER_YEAR, START)
        print(f"   {K:>12,d}  {days:>10.1f}  {r1['dilution_pct']:>13.2f}%  "
              f"{r5['dilution_pct']:>13.2f}%  {r1['cycles']:>10d}")

    print(f"\n   Baseline (no SCA, unlimited):")
    hist_1y = simulate_partition(N, M_0, EPOCHS_PER_YEAR, START)
    supply_1y = cumulative_supply_at(START + EPOCHS_PER_YEAR)
    print(f"   {'unlimited':>12s}  {'infinite':>10s}  {hist_1y[-1]/supply_1y*100:>13.2f}%")

    # -- 3. SCA + merge audit --
    print(f"\n3. SCA + MERGE-TIME TRUST AUDIT")
    print("=" * 74)
    print(f"   Fresh identities (no cross-trust): audit discount = 100%")
    print(f"   Pre-planned (1 real trust link): audit discount = 99%")
    print(f"   Pre-planned (infiltrated): audit discount = 50%")
    print()

    K = 10_000  # ~69 days, the recommended value
    print(f"   K = {K:,d} epochs (~{K*10/60/24:.0f} days)")
    print()
    print(f"   {'Scenario':<35s}  {'Discount':>10s}  {'1yr dilution':>14s}  {'5yr dilution':>14s}")
    print(f"   {'-'*35}  {'-'*10}  {'-'*14}  {'-'*14}")

    for label, discount in [("No SCA, no audit (current)", -1),
                            ("SCA only (K=10K)", 0.0),
                            ("SCA + audit, fresh IDs", 1.0),
                            ("SCA + audit, 1 trust link", 0.99),
                            ("SCA + audit, infiltrated", 0.50)]:
        if discount == -1:
            # Baseline
            h1 = simulate_partition(N, M_0, EPOCHS_PER_YEAR, START)
            h5 = simulate_partition(N, M_0, 5 * EPOCHS_PER_YEAR, START)
            s1 = cumulative_supply_at(START + EPOCHS_PER_YEAR)
            s5 = cumulative_supply_at(START + 5 * EPOCHS_PER_YEAR)
            d1 = h1[-1] / s1 * 100
            d5 = h5[-1] / s5 * 100
            print(f"   {label:<35s}  {'N/A':>10s}  {d1:>13.2f}%  {d5:>13.2f}%")
        elif discount == 0.0:
            r1 = simulate_sca_attack(N, M_0, K, EPOCHS_PER_YEAR, START)
            r5 = simulate_sca_attack(N, M_0, K, 5 * EPOCHS_PER_YEAR, START)
            print(f"   {label:<35s}  {'0%':>10s}  {r1['dilution_pct']:>13.2f}%  "
                  f"{r5['dilution_pct']:>13.2f}%")
        else:
            r1 = simulate_sca_with_merge_audit(N, M_0, K, EPOCHS_PER_YEAR, START, discount)
            r5 = simulate_sca_with_merge_audit(N, M_0, K, 5 * EPOCHS_PER_YEAR, START, discount)
            print(f"   {label:<35s}  {discount*100:>9.0f}%  {r1['dilution_pct']:>13.2f}%  "
                  f"{r5['dilution_pct']:>13.2f}%")

    # -- 4. Recommended K analysis --
    print(f"\n4. RECOMMENDED K VALUE ANALYSIS")
    print("=" * 74)
    print("""
   K too short: legitimate isolated communities lose minting too quickly.
   K too long: attacker gets more minting per cycle.

   Tradeoff table (SCA + merge audit with 100% discount for fresh IDs):
""")
    print(f"   {'K':>8s}  {'Days':>8s}  {'Atk 1yr':>10s}  {'Village impact':>18s}")
    print(f"   {'-'*8}  {'-'*8}  {'-'*10}  {'-'*18}")

    for K in [1000, 2500, 5000, 10000, 25000]:
        days = K * 10 / 60 / 24
        r = simulate_sca_with_merge_audit(N, M_0, K, EPOCHS_PER_YEAR, START, 1.0)
        if days <= 7:
            village = "Loses minting in <1wk"
        elif days <= 17:
            village = "Loses minting in ~2wk"
        elif days <= 35:
            village = "Loses minting in ~1mo"
        elif days <= 70:
            village = "Loses minting in ~2mo"
        else:
            village = "Loses minting in ~6mo"
        print(f"   {K:>8,d}  {days:>8.1f}  {r['dilution_pct']:>9.2f}%  {village:>18s}")

    print(f"""
   RECOMMENDATION: K = 10,000 epochs (~69 days)
     - Legitimate villages: can be isolated for ~2 months before
       minting stops (they can still TRANSACT, just not mint)
     - Fresh-identity attacker: 0% dilution (merge audit rejects all)
     - Pre-planned attacker: limited to K epochs per cycle, must
       reconnect (visible) to refresh SCAs
""")

    # -- 5. Neighborhood-scoped minting (future) --
    print(f"5. FUTURE: NEIGHBORHOOD-SCOPED MINTING (DISTRIBUTED ECONOMY)")
    print("=" * 74)
    print("""
   The most fundamental fix: make minted tokens NON-GLOBALLY-FUNGIBLE.

   Design:
     - Each trust neighborhood has its own minting pool
     - Minted supply is tagged with the neighborhood's trust root
     - Cross-neighborhood payments use bilateral exchange channels
     - Exchange rate = market price (how much real service does this
       neighborhood provide to the broader network?)

   Attack outcome:
     - Attacker creates "Attacker-MHR" in their partition
     - Nobody exchanges it for real Portland-MHR
     - Zero impact on any other neighborhood's economy

   Tradeoffs:
     - Users deal with exchange rates (complexity)
     - New neighborhoods need bootstrapping
     - Cross-community payments have conversion friction

   This is how real-world economies work: different currencies backed by
   different real economies. The exchange rate IS the proof of legitimacy.

   Implementation complexity: HIGH. This is a v2.0 feature if SCA + merge
   audit prove insufficient.
""")

    # -- Plot --
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: dilution comparison across defenses
    ax = axes[0]
    K_values = [1000, 2500, 5000, 10000, 25000, 50000]
    sca_only = []
    sca_audit_fresh = []
    sca_audit_preplan = []
    for K in K_values:
        r = simulate_sca_attack(N, M_0, K, EPOCHS_PER_YEAR, START)
        sca_only.append(r['dilution_pct'])
        r = simulate_sca_with_merge_audit(N, M_0, K, EPOCHS_PER_YEAR, START, 1.0)
        sca_audit_fresh.append(r['dilution_pct'])
        r = simulate_sca_with_merge_audit(N, M_0, K, EPOCHS_PER_YEAR, START, 0.50)
        sca_audit_preplan.append(r['dilution_pct'])

    baseline = hist_1y[-1] / supply_1y * 100
    K_days = [K * 10 / 60 / 24 for K in K_values]

    ax.axhline(y=baseline, color="#F44336", linestyle="--", linewidth=2,
               label=f"No SCA (current): {baseline:.1f}%")
    ax.plot(K_days, sca_only, "o-", color="#FF9800", linewidth=2,
            label="SCA only", markersize=6)
    ax.plot(K_days, sca_audit_preplan, "s-", color="#2196F3", linewidth=2,
            label="SCA + audit (50% discount)", markersize=6)
    ax.plot(K_days, sca_audit_fresh, "^-", color="#4CAF50", linewidth=2,
            label="SCA + audit (fresh IDs)", markersize=6)
    ax.axvline(x=69, color="#9C27B0", linestyle=":", linewidth=1,
               label="K=10K (~69 days)")
    ax.set_xlabel("SCA lifetime K (days)")
    ax.set_ylabel("First-year dilution (%)")
    ax.set_title("Partition Attack: Defense Comparison (N=100)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    # Right: 5-year supply trajectory comparison
    ax = axes[1]
    epochs_5y = 5 * EPOCHS_PER_YEAR

    # Baseline (no SCA)
    h_base = simulate_partition(N, M_0, epochs_5y, START)
    x_years = np.arange(epochs_5y + 1) / EPOCHS_PER_YEAR

    ax.plot(x_years, h_base, color="#F44336", linewidth=2, label="No SCA (current)")

    # SCA only, K=10K
    K = 10_000
    # Simulate cycle-by-cycle
    S = M_0
    h_sca = [S]
    epoch = 0
    while epoch < epochs_5y:
        mint_ep = min(K, epochs_5y - epoch)
        for k in range(mint_ep):
            E_s = scaled_emission(N, START + epoch + k)
            min_spend = E_s / (MINTING_CAP * (1 - BURN_RATE))
            A = min(S, min_spend) if S < min_spend else min_spend
            burns = BURN_RATE * A
            income = (1 - BURN_RATE) * A
            minting = min(E_s, MINTING_CAP * income)
            S = S - burns + minting
            h_sca.append(S)
        epoch += mint_ep
        # SCA expires -> no minting, but track time
        reconnect = min(10, epochs_5y - epoch)
        for _ in range(reconnect):
            h_sca.append(S)
        epoch += reconnect

    # Pad if needed
    while len(h_sca) < len(h_base):
        h_sca.append(h_sca[-1])

    x_sca = np.arange(len(h_sca)) / EPOCHS_PER_YEAR
    ax.plot(x_sca[:len(h_base)], h_sca[:len(h_base)], color="#FF9800",
            linewidth=2, label=f"SCA only (K={K:,d})")

    # SCA + audit (fresh IDs) -> 0 net minting
    ax.axhline(y=M_0, color="#4CAF50", linestyle="--", linewidth=2,
               label="SCA + audit (fresh IDs): ~0")

    ax.set_xlabel("Years since attack start")
    ax.set_ylabel("Attacker MHR supply")
    ax.set_title("5-Year Attack Supply: Defense Comparison")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.ticklabel_format(style="plain", axis="y")

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "sca_partition_analysis.png"), dpi=150)
    plt.close(fig)

    # -- Summary --
    print("=" * 74)
    print("SUMMARY: THREE-LAYER DEFENSE")
    print("=" * 74)
    print("""
  Layer 1: Service Continuity Attestation (SCA)
    - Generalizes GenesisAttestation permanently (no sunset)
    - A node's minting eligibility requires a non-expired SCA
    - SCAs propagate through trusted peers (like GenesisAttestation)
    - SCAs expire after K=10,000 epochs (~69 days) without connectivity
    - Fresh-identity localhost attack: BLOCKED (no SCA source)
    - Pre-planned attack: LIMITED to K epochs per cycle

  Layer 2: Merge-time trust audit
    - On reconnection, partition's minting is validated
    - Validation: how many partition nodes have cross-partition trust?
    - Nodes with zero cross-trust: minting quarantined and rejected
    - CRDT data merge is unaffected (settlements, counters converge)
    - Only the MINTING COMPONENT is audited
    - Fresh-identity attack: 100% rejection (0% dilution)
    - Pre-planned attack: proportional rejection

  Layer 3 (future): Neighborhood-scoped minting
    - Each trust neighborhood mints its own supply
    - Cross-neighborhood exchange at market rates
    - Attacker tokens worthless (no real service backing)
    - Fundamentally eliminates the global inflation vector
    - HIGH implementation complexity; v2.0 if needed

  Combined result (SCA + merge audit):
    - Fresh localhost attack: 0% dilution
    - Pre-planned attack (K=10K): <5% per cycle, visible on reconnect
    - Legitimate village (69-day isolation): mints normally, then pauses
    - No sunset, no central authority (attestation chain is decentralized)
""")

    # Save summary
    summary_path = os.path.join(output_dir, "sca_partition_table.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=" * 74 + "\n")
        f.write("SCA + MERGE AUDIT -- PARTITION DEFENSE SUMMARY\n")
        f.write("=" * 74 + "\n\n")
        f.write("Service Continuity Attestation (K = 10,000 epochs, ~69 days):\n\n")
        f.write(f"  {'Scenario':<35s}  {'1yr dilution':>14s}  {'5yr dilution':>14s}\n")
        f.write(f"  {'-'*35}  {'-'*14}  {'-'*14}\n")

        # Baseline
        h1 = simulate_partition(N, M_0, EPOCHS_PER_YEAR, START)
        h5 = simulate_partition(N, M_0, 5 * EPOCHS_PER_YEAR, START)
        s1 = cumulative_supply_at(START + EPOCHS_PER_YEAR)
        s5 = cumulative_supply_at(START + 5 * EPOCHS_PER_YEAR)
        f.write(f"  {'No SCA (current design)':<35s}  {h1[-1]/s1*100:>13.2f}%  {h5[-1]/s5*100:>13.2f}%\n")

        K = 10_000
        r1 = simulate_sca_attack(N, M_0, K, EPOCHS_PER_YEAR, START)
        r5 = simulate_sca_attack(N, M_0, K, 5 * EPOCHS_PER_YEAR, START)
        f.write(f"  {'SCA only (K=10K)':<35s}  {r1['dilution_pct']:>13.2f}%  {r5['dilution_pct']:>13.2f}%\n")

        r1 = simulate_sca_with_merge_audit(N, M_0, K, EPOCHS_PER_YEAR, START, 1.0)
        r5 = simulate_sca_with_merge_audit(N, M_0, K, 5 * EPOCHS_PER_YEAR, START, 1.0)
        f.write(f"  {'SCA + audit (fresh IDs)':<35s}  {r1['dilution_pct']:>13.2f}%  {r5['dilution_pct']:>13.2f}%\n")

        r1 = simulate_sca_with_merge_audit(N, M_0, K, EPOCHS_PER_YEAR, START, 0.99)
        r5 = simulate_sca_with_merge_audit(N, M_0, K, 5 * EPOCHS_PER_YEAR, START, 0.99)
        f.write(f"  {'SCA + audit (1 trust link)':<35s}  {r1['dilution_pct']:>13.2f}%  {r5['dilution_pct']:>13.2f}%\n")

        f.write(f"\nRecommended: K = 10,000 epochs (~69 days)\n")
        f.write(f"  Fresh localhost attack: 0% dilution (fully blocked)\n")
        f.write(f"  Pre-planned: bounded to K epochs, visible on reconnect\n")
        f.write(f"  Legitimate village: mints for ~69 days, then pauses (can still transact)\n")

    print(f"\nOutput saved to {output_dir}/")
    print(f"  - sca_partition_analysis.png")
    print(f"  - sca_partition_table.txt")


if __name__ == "__main__":
    main()

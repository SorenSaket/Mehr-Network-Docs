"""
Mehr Network -- Double-Spend Profitability Analysis

Empirically determines at what scale (reputation buildup, channel count,
credit limit, network size) a double-spend attack becomes profitable.

All constants are drawn directly from the Mehr protocol specification.
"""

import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --- PROTOCOL CONSTANTS (from spec) -----------------------------------------

PER_PACKET_COST_uMHR = 5           # payment-channels.md: relay cost per packet
LOTTERY_PAYOUT_uMHR = 500           # payment-channels.md: payout on VRF win
LOTTERY_WIN_PROB = 1 / 100          # payment-channels.md: default win probability
GOSSIP_INTERVAL_SEC = 60            # network-protocol.md: gossip round interval
EPOCH_DURATION_MIN = 10             # mhr-token.md: ~10 min per epoch estimate
PACKETS_PER_MIN_DEFAULT = 10        # conservative relay throughput assumption
NETWORK_LIFETIME_EPOCHS = 52_600    # ~1 year at 10 min/epoch
FRIEND_OF_FRIEND_CREDIT_RATE = 0.10 # trust-neighborhoods.md: FoF = 10%
REP_MAX = 10_000                    # security.md: max reputation score
DISCOUNT_RATE = 0.0                 # no discounting (conservative for defender)

# --- REPUTATION MODEL -------------------------------------------------------

def reputation_trajectory(T_epochs, successes_per_epoch=10):
    """Iterate the diminishing-returns reputation formula over T epochs.
    gain per success = (10000 - score) / 100
    """
    scores = []
    score = 0.0
    for _ in range(T_epochs):
        for _ in range(successes_per_epoch):
            score += (REP_MAX - score) / 100
        scores.append(score)
    return np.array(scores)


def reputation_at(T_epochs, successes_per_epoch=10):
    """Return reputation score after T epochs of honest work."""
    score = 0.0
    for _ in range(T_epochs):
        for _ in range(successes_per_epoch):
            score += (REP_MAX - score) / 100
    return score

# --- PROPAGATION WINDOW -----------------------------------------------------

def propagation_window_sec(N, M_colluding=0):
    """Gossip convergence time in seconds: O(log2 N) rounds × 60s.
    Colluding nodes extend the window by factor (1 + M/N_honest).
    """
    if N < 2:
        return GOSSIP_INTERVAL_SEC
    base = math.log2(N) * GOSSIP_INTERVAL_SEC
    if M_colluding > 0:
        N_honest = max(N - M_colluding, 1)
        base *= (1 + M_colluding / N_honest)
    return base

# --- GAIN MODEL --------------------------------------------------------------

def gain(K_channels, credit_per_channel_uMHR):
    """Total extractable credit: attacker broadcasts to all K channels
    simultaneously before blacklist propagates.
    This is the upper bound -- assumes all channels exploited.
    """
    return K_channels * credit_per_channel_uMHR


def credit_from_reputation(score, base_direct_limit_uMHR=100_000):
    """Map reputation score to credit limit extended by a single peer.
    Linear model: credit = base_limit × (score / REP_MAX).
    """
    return base_direct_limit_uMHR * (score / REP_MAX)

# --- COST MODEL --------------------------------------------------------------

def relay_income_per_epoch(packets_per_min=PACKETS_PER_MIN_DEFAULT):
    """Expected relay income per epoch in uMHR.
    Expected value per packet = PER_PACKET_COST (stochastic lottery is neutral).
    """
    return packets_per_min * 60 * EPOCH_DURATION_MIN * PER_PACKET_COST_uMHR


def cost_of_cheating(T_invested_epochs, packets_per_min=PACKETS_PER_MIN_DEFAULT,
                     remaining_epochs=None):
    """Total cost of cheating: future income lost + reputation investment.

    Future income = income_per_epoch × remaining_epochs
    Reputation investment = T × income_per_epoch (opportunity cost of honest work)
    """
    if remaining_epochs is None:
        remaining_epochs = NETWORK_LIFETIME_EPOCHS - T_invested_epochs
    income = relay_income_per_epoch(packets_per_min)
    future_income = income * max(remaining_epochs, 0)
    reputation_investment = income * T_invested_epochs
    return future_income + reputation_investment

# --- BREAK-EVEN ANALYSIS ----------------------------------------------------

def find_breakeven_credit(T_epochs, K_channels, packets_per_min=PACKETS_PER_MIN_DEFAULT):
    """Find minimum credit-per-channel where gain >= cost."""
    total_cost = cost_of_cheating(T_epochs, packets_per_min)
    if K_channels == 0:
        return float("inf")
    return total_cost / K_channels


def sweep_parameters():
    """Full parameter sweep. Returns list of result dicts."""
    T_values = [10, 50, 100, 500, 1000]
    K_values = [1, 5, 10, 50, 100]
    C_values = [1_000, 10_000, 100_000, 1_000_000]
    N_values = [100, 1_000, 10_000, 1_000_000]

    results = []
    for T in T_values:
        score = reputation_at(T)
        max_credit = credit_from_reputation(score)
        for K in K_values:
            for C in C_values:
                # Credit per channel is min of requested and reputation-allowed
                effective_C = min(C, max_credit)
                total_gain = gain(K, effective_C)
                total_cost = cost_of_cheating(T)
                ratio = total_gain / total_cost if total_cost > 0 else float("inf")
                for N in N_values:
                    window = propagation_window_sec(N)
                    results.append({
                        "T": T, "K": K, "C_requested": C,
                        "C_effective": effective_C,
                        "N": N, "score": score,
                        "window_sec": window,
                        "gain_uMHR": total_gain,
                        "cost_uMHR": total_cost,
                        "ratio": ratio,
                        "profitable": total_gain >= total_cost,
                    })
    return results

# --- COLLUSION MODEL --------------------------------------------------------

def collusion_window_multiplier(M, N):
    """How much colluding nodes extend the propagation window."""
    N_honest = max(N - M, 1)
    return 1 + M / N_honest

# --- PLOTTING ----------------------------------------------------------------

def plot_all():
    fig, axes = plt.subplots(3, 2, figsize=(16, 20))
    fig.suptitle("Mehr Network -- Double-Spend Profitability Analysis", fontsize=16, y=0.98)

    # -- Plot 1: Gain vs Cost as network size varies --
    ax = axes[0, 0]
    N_range = np.logspace(1, 7, 200)
    K, C = 10, 10_000
    T = 100
    gains = [gain(K, min(C, credit_from_reputation(reputation_at(T)))) for _ in N_range]
    costs = [cost_of_cheating(T) for _ in N_range]
    windows = [propagation_window_sec(n) for n in N_range]
    ax.semilogy(N_range, gains, "r-", linewidth=2, label=f"Gain (K={K}, C={C} uMHR)")
    ax.semilogy(N_range, costs, "g-", linewidth=2, label=f"Cost (T={T} epochs)")
    ax.set_xscale("log")
    ax.set_xlabel("Network Size (N nodes)")
    ax.set_ylabel("uMHR")
    ax.set_title("Gain vs Cost of Cheating")
    ax.legend()
    ax.grid(True, alpha=0.3)
    # Add propagation window on twin axis
    ax2 = ax.twinx()
    ax2.plot(N_range, windows, "b--", alpha=0.5, label="Propagation window")
    ax2.set_ylabel("Window (seconds)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")

    # -- Plot 2: Break-even credit heatmap --
    ax = axes[0, 1]
    T_range = np.array([10, 50, 100, 200, 500, 1000])
    K_range = np.array([1, 5, 10, 25, 50, 100])
    breakeven = np.zeros((len(T_range), len(K_range)))
    for i, T in enumerate(T_range):
        for j, K in enumerate(K_range):
            be = find_breakeven_credit(T, K)
            breakeven[i, j] = be
    im = ax.imshow(np.log10(breakeven), aspect="auto", cmap="RdYlGn_r",
                   origin="lower")
    ax.set_xticks(range(len(K_range)))
    ax.set_xticklabels(K_range)
    ax.set_yticks(range(len(T_range)))
    ax.set_yticklabels(T_range)
    ax.set_xlabel("Channels (K)")
    ax.set_ylabel("Buildup Epochs (T)")
    ax.set_title("Break-Even Credit per Channel (log10 uMHR)")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("log10(uMHR)")
    # Annotate cells
    for i in range(len(T_range)):
        for j in range(len(K_range)):
            val = breakeven[i, j]
            if val < 1e9:
                text = f"{val/1e6:.1f}M" if val >= 1e6 else f"{val/1e3:.0f}K"
            else:
                text = f"{val/1e9:.1f}B"
            ax.text(j, i, text, ha="center", va="center", fontsize=7,
                    color="white" if np.log10(val) > 8 else "black")

    # -- Plot 3: Reputation buildup curves --
    ax = axes[1, 0]
    for rate in [1, 5, 10, 50]:
        traj = reputation_trajectory(200, successes_per_epoch=rate)
        ax.plot(range(1, 201), traj, label=f"{rate} successes/epoch")
    ax.axhline(y=5000, color="gray", linestyle="--", alpha=0.5, label="50% threshold")
    ax.axhline(y=9000, color="gray", linestyle=":", alpha=0.5, label="90% threshold")
    ax.set_xlabel("Epochs")
    ax.set_ylabel("Reputation Score")
    ax.set_title("Reputation Buildup Over Time")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, REP_MAX + 500)

    # -- Plot 4: G-L contour over (T, K) space --
    ax = axes[1, 1]
    T_fine = np.arange(10, 1001, 10)
    K_fine = np.arange(1, 101, 1)
    T_grid, K_grid = np.meshgrid(T_fine, K_fine, indexing="ij")
    C_fixed = 50_000  # moderate credit assumption
    diff_grid = np.zeros_like(T_grid, dtype=float)
    for i, T in enumerate(T_fine):
        score = reputation_at(int(T))
        eff_C = min(C_fixed, credit_from_reputation(score))
        for j, K in enumerate(K_fine):
            G = gain(int(K), eff_C)
            L = cost_of_cheating(int(T))
            diff_grid[i, j] = G - L
    # Normalize for color: log scale of absolute value, signed
    contour = ax.contourf(K_fine, T_fine, diff_grid, levels=50, cmap="RdYlGn_r")
    ax.contour(K_fine, T_fine, diff_grid, levels=[0], colors="black", linewidths=2)
    fig.colorbar(contour, ax=ax, label="Gain − Cost (uMHR)")
    ax.set_xlabel("Channels (K)")
    ax.set_ylabel("Buildup Epochs (T)")
    ax.set_title(f"Profitability Surface (C={C_fixed} uMHR/ch)")

    # -- Plot 5: Propagation window vs network size --
    ax = axes[2, 0]
    N_range = np.logspace(1, 7, 500)
    windows = [propagation_window_sec(n) for n in N_range]
    ax.semilogx(N_range, windows, "b-", linewidth=2)
    ax.set_xlabel("Network Size (N)")
    ax.set_ylabel("Propagation Window (seconds)")
    ax.set_title("Blacklist Propagation Window vs Network Size")
    ax.grid(True, alpha=0.3)
    # Annotate key points
    for n in [100, 1000, 10_000, 1_000_000]:
        w = propagation_window_sec(n)
        ax.annotate(f"N={n:,}\n{w:.0f}s ({w/60:.1f}m)",
                    xy=(n, w), fontsize=8,
                    xytext=(10, 10), textcoords="offset points",
                    arrowprops=dict(arrowstyle="->", color="gray"))

    # -- Plot 6: Collusion multiplier --
    ax = axes[2, 1]
    for N in [100, 1000, 10_000]:
        M_range = np.arange(0, int(N * 0.4), max(1, int(N * 0.01)))
        multipliers = [collusion_window_multiplier(m, N) for m in M_range]
        fractions = M_range / N * 100
        ax.plot(fractions, multipliers, label=f"N={N:,}")
    ax.set_xlabel("Colluding Nodes (% of network)")
    ax.set_ylabel("Window Multiplier")
    ax.set_title("Collusion Effect on Propagation Window")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 40)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    os.makedirs("scripts/output", exist_ok=True)
    plt.savefig("scripts/output/double_spend_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: scripts/output/double_spend_analysis.png")


def print_table(results):
    """Print and save the break-even summary table."""
    header = (f"{'T':>6} {'K':>5} {'C_req':>10} {'C_eff':>10} {'N':>10} "
              f"{'Score':>7} {'Gain':>14} {'Cost':>14} {'G/C':>8} {'Verdict':>10}")
    lines = [header, "-" * len(header)]

    # Filter to interesting cases: show only where ratio > 0.01 or profitable
    interesting = [r for r in results if r["ratio"] > 0.001 or r["profitable"]]
    # Deduplicate by (T, K, C_requested) since N doesn't affect gain/cost
    seen = set()
    for r in interesting:
        key = (r["T"], r["K"], r["C_requested"])
        if key in seen:
            continue
        seen.add(key)
        verdict = "PROFITABLE" if r["profitable"] else "unprofitable"
        lines.append(
            f"{r['T']:>6} {r['K']:>5} {r['C_requested']:>10,} "
            f"{r['C_effective']:>10,.0f} {r['N']:>10,} {r['score']:>7,.0f} "
            f"{r['gain_uMHR']:>14,.0f} {r['cost_uMHR']:>14,.0f} "
            f"{r['ratio']:>8.4f} {verdict:>10}"
        )

    table_text = "\n".join(lines)
    print(table_text)

    os.makedirs("scripts/output", exist_ok=True)
    with open("scripts/output/double_spend_table.txt", "w") as f:
        f.write(table_text)
    print("\n  Saved: scripts/output/double_spend_table.txt")


def print_key_findings(results):
    """Print the most important conclusions."""
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)

    income_per_epoch = relay_income_per_epoch()
    print(f"\n  Expected relay income per epoch: {income_per_epoch:,.0f} uMHR")
    print(f"  Expected relay income per year:  {income_per_epoch * NETWORK_LIFETIME_EPOCHS:,.0f} uMHR")

    # Find minimum T where reputation > 50%
    for t in range(1, 2000):
        if reputation_at(t) >= 5000:
            print(f"\n  Epochs to 50% reputation (10 successes/epoch): {t}")
            break

    for t in range(1, 2000):
        if reputation_at(t) >= 9000:
            print(f"  Epochs to 90% reputation (10 successes/epoch): {t}")
            break

    # Break-even at different scales
    print("\n  Break-even credit per channel (to make cheating profitable):")
    for T in [10, 100, 500, 1000]:
        for K in [1, 10, 100]:
            be = find_breakeven_credit(T, K)
            score = reputation_at(T)
            max_c = credit_from_reputation(score)
            achievable = "YES" if max_c >= be / K else "NO"
            print(f"    T={T:>4}, K={K:>3}: need {be:>14,.0f} uMHR total "
                  f"(rep allows {max_c:>10,.0f}/ch) -> Achievable: {achievable}")

    # Propagation windows
    print("\n  Propagation windows:")
    for N in [100, 1_000, 10_000, 100_000, 1_000_000]:
        w = propagation_window_sec(N)
        print(f"    N={N:>10,}: {w:>6.0f}s ({w/60:>5.1f} min)")

    # Core conclusion
    any_profitable = any(r["profitable"] for r in results)
    if any_profitable:
        profitable = [r for r in results if r["profitable"]]
        min_gain = min(r["gain_uMHR"] for r in profitable)
        print(f"\n  WARNING: Profitable scenarios exist! Minimum gain: {min_gain:,.0f} uMHR")
        # Find the easiest profitable scenario
        easiest = min(profitable, key=lambda r: r["T"])
        print(f"    Easiest: T={easiest['T']}, K={easiest['K']}, "
              f"C={easiest['C_requested']:,} uMHR, G/C ratio={easiest['ratio']:.4f}")
    else:
        print("\n  No profitable double-spend scenario found in parameter sweep.")
        print("  The protocol's claim holds: cheating is unprofitable at all tested scales.")

    # Reputation-constrained analysis
    print("\n  Reputation-constrained analysis (credit limited by earned reputation):")
    for T in [100, 500, 1000]:
        score = reputation_at(T)
        max_c = credit_from_reputation(score)
        cost = cost_of_cheating(T)
        # Max channels an attacker could plausibly have
        for K in [10, 50, 100]:
            max_gain = gain(K, max_c)
            ratio = max_gain / cost if cost > 0 else 0
            print(f"    T={T:>4}, K={K:>3}, rep={score:>7,.0f}, "
                  f"max_credit/ch={max_c:>10,.0f}, "
                  f"gain={max_gain:>12,.0f}, cost={cost:>12,.0f}, "
                  f"ratio={ratio:.6f}")


# --- MAIN --------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("MEHR NETWORK -- DOUBLE-SPEND PROFITABILITY ANALYSIS")
    print("=" * 70)
    print()

    print("Running parameter sweep...")
    results = sweep_parameters()

    print(f"  {len(results)} scenarios evaluated\n")
    print_table(results)
    print_key_findings(results)

    print("\nGenerating plots...")
    plot_all()
    print("\nDone.")

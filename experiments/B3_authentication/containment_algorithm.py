import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import random

random.seed(42)
np.random.seed(42)

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__),
                             '..', 'B1_graph_amplification'))
from graph_model import (generate_kinship_graph,
                          simulate_registration,
                          simulate_breach)


# ═══════════════════════════════════════════════════════════════
# 1. BOUNDARY-BASED CONTAINMENT
# ═══════════════════════════════════════════════════════════════

def compute_containment_targets(G, registered_nodes,
                                compromised_nodes, top_k=20):
    comp_set = set(compromised_nodes)
    reg_set  = set(registered_nodes)

    boundary = set()
    for node in comp_set:
        for neighbor in G.neighbors(node):
            if neighbor in reg_set and neighbor not in comp_set:
                boundary.add(neighbor)

    boundary_list = sorted(boundary,
                           key=lambda n: G.degree(n),
                           reverse=True)
    return boundary_list[:top_k], boundary


def simulate_contained_breach(G, registered_nodes,
                               compromised_nodes,
                               containment_targets, max_hops=3):
    locked   = set(containment_targets)
    exposed  = set(compromised_nodes)
    frontier = set(compromised_nodes) - locked

    for hop in range(max_hops):
        next_frontier = set()
        for node in frontier:
            for neighbor in G.neighbors(node):
                if (neighbor not in exposed
                        and G.nodes[neighbor]["registered"]
                        and neighbor not in locked):
                    exposed.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
        if not frontier:
            break

    return exposed, locked


def analyze_containment_effectiveness(G, registered_nodes,
                                      n_compromised, k_values):
    # Pre-select compromised nodes from periphery ONCE
    # Same set used for baseline AND all containment runs
    reg_list  = sorted(registered_nodes,
                       key=lambda n: G.degree(n))
    periphery = reg_list[len(reg_list)//4 : len(reg_list)//2]
    n_comp    = min(n_compromised, len(periphery))
    compromised = random.sample(periphery, n_comp)

    # Reset state
    for n in G.nodes():
        G.nodes[n]["exposed"]     = False
        G.nodes[n]["compromised"] = False
    for n in compromised:
        G.nodes[n]["compromised"] = True
        G.nodes[n]["exposed"]     = True

    # Baseline — same compromised nodes, no containment
    baseline_exposed_set, _ = simulate_contained_breach(
        G, registered_nodes, compromised,
        containment_targets=[], max_hops=3
    )
    baseline_exposed = len(baseline_exposed_set)

    results = []
    for k in k_values:
        # Reset exposure state for each run
        for n in G.nodes():
            G.nodes[n]["exposed"]     = False
            G.nodes[n]["compromised"] = False
        for n in compromised:
            G.nodes[n]["compromised"] = True
            G.nodes[n]["exposed"]     = True

        targets, _ = compute_containment_targets(
            G, registered_nodes, compromised, top_k=k
        )
        exposed, locked = simulate_contained_breach(
            G, registered_nodes, compromised,
            targets, max_hops=3
        )
        n_exposed        = len(exposed)
        reduction_pct    = round(
            (1 - n_exposed / baseline_exposed) * 100, 2
        ) if baseline_exposed > 0 else 0
        containment_cost = round(
            k / len(registered_nodes) * 100, 2
        )
        results.append({
            "k"               : k,
            "n_exposed"       : n_exposed,
            "baseline_exposed": baseline_exposed,
            "reduction_pct"   : reduction_pct,
            "containment_cost": containment_cost,
            "efficiency"      : round(
                reduction_pct / containment_cost, 2
            ) if containment_cost > 0 else 0,
        })

    return results, baseline_exposed

def analyze_attack_origins(G, registered_nodes, k_values):
    """
    Compare containment effectiveness across three breach
    origin classes based on compromised node degree:
    
    Low-degree  : peripheral accounts (easiest to contain)
    Mid-degree  : average users (realistic credential stuffing)
    High-degree : hub accounts (hardest to contain)
    
    Same containment strategy applied to all three —
    reveals how attack origin affects containment outcome.
    """
    reg_list = sorted(registered_nodes,
                      key=lambda n: G.degree(n))
    n        = len(reg_list)
    n_comp   = max(5, int(n * 0.005))

    origin_classes = {
        "Low-Degree\n(Peripheral)": reg_list[:n//4],
        "Mid-Degree\n(Average User)": reg_list[n//4:n//2],
        "High-Degree\n(Hub Account)": reg_list[3*n//4:],
    }

    all_results = {}

    for label, pool in origin_classes.items():
        compromised = random.sample(
            pool, min(n_comp, len(pool))
        )

        # Reset state
        for node in G.nodes():
            G.nodes[node]["exposed"]     = False
            G.nodes[node]["compromised"] = False
        for node in compromised:
            G.nodes[node]["compromised"] = True
            G.nodes[node]["exposed"]     = True

        # Baseline for this origin class
        baseline_set, _ = simulate_contained_breach(
            G, registered_nodes, compromised,
            containment_targets=[], max_hops=3
        )
        baseline = len(baseline_set)

        class_results = []
        for k in k_values:
            for node in G.nodes():
                G.nodes[node]["exposed"]     = False
                G.nodes[node]["compromised"] = False
            for node in compromised:
                G.nodes[node]["compromised"] = True
                G.nodes[node]["exposed"]     = True

            targets, _ = compute_containment_targets(
                G, registered_nodes, compromised, top_k=k
            )
            exposed, _ = simulate_contained_breach(
                G, registered_nodes, compromised,
                targets, max_hops=3
            )
            reduction = round(
                (1 - len(exposed) / baseline) * 100, 2
            ) if baseline > 0 else 0

            class_results.append({
                "k"           : k,
                "baseline"    : baseline,
                "n_exposed"   : len(exposed),
                "reduction"   : reduction,
            })

        all_results[label] = {
            "results" : class_results,
            "baseline": baseline,
        }

    return all_results


def plot_attack_origin_comparison(origin_results):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        "Module B3 — Containment Effectiveness by Attack Origin\n"
        "Project GenoPhylax",
        fontsize=13, fontweight="bold", color="#0D1B2A"
    )
    fig.patch.set_facecolor("#F1F5F9")

    colors = {
        "Low-Degree\n(Peripheral)" : "#15803D",
        "Mid-Degree\n(Average User)": "#D97706",
        "High-Degree\n(Hub Account)": "#C0392B",
    }
    markers = {
        "Low-Degree\n(Peripheral)" : "o",
        "Mid-Degree\n(Average User)": "s",
        "High-Degree\n(Hub Account)": "^",
    }

    # ── Plot 1: Reduction % vs k for each origin class ──
    ax = axes[0]
    ax.set_facecolor("white")
    for label, data in origin_results.items():
        ks         = [r["k"] for r in data["results"]]
        reductions = [r["reduction"] for r in data["results"]]
        ax.plot(ks, reductions, color=colors[label],
                lw=2.5, marker=markers[label],
                markersize=7, label=label.replace("\n", " "))

    ax.axhline(50, color="gray", linestyle="--",
               lw=1.5, alpha=0.7,
               label="50% reduction threshold")
    ax.axhline(99, color="gray", linestyle=":",
               lw=1.5, alpha=0.5,
               label="99% reduction threshold")
    ax.set_xlabel("Accounts Locked for Containment (k)",
                  fontsize=10)
    ax.set_ylabel("Breach Reduction (%)", fontsize=10)
    ax.set_title("Containment Effectiveness by Attack Origin",
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-10, 105)

    # ── Plot 2: Baseline exposure by origin class ──
    ax = axes[1]
    ax.set_facecolor("white")
    labels    = [l.replace("\n", " ")
                 for l in origin_results.keys()]
    baselines = [d["baseline"]
                 for d in origin_results.values()]
    bar_cols  = list(colors.values())

    bars = ax.bar(labels, baselines, color=bar_cols,
                  edgecolor="white", width=0.5)
    for bar, val in zip(bars, baselines):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 5,
                str(val), ha="center", va="bottom",
                fontsize=11, fontweight="bold")

    ax.set_ylabel("Baseline Exposed Users (no containment)",
                  fontsize=10)
    ax.set_title("Breach Blast Radius by Attack Origin\n"
                 "(Before Containment)",
                 fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig("B3_attack_origin_comparison.png", dpi=150,
                bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("Saved: B3_attack_origin_comparison.png")


# ═══════════════════════════════════════════════════════════════
# 2. CREDENTIAL STUFFING DETECTION
# ═══════════════════════════════════════════════════════════════

def generate_access_sessions(n_normal=200, n_attack=50, seed=42):
    rng      = np.random.default_rng(seed)
    sessions = []

    for _ in range(n_normal):
        sessions.append({
            "label"            : 0,
            "access_rate"      : rng.normal(2.5, 1.0),
            "account_diversity": rng.integers(1, 4),
            "query_diversity"  : rng.integers(1, 5),
            "ip_changes"       : rng.integers(0, 2),
            "graph_depth"      : rng.integers(0, 2),
            "session_duration" : rng.normal(12.0, 5.0),
            "failed_logins"    : rng.integers(0, 2),
        })

    for _ in range(n_attack):
        sessions.append({
            "label"            : 1,
            "access_rate"      : rng.normal(45.0, 15.0),
            "account_diversity": rng.integers(10, 100),
            "query_diversity"  : rng.integers(1, 3),
            "ip_changes"       : rng.integers(2, 10),
            "graph_depth"      : rng.integers(2, 5),
            "session_duration" : rng.normal(3.0, 1.5),
            "failed_logins"    : rng.integers(3, 20),
        })

    return sessions


def compute_anomaly_score(session):
    score = 0.0
    score += min(session["access_rate"] / 50.0, 1.0)       * 3.0
    score += min(session["account_diversity"] / 50.0, 1.0) * 2.5
    score += min(session["ip_changes"] / 10.0, 1.0)        * 1.5
    score += min(session["graph_depth"] / 5.0, 1.0)        * 2.0
    score += min(session["failed_logins"] / 20.0, 1.0)     * 1.0
    return round(min(score, 10.0), 2)


def evaluate_detection(sessions, threshold=4.5):
    results = []
    tp = fp = tn = fn = 0

    for s in sessions:
        score    = compute_anomaly_score(s)
        detected = score >= threshold
        label    = s["label"]

        if detected and label == 1:        tp += 1
        elif detected and label == 0:      fp += 1
        elif not detected and label == 0:  tn += 1
        else:                              fn += 1

        results.append({**s, "anomaly_score": score,
                        "detected": detected})

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0)
    accuracy  = (tp + tn) / len(sessions)

    return results, {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 4),
        "recall"   : round(recall, 4),
        "f1"       : round(f1, 4),
        "accuracy" : round(accuracy, 4),
    }


# ═══════════════════════════════════════════════════════════════
# 3. GRI D4 SCORING
# ═══════════════════════════════════════════════════════════════

def compute_d4_score(containment_reduction_pct, auth_f1_score):
    containment_eff = max(containment_reduction_pct / 100.0, 0.0)
    combined        = (containment_eff + auth_f1_score) / 2.0
    d4              = round((1.0 - combined) * 10.0, 2)
    return max(d4, 0.0)


# ═══════════════════════════════════════════════════════════════
# 4. PLOT
# ═══════════════════════════════════════════════════════════════

def plot_b3_results(containment_results, baseline_exposed,
                    auth_results, metrics):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Module B3 — Graph-Aware Containment & Authentication\n",
        fontsize=13, fontweight="bold", color="#0D1B2A"
    )
    fig.patch.set_facecolor("#F1F5F9")

    # ── Plot 1: Containment effectiveness ──
    ax = axes[0, 0]
    ax.set_facecolor("white")
    ks         = [r["k"] for r in containment_results]
    reductions = [r["reduction_pct"] for r in containment_results]
    ax.plot(ks, reductions, color="#0D9488", lw=2.5,
            marker="o", markersize=7)
    ax.fill_between(ks, reductions, alpha=0.2, color="#0D9488")
    ax.axhline(50, color="#D97706", linestyle="--", lw=1.5,
               label="50% reduction threshold")
    ax.set_xlabel("Accounts Locked for Containment (k)", fontsize=10)
    ax.set_ylabel("Breach Reduction (%)", fontsize=10)
    ax.set_title("Containment Effectiveness vs Accounts Locked",
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ── Plot 2: Efficiency ──
    ax = axes[0, 1]
    ax.set_facecolor("white")
    efficiencies = [r["efficiency"] for r in containment_results]
    ax.bar(ks, efficiencies, color="#1B3A6B",
           edgecolor="white", width=2.5)
    best_idx = int(np.argmax(efficiencies))
    best_k   = containment_results[best_idx]["k"]
    ax.annotate(f"Best k={best_k}",
                xy=(best_k, efficiencies[best_idx]),
                xytext=(best_k + 3,
                        efficiencies[best_idx] * 0.85),
                arrowprops=dict(arrowstyle="->",
                                color="#C0392B"),
                fontsize=9, color="#C0392B")
    ax.set_xlabel("Accounts Locked (k)", fontsize=10)
    ax.set_ylabel("Efficiency (% reduction / % cost)",
                  fontsize=10)
    ax.set_title("Containment Efficiency",
                 fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    # ── Plot 3: Anomaly score distribution ──
    ax = axes[1, 0]
    ax.set_facecolor("white")
    normal_scores = [r["anomaly_score"] for r in auth_results
                     if r["label"] == 0]
    attack_scores = [r["anomaly_score"] for r in auth_results
                     if r["label"] == 1]
    ax.hist(normal_scores, bins=15, alpha=0.7,
            color="#0D9488", label="Normal Sessions",
            edgecolor="white")
    ax.hist(attack_scores, bins=15, alpha=0.7,
            color="#C0392B", label="Attack Sessions",
            edgecolor="white")
    ax.axvline(x=4.5, color="#D97706", linestyle="--",
               lw=2, label="Detection threshold (4.5)")
    ax.set_xlabel("Anomaly Score (0-10)", fontsize=10)
    ax.set_ylabel("Session Count", fontsize=10)
    ax.set_title("Credential Stuffing Detection\n"
                 "Anomaly Score Distribution",
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ── Plot 4: Detection metrics ──
    ax = axes[1, 1]
    ax.set_facecolor("white")
    metric_names = ["Precision", "Recall", "F1 Score", "Accuracy"]
    metric_vals  = [metrics["precision"], metrics["recall"],
                    metrics["f1"],        metrics["accuracy"]]
    bar_colors   = ["#1B3A6B", "#0D9488", "#C0392B", "#D97706"]
    bars = ax.bar(metric_names, metric_vals,
                  color=bar_colors, edgecolor="white", width=0.5)
    for bar, val in zip(bars, metric_vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", va="bottom",
                fontsize=10, fontweight="bold")
    ax.set_ylabel("Score (0-1)", fontsize=10)
    ax.set_title("Authentication Detection Performance\n"
                 "Credential Stuffing vs Normal Access",
                 fontweight="bold")
    ax.set_ylim(0, 1.15)
    ax.axhline(0.9, color="gray", linestyle=":",
               lw=1.5, alpha=0.7,
               label="Target threshold (0.9)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig("B3_containment_auth.png", dpi=150,
                bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("Plot saved as B3_containment_auth.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Module B3 — Graph-Aware Containment & Authentication")
    print("=" * 60)

    print("\n[1/4] Building kinship graph...")
    G, family_data = generate_kinship_graph(
        n_families=800, avg_children=2, cousin_prob=0.20
    )
    registered = simulate_registration(G, registration_rate=0.4)
    print(f"      Nodes: {G.number_of_nodes():,} | "
          f"Registered: {len(registered):,}")

    print("\n[2/4] Computing containment effectiveness...")
    k_values = [5, 10, 15, 20, 30, 40, 50]
    n_comp   = max(5, int(len(registered) * 0.005))
    containment_results, baseline = analyze_containment_effectiveness(
        G, registered, n_comp, k_values
    )
    print(f"      Baseline exposed (no containment): {baseline:,}")
    print(f"\n      {'k':>5} {'Exposed':>10} {'Reduction%':>12} "
          f"{'Cost%':>8} {'Efficiency':>12}")
    print("      " + "-" * 52)
    for r in containment_results:
        print(f"      {r['k']:>5} {r['n_exposed']:>10} "
              f"{r['reduction_pct']:>11.1f}% "
              f"{r['containment_cost']:>7.2f}% "
              f"{r['efficiency']:>12.2f}")

    print("\n[3/4] Running credential stuffing detection...")
    sessions = generate_access_sessions(n_normal=200, n_attack=50)
    auth_results, metrics = evaluate_detection(
        sessions, threshold=4.5
    )
    print(f"      Precision : {metrics['precision']:.4f}")
    print(f"      Recall    : {metrics['recall']:.4f}")
    print(f"      F1 Score  : {metrics['f1']:.4f}")
    print(f"      Accuracy  : {metrics['accuracy']:.4f}")
    print(f"      TP={metrics['tp']} FP={metrics['fp']} "
          f"TN={metrics['tn']} FN={metrics['fn']}")

    print("\n[4/4] Computing GRI D4 score...")
    best_reduction = max(r["reduction_pct"]
                         for r in containment_results)
    d4 = compute_d4_score(best_reduction, metrics["f1"])
    print(f"      Best containment reduction : {best_reduction}%")
    print(f"      Auth F1 score              : {metrics['f1']}")
    print(f"      GRI D4 Score               : {d4} / 10")

    print("\n[5/4] Analyzing attack origin classes...")
    origin_results = analyze_attack_origins(
        G, registered, k_values
    )
    print(f"\n  {'Origin':<25} {'Baseline':>10} "
          f"{'k=10 Reduction':>16}")
    print("  " + "-" * 54)
    for label, data in origin_results.items():
        k10 = next(r for r in data["results"] if r["k"] == 10)
        print(f"  {label.replace(chr(10), ' '):<25} "
              f"{data['baseline']:>10} "
              f"{k10['reduction']:>15.1f}%")
    plot_attack_origin_comparison(origin_results)
    
    print("\nGenerating plots...")
    plot_b3_results(containment_results, baseline,
                    auth_results, metrics)
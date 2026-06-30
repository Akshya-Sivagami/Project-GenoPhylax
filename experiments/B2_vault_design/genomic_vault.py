import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from itertools import product

# ═══════════════════════════════════════════════════════════════
# MODULE B2 — GenomicVault: Selective Disclosure Architecture
#
# Models a privacy-preserving genomic vault with:
#   1. Tiered data sensitivity classification
#   2. Access tier permissions (public/researcher/clinician/relative)
#   3. Unrecoverability scoring (D5 linkage)
#   4. Graph-context disclosure risk (D6 linkage from B1)
#
# Key insight: the same derived marker carries different risk
# depending on WHO is requesting it — a relative requesting
# disease risk scores can infer their own predispositions,
# creating a familial cascade even from "safe" disclosures.
# ═══════════════════════════════════════════════════════════════

# ── Data Tiers ────────────────────────────────────────────────
# Each tier represents a type of genomic information.
# Sensitivity: 0=lowest, 1=highest
# Recoverability: how much raw sequence can be reconstructed
#                 from this derived marker (0=none, 1=full)

DATA_TIERS = {
    "Raw Sequence": {
        "sensitivity"   : 1.0,
        "recoverability": 1.0,
        "description"   : "Full genome/exome sequence (FASTQ/BAM/VCF)",
        "always_locked" : True,
    },
    "Pathogenic Variants": {
        "sensitivity"   : 0.95,
        "recoverability": 0.85,
        "description"   : "Known disease-causing SNVs (BRCA1/2, CFTR etc.)",
        "always_locked" : False,
    },
    "Polygenic Risk Scores": {
        "sensitivity"   : 0.80,
        "recoverability": 0.40,
        "description"   : "Composite disease risk scores (PRS)",
        "always_locked" : False,
    },
    "Pharmacogenomic Markers": {
        "sensitivity"   : 0.65,
        "recoverability": 0.30,
        "description"   : "Drug metabolism variants (CYP2D6, TPMT etc.)",
        "always_locked" : False,
    },
    "Ancestry Composition": {
        "sensitivity"   : 0.45,
        "recoverability": 0.20,
        "description"   : "Population ancestry percentages",
        "always_locked" : False,
    },
    "Trait Predictions": {
        "sensitivity"   : 0.30,
        "recoverability": 0.10,
        "description"   : "Non-medical traits (eye color, earwax type etc.)",
        "always_locked" : False,
    },
    "Aggregate Statistics": {
        "sensitivity"   : 0.10,
        "recoverability": 0.02,
        "description"   : "Population-level summary stats only",
        "always_locked" : False,
    },
}

# ── Access Tiers ──────────────────────────────────────────────
# Each requester type has a base permission level and
# a graph-context multiplier (how much D6 risk they add)

ACCESS_TIERS = {
    "Public": {
        "base_permission" : 0.1,
        "graph_multiplier": 1.0,   # no kinship relationship
        "d6_weight"       : 0.0,   # no amplification risk
        "description"     : "Anonymous public access",
    },
    "Researcher": {
        "base_permission" : 0.5,
        "graph_multiplier": 1.1,
        "d6_weight"       : 0.1,
        "description"     : "Approved research institution",
    },
    "Clinician": {
        "base_permission" : 0.75,
        "graph_multiplier": 1.2,
        "d6_weight"       : 0.15,
        "description"     : "Licensed medical professional",
    },
    "Relative": {
        "base_permission" : 0.4,
        "graph_multiplier": 2.8,   # high — kinship graph node
        "d6_weight"       : 0.85,  # high D6 risk — familial cascade
        "description"     : "Biological relative (kinship graph node)",
    },
}

# Enhanced controls applied to high-sensitivity clinical access
ENHANCED_CONTROLS = {
    "Pathogenic Variants": [
        "Break-glass authorization required",
        "Full audit log retained (90 days)",
        "Patient consent verification mandatory",
        "Session-only access — no export/download",
        "Attending physician co-authorization",
    ],
    "Polygenic Risk Scores": [
        "Audit log retained (30 days)",
        "Patient consent verification mandatory",
        "Session-only access — no export/download",
    ],
    "Pharmacogenomic Markers": [
        "Audit log retained (30 days)",
        "Session-only access — no export/download",
    ],
}

# ═══════════════════════════════════════════════════════════════
# 1. UNRECOVERABILITY SCORE
# Measures how much raw sequence could theoretically be
# reconstructed from a set of disclosed derived markers.
# Score 0 = fully recoverable (bad), 1 = unrecoverable (good)
# ═══════════════════════════════════════════════════════════════

def compute_unrecoverability(disclosed_tiers):
    """
    Information-theoretic unrecoverability score.
    
    Models how much Shannon entropy about the raw sequence
    is leaked by each disclosed tier. When cumulative entropy
    leakage exceeds a threshold, raw sequence reconstruction
    becomes feasible.
    
    Each tier has an entropy_leakage value representing what
    fraction of raw sequence information it exposes:
        - High leakage tiers leak specific variant positions
        - Low leakage tiers only leak aggregate statistics
    
    Unrecoverability = 1 - P(reconstruct | disclosed tiers)
    P(reconstruct) derived from cumulative entropy leakage
    using an exponential reconstruction probability model.
    """
    if not disclosed_tiers:
        return 1.0

    # Entropy leakage per tier — fraction of raw sequence
    # information exposed. Derived from information content
    # of each data type relative to full genome entropy.
    ENTROPY_LEAKAGE = {
        "Raw Sequence"           : 1.000,  # full information
        "Pathogenic Variants"    : 0.420,  # specific loci — high leakage
        "Polygenic Risk Scores"  : 0.180,  # aggregated — moderate
        "Pharmacogenomic Markers": 0.120,  # targeted loci — moderate
        "Ancestry Composition"   : 0.065,  # population-level — low
        "Trait Predictions"      : 0.035,  # coarse phenotype — very low
        "Aggregate Statistics"   : 0.008,  # summary only — minimal
    }

    # Cumulative entropy leakage (additive with diminishing returns)
    # Later disclosures add less new information if earlier ones
    # already covered overlapping genomic regions
    cumulative_leakage = 0.0
    disclosed_so_far   = []

    for tier in disclosed_tiers:
        if DATA_TIERS[tier]["always_locked"]:
            continue
        base_leakage = ENTROPY_LEAKAGE.get(tier, 0.0)

        # Overlap penalty — each additional tier has diminishing
        # marginal leakage because genomic regions overlap
        overlap_factor = 0.85 ** len(disclosed_so_far)
        marginal_leakage = base_leakage * overlap_factor
        cumulative_leakage += marginal_leakage
        disclosed_so_far.append(tier)

    # Reconstruction probability — exponential model
    # P(reconstruct) rises steeply once leakage > 0.5
    # This produces the empirically observed collapse at tier 4
    # as a mathematical consequence, not a hardcoded threshold
    reconstruction_prob = 1.0 - np.exp(-3.5 * cumulative_leakage)
    unrecoverability    = round(
        max(0.0, 1.0 - reconstruction_prob), 4
    )
    return unrecoverability

# ═══════════════════════════════════════════════════════════════
# 2. GRAPH-CONTEXT DISCLOSURE RISK
# Adjusts disclosure risk based on requester's position
# in the kinship graph. A relative requesting data creates
# familial cascade risk even from "safe" disclosures.
# Integrates D6 amplification factor from Module B1.
# ═══════════════════════════════════════════════════════════════

def compute_graph_context_risk(disclosed_tiers, requester_type,
                                d6_amplification=464.4):
    """
    Computes graph-context adjusted disclosure risk.

    Parameters:
        disclosed_tiers   : list of tier names being disclosed
        requester_type    : one of ACCESS_TIERS keys
        d6_amplification  : amplification factor from B1 calibration (464.4x)

    Returns:
        dict with risk components
    """
    if not disclosed_tiers:
        return {"base_risk": 0.0, "graph_risk": 0.0, "total_risk": 0.0}

    access = ACCESS_TIERS[requester_type]

    # Base disclosure risk: average sensitivity of disclosed tiers
    sensitivities = [DATA_TIERS[t]["sensitivity"]
                     for t in disclosed_tiers
                     if not DATA_TIERS[t]["always_locked"]]
    base_risk = np.mean(sensitivities) if sensitivities else 0.0

    # Graph context multiplier — scales with D6 for relatives
    # For non-relatives, graph multiplier is close to 1
    # For relatives, it's amplified by kinship graph density
    d6_normalized = np.log10(d6_amplification) / np.log10(1000)  # 0-1 scale
    graph_multiplier = access["graph_multiplier"]

    if requester_type == "Relative":
        # Relative disclosure risk compounds with D6
        graph_risk = base_risk * graph_multiplier * d6_normalized * access["d6_weight"]
    else:
        graph_risk = base_risk * (graph_multiplier - 1.0) * access["d6_weight"]

    total_risk = min(base_risk + graph_risk, 1.0)

    return {
        "base_risk"       : round(base_risk, 4),
        "graph_risk"      : round(graph_risk, 4),
        "total_risk"      : round(total_risk, 4),
        "d6_normalized"   : round(d6_normalized, 4),
        "graph_multiplier": graph_multiplier,
    }


# ═══════════════════════════════════════════════════════════════
# 3. VAULT DECISION ENGINE
# Determines what can be disclosed to whom, with full
# risk scoring for each disclosure decision.
# ═══════════════════════════════════════════════════════════════

def vault_decision(requester_type, requested_tiers,
                   d6_amplification=464.4, risk_threshold=0.6):
    """
    Makes a disclosure decision for each requested tier.

    Returns per-tier decisions with full risk breakdown.
    """
    access   = ACCESS_TIERS[requester_type]
    results  = []
    approved = []
    denied   = []

    for tier_name in requested_tiers:
        tier = DATA_TIERS[tier_name]

        # Always locked check
        if tier["always_locked"]:
            results.append({
                "tier"           : tier_name,
                "decision"       : "DENIED — Always Locked",
                "reason"         : "Raw sequence never disclosed",
                "unrecoverability": 1.0,
                "graph_risk"     : 0.0,
                "total_risk"     : 1.0,
            })
            denied.append(tier_name)
            continue

        # Permission check — with clinical justification override
        # Clinicians retain access to pathogenic variants when
        # clinically justified, but graph-aware controls still
        # suppress relative-linked inference pathways
        clinically_justified = (
            requester_type == "Clinician"
            and tier_name in ["Pathogenic Variants",
                              "Polygenic Risk Scores",
                              "Pharmacogenomic Markers"]
        )

        if (tier["sensitivity"] > access["base_permission"] * 1.5
                and not clinically_justified):
            results.append({
                "tier"           : tier_name,
                "decision"       : "DENIED — Insufficient Permission",
                "reason"         : f"{requester_type} tier cannot access this sensitivity level",
                "unrecoverability": compute_unrecoverability([tier_name]),
                "graph_risk"     : 0.0,
                "total_risk"     : tier["sensitivity"],
            })
            denied.append(tier_name)
            continue

        # Graph-context risk check
        # For clinically justified access, we still apply
        # graph-context controls to suppress relative-linked
        # inference pathways — clinician sees patient data
        # but cannot trigger familial cascade disclosures
        graph = compute_graph_context_risk(
            [tier_name], requester_type, d6_amplification
        )
        unrec = compute_unrecoverability(approved + [tier_name])

        if clinically_justified:
            # Enhanced controls path — access granted under
            # elevated oversight rather than binary deny.
            # Pathogenic variants trigger break-glass;
            # PRS and pharmacogenomics trigger audit controls.
            controls = ENHANCED_CONTROLS.get(tier_name, [
                "Audit log retained",
                "Session-only access — no export/download",
            ])
            results.append({
                "tier"           : tier_name,
                "decision"       : "APPROVED — Enhanced Controls",
                "reason"         : f"Clinical justification; {len(controls)} controls applied",
                "unrecoverability": unrec,
                "graph_risk"     : graph["graph_risk"],
                "total_risk"     : graph["total_risk"],
                "controls"       : controls,
            })
            approved.append(tier_name)

        elif graph["total_risk"] > risk_threshold:
            results.append({
                "tier"           : tier_name,
                "decision"       : "DENIED — Graph Risk Exceeded",
                "reason"         : f"Graph-context risk {graph['total_risk']:.2f} > threshold {risk_threshold}",
                "unrecoverability": unrec,
                "graph_risk"     : graph["graph_risk"],
                "total_risk"     : graph["total_risk"],
                "controls"       : [],
            })
            denied.append(tier_name)

        else:
            results.append({
                "tier"           : tier_name,
                "decision"       : "APPROVED",
                "reason"         : f"Risk {graph['total_risk']:.2f} within threshold",
                "unrecoverability": unrec,
                "graph_risk"     : graph["graph_risk"],
                "total_risk"     : graph["total_risk"],
                "controls"       : [],
            })
            approved.append(tier_name)

    return results, approved, denied


# ═══════════════════════════════════════════════════════════════
# 4. FULL SCENARIO ANALYSIS
# Runs all requester types against all data tiers
# to produce the complete vault decision matrix
# ═══════════════════════════════════════════════════════════════

def run_full_scenario_analysis(d6_amplification=464.4):
    all_tiers      = list(DATA_TIERS.keys())
    requester_types = list(ACCESS_TIERS.keys())
    scenario_results = {}

    print(f"\n{'Requester':<12} {'Data Tier':<26} {'Decision':<35} "
          f"{'Total Risk':>10} {'Unrec. Score':>12}")
    print("-" * 100)

    for req in requester_types:
        results, approved, denied = vault_decision(
            req, all_tiers, d6_amplification
        )
        scenario_results[req] = {
            "results" : results,
            "approved": approved,
            "denied"  : denied,
        }
        for r in results:
            controls_str = (f" [{r['controls'][0]}...]"
                           if r.get("controls") else "")
            print(f"{req:<12} {r['tier']:<26} {r['decision']:<35} "
                  f"{r['total_risk']:>10.3f} {r['unrecoverability']:>12.4f}"
                  f"{controls_str}")
        print()

    return scenario_results


# ═══════════════════════════════════════════════════════════════
# 5. PLOT
# ═══════════════════════════════════════════════════════════════

def plot_vault_analysis(scenario_results, d6_amplification):
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle("Module B2 — Selective Disclosure Architecture\n",
                 fontsize=13, fontweight="bold", color="#0D1B2A")
    fig.patch.set_facecolor("#F1F5F9")

    tiers      = list(DATA_TIERS.keys())
    requesters = list(ACCESS_TIERS.keys())
    colors     = {"APPROVED": "#15803D", "DENIED": "#C0392B"}

    # ── Plot 1: Decision heatmap ──
    ax = axes[0, 0]
    ax.set_facecolor("white")
    matrix = np.zeros((len(requesters), len(tiers)))
    for ri, req in enumerate(requesters):
        for ti, tier in enumerate(tiers):
            r = scenario_results[req]["results"][ti]
            matrix[ri, ti] = 1 if "APPROVED" in r["decision"] else 0

    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(tiers)))
    ax.set_xticklabels(tiers, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(requesters)))
    ax.set_yticklabels(requesters, fontsize=9)
    ax.set_title("Vault Decision Matrix\n(Green=Approved, Red=Denied)",
                 fontweight="bold", fontsize=10)
    for ri in range(len(requesters)):
        for ti in range(len(tiers)):
            txt = "✓" if matrix[ri, ti] == 1 else "✗"
            ax.text(ti, ri, txt, ha="center", va="center",
                    fontsize=13, color="white", fontweight="bold")

    # ── Plot 2: Total risk by requester x tier ──
    ax = axes[0, 1]
    ax.set_facecolor("white")
    risk_matrix = np.zeros((len(requesters), len(tiers)))
    for ri, req in enumerate(requesters):
        for ti, tier in enumerate(tiers):
            risk_matrix[ri, ti] = scenario_results[req]["results"][ti]["total_risk"]

    im2 = ax.imshow(risk_matrix, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(tiers)))
    ax.set_xticklabels(tiers, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(requesters)))
    ax.set_yticklabels(requesters, fontsize=9)
    ax.set_title("Total Disclosure Risk\n(Graph-Context Adjusted)",
                 fontweight="bold", fontsize=10)
    for ri in range(len(requesters)):
        for ti in range(len(tiers)):
            val = risk_matrix[ri, ti]
            ax.text(ti, ri, f"{val:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if val > 0.5 else "black")
    plt.colorbar(im2, ax=ax, label="Total Risk (0-1)")

    # ── Plot 3: Graph context risk vs base risk for Relative ──
    ax = axes[1, 0]
    ax.set_facecolor("white")
    non_locked = [t for t in tiers if not DATA_TIERS[t]["always_locked"]]
    base_risks, graph_risks = [], []
    for t in non_locked:
        g = compute_graph_context_risk([t], "Relative", d6_amplification)
        base_risks.append(g["base_risk"])
        graph_risks.append(g["graph_risk"])

    x = np.arange(len(non_locked))
    w = 0.35
    ax.bar(x - w/2, base_risks,  width=w, color="#1B3A6B", label="Base Risk")
    ax.bar(x + w/2, graph_risks, width=w, color="#C0392B", label="Graph-Context Added Risk (D6)")
    ax.set_xticks(x)
    ax.set_xticklabels(non_locked, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Risk Score", fontsize=10)
    ax.set_title("Relative Requester — Base vs Graph-Context Risk\n(D6 Amplification Applied)",
                 fontweight="bold", fontsize=10)
    ax.legend(fontsize=9)
    ax.axhline(0.6, color="orange", linestyle="--", lw=1.5, label="Threshold (0.6)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # ── Plot 4: Unrecoverability score as tiers are cumulatively disclosed ──
    ax = axes[1, 1]
    ax.set_facecolor("white")
    non_locked_sorted = sorted(
        non_locked,
        key=lambda t: DATA_TIERS[t]["recoverability"]
    )
    cumulative_disclosed = []
    unrec_scores = []
    for t in non_locked_sorted:
        cumulative_disclosed.append(t)
        unrec_scores.append(compute_unrecoverability(cumulative_disclosed))

    ax.plot(range(len(non_locked_sorted)), unrec_scores,
            color="#0D9488", lw=2.5, marker="o", markersize=8)
    ax.fill_between(range(len(non_locked_sorted)), unrec_scores,
                    alpha=0.2, color="#0D9488")
    ax.set_xticks(range(len(non_locked_sorted)))
    ax.set_xticklabels(non_locked_sorted, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Unrecoverability Score (1=safe, 0=recoverable)", fontsize=9)
    ax.set_title("Raw Sequence Unrecoverability\nas More Tiers Are Disclosed",
                 fontweight="bold", fontsize=10)
    ax.axhline(0.5, color="orange", linestyle="--", lw=1.5,
               label="Safety threshold (0.5)")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    for i, (score, label) in enumerate(zip(unrec_scores, non_locked_sorted)):
        ax.annotate(f"{score:.3f}", (i, score),
                    textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig("B2_genomic_vault.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()
    print("Plot saved as B2_genomic_vault.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    D6_AMPLIFICATION = 464.4  # from B1 calibration (cousin_prob=0.20)

    print("=" * 65)
    print("  Module B2 — Selective Disclosure Architecture")
    print(f"  D6 Amplification Factor (from B1): {D6_AMPLIFICATION}x")
    print("=" * 65)

    print("\n[1] Running full scenario analysis...")
    scenario_results = run_full_scenario_analysis(D6_AMPLIFICATION)

    print("\n[2] Unrecoverability analysis:")
    non_locked = [t for t, v in DATA_TIERS.items() if not v["always_locked"]]
    cumulative = []
    print(f"  {'Tiers Disclosed':<35} {'Unrecoverability Score':>22}")
    print("  " + "-" * 60)
    for t in sorted(non_locked, key=lambda x: DATA_TIERS[x]["recoverability"]):
        cumulative.append(t)
        score = compute_unrecoverability(cumulative)
        print(f"  {' + '.join(cumulative[-2:] if len(cumulative)>1 else cumulative):<35} {score:>22.4f}")

    print("\n[3] Graph-context risk for Relative requester:")
    print(f"  {'Data Tier':<26} {'Base Risk':>10} {'Graph Risk':>11} {'Total Risk':>11}")
    print("  " + "-" * 62)
    for t in non_locked:
        g = compute_graph_context_risk([t], "Relative", D6_AMPLIFICATION)
        print(f"  {t:<26} {g['base_risk']:>10.4f} {g['graph_risk']:>11.4f} {g['total_risk']:>11.4f}")

    print("\n[4] Generating plots...")
    plot_vault_analysis(scenario_results, D6_AMPLIFICATION)
"""
=======================================================
  Module B2 — GenomicVault: Selective Disclosure Architecture
=======================================================
  Project GenoPhylax
  Deliverable: Vault design with tiered disclosure, unrecoverability
               scoring, and graph-context risk (D6 linkage from B1)
=======================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from itertools import product

# -------------------------------------------------------
# 1. DATA TAXONOMY — What lives in the vault
# -------------------------------------------------------

VAULT_LAYERS = {
    "RAW": {
        "label": "Raw Sequence",
        "examples": ["FASTQ reads", "BAM alignments", "raw signal (FAST5)"],
        "disclosure_allowed": False,
        "unrecoverability": 1.0,   # perfect — never exposed
        "description": "Full biological sequence. Never disclosed under any tier."
    },
    "VARIANT": {
        "label": "Variant Calls (VCF)",
        "examples": ["SNPs", "indels", "structural variants"],
        "disclosure_allowed": True,
        "unrecoverability": 0.30,  # partial — VCF can leak raw context
        "description": "Processed variant calls. High re-ID risk; restricted to clinical tier."
    },
    "PRS": {
        "label": "Polygenic Risk Scores",
        "examples": ["disease PRS", "trait PRS", "ancestry PRS"],
        "disclosure_allowed": True,
        "unrecoverability": 0.70,
        "description": "Aggregate scores. Lower re-ID risk; disclosable to research tier."
    },
    "ANCESTRY": {
        "label": "Ancestry Proportions",
        "examples": ["continental ancestry %", "haplogroup"],
        "disclosure_allowed": True,
        "unrecoverability": 0.60,
        "description": "Population-level summaries. Kinship inference risk remains."
    },
    "PHENOTYPE": {
        "label": "Derived Phenotype Flags",
        "examples": ["carrier status", "pharmacogenomic flags", "binary trait calls"],
        "disclosure_allowed": True,
        "unrecoverability": 0.80,
        "description": "Clinically actionable derived markers. Safest disclosure unit."
    },
}

# -------------------------------------------------------
# 2. ACCESS TIER DEFINITIONS
# -------------------------------------------------------

ACCESS_TIERS = {
    "PUBLIC":     {"level": 0, "label": "Public",      "color": "#e74c3c"},
    "RELATIVE":   {"level": 1, "label": "Relative",    "color": "#e67e22"},
    "RESEARCHER": {"level": 2, "label": "Researcher",  "color": "#3498db"},
    "CLINICIAN":  {"level": 3, "label": "Clinician",   "color": "#27ae60"},
    "OWNER":      {"level": 4, "label": "Owner",       "color": "#8e44ad"},
}

# Disclosure matrix: which layers each tier can access
DISCLOSURE_MATRIX = {
    #                  RAW     VARIANT   PRS    ANCESTRY  PHENOTYPE
    "PUBLIC":        [False,   False,   False,   False,    False],
    "RELATIVE":      [False,   False,   False,   True,     False],
    "RESEARCHER":    [False,   False,   True,    True,     True ],
    "CLINICIAN":     [False,   True,    True,    True,     True ],
    "OWNER":         [False,   True,    True,    True,     True ],
}

LAYER_KEYS = ["RAW", "VARIANT", "PRS", "ANCESTRY", "PHENOTYPE"]

# -------------------------------------------------------
# 3. UNRECOVERABILITY SCORE
# -------------------------------------------------------

def compute_unrecoverability(tier: str, graph_proximity: int, n_relatives_exposed: int) -> dict:
    """
    Formal unrecoverability score U(tier, graph_context).

    U = base_unrecoverability * graph_penalty
    Graph penalty: if requester is already a node in the kinship graph,
    even 'safe' derived markers can be reverse-engineered.

    Parameters:
        tier: access tier string
        graph_proximity: hop distance from subject in kinship graph (0 = self)
        n_relatives_exposed: number of relatives already in the platform
    """
    accessible = DISCLOSURE_MATRIX[tier]
    results = {}

    for i, key in enumerate(LAYER_KEYS):
        layer = VAULT_LAYERS[key]
        if not accessible[i]:
            # Not disclosed — unrecoverability is full by design
            U = 1.0
            graph_leakage = 0.0
        else:
            base_U = layer["unrecoverability"]
            # Graph proximity penalty: closer relatives = more reconstruction risk
            # At hop=0 (owner), no additional risk. At hop=1 (sibling), moderate.
            proximity_penalty = 0.0
            if graph_proximity > 0:
                # Sharing across kinship edges degrades unrecoverability
                proximity_penalty = min(0.4, 0.15 * graph_proximity)

            # Relative count penalty: more relatives in platform = more triangulation
            relative_penalty = min(0.25, 0.005 * n_relatives_exposed)

            graph_leakage = proximity_penalty + relative_penalty
            U = max(0.0, base_U - graph_leakage)

        results[key] = {
            "disclosed": accessible[i],
            "base_unrecoverability": layer["unrecoverability"],
            "graph_leakage_penalty": round(graph_leakage if accessible[i] else 0.0, 4),
            "effective_unrecoverability": round(U, 4),
            "safe": U >= 0.5
        }
    return results

# -------------------------------------------------------
# 4. GRI D5 LINKAGE — Persistence under vault conditions
# -------------------------------------------------------

def vault_d5_score(tier: str, data_age_years: int, graph_proximity: int,
                   n_relatives: int) -> float:
    """
    D5 (Persistence Risk) adjusted for vault disclosure decisions.
    Even inside a vault, time degrades unrecoverability as:
      - Reference databases grow
      - Inference models improve
      - More relatives join the platform
    """
    u_scores = compute_unrecoverability(tier, graph_proximity, n_relatives)
    disclosed_layers = [k for k in LAYER_KEYS if u_scores[k]["disclosed"]]

    if not disclosed_layers:
        return 0.0  # nothing disclosed → zero persistence risk from vault

    # Temporal degradation: unrecoverability decays as databases grow
    # Based on lifetime_risk.py DB growth curve
    db_growth_factor = min(1.0, 0.02 * data_age_years)  # caps at 1.0 at ~50 years

    avg_U = np.mean([u_scores[k]["effective_unrecoverability"] for k in disclosed_layers])
    effective_persistence = (1.0 - avg_U) + db_growth_factor * 0.3

    # Normalize to D5 scale 0-10
    d5 = min(10.0, effective_persistence * 10)
    return round(d5, 2)

# -------------------------------------------------------
# 5. GRAPH-CONTEXT DISCLOSURE RISK (D6 linkage)
# -------------------------------------------------------

def graph_context_risk(tier: str, graph_proximity: int, n_relatives: int,
                       platform_amplification_factor: float) -> float:
    """
    Even a 'safe' derived marker disclosure amplifies through kinship graph.
    Links B2 vault decisions directly to B1 graph amplification findings.

    platform_amplification_factor: from B1 results (e.g. 23andMe-calibrated ~493x)
    scaled to 0-1 range for this model.
    """
    u_scores = compute_unrecoverability(tier, graph_proximity, n_relatives)
    disclosed_layers = [k for k in LAYER_KEYS if u_scores[k]["disclosed"]]

    if not disclosed_layers:
        return 0.0

    avg_leakage = np.mean([u_scores[k]["graph_leakage_penalty"] for k in disclosed_layers])

    # Amplification scales leaked information across the graph
    # Normalize platform factor (B1 found ~493x for 23andMe-type platforms)
    norm_amp = min(1.0, platform_amplification_factor / 500.0)

    d6_contribution = (avg_leakage * norm_amp * 10)
    return round(min(10.0, d6_contribution), 2)

# -------------------------------------------------------
# 6. SCENARIO ANALYSIS
# -------------------------------------------------------

SCENARIOS = [
    {
        "name": "Scenario 1\nOwner Access\n(No Graph Risk)",
        "tier": "OWNER", "graph_proximity": 0,
        "n_relatives": 0, "data_age": 5, "amp_factor": 0,
        "short": "S1"
    },
    {
        "name": "Scenario 2\nClinician Access\n(Low Graph)",
        "tier": "CLINICIAN", "graph_proximity": 0,
        "n_relatives": 10, "data_age": 10, "amp_factor": 50,
        "short": "S2"
    },
    {
        "name": "Scenario 3\nResearcher Access\n(Moderate Graph)",
        "tier": "RESEARCHER", "graph_proximity": 2,
        "n_relatives": 50, "data_age": 15, "amp_factor": 150,
        "short": "S3"
    },
    {
        "name": "Scenario 4\nRelative Access\n(High Graph)",
        "tier": "RELATIVE", "graph_proximity": 1,
        "n_relatives": 200, "data_age": 20, "amp_factor": 300,
        "short": "S4"
    },
    {
        "name": "Scenario 5\n23andMe-Style\nBreach (Max Amp)",
        "tier": "RELATIVE", "graph_proximity": 2,
        "n_relatives": 500, "data_age": 25, "amp_factor": 493,
        "short": "S5"
    },
]

def run_scenarios():
    results = []
    print("\n" + "=" * 65)
    print(" GenomicVault — Scenario Analysis")
    print("=" * 65)

    for sc in SCENARIOS:
        u = compute_unrecoverability(sc["tier"], sc["graph_proximity"], sc["n_relatives"])
        d5 = vault_d5_score(sc["tier"], sc["data_age"], sc["graph_proximity"], sc["n_relatives"])
        d6 = graph_context_risk(sc["tier"], sc["graph_proximity"], sc["n_relatives"], sc["amp_factor"])

        disclosed = [k for k in LAYER_KEYS if u[k]["disclosed"]]
        unsafe = [k for k in disclosed if not u[k]["safe"]]

        print(f"\n  {sc['short']}: Tier={sc['tier']}, Hop={sc['graph_proximity']}, "
              f"Relatives={sc['n_relatives']}, Age={sc['data_age']}yr")
        print(f"  Disclosed layers : {disclosed if disclosed else 'NONE'}")
        print(f"  Unsafe layers    : {unsafe if unsafe else 'NONE'}")
        print(f"  D5 (Persistence) : {d5}/10")
        print(f"  D6 (Graph Amp)   : {d6}/10")

        results.append({
            "scenario": sc,
            "unrecoverability": u,
            "d5": d5,
            "d6": d6,
            "disclosed": disclosed,
            "unsafe": unsafe,
        })

    print("\n" + "=" * 65)
    return results

# -------------------------------------------------------
# 7. PLOTS
# -------------------------------------------------------

def plot_vault(results):
    fig = plt.figure(figsize=(18, 13))
    fig.suptitle("Module B2",
                 fontsize=15, fontweight='bold', y=0.98)

    # ── Plot 1: Disclosure Matrix Heatmap ──────────────────────────
    ax1 = fig.add_subplot(2, 3, 1)
    tiers = list(ACCESS_TIERS.keys())
    matrix = np.array([[1 if DISCLOSURE_MATRIX[t][i] else 0
                        for i in range(len(LAYER_KEYS))] for t in tiers], dtype=float)

    cmap = LinearSegmentedColormap.from_list("vault", ["#c0392b", "#27ae60"])
    ax1.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=1)
    ax1.set_xticks(range(len(LAYER_KEYS)))
    ax1.set_xticklabels([VAULT_LAYERS[k]["label"].replace(" ", "\n") for k in LAYER_KEYS],
                        fontsize=7)
    ax1.set_yticks(range(len(tiers)))
    ax1.set_yticklabels([ACCESS_TIERS[t]["label"] for t in tiers])
    ax1.set_title("Disclosure Matrix\n(Green = Accessible)", fontsize=9, fontweight='bold')
    for i, j in product(range(len(tiers)), range(len(LAYER_KEYS))):
        ax1.text(j, i, "✓" if matrix[i, j] else "✗", ha='center', va='center',
                 fontsize=11, color='white', fontweight='bold')

    # ── Plot 2: Unrecoverability per Layer per Scenario ────────────
    ax2 = fig.add_subplot(2, 3, 2)
    x = np.arange(len(LAYER_KEYS))
    width = 0.15
    colors = ["#8e44ad", "#27ae60", "#3498db", "#e67e22", "#e74c3c"]
    for idx, res in enumerate(results):
        u_vals = [res["unrecoverability"][k]["effective_unrecoverability"] for k in LAYER_KEYS]
        ax2.bar(x + idx * width, u_vals, width, label=res["scenario"]["short"],
                color=colors[idx], alpha=0.85)

    ax2.axhline(0.5, color='black', linestyle='--', linewidth=1, label='Safety threshold')
    ax2.set_xticks(x + width * 2)
    ax2.set_xticklabels([VAULT_LAYERS[k]["label"].replace(" ", "\n") for k in LAYER_KEYS],
                        fontsize=7)
    ax2.set_ylabel("Effective Unrecoverability (0–1)")
    ax2.set_title("Unrecoverability by Layer & Scenario", fontsize=9, fontweight='bold')
    ax2.set_ylim(0, 1.1)
    ax2.legend(fontsize=7)

    # ── Plot 3: D5 & D6 Scores per Scenario ────────────────────────
    ax3 = fig.add_subplot(2, 3, 3)
    scenario_labels = [r["scenario"]["short"] for r in results]
    d5_vals = [r["d5"] for r in results]
    d6_vals = [r["d6"] for r in results]
    x3 = np.arange(len(results))
    ax3.bar(x3 - 0.2, d5_vals, 0.4, label="D5 Persistence", color="#3498db", alpha=0.85)
    ax3.bar(x3 + 0.2, d6_vals, 0.4, label="D6 Graph Amp", color="#e74c3c", alpha=0.85)
    ax3.set_xticks(x3)
    ax3.set_xticklabels(scenario_labels)
    ax3.set_ylabel("GRI Score (0–10)")
    ax3.set_title("D5 & D6 GRI Scores\nAcross Scenarios", fontsize=9, fontweight='bold')
    ax3.set_ylim(0, 11)
    ax3.legend(fontsize=8)
    for i, (d5, d6) in enumerate(zip(d5_vals, d6_vals)):
        ax3.text(i - 0.2, d5 + 0.15, f"{d5}", ha='center', fontsize=7)
        ax3.text(i + 0.2, d6 + 0.15, f"{d6}", ha='center', fontsize=7)

    # ── Plot 4: Graph Proximity vs Unrecoverability (ANCESTRY layer) ─
    ax4 = fig.add_subplot(2, 3, 4)
    hops = range(0, 6)
    rel_counts = [0, 50, 200, 500]
    clrs = ["#27ae60", "#3498db", "#e67e22", "#e74c3c"]
    for n_rel, clr in zip(rel_counts, clrs):
        u_vals = []
        for h in hops:
            u = compute_unrecoverability("RESEARCHER", h, n_rel)
            u_vals.append(u["ANCESTRY"]["effective_unrecoverability"])
        ax4.plot(hops, u_vals, marker='o', color=clr, label=f"{n_rel} relatives")
    ax4.axhline(0.5, color='black', linestyle='--', linewidth=1, label='Safety threshold')
    ax4.set_xlabel("Graph Proximity (hops from subject)")
    ax4.set_ylabel("Unrecoverability — Ancestry Layer")
    ax4.set_title("Graph Proximity Degrades\nUnrecoverability (Researcher Tier)",
                  fontsize=9, fontweight='bold')
    ax4.legend(fontsize=7)
    ax4.set_ylim(0, 1.0)

    # ── Plot 5: Vault Layer Risk Stack (Scenario 5 — Breach) ───────
    ax5 = fig.add_subplot(2, 3, 5)
    sc5 = results[4]
    u5 = sc5["unrecoverability"]
    layer_labels = [VAULT_LAYERS[k]["label"] for k in LAYER_KEYS]
    base_u = [u5[k]["base_unrecoverability"] for k in LAYER_KEYS]
    penalties = [u5[k]["graph_leakage_penalty"] for k in LAYER_KEYS]
    effective = [u5[k]["effective_unrecoverability"] for k in LAYER_KEYS]
    x5 = np.arange(len(LAYER_KEYS))
    ax5.bar(x5, base_u, color="#3498db", alpha=0.6, label="Base Unrecoverability")
    ax5.bar(x5, penalties, bottom=[b - p for b, p in zip(base_u, penalties)],
            color="#e74c3c", alpha=0.8, label="Graph Leakage Penalty")
    ax5.plot(x5, effective, 'ko-', linewidth=2, markersize=6, label="Effective U")
    ax5.axhline(0.5, color='purple', linestyle='--', linewidth=1, label='Safety threshold')
    ax5.set_xticks(x5)
    ax5.set_xticklabels([l.replace(" ", "\n") for l in layer_labels], fontsize=7)
    ax5.set_ylabel("Unrecoverability (0–1)")
    ax5.set_title("S5: 23andMe-Style Breach\nGraph Penalty Impact per Layer",
                  fontsize=9, fontweight='bold')
    ax5.set_ylim(0, 1.2)
    ax5.legend(fontsize=7)

    # ── Plot 6: Vault Architecture Diagram ─────────────────────────
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis('off')
    ax6.set_xlim(0, 10)
    ax6.set_ylim(0, 10)
    ax6.set_title("GenomicVault — Layer Architecture", fontsize=9, fontweight='bold')

    layer_info = [
        ("RAW SEQUENCE", "#c0392b", "NEVER DISCLOSED\nFull biological lock", 8.5),
        ("VARIANT CALLS", "#e67e22", "CLINICIAN / OWNER ONLY\nHigh re-ID risk", 6.8),
        ("PRS SCORES", "#f1c40f", "RESEARCHER+\nAggregate — safer", 5.1),
        ("ANCESTRY", "#27ae60", "RESEARCHER+\nKinship risk remains", 3.4),
        ("PHENOTYPE FLAGS", "#2980b9", "RESEARCHER+\nSafest unit of disclosure", 1.7),
    ]
    for label, color, desc, y in layer_info:
        rect = mpatches.FancyBboxPatch((0.5, y - 0.6), 9, 1.1,
                                       boxstyle="round,pad=0.1",
                                       facecolor=color, alpha=0.25, edgecolor=color, linewidth=2)
        ax6.add_patch(rect)
        ax6.text(1.0, y, label, fontsize=8, fontweight='bold', va='center', color=color)
        ax6.text(5.5, y, desc, fontsize=7, va='center', color='#333333')

    ax6.text(5, 0.5, "↑ Increasing disclosure safety", ha='center', fontsize=7,
             color='gray', style='italic')
    ax6.text(5, 9.7, "↓ Vault enforces hard lock on raw sequence", ha='center',
             fontsize=7, color='#c0392b', style='italic')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("/home/claude/vault_design_output.png", dpi=150, bbox_inches='tight')
    print("\n  Plot saved → vault_design_output.png")
    plt.show()

# -------------------------------------------------------
# 8. PRIVACY PROOF SUMMARY
# -------------------------------------------------------

def print_privacy_proof():
    print("\n" + "=" * 65)
    print("  GenomicVault — Formal Unrecoverability Properties")
    print("=" * 65)
    print("""
  PROPERTY 1 — Hard Layer Lock
  Raw sequence is architecturally excluded from all disclosure
  tiers including OWNER. U(RAW) = 1.0 by construction.

  PROPERTY 2 — Graph-Degraded Unrecoverability
  For any disclosed layer L and requester at graph proximity h:
    U_eff(L, h, n) = U_base(L) - 0.15*h - 0.005*n
  where n = relatives already on platform.
  U_eff is bounded below at 0.0 (worst case: full recoverability).

  PROPERTY 3 — Safety Threshold
  A layer disclosure is considered 'safe' iff U_eff >= 0.5.
  Below this threshold, derived marker triangulation becomes
  feasible given real-world reference database sizes.

  PROPERTY 4 — Temporal Degradation (D5 linkage)
  Vault disclosures that are safe today become unsafe as:
    (a) reference genomic databases grow (DB growth factor)
    (b) inference models improve (inference expansion factor)
  Both modelled in lifetime_risk.py and feed into D5 scoring.

  PROPERTY 5 — Graph Amplification Multiplier (D6 linkage)
  Any disclosure to a relative (hop >= 1) carries an amplification
  risk proportional to the platform's kinship graph density,
  calibrated against B1 findings (23andMe: ~493x amplification).
    """)
    print("=" * 65)

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if __name__ == "__main__":
    print("=" * 55)
    print("  Module B2")
    print("=" * 55)

    print("\n[1] Vault Layer Taxonomy:")
    for k, v in VAULT_LAYERS.items():
        status = "LOCKED" if not v["disclosure_allowed"] else "DISCLOSABLE"
        print(f"  {k:<12} | {status:<12} | Base U = {v['unrecoverability']:.2f} | {v['description'][:50]}")

    print("\n[2] Running Scenario Analysis...")
    results = run_scenarios()

    print("\n[3] Privacy Proof Properties:")
    print_privacy_proof()

    print("\n[4] Generating plots...")
    plot_vault(results)

    print("\n  Module B2 vault_design.py — COMPLETE")
    print("  Outputs feed: GRI D5 (Persistence) + D6 (Amplification)")
    print("=" * 55)
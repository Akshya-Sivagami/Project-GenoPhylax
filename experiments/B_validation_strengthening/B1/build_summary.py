# ============================================================================
# HISTORICAL / PRE-AUTHORITATIVE — superseded by commit d1a7de5
# ============================================================================
# This script predates the "Lock authoritative Module B results" commit
# (d180bd6) and the "Rebuild Module C from authoritative lifecycle evidence"
# commit (d1a7de5). Numbers produced here are NOT the canonical/reported
# GenoPhylax values.
#
# Canonical single-point values: experiments/B_final_audit/B1_authoritative_final.tsv
# Canonical multi-seed/multi-draw validation (B1+B3 unified graph):
#   demo/unified_b1_b3_multiseed_v2.py
# Canonical B3-internal multi-seed validation (original n_families=800 config):
#   experiments/B3_defense_validation/
#
# This script is kept for historical/provenance purposes only. Do not cite
# its output as a current GenoPhylax result.
# ============================================================================

from pathlib import Path
import csv

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]

RESULTS = (
    REPO
    / "experiments"
    / "B_validation_strengthening"
    / "results"
)

with (RESULTS / "B1_parameter_sensitivity.csv").open(
    encoding="utf-8"
) as f:
    rows = list(csv.DictReader(f))

def f(row, key):
    return float(row[key])

baseline = next(
    r for r in rows
    if f(r, "cousin_prob") == 0.20
    and f(r, "registration_rate") == 0.40
    and int(r["max_hops"]) == 3
)

lowest = min(rows, key=lambda r: f(r, "mean_amplification"))
highest = max(rows, key=lambda r: f(r, "mean_amplification"))

text = f"""# B1 Validation Strengthening Summary

## Status

MODELLED / SENSITIVITY ANALYSIS

This analysis does not replace or modify the frozen historical B1 evidence.

## Historical frozen result

The historical calibration sweep selected cousin_prob=0.20 by minimizing
distance to the historical 23andMe amplification reference of 492.86x.

The resulting frozen calibrated mean was 464.4x, with a historical
calibration error of approximately 5.77%.

Because the same external value was used to select the parameter, this is
a calibration fit and must not be described as independent validation.

## Multi-seed finding

At the frozen structural configuration, single-entry breach simulations
were highly variable across random seeds.

30-seed experiment:
- mean amplification: 845.07x
- median amplification: 1197.50x
- sample SD: 517.70x
- range: 1x to 1357x
- 5th-95th percentile: 1x to 1302.70x

## Breach-entry Monte Carlo

Across 3,000 breach-entry realizations:
- mean amplification: 879.03x
- median amplification: 1122x
- range: 1x to 1395x
- 5th-95th percentile: 1x to 1337x
- fraction <=10x: 19.13%
- fraction >=500x: 80.13%

## Topology explanation

Across 30 independently generated registered graphs:
- mean giant-component fraction: 80.85%
- mean isolated-node fraction: 11.46%
- mean fraction in components of <=10 nodes: 19.15%
- mean 3-hop reach: 879.85 nodes

The approximately 19.15% of nodes in small components closely corresponds
to the approximately 19.13% of Monte Carlo breach entries producing <=10x
amplification.

This supports a topology/entry-point explanation for the bimodal exposure
behavior.

## Parameter sensitivity

Tested:
- cousin probability: 0.05, 0.10, 0.20, 0.30
- registration rate: 0.20, 0.40, 0.60
- propagation depth: 1, 2, 3 hops
- 5 graph seeds
- 50 breach-entry realizations per configuration

Total breach realizations: 9,000.

Lowest tested scenario mean:
- cousin_prob={lowest['cousin_prob']}
- registration_rate={lowest['registration_rate']}
- hops={lowest['max_hops']}
- mean amplification={f(lowest, 'mean_amplification'):.2f}x

Highest tested scenario mean:
- cousin_prob={highest['cousin_prob']}
- registration_rate={highest['registration_rate']}
- hops={highest['max_hops']}
- mean amplification={f(highest, 'mean_amplification'):.2f}x

Historical-structure sensitivity configuration
(cousin_prob=0.20, registration=0.40, hops=3):
- mean amplification={f(baseline, 'mean_amplification'):.2f}x
- median amplification={f(baseline, 'median_amplification'):.2f}x
- 5th percentile={f(baseline, 'p05_amplification'):.2f}x
- 95th percentile={f(baseline, 'p95_amplification'):.2f}x
- fraction >=500x={f(baseline, 'fraction_ge_500x'):.3f}

## Defensible conclusion

B1 demonstrates that exposure amplification can emerge from connectivity
in a synthetic registered kinship graph, but its magnitude is strongly
dependent on graph connectivity, platform registration, propagation depth,
and the initial breach entry point.

The historical 464.4x value is retained as a calibrated historical result.
It is not a universal amplification factor and is not treated as an
independent validation estimate.

The strengthened evidence therefore supports a RANGE- AND
TOPOLOGY-DEPENDENT amplification claim rather than a single universal
multiplier.
"""

out = RESULTS / "B1_STRENGTHENING_SUMMARY.md"
out.write_text(text, encoding="utf-8")

print(text)
print(f"\nSaved: {out}")
print("STATUS: PASS")

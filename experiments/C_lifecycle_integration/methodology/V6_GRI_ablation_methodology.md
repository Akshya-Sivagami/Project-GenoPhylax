# V6 — GenoPhylax Risk Index Ablation Analysis

## Purpose

V6 tests whether the baseline GenoPhylax Risk Index is dominated by individual
dimensions or by correlated evidence families.

The baseline GRI is not changed.

Ablation is a validation analysis.

---

# Baseline aggregation

For each case:

    GRI_base =
        mean(scored dimensions)

Only dimensions with profile_status=SCORED are included.

Non-scored dimensions remain absent rather than zero.

---

# Test 1 — Leave-One-Dimension-Out

For each scored dimension d:

    GRI_without_d =
        mean(all other scored dimensions)

The absolute change is:

    Delta_d =
        GRI_without_d - GRI_base

The absolute influence is:

    |Delta_d|

This test identifies dimensions that strongly control the composite.

---

# F11 interpretation

The F11 baseline contains:

D2 = 1.0

D7 = 1.0

Removing either dimension leaves the remaining dimension equal to 1.0.

Therefore the leave-one-out GRI remains 1.0.

This must NOT be interpreted as independent replication.

D2 and D7 are related observations from the same controlled F11 integrity
pathway.

The correct interpretation is:

the baseline magnitude is invariant to removal of either one of the two scored
representations because both individually occupy the upper normalized boundary.

---

# Privacy interpretation

The Privacy baseline contains:

D1 — Identity Risk

D3 — Familial Cascade Risk

D5 — Persistence Risk

D6 — Amplification Risk

D1, D3 and D5 are not independent.

They are derived from the B2 lifetime-risk evidence family.

D6 derives from the B1 calibrated amplification model.

Therefore single-dimension ablation is necessary but insufficient.

---

# Test 2 — Grouped Provenance Ablation

Privacy is additionally tested by evidence family.

## B2 lifetime-model family

D1 + D3 + D5

## B1 amplification family

D6

Two complementary profiles are therefore calculated:

1. remove D6 and retain only the B2 lifetime-model family;

2. remove D1/D3/D5 and retain only D6.

This exposes whether the final Privacy GRI is driven primarily by the B2
lifetime model or the B1 amplification model.

---

# D5 structural dependence

D5 was defined as the equal mean of the provenance-eligible re-identification
and familial temporal AUC values.

Therefore D5 is mathematically related to D1 and D3.

V6 explicitly records this dependence.

D1, D3 and D5 must not be described as three independent confirmations of the
Privacy result.

---

# Interpretation thresholds

V6 does not create arbitrary pass/fail thresholds such as:

"less than 10 percent change = robust."

Instead the exact score changes are reported.

Claims such as stable, sensitive, dominant or highly dependent must be tied to
the observed ablation values.

---

# Modifiers

M1-M5 are not applied during V6.

M6 evidence tiers are not converted into numerical weights.

This isolates dimension-level structural dependence.

---

# Publication use

V6 supports statements about:

- dimension influence;
- score dependence;
- correlated evidence families;
- robustness of the numerical index to component removal.

It does not establish external validity.

---

# Status after V6

Baseline GRI: unchanged.

Ablation diagnostics: calculated.

Modifier sensitivity: deferred to V7.

Weight sensitivity: deferred to V7.

Temporal-scalarization sensitivity: deferred to V7.

M5 scenario sensitivity: deferred to V7.

Claims audit: deferred to V8.

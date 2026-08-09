# V7 — GenoPhylax Risk Index Sensitivity Analysis

## Purpose

V7 tests whether the primary GenoPhylax Risk Index conclusions depend strongly
on methodological choices that are not empirically fixed.

The primary C4.8 GRI remains unchanged.

Sensitivity analyses are secondary validation results.

---

# Baseline

F11:

D2 = 1.0

D7 = 1.0

Baseline equal-dimension GRI = 1.0

Privacy:

D1 = 0.8886656512

D3 = 0.8817416604

D5 = 0.8852036558

D6 = 0.9904301172

Baseline equal-dimension GRI = 0.9115102712

---

# Sensitivity family 1 — Correlation-aware dimension weighting

The C4.8 baseline uses equal weights over four Privacy dimensions:

D1 = 0.25

D3 = 0.25

D5 = 0.25

D6 = 0.25

However, D1, D3 and D5 belong to the same B2 lifetime-model family.

Therefore the equal-dimension baseline assigns:

75 percent total weight to B2 lifetime-model evidence

25 percent total weight to B1 calibrated amplification evidence.

This is transparent but structurally favors the B2 evidence family.

V7 therefore defines a family-weight parameter alpha:

alpha =
    total weight assigned to the B2 family D1/D3/D5.

1-alpha =
    weight assigned to D6.

Within the B2 family, alpha is divided equally across D1/D3/D5.

The sweep is:

alpha = 0.00
alpha = 0.25
alpha = 0.50
alpha = 0.75
alpha = 1.00

Interpretation:

alpha=0.75 reproduces the C4.8 equal-dimension baseline.

alpha=0.50 is the correlation-aware equal-family baseline.

alpha=0 and alpha=1 are stress-test endpoints and are not proposed as primary
weights.

No evidence tier is used numerically in this weighting.

---

# F11 weight sensitivity

F11 receives a complete D2/D7 weight sweep.

Because both normalized dimensions equal 1.0:

any convex weighting of D2 and D7 must return GRI=1.0.

This demonstrates numerical weight invariance.

It does not establish evidence independence.

---

# Sensitivity family 2 — Temporal scalarization

C4.3 selected horizon-normalized trapezoidal AUC.

V7 compares this against the annual sample mean.

The alternative remains scientifically plausible because the model contains
regular annual sampling over years 0 through 80.

For Privacy:

D1 uses REID.

D3 uses FAMILIAL.

D5 remains the equal mean of the provenance-eligible D1 and D3 temporal
summaries.

D6 is unchanged.

The comparison therefore isolates the temporal scalarization choice.

Terminal probability and maximum probability are not promoted to full
alternative baselines because they erase timing differences through saturation.

They remain diagnostic context.

---

# Sensitivity family 3 — D6 reference anchor

D6 uses:

    log(1+x) / log(1+R)

with clipping to [0,1].

Locked values:

x = 464.4-fold calibrated amplification.

R = 492.86-fold reference anchor.

V7 perturbs R by:

-20 percent
-10 percent
baseline
+10 percent
+20 percent

This tests the degree to which Privacy GRI depends on the selected calibration
reference.

The calibrated x value itself is not changed.

If x exceeds a reduced reference anchor, the normalized value clips at 1.0 as
defined by the C4.2 normalization.

---

# Sensitivity family 4 — M5 containment scenarios

Privacy M5 remains a modifier rather than a Base GRI dimension.

Source-backed scenarios:

low-degree/peripheral:
residual difficulty = 0.008

mid-degree/average:
residual difficulty = 0.795

high-degree/hub:
residual difficulty = 0.980

V7 verifies that the modifier profile changes substantially across these
scenarios while the primary Base GRI remains unchanged because C4.8 explicitly
does not multiply M5 into the GRI.

This is intentional.

The result demonstrates scenario uncertainty without inventing an unsupported
modifier-adjustment equation.

---

# One-at-a-time interpretation

Weight, temporal, reference-anchor and M5 tests are reported separately.

Their extrema must not be described as a statistical confidence interval.

The complete observed numerical range across the deterministic sensitivity
tests may be reported as a sensitivity envelope or stress-test range only.

---

# Correlation-aware interpretation

D5 is mathematically related to D1 and D3.

Therefore family-balanced weighting is particularly important.

If the correlation-aware result remains in the same broad risk region as the
equal-dimension baseline, that supports structural stability of the conclusion.

It does not imply statistical independence.

---

# Evidence

M6 evidence tiers remain categorical.

No E1-E5 numeric weighting is introduced during sensitivity analysis.

---

# Publication safeguards

V7 may support wording such as:

"the index remained high across tested weighting and normalization choices"

only if supported by the actual results.

V7 may not support:

- a probabilistic confidence interval;
- an external-validation claim;
- a universal threshold claim;
- a probability-of-harm interpretation.

---

# Status after V7

Base GRI: unchanged.

Weight sensitivity: complete.

Temporal scalarization sensitivity: complete.

D6 reference-anchor sensitivity: complete.

M5 scenario sensitivity: complete.

Evidence multipliers: not used.

Publication claims audit: V8 still required.

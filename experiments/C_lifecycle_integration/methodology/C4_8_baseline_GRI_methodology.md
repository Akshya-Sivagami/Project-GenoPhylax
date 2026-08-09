# C4.8 Baseline GenoPhylax Risk Index

## Purpose

C4.8 computes the first baseline GenoPhylax Risk Index for each worked case.

The baseline GRI combines only dimensions that have a defensible scored
baseline value.

It does not impute missing or non-applicable dimensions as zero.

It does not numerically discount model-derived evidence.

It does not automatically multiply M1-M5 modifiers into the GRI.

---

# Baseline aggregation

For a worked case with scored-dimension set A:

    GRI_base =
        (1 / |A|) * sum(D_d for d in A)

All scored dimensions receive equal weight within the baseline.

Thus:

    w_d = 1 / |A|

for d in A.

Dimensions outside A receive no weight because they are not part of the
baseline denominator.

This is different from assigning them a numerical weight of zero in a full
seven-dimensional vector.

---

# Why equal weighting

No empirical evidence currently establishes a superior cross-dimensional
weighting scheme.

Equal weighting is therefore selected as the transparent baseline because it:

- introduces the fewest unsupported assumptions;
- is straightforward to reproduce;
- avoids using arbitrary expert weights as primary results;
- supports later weight-sensitivity analysis.

Equal weighting is not a claim that all risk dimensions are biologically or
operationally equivalent.

---

# F11 baseline

Scored dimensions:

- D2 Clinical Interpretation Risk = 1.0
- D7 Pipeline Exposure Risk = 1.0

Therefore:

    GRI_base_F11 =
        (D2 + D7) / 2

                   = 1.0

F11 D5 remains context only.

D1, D3, D4 and D6 remain not applicable to the current worked-case baseline.

---

# Privacy baseline

Scored dimensions:

- D1 Identity Risk
- D3 Familial Cascade Risk
- D5 Persistence Risk
- D6 Amplification Risk

Therefore:

    GRI_base_Privacy =
        (D1 + D3 + D5 + D6) / 4

Privacy D2 remains context only.

Privacy D4 remains without a direct baseline severity anchor.

Privacy D7 is not applicable.

---

# Interpretation scale

The baseline GRI remains on [0,1].

0 represents the lower end of the normalized scored dimensions.

1 represents the upper end of the normalized scored dimensions.

A high GRI does not mean:

- probability of compromise;
- probability of patient harm;
- probability that every real-world system is vulnerable;
- independently validated population risk.

It is a composite normalized risk magnitude within the GenoPhylax framework.

---

# Evidence confidence

M6 does not numerically alter the baseline GRI.

Instead, every GRI is reported alongside its evidence profile.

F11:

CONTROLLED_EMPIRICAL_CASE

Privacy:

MODEL_DEPENDENT_MIXED_SUPPORT

Therefore a Privacy GRI and F11 GRI must not be interpreted as having identical
evidential strength simply because both are on the same numerical scale.

---

# Modifier policy

M1-M5 are not automatically multiplied into the baseline GRI.

Reasons include:

1. some modifier values share the same source evidence as dimensions;
2. some modifiers are unmeasured;
3. some modifiers are not applicable;
4. M5 is scenario dependent;
5. no validated functional form currently establishes how modifiers should
   mathematically rescale dimension severity.

Therefore C4.8 reports modifiers alongside the base GRI.

---

# F11 modifiers

M1 Integrity Impact:
resolved at 1.0 but correlated with D2.

M2 Clinical Severity:
applicable but unquantified.

M3 Detectability:
unmeasured.

M4 Recoverability:
unmeasured.

M5 Containment Difficulty:
unmeasured.

These missing states are not assigned numerical defaults.

---

# Privacy modifiers

M1:
not applicable.

M2:
not applicable.

M3:
model-supported detectability descriptor.

M4:
model-supported recoverability descriptor.

M5:
source-backed scenario envelope.

M5 remains an envelope:

low-degree/peripheral residual difficulty = 0.008

mid-degree/average residual difficulty = 0.795

high-degree/hub residual difficulty = 0.980

No single M5 scalar is inserted into the baseline GRI.

---

# Primary GenoPhylax output structure

The primary result is therefore represented as:

    Base GRI
    + M6 Evidence Profile
    + Modifier Profile
    + later Sensitivity / Ablation Range

rather than:

    one opaque adjusted scalar

This preserves epistemic and mechanistic distinctions.

---

# Correlation caveat

F11 D2 and D7 are causally related observations from one controlled integrity
pathway.

Privacy D1, D3 and D5 derive from related lifetime-risk modeling.

Therefore the baseline equal-weight GRI is an index, not an estimator formed
from statistically independent variables.

Ablation and weight sensitivity must test dependence on these correlated
dimensions.

---

# Status after C4.8

Baseline GRI: DEFINED.

Dimension weights: equal across scored dimensions for primary baseline.

Missing-as-zero: PROHIBITED.

Modifier multiplication: NOT USED in primary baseline.

Evidence discounting: NOT USED.

Ablation: NEXT.

Weight sensitivity: NEXT.

Modifier scenario sensitivity: NEXT.

Final publication claim remains conditional on V6-V8 validation.

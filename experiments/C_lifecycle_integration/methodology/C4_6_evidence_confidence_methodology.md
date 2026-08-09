# C4.6 M6 Evidence-Confidence Treatment

## Purpose

M6 represents the strength and type of evidence supporting a GenoPhylax
dimension result.

M6 is deliberately separated from risk magnitude.

A high modeled risk with limited evidence remains a high modeled risk, but the
strength of the conclusion must be described differently from a directly
observed empirical result.

---

# M6 is not an epistemic probability

The evidence tiers E1-E5 are ordinal evidence classes.

They are not probabilities that a claim is true.

Therefore C4.6 prohibits arbitrary mappings such as:

E1 = 1.0

E2 = 0.8

E3 = 0.6

E4 = 0.4

E5 = 0.2

No such numerical confidence multipliers are introduced.

---

# Locked evidence tiers

## E1 — Replicated direct empirical evidence

Direct empirical effect reproduced across independent conditions, seeds,
replications, or equivalent experimental repeats.

Interpretation:

strongest project-internal empirical support.

This does not automatically imply external clinical or population validation.

---

## E2 — Controlled direct empirical case study

Direct empirical evidence within a controlled worked case.

Interpretation:

strong case-specific empirical support.

External generalization remains limited.

---

## E3 — Calibrated simulation/model

Model output with an explicit external or reference calibration target.

Interpretation:

model-derived risk with some calibration support.

Calibration of one target does not validate all model assumptions.

---

## E4 — Uncalibrated simulation/internal model/design benchmark

Project-internal simulation or generated benchmark.

Interpretation:

useful mechanistic/model evidence, but conclusions remain strongly
model-dependent.

---

## E5 — Illustrative or hypothetical lifecycle propagation

Conceptual downstream propagation not directly observed or quantitatively
validated in the current experiment.

Interpretation:

illustrative only.

E5 cannot establish observed severity.

---

# Evidence-order semantics

For reporting purposes only, evidence strength follows:

E1 > E2 > E3 > E4 > E5

This ordering is ordinal.

Distances between tiers are undefined.

For example:

the difference between E2 and E3 is not assumed equal to the difference between
E3 and E4.

Therefore arithmetic operations on tier numbers are prohibited.

---

# Dimension-level M6

Each scored dimension inherits the evidence tier of its locked primary severity
anchor.

A dimension does not automatically inherit stronger evidence from unrelated or
broader mechanism experiments.

This preserves the C3 principle:

evidence strength is not automatically inherited across handoffs.

---

# F11 evidence profile

The F11 worked case has two scored dimensions:

D2 Clinical Interpretation Risk

D7 Pipeline Exposure Risk

Both use HF11_04 as the locked primary severity anchor.

HF11_04 is controlled direct empirical F11 evidence and carries E2.

Therefore:

F11 D2 -> E2

F11 D7 -> E2

Interpretation:

the quantitative F11 case result is supported by controlled direct empirical
evidence in one worked locus/individual/basecaller setting.

It is not external replication.

---

# Privacy evidence profile

Privacy D1, D3 and D5 are anchored in HPRIV_03.

The underlying evidence is the B2 lifetime-risk simulation.

Therefore:

Privacy D1 -> E4

Privacy D3 -> E4

Privacy D5 -> E4

Privacy D6 is anchored in HPRIV_02.

The amplification result includes calibrated B1 evidence.

Therefore:

Privacy D6 -> E3

Interpretation:

the privacy GRI magnitude is substantially model-dependent.

D6 has calibrated-model support, while D1/D3/D5 remain internal-model outputs.

---

# D4

Privacy D4 has no direct baseline risk-severity anchor.

It therefore does not receive a scored M6 severity entry.

Its context and mitigation evidence may still carry evidence tiers in narrative
reporting.

---

# Case-level evidence profiles

Case-level M6 is not calculated as an arithmetic average of evidence tiers.

Instead each case receives an evidence-support profile.

F11:

CONTROLLED_EMPIRICAL_CASE

because all currently scored dimensions are E2.

Privacy:

MODEL_DEPENDENT_MIXED_SUPPORT

because scored dimensions contain E3 and E4 support.

No single number is used to conceal that mixture.

---

# Modifier evidence

M1-M5 values retain their own evidence scope.

Examples:

F11 M1 shares direct controlled evidence with D2.

Privacy M3 is UNMEASURED. The internally generated B3 authentication benchmark is retained as contextual mitigation performance evidence only and does not constitute a measurement of privacy-event detectability.

Privacy M4 is based on the B2 internal vault model.

Privacy M5 is a B3 internal-model scenario envelope.

These modifier evidence classes are recorded but are not used as independent
confidence multipliers.

---

# Final GRI reporting policy

The eventual GenoPhylax output must separate:

1. RISK MAGNITUDE

   Computed from resolved D-dimension inputs.

2. EVIDENCE SUPPORT

   M6 evidence tier/profile.

3. UNCERTAINTY / SENSITIVITY

   Derived from model assumptions, scenario ranges, weight perturbations and
   ablation analysis.

These three concepts must not be collapsed into one pseudo-precise number.

---

# Evidence-adjusted reporting

C4.6 does not define:

Risk × EvidenceMultiplier

as the evidence-adjusted GRI.

Instead, later reporting may present:

Base GRI

+ Evidence Profile

+ Sensitivity / Scenario Range

This is preferred over numerically shrinking a risk score because an E4 model
has less empirical evidence.

---

# Missing evidence

Absence of empirical validation does not mean zero risk.

Therefore:

E4 does not reduce a risk value toward zero.

E5 does not mean zero severity.

UNMEASURED does not mean zero.

Evidence class affects confidence and permitted claim strength, not the
existence of the modeled risk.

---

# Claim-strength policy

E1:
may be described as replicated project empirical evidence.

E2:
may be described as controlled direct empirical evidence.

E3:
must be described as calibrated model evidence.

E4:
must be described as project-internal/model-derived evidence.

E5:
must be described as modelled, illustrative or hypothetical propagation.

No tier alone supports:

- clinical validation;
- population validation;
- universal real-world effectiveness;
- proven patient harm.

---

# Status after C4.6

Dimension risk values: unchanged.

M1-M5 architecture: unchanged.

M6 evidence classes: defined.

Numeric evidence multipliers: NOT DEFINED.

Evidence-tier arithmetic: PROHIBITED.

Dimension weights: NOT DEFINED.

Final GRI: NOT COMPUTED.

Next:

assemble base case dimension profiles before final aggregation.

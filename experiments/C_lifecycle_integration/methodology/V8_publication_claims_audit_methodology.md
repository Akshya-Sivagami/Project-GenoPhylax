# V8 — GenoPhylax Publication Claims and Wording Audit

## Purpose

V8 controls how GenoPhylax GRI findings may be described in:

- the paper;
- project report;
- presentation;
- findings notes;
- figure captions;
- abstract and conclusion.

No new risk values are created in V8.

This stage translates the locked evidence and validation architecture into
permitted and prohibited scientific language.

---

# Core distinction

The GenoPhylax Risk Index is a normalized framework index.

It is not:

- a probability of compromise;
- a probability of patient harm;
- a probability of privacy breach;
- a calibrated clinical-risk probability;
- a population-prevalence estimate.

Therefore index values must be described as normalized risk-index values.

---

# F11 claim scope

F11 baseline GRI:

1.0000000000

Scored dimensions:

D2 Clinical Interpretation Risk

D7 Pipeline Exposure Risk

Evidence profile:

CONTROLLED_EMPIRICAL_CASE

Tier:

E2

Permitted interpretation:

Within the controlled F11 worked case, both scored normalized dimensions reached
their upper normalized boundaries, producing a baseline GRI of 1.0.

This is supported by controlled direct empirical evidence within the tested
locus, individual, dataset and basecalling configuration.

---

# F11 prohibited interpretations

GRI = 1.0 must not be described as:

- 100 percent clinical risk;
- 100 percent probability of patient harm;
- universal failure of genomic pipelines;
- evidence that every F11 variant can be suppressed;
- external clinical validation;
- population validation;
- proof of successful clinical-database ingestion.

The S5 -> S6 storage extension remains modelled only.

---

# Privacy claim scope

Privacy baseline GRI:

0.9115102712

Evidence profile:

MODEL_DEPENDENT_MIXED_SUPPORT

Evidence tiers:

E3 and E4.

Permitted interpretation:

Under the primary equal-dimension GenoPhylax aggregation, the Privacy worked
case produced a normalized baseline GRI of approximately 0.9115.

The value is model-derived.

D6 has calibrated-model support.

D1, D3 and D5 derive from project-internal lifetime-risk modeling.

---

# Privacy sensitivity

The tested deterministic family-weight sweep produced:

minimum:

0.8852036558

maximum:

0.9904301172

The correlation-aware 50/50 family-balanced configuration produced:

0.9378168865

The annual sample-mean temporal alternative produced:

0.9082052704

The D6 reference-anchor sweep produced Privacy GRI values approximately:

0.9044521653 through 0.9139027419.

These are deterministic sensitivity results.

They are not statistical confidence intervals.

---

# Privacy M5 claim scope

Containment residual difficulty varied by attack origin:

low-degree/peripheral:

0.008

mid-degree/average:

0.795

high-degree/hub:

0.980

These results demonstrate strong topology/scenario dependence in the project
containment model.

They do not represent universal real-world containment probabilities.

M5 remains separate from the primary Base GRI.

---

# Evidence language

## E2

Use:

controlled direct empirical evidence

or:

controlled empirical case-study evidence

Do not use:

externally validated

clinically validated

population validated

unless independent evidence is later added.

## E3

Use:

calibrated model evidence

Do not use:

empirically proven population risk.

## E4

Use:

project-internal model-derived evidence

or:

internal simulation/model evidence

Do not use:

real-world observed risk.

## E5

Use:

modelled propagation

illustrative propagation

hypothetical downstream extension

Do not use:

observed downstream propagation.

---

# Sensitivity language

Permitted:

deterministic sensitivity range

tested stress-test range

family-weight sensitivity

normalization sensitivity

scenario envelope

Prohibited:

95 percent confidence interval

credible interval

statistical uncertainty interval

unless a statistical model supporting such an interval is later implemented.

---

# Robustness language

For F11:

The index is invariant to D2/D7 convex reweighting because both normalized
dimensions equal 1.0.

This does not imply independent replication.

For Privacy:

The index remained high across the tested deterministic weighting and
normalization configurations.

This is permitted because all tested GRI configurations remained between
approximately 0.8852 and 0.9904.

However, this does not establish external robustness across populations,
datasets, genomic technologies or threat models.

---

# Correlation language

D1, D3 and D5 must not be called three independent confirmations.

D5 is mathematically constructed from D1 and D3 temporal summaries.

They may be described as separate framework dimensions derived from a shared
B2 evidence family.

---

# Comparative language

F11 GRI = 1.0

and

Privacy GRI = 0.9115

must not be interpreted as direct empirical evidence that the F11 attack is
"more dangerous" than the Privacy case.

The two cases have different:

- scored dimension sets;
- mechanisms;
- evidence profiles;
- empirical versus model support.

Cross-case numerical comparison is descriptive within the common normalized
framework only.

---

# Modifier language

M1-M5 are reported as qualifying modifiers.

They were not automatically multiplied into the Base GRI.

Therefore the paper must not describe the primary result as a fully
modifier-adjusted GRI.

The correct term is:

Baseline GenoPhylax Risk Index

or:

Base GRI

until a separately justified modifier-adjusted formulation is developed.

---

# Publication readiness

V8 considers the quantitative GRI methodology internally publication-ready when:

- source provenance is locked;
- normalization is locked;
- baseline aggregation is validated;
- evidence strength is separated from magnitude;
- ablation is complete;
- deterministic sensitivity is complete;
- wording restrictions are enforced.

Publication-ready does not mean externally validated.

It means the current methodology and claims are internally auditable and
appropriately scoped for the reported worked cases.

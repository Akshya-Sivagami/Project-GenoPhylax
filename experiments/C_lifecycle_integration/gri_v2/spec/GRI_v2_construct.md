# GenoPhylax Risk Index v2 — Construct Specification

## 1. Purpose

The GenoPhylax Risk Index (GRI) is a structured composite indicator for
characterizing cyber-biosecurity risk represented by a genomic data,
software, or processing scenario across the genomic information lifecycle.

GRI is not a probability of patient harm, compromise, exploitation,
disease, or population-level impact.

## 2. Target construct

GRI measures:

"The magnitude and lifecycle reach of demonstrated or evidence-supported
cyber-biosecurity risk associated with the confidentiality, integrity,
interpretation, propagation, persistence, and processing of genomic
information."

The construct is multidimensional. A case may express only a subset of
dimensions.

## 3. Unit of assessment

The unit scored by GRI is a defined CASE.

A case must specify:
- the genomic asset or information involved;
- the relevant pipeline or lifecycle context;
- the event, exposure, vulnerability, or scenario being assessed;
- the evidence supporting each scored dimension;
- the boundaries of the claim.

Different cases must not be merged solely to obtain a more complete
risk vector.

## 4. Dimensions

D1 — Identity Risk
Persistent re-identification of an individual enabled by genomic
information.

D2 — Clinical Interpretation Risk
Change, corruption, suppression, fabrication, or disclosure of genomic
information capable of affecting clinically relevant interpretation.

D3 — Familial Cascade Risk
Extension of genomic exposure or inference from one individual to
biologically related individuals.

D4 — Accessibility Risk
Exposure resulting from unauthorized, inappropriate, or insufficiently
controlled access to genomic information.

D5 — Persistence Risk
Degree to which genomic exposure or its consequences remain difficult
to reverse over time.

D6 — Amplification Risk
Expansion of an initial genomic exposure through kinship, sharing,
reuse, inference, or downstream propagation.

D7 — Pipeline Exposure Risk
Propagation of an integrity or security-relevant effect through genomic
processing stages.

## 5. Separation of concepts

GRI v2 separates three questions:

1. RISK MAGNITUDE
   What magnitude of risk is represented by the available evidence?

2. EVIDENCE STRENGTH
   How strongly is the assigned risk vector supported?

3. COVERAGE
   How much of the GRI construct is actually assessable for this case?

Evidence weakness must not automatically be interpreted as low risk.

An unmeasured or non-applicable dimension must not be converted to zero.

## 6. Evidence classes

Evidence supporting a dimension must be classified using controlled
categories such as:

- EXPERIMENTAL
- OBSERVATIONAL
- CALIBRATED_MODEL
- MODELLED
- INFERRED

Evidence class is metadata describing support for the score. It is not
automatically a numerical multiplier.

## 7. Required provenance

Every scored dimension must contain:

- raw metric or qualitative observation;
- source;
- evidence class;
- normalization rule;
- normalized value;
- applicability status;
- limitations.

A normalized score without traceable provenance is invalid.

## 8. Normalization principle

GRI v2 must not assign dimension scores merely because an outcome appears
severe.

Each quantitative normalization must define:

- metric;
- direction;
- lower anchor;
- upper anchor;
- transformation;
- clipping behavior;
- justification for anchors.

Qualitative mappings, where unavoidable, must use predefined criteria and
must be tested for inter-rater reproducibility.

## 9. Aggregation principle

The aggregation function and dimension weights are validation targets,
not assumptions.

GRI v1 equal-weight arithmetic aggregation remains the historical baseline.

GRI v2 will compare candidate aggregation and weighting approaches using
predefined validation and robustness criteria before selecting a primary
method.

## 10. Reporting

A GRI v2 assessment should report at minimum:

- D1–D7 risk vector;
- applicable dimensions;
- composite GRI, when aggregation is justified;
- dimension coverage;
- evidence profile;
- provenance;
- sensitivity/robustness results;
- important limitations.

The composite score must never replace the underlying dimension vector.

## 11. Interpretation boundary

GRI scores are normalized comparative indicators within the GenoPhylax
framework.

They are not:
- probabilities of harm;
- probabilities of successful attack;
- clinical outcome probabilities;
- population prevalence estimates;
- substitutes for clinical risk assessment;
- substitutes for vulnerability exploitability assessment.

## 12. Versioning

GRI v1 results are frozen historical results.

Development of GRI v2 must not retroactively alter:
- F11 v1 Base GRI = 1.0000000000
- Privacy v1 Base GRI = 0.9373875000

Any v2 rescoring must be explicitly labelled as GRI v2 and remain
traceable to the v1 case and evidence.

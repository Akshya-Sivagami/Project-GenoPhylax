# GenoPhylax Risk Index v2 — Development Validation Report

## 1. Status

GRI v2 is a development-stage normalized comparative cyber-biosecurity
risk indicator.

This report documents the validation and robustness evidence obtained
during development. It does not claim that GRI v2 is a clinically
validated instrument, a probability model, or a universally calibrated
risk scale.

The validation corpus contains:

- 15 cases;
- 23 applicable dimension observations;
- GenoPhylax experimental/model cases;
- external experimental cases;
- external observational/incident cases;
- calibrated/modelled cases;
- mitigated and lower-magnitude cases;
- cases deliberately withheld from point scoring where magnitude or
  construct mapping could not be justified.

All corpus and metric-registry validators passed with zero errors and
zero warnings at the final development-validation stage.

## 2. Construct under evaluation

GRI v2 targets:

"The magnitude and lifecycle reach of demonstrated or evidence-supported
cyber-biosecurity risk associated with the confidentiality, integrity,
interpretation, propagation, persistence, and processing of genomic
information."

The unit of assessment is a defined CASE.

GRI v2 separates:

1. risk magnitude;
2. evidence strength;
3. resolution coverage and construct breadth.

Evidence weakness is not interpreted as low risk.

Missing, unmeasured, construct-unresolved, or non-applicable dimensions
are not converted to zero.

GRI is not a probability of patient harm, successful exploitation,
clinical outcome, compromise, or population prevalence.

## 3. Corpus integrity and provenance controls

Final development corpus:

- Cases: 15
- Registered metrics: 23
- Used metrics: 23
- Case-validation errors: 0
- Metric-registry errors: 0
- Metric-registry warnings: 0

Scientific safeguards enforced by the case schema and scoring pipeline:

- manual normalized scores are not allowed;
- missing dimensions are not converted to zero;
- provenance is required;
- evidence class is required;
- limitations are required;
- evidence class does not numerically multiply risk magnitude.

Quantitative provenance completeness for quantitatively resolved
dimensions was 1.0 in the reliability-envelope output.

## 4. Construct-validity gating

GRI v2 distinguishes between two important unresolved states.

### 4.1 Positive magnitude unresolved

A binary demonstration may establish that a risk mechanism exists
without establishing a calibrated magnitude.

Such observations are reported as:

POSITIVE_MAGNITUDE_UNRESOLVED

They do not automatically receive a score of 1.0 and prevent issuance
of a case composite when the unresolved dimension is applicable.

Examples include binary capability evidence in Beacon, Homer,
Von Thenen, and GEDmatch cases.

### 4.2 Construct unresolved

A quantitative metric may be valid in its source study while its mapping
to a particular GRI dimension remains insufficiently justified.

Such observations are reported as:

CONSTRUCT_UNRESOLVED

They receive no point score until the metric-to-dimension mapping is
accepted.

This rule was applied to genomic reconstruction efficacy metrics in:

- EXT-BEACON-RECON-2025 D4;
- EXT-EDGECOOP-2020 D4.

This prevents reconstruction performance from being silently equated
with accessibility risk.

## 5. Quantitatively resolved case range

Nine cases produced fully resolved candidate composites at the final
development stage.

Arithmetic candidate composites were:

- EXT-GYMREK-2013: 0.1190000000
- EXT-BEACON-MITIGATED-2017: 0.2000000000
- EXT-BEACON-S2-2017: 0.3500000000
- EXT-ERLICH-2018: 0.6000000000
- EXT-GURSOY-2020: 0.8000000000
- EXT-23ANDME-2023: 0.9132601525
- GP-PRIVACY-001: 0.9351285176
- EXT-NEY-2017: 1.0000000000
- GP-F11-001: 1.0000000000

Six cases had their headline composite withheld because at least one
applicable dimension lacked an accepted quantitative point estimate.

The observed quantitative range demonstrates discrimination below the
upper boundary, but it does not establish universal calibration of the
0–1 scale.

## 6. Aggregation robustness

Candidate aggregation was evaluated using:

- arithmetic mean;
- geometric mean;
- root-mean-square aggregation.

Across the nine quantitatively eligible cases:

- eligible cases: 9;
- cases changing rank: 0;
- stable-rank fraction: 1.0000.

For multidimensional cases:

EXT-23ANDME-2023:
- AM = 0.9132601525
- GM = 0.9091316214
- RMS = 0.9173701038

GP-PRIVACY-001:
- AM = 0.9351285176
- GM = 0.9327678966
- RMS = 0.9374692690

GP-F11-001:
- AM = 1.0000000000
- GM = 1.0000000000
- RMS = 1.0000000000

The evaluated corpus therefore showed complete rank stability across
these three prespecified aggregation alternatives.

This is a robustness result for the current corpus. It does not prove
that arithmetic aggregation is universally optimal.

## 7. Leave-one-dimension-out sensitivity

Leave-one-dimension-out sensitivity was evaluated for quantitatively
resolved cases containing at least two scored dimensions.

Maximum observed absolute changes were:

- EXT-23ANDME-2023: 0.0867398475
- GP-F11-001: 0.0000000000
- GP-PRIVACY-001: 0.0278595059

For GP-PRIVACY-001, individual omission effects ranged from
0.0153881491 to 0.0278595059.

These results indicate limited single-dimension dependence in the
multidimensional cases evaluated, with the largest observed sensitivity
occurring in the two-dimensional 23andMe case.

Leave-one-dimension-out differences are sensitivity diagnostics and are
not confidence intervals.

## 8. Ceiling behaviour

Final ceiling diagnostic:

- quantitatively scored dimension observations: 15;
- exact 1.0 observations: 6;
- exact ceiling fraction: 0.4000;
- observations >= 0.9: 6;
- fraction >= 0.9: 0.4000;
- binary-demonstration ceiling observations: 0.

The six exact-ceiling observations arose from:

- 1 inverse raw fraction at its boundary;
- 2 raw fractions at their boundary;
- 3 maximum rubric levels.

No ceiling observation resulted from automatically converting binary
demonstration evidence to 1.0.

The remaining 40 percent ceiling fraction indicates limited
discrimination among some severe/boundary cases and remains a known
development limitation.

Ceiling values must not be artificially suppressed merely to improve
score dispersion.

## 9. D6 amplification sensitivity

D6 uses a log10 transformation of amplification ratio with an explicit
development anchor.

Sensitivity was evaluated using upper anchors of:

- 100x;
- 1000x;
- 10000x.

GP-PRIVACY-001:

- anchor 100: 1.0000000000
- anchor 1000: 0.8889640704
- anchor 10000: 0.6667230528

EXT-23ANDME-2023:

- anchor 100: 1.0000000000
- anchor 1000: 0.8265203050
- anchor 10000: 0.6198902288

The D6 score is therefore materially sensitive to the selected upper
anchor.

The 1000x anchor remains a development normalization candidate used for
the primary development analysis. It is not an externally validated or
universal genomic amplification threshold.

D6 results must be reported with this sensitivity information.

## 10. Post-hoc known-groups sanity check

No known-groups hypothesis was preregistered before examination of the
current scores.

Therefore, the available directional comparison is explicitly labelled
POST-HOC and must not be represented as confirmatory validation.

Comparison KG01 used two closely related membership-inference cases:

- EXT-BEACON-MITIGATED-2017 D1 = 0.2000000000
- EXT-BEACON-S2-2017 D1 = 0.3500000000

Expected directional relation:

0.20 < 0.35

Result:

PASS

The scoring system preserved the externally reported directional
contrast.

This is an exploratory directional sanity check only. It is not
independent construct validation and must not be used to tune the
scoring function.

## 11. Reliability envelope

GRI v2 reports reliability information separately from risk magnitude.

The reliability envelope contains:

- resolution coverage;
- construct breadth;
- evidence profile;
- leave-one-dimension-out sensitivity where applicable;
- corpus-level aggregation rank stability;
- quantitative provenance completeness.

Reliability does not multiply, discount, or silently modify the GRI
magnitude.

Examples from the final corpus include:

GP-PRIVACY-001:
- GRI = 0.9351285176
- resolution coverage = 1.0000
- breadth = 4/7
- maximum LOO change = 0.0278595059
- quantitative provenance completeness = 1.0000

GP-F11-001:
- GRI = 1.0000000000
- resolution coverage = 1.0000
- breadth = 2/7
- maximum LOO change = 0.0000000000
- quantitative provenance completeness = 1.0000

EXT-BEACON-RECON-2025:
- composite = WITHHELD
- resolution coverage = 0.5000
- quantitative breadth = 1/7
- D4 = CONSTRUCT_UNRESOLVED

Full resolution coverage does not imply comprehensive seven-dimension
lifecycle coverage.

## 12. Relationship to frozen GRI v1

GRI v1 remains a frozen historical comparator.

Frozen v1 results:

- F11 Base GRI = 1.0000000000
- Privacy Base GRI = 0.9373875000

Current v2 development results:

- GP-F11-001 = 1.0000000000
- GP-PRIVACY-001 = 0.9351285176

The numerical similarity between v1 and v2 Privacy scores is not
evidence of validity.

GRI v2 differs methodologically by adding explicit metric registration,
construct gating, normalization provenance, unresolved-state handling,
external cases, sensitivity testing, and a separate reliability
envelope.

GRI v2 does not retroactively alter the frozen v1 results.

## 13. Evidence supported by the current validation stage

The current development evidence supports the following statements:

1. The implementation preserves missing/unresolved dimensions rather
   than treating them as zero.

2. Binary capability evidence is not automatically interpreted as
   maximum quantitative risk.

3. Metrics with unresolved construct mappings can be withheld without
   forcing a numerical score.

4. The current corpus contains low, moderate, high, and boundary
   quantitative observations rather than only maximum-risk examples.

5. Arithmetic, geometric, and RMS aggregation produced identical case
   ordering among the nine quantitatively eligible cases in the current
   corpus.

6. Multidimensional cases showed bounded leave-one-dimension-out
   sensitivity in the current corpus.

7. All quantitatively scored dimensions retained source provenance.

8. A post-hoc within-study-family directional comparison preserved the
   expected ordering.

These findings support internal consistency and development-stage
robustness of the current GRI v2 implementation.

## 14. Claims not established

The current validation does NOT establish that:

- GRI v2 is a probability of harm or attack success;
- the 0–1 scale is universally calibrated;
- a score has the same empirical meaning across every genomic domain;
- arithmetic aggregation is universally optimal;
- equal dimension weighting is universally correct;
- the 1000x D6 anchor is a universal threshold;
- all seven dimensions have externally validated normalization anchors;
- ceiling behaviour has been fully resolved;
- GRI v2 predicts future incidents or clinical outcomes;
- the current external corpus is representative of all genomic
  cyber-biosecurity scenarios;
- the current post-hoc known-groups check constitutes independent
  construct validation;
- inter-rater reproducibility has been established for all qualitative
  rubric assignments.

## 15. Remaining validation requirements

Before describing GRI v2 as an externally validated general-purpose
index, future work should include:

1. preregistered known-groups hypotheses tested on cases not used during
   development;

2. a larger independent external corpus spanning all seven dimensions;

3. additional multidimensional external cases;

4. independent justification or empirical calibration of normalization
   anchors, especially D6;

5. inter-rater testing for rubric-based dimensions;

6. evaluation of alternative weighting strategies without selecting
   weights to optimize GenoPhylax results;

7. prospective or held-out evaluation where feasible;

8. continued analysis of ceiling effects and discrimination among
   severe cases.

## 16. Development-stage conclusion

GRI v2 is more defensible than the frozen v1 formulation because its
scoring decisions are explicitly registered, provenance-traceable,
construct-gated, sensitivity-tested, and accompanied by separate
reliability information.

The current results support describing GRI v2 as:

"A development-stage, provenance-aware normalized comparative indicator
with demonstrated internal robustness on the evaluated GenoPhylax and
external genomic cyber-biosecurity case corpus."

The current results do not support describing GRI v2 as a universally
validated risk scale or probability model.

The appropriate next engineering step is to freeze this development
methodology and expose the reproducible scoring workflow through the
GRI CLI without expanding its scientific claims.

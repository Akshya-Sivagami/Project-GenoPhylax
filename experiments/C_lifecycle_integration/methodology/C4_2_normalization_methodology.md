# C4.2 GenoPhylax Raw-Metric Normalization Methodology

## Purpose

C4.2 defines how heterogeneous GenoPhylax measurements may later be converted
to a common risk-oriented interval.

The normalization convention is:

`0 = lower represented risk`

`1 = higher represented risk`

C4.2 does not aggregate dimensions, assign dimension weights, assign evidence
weights, or calculate a final GenoPhylax Risk Index.

---

# Core principles

## 1. Preserve empirical meaning

Normalization must use the natural mathematical structure of the underlying
measurement whenever possible.

Probabilities should remain probabilities.

Fractions should remain fractions.

Mitigation effectiveness should be inverted into residual risk.

Multiplicative amplification should not be linearly scaled in raw fold units.

## 2. Avoid arbitrary min-max normalization

A metric must not be normalized merely using the minimum and maximum observed
inside the current experiment unless those values have an independently
defensible semantic meaning.

Using experiment-specific extrema would make the GRI dependent on which
conditions happened to be tested.

## 3. Risk direction must be consistent

After normalization:

- larger value always means greater represented risk;
- smaller value always means lower represented risk.

Metrics whose raw direction is protective must be inverted.

## 4. Missing direct severity remains missing

A case × dimension without a DIRECT RISK_INCREASING severity anchor in C4.1
must not receive an observed severity value merely because an indirect or
mitigating metric can be normalized.

In particular:

- F11 D5 remains context/modelled only;
- Privacy D2 remains context only;
- Privacy D4 has indirect risk context and direct mitigation but no direct
  risk-increasing severity anchor.

## 5. Mitigation is not baseline risk

Containment or authentication performance may be normalized as residual risk
or mitigation strength.

It must not manufacture an absent baseline-risk severity anchor.

## 6. Propagation coverage is separate

Lifecycle propagation coverage must not be raw-summed with normalized severity.

Coverage and severity remain distinct inputs until a later formally specified
aggregation stage.

---

# Normalization families

## PROPORTION_RISK

Use when the raw metric is already a probability or fraction where larger
means greater risk.

Formula:

`N(x) = clip(x, 0, 1)`

Examples:

- re-identification probability;
- familial exposure probability;
- observed suppression fraction.

---

## COMPLEMENT_PROPORTION

Use when the raw metric is a bounded fraction where larger means safer or more
recoverable.

Formula:

`N(x) = 1 - clip(x, 0, 1)`

Examples:

- unrecoverability when interpreting low unrecoverability as greater residual
  genomic recoverability risk, only when the model semantics justify this
  inversion;
- retention fractions when loss represents harm.

The raw metric meaning must be explicitly recorded before inversion.

---

## LOSS_FRACTION

Use when a clean/reference count exists and risk is represented by loss under
attack or perturbation.

Formula:

`N = clip((baseline - attacked) / baseline, 0, 1)`

Requirements:

- baseline > 0;
- baseline and attacked counts must represent the same unit;
- attacked must be paired to the same experimental condition definition.

Example:

F11 ALT-support retention loss.

Clean ALT-supporting parents = 14.

PM2 ALT-supporting parents = 0.

Loss fraction = (14 - 0) / 14 = 1.

This does not imply universal clinical risk. It describes complete target-state
loss within this controlled F11 experiment.

---

## BINARY_TERMINAL_EFFECT

Use for a directly observed terminal categorical outcome when the endpoint is
meaningfully binary.

Formula:

- preserved expected endpoint = 0
- lost/suppressed expected endpoint = 1

Example:

clean pathogenic F11 genotype call present versus attacked condition producing
NO_CALL.

Binary normalization is used only when the source endpoint is itself binary;
continuous measurements must not be artificially binarized.

---

## LOG_REFERENCE_RATIO

Use for large multiplicative amplification factors.

Formula:

`N(x) = clip(log(1 + x) / log(1 + R), 0, 1)`

where `R` is an independently documented reference anchor.

For B1, the approximately 493x external amplification target used in the
calibration experiment may serve as the reference anchor.

The currently retained calibrated model result is approximately 464.4x.

The logarithm prevents raw fold amplification from dominating other dimensions
simply because its measurement unit has a large numeric range.

The reference anchor must be stored explicitly and sensitivity-tested later.

---

## RESIDUAL_RISK

Use when the raw metric measures mitigation effectiveness.

Formula:

`N_residual = 1 - mitigation_effectiveness`

Example:

99.2 percent containment reduction corresponds to approximately 0.008 residual
exposure fraction for that modeled scenario.

Residual risk must remain labelled as mitigation-derived.

It cannot act as a baseline severity anchor where C4.1 identified none.

---

## QUALITY_COMPLEMENT

Use when a bounded quality/performance measure has higher values representing
better protection or detection.

Formula:

`N = 1 - quality`

Example:

authentication F1 of 0.9899 corresponds to a performance-complement value of
0.0101.

This value describes residual classifier performance risk under the generated
test distribution.

It is not an estimate of real-world authentication compromise probability.

---

# Lifetime-risk handling

Time-to-threshold values are not automatically normalized using an arbitrary
maximum year.

For B2 lifetime models, retain:

1. modeled risk probability;
2. time to defined probability thresholds;
3. model horizon;
4. saturation behavior.

Where a probability is available, the probability is the preferred normalized
severity variable.

Time-to-threshold remains interpretability metadata unless a later temporal
normalization is independently justified.

This prevents arbitrary transforms such as:

`1 - year_to_threshold / 80`

from entering the GRI without scientific justification.

---

# D7 pipeline handling

Pipeline Exposure Risk is structurally different from outcome severity.

C4.1 already separates:

- primary severity anchor;
- observed propagation coverage;
- modelled propagation extension.

C4.2 therefore does not add the four F11 direct D7 handoffs.

Later D7 calculation must preserve this distinction.

A terminal clinical-stage integrity effect may act as the severity anchor,
while observed stage coverage remains a separate propagation descriptor.

---

# Evidence confidence

E1-E5 tiers are not converted to numerical probabilities in C4.2.

Evidence-confidence adjustment is deferred to the dedicated M6/evidence stage.

---

# Numerical status after C4.2

Normalization functions: DEFINED

Eligible metric mappings: DEFINED

Boundary behavior: TESTED

Case-level dimension scores: NOT YET COMPUTED

Dimension weights: NOT DEFINED

Evidence multipliers: NOT DEFINED

Final GRI: NOT DEFINED

---

# Multiple measurements for one severity anchor

Multiple measurements derived from the same attacked event are not automatically
independent severity contributions.

They must receive explicit roles.

For the F11 D2 anchor:

- ALT-support loss fraction is the PRIMARY_SEVERITY_METRIC.
- Pathogenic call loss / NO_CALL is a CORROBORATING_TERMINAL_ENDPOINT.

These two measurements must not be summed, averaged, multiplied, or otherwise
combined as though they represent independent harms.

A later aggregation rule may use corroborating endpoints for validation or
confidence interpretation, but not for duplicate severity counting.

---

# Probability normalization versus temporal scalarization

A modeled probability trajectory has two distinct methodological operations.

## Probability normalization

If p(t) is already a probability in [0,1], then each individual p(t) requires
no arbitrary scale conversion.

The risk-oriented normalized value at each time point is simply p(t).

## Temporal scalarization

Converting the entire trajectory p(t) into one case-level number is a separate
decision.

C4.2 does NOT select:

- a preferred evaluation year;
- the terminal modeled year;
- the first saturation year;
- an arbitrary 80-year denominator;
- the maximum probability merely because it is available.

C4.3 must first reconstruct the complete authoritative trajectory.

Only then may candidate temporal summaries be evaluated.

A candidate such as the mean modeled probability across the declared model
horizon may be examined because it incorporates both magnitude and onset, but
it is not adopted in C4.2.

Therefore:

- D1 probability normalization: DEFINED.
- D1 temporal scalarization: DEFERRED.
- D3 probability normalization: DEFINED.
- D3 temporal scalarization: DEFERRED.
- D5 full-trajectory normalization semantics: DEFINED.
- D5 temporal scalarization: DEFERRED.

---

# Anti-cherry-picking rule

A lifetime-risk case-level severity must not be based on a single selected year
unless that year has an independently justified semantic role established
before observing the resulting score.

Terminal saturation alone must not be used when it would erase meaningful
differences in onset or trajectory shape.


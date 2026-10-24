# GRI v2 Development Methodology Freeze

Freeze status: DEVELOPMENT METHODOLOGY FROZEN

This freeze captures the GenoPhylax Risk Index v2 methodology after
development-stage validation and before CLI packaging.

## Frozen validation state

- Cases: 15
- Registered/used metrics: 23
- Applicable dimension observations: 23
- Quantitative dimension scores: 15
- Quantitatively resolved case composites: 9
- Exact ceiling scores: 6
- Exact ceiling fraction: 0.4000
- Validation errors: 0
- Development warnings: 2

## Development warnings retained

1. D6 1000x upper anchor remains a development candidate and is not
   an externally validated universal amplification threshold.

2. Exact ceiling fraction remains 0.4000, indicating limited
   discrimination among some severe/boundary cases.

These warnings are intentionally retained and must not be suppressed
merely to obtain a warning-free validation result.

## Robustness results

- AM/GM/RMS eligible cases: 9
- Cases changing rank: 0
- Stable-rank fraction: 1.0000

Maximum leave-one-dimension-out changes:
- EXT-23ANDME-2023: 0.0867398475
- GP-F11-001: 0.0000000000
- GP-PRIVACY-001: 0.0278595059

Post-hoc directional sanity check:
- EXT-BEACON-MITIGATED-2017 D1 = 0.2000000000
- EXT-BEACON-S2-2017 D1 = 0.3500000000
- relation preserved: PASS

## Frozen GenoPhylax v2 development results

GP-F11-001:
- GRI v2 candidate composite = 1.0000000000
- resolution coverage = 1.0000
- breadth = 2/7

GP-PRIVACY-001:
- GRI v2 candidate composite = 0.9351285176
- resolution coverage = 1.0000
- breadth = 4/7

These do not replace frozen GRI v1 results:
- F11 v1 Base GRI = 1.0000000000
- Privacy v1 Base GRI = 0.9373875000

## Methodological safeguards

- missing/unmeasured dimensions are not zero;
- evidence strength does not multiply risk magnitude;
- binary demonstrations do not automatically score 1.0;
- construct-unresolved metrics receive no point score;
- incomplete applicable cases receive no headline composite;
- reliability is reported separately from risk magnitude;
- corpus maxima do not define normalization;
- D6 1000x is not claimed as universal;
- GRI is not a probability of harm or attack success.

## Freeze boundary

Subsequent CLI implementation must reproduce this methodology rather
than silently modify it.

Any later scientific change to:
- dimensions;
- metric semantics;
- normalization;
- anchors;
- rubrics;
- aggregation;
- unresolved-state policy;
- reliability definitions

must be explicitly versioned as a post-freeze methodology revision.

CLI engineering, serialization, input validation, output formatting and
reproducibility packaging may proceed without changing this methodology.

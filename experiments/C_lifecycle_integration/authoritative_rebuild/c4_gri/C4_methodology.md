# C4 Authoritative GRI Methodology

## Core rule

The Base GenoPhylax Risk Index is the arithmetic mean of only the
applicable, evidence-backed dimensions for a case.

Missing, non-applicable, contextual and unmeasured dimensions are not
converted to zero.

Evidence tiers describe evidentiary strength and are not numerical
multipliers.

Mitigation modifiers are reported separately and do not alter Base GRI.

## F11 case

Applicable dimensions:

- D2 Disease Inference / Clinical Interpretation Risk = 1.0000
- D7 Pipeline Exposure Risk = 1.0000

Base GRI = 1.0000000000

The F11 score is an experimental-case severity score for the demonstrated
computational chain. It is not a patient-outcome probability.

## Privacy case

Applicable dimensions:

- D1 Identity Risk = 1.0000
- D3 Familial Cascade Risk = 1.0000
- D5 Persistence Risk = 0.8516
- D6 Amplification Risk = 0.8980

D5 is the mean of:

- irreversibility component = 1 - 0.2299
  = 0.7701
- year-50 persistence component = 9.33 / 10
  = 0.9330

Base Privacy GRI = 0.9373875000

## B3 mitigation

Authentication threshold = 3.6
Authentication F1 = 0.8387

These values are mitigation-performance context and are not used as M3
detectability.

M5 containment-difficulty residual candidates at fixed k=10 are:

- peripheral origin: 0.008
- mid-degree origin: 0.795
- hub origin: 0.970

They are scenario-specific and are not multiplied into Base GRI.

## Sensitivity

The 50/50 B2-vs-B1 provenance-balanced Privacy sensitivity score is
0.9242583333.

Sensitivity analyses are robustness checks, not confidence intervals.

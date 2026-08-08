# C4.1a Semantic Patch

## D2 naming refinement

D2 was renamed from:

`Disease Inference Risk`

to:

`Disease Inference / Clinical Interpretation Risk`

The broader name reflects both principal GenoPhylax uses of this dimension:

- privacy-side inference of disease-relevant genomic information; and
- integrity-side suppression or distortion of clinically meaningful genomic
  interpretation.

The underlying dimension definition remains focused on clinically meaningful
disease-related genomic information.

## Privacy D4 correction

HPRIV_01 (S6 -> S7) was changed from DIRECT to INDIRECT for Accessibility Risk.

Reason:

The B2 vault/disclosure model demonstrates that genomic information leaves or
expands beyond the original controlled-storage scope and becomes less
recoverable as more layers are disclosed.

It does not directly demonstrate unauthorized access.

Therefore disclosure provides risk-increasing accessibility context, but not a
direct unauthorized-access severity measurement.

HPRIV_04 remains DIRECT RISK_MITIGATING because B3 directly measures
authentication and containment behavior.

## Consequence

Privacy D4 now has:

- HPRIV_01: INDIRECT RISK_INCREASING context;
- HPRIV_04: DIRECT RISK_MITIGATING evidence;
- no DIRECT RISK_INCREASING severity anchor.

Mitigation evidence cannot be used to manufacture a missing risk severity
anchor.

## Final primary-anchor count

6

No numerical normalization, weights, or GRI scores were introduced.

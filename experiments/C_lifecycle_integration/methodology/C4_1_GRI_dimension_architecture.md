# C4.1 GenoPhylax Risk Index Dimension Architecture

## Purpose

C4.1 defines the semantic structure of the GenoPhylax Risk Index before any
normalization, weighting, evidence adjustment, or numerical aggregation.

C4.1 defines:

1. D1-D7 risk dimensions.
2. DIRECT / INDIRECT / NONE applicability rules.
3. Risk-increasing versus risk-mitigating polarity.
4. Handoff-to-dimension relationships.
5. Case-level severity anchors.
6. Propagation coverage semantics.
7. Double-counting guardrails.

No numerical GRI score is produced in C4.1.

---

# D1-D7 dimensions

## D1 — Identity Risk

Risk that genomic information can enable identification or re-identification
of an individual.

## D2 — Disease Inference / Clinical Interpretation Risk

Risk that genomic evidence can reveal, suppress, distort, or otherwise alter
clinically meaningful disease-related genomic information.

## D3 — Familial Cascade Risk

Risk that genomic compromise affecting one individual extends to biological
relatives through shared genomic information or kinship structure.

## D4 — Accessibility Risk

Risk arising from genomic information becoming accessible to unauthorized or
unintended actors through disclosure, weak access control, or failed
authentication.

## D5 — Persistence Risk

Risk that a genomic compromise becomes difficult to reverse because the
information or consequence persists through storage, disclosure, reuse,
inference, replication, or time.

## D6 — Amplification Risk

Risk that an initial compromise expands in scale beyond the initially affected
person, record, disclosure, or access event.

## D7 — Pipeline Exposure Risk

Risk that an upstream genomic-integrity failure survives successive genomic
processing stages rather than being rejected, corrected, or detected.

---

# Applicability rules

Every handoff × dimension cell receives exactly one classification.

## DIRECT

DIRECT means the handoff's source evidence directly measures, demonstrates,
or operationalizes an outcome represented by that dimension.

A merely plausible downstream consequence is not DIRECT.

## INDIRECT

INDIRECT means there is a specific and defensible causal relationship to the
dimension, but the handoff evidence measures an upstream, adjacent, enabling,
or mitigating effect rather than the dimension outcome itself.

Every INDIRECT relationship requires an explicit causal rationale.

INDIRECT is not a generic "possibly related" category.

## NONE

NONE means there is no sufficiently defensible causal or evidential link.

When uncertain between speculative INDIRECT and NONE, C4.1 prefers NONE.

---

# Effect polarity

Applicable relationships are additionally labelled:

- RISK_INCREASING
- RISK_MITIGATING

NONE relationships use NOT_APPLICABLE.

Polarity is semantic only in C4.1 and is not yet a numerical sign.

---


## Accessibility-risk guardrail

Authorized sharing or secondary use does not by itself constitute direct
evidence of unauthorized accessibility.

A disclosure handoff may therefore be INDIRECT for D4 when it expands
information availability without directly measuring unauthorized access.

Direct mitigating access-control evidence must not be used to manufacture a
missing direct risk-increasing severity anchor.


# Case-level roll-up

Multiple handoffs can relate to one case-level dimension.

They must not be simply summed.

Each case × dimension is represented by:

1. a primary severity anchor, where direct risk evidence exists;
2. additional direct supporting evidence;
3. direct mitigating evidence;
4. indirect contextual evidence;
5. observed propagation coverage;
6. model-supported propagation coverage;
7. modelled propagation coverage.

## Primary severity anchor

The primary severity anchor must be:

- DIRECT; and
- RISK_INCREASING.

Where multiple DIRECT risk-increasing handoffs exist, the anchor is the
handoff representing the clearest directly measured manifestation of that
dimension.

An upstream proxy must not replace a more direct downstream outcome.

## Context-only dimensions

If a case has only INDIRECT evidence for a dimension, no direct observed
severity value is invented.

The structural state is CONTEXT_ONLY_NO_DIRECT_RISK_ANCHOR.

## Modelled propagation

MODELLED_PROPAGATION / E5 may extend lifecycle scope but cannot define
observed severity.

---

# Propagation coverage

Coverage is stored separately from severity.

Coverage may be:

- OBSERVED_EMPIRICAL
- MODEL_SUPPORTED
- MODELLED_PROPAGATION

A longer lifecycle chain must not automatically produce a larger severity
score merely because more handoffs are present.

---

# Double-counting guardrails

C4.1 prohibits:

- raw summation of handoff contributions;
- counting the same propagated effect multiple times as independent severity;
- converting INDIRECT evidence into a DIRECT severity anchor;
- allowing E5-only propagation to define observed severity;
- automatically inheriting evidence strength from another experiment;
- treating mitigating evidence as additional risk;
- assigning a dimension merely because it is generically related to genomics.

---

# Dimensions versus modifiers

D1-D7 describe WHAT TYPE of risk exists.

M1-M6 describe properties of a handoff:

- M1 Integrity Impact
- M2 Clinical Severity
- M3 Detectability
- M4 Recoverability
- M5 Containment Difficulty
- M6 Evidence Confidence

The two layers remain separate in C4.1.

---

# Numerical status

Numerical normalization: NOT DEFINED

Dimension scores: NOT DEFINED

Modifier weights: NOT DEFINED

Evidence multipliers: NOT DEFINED

GRI aggregation weights: NOT DEFINED

---

# Next stage

C4.2 defines normalization of authoritative raw evidence measurements.

Normalization must preserve the convention:

0 = lower risk
1 = higher risk

before any GRI aggregation is permitted.

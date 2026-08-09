# C4.5 GenoPhylax Modifier Architecture

## Purpose

C4.5 defines the M1-M5 risk modifiers used by GenoPhylax.

Modifiers describe properties that shape interpretation of the base D1-D7
dimension profile.

They do not replace the base dimensions.

They are not automatically multiplied into dimension scores.

Final integration is deferred until after evidence-confidence treatment and
sensitivity analysis.

---

# Common direction

Where a modifier can be normalized:

0 = less concerning

1 = more concerning

---

# Modifier status vocabulary

Each case × modifier receives one of four states.

## NUMERICALLY_RESOLVED

The current project evidence supports a defensible normalized value.

## APPLICABLE_BUT_UNQUANTIFIED

The concept clearly applies, but the current experiment does not contain a
defensible quantitative measurement.

## UNMEASURED

The modifier could matter to the case, but the current experiment did not test
it.

## NOT_APPLICABLE

The modifier does not meaningfully describe the current worked-case mechanism.

NOT_APPLICABLE and UNMEASURED must never be silently converted to zero.

---

# M1 — Integrity Impact

Definition:

Degree to which the relevant genomic evidence state is altered from the
controlled baseline.

Risk direction:

greater integrity alteration -> larger M1.

For the F11 worked case, the primary integrity-impact measurement is the same
controlled ALT-support loss already used to establish D2 severity:

clean ALT-supporting parents = 14

PM2 ALT-supporting parents = 0

Therefore:

M1_F11 = 1.0

Important:

M1 and D2 share source evidence.

They are therefore CORRELATED.

M1 must not later be multiplied into D2 as though it were an independent
measurement of harm.

For the privacy case, integrity alteration is not the primary mechanism.

M1 is NOT_APPLICABLE.

---

# M2 — Clinical Severity

Definition:

Severity of the plausible clinical consequence associated with the affected
genomic interpretation.

The F11 target is a pathogenic nonsense variant with clinical relevance.

However, this project did not measure:

- patient outcome;
- penetrance;
- actual clinical decision change;
- treatment consequence;
- morbidity;
- mortality;
- real clinical ingestion.

Pathogenic classification alone is not converted into a numerical clinical
severity probability.

Therefore:

F11 M2 = APPLICABLE_BUT_UNQUANTIFIED.

This prevents a pathogenic ClinVar label from being silently converted into
M2 = 1.0.

For the current privacy worked case:

M2 = NOT_APPLICABLE.

Disease inference remains contextual in that case and does not form a locked
direct clinical-severity measurement.

---

# M3 — Detectability

Definition:

Difficulty of detecting the harmful or unauthorized state.

Risk direction:

0 = readily detected

1 = difficult to detect

For F11, the current experiment demonstrates an integrity effect but does not
contain a validated attack-detection classifier or operational detection study.

Therefore:

F11 M3 = UNMEASURED.

For the privacy pathway, B3 includes an authentication classifier with:

F1 = 0.9899

A performance-complement descriptor may therefore be represented as:

M3_privacy = 1 - F1

              = 0.0101

Interpretation:

This is residual classifier-performance difficulty under the generated B3 test
distribution.

It is not a real-world probability of undetected compromise.

Evidence class:

MODEL_SUPPORTED.

---

# M4 — Recoverability

Definition:

Difficulty of restoring confidentiality or reducing recoverability once genomic
information has been disclosed or propagated.

Risk direction:

0 = highly recoverable / reversible

1 = difficult to recover or retract

For F11, the experiment did not test remediation or recovery after the attacked
variant state.

Therefore:

F11 M4 = UNMEASURED.

For the privacy pathway, B2 defines an unrecoverability model.

Because lower unrecoverability means greater ability to reconstruct genomic
information, the risk-oriented complement is:

RecoverabilityRisk = 1 - unrecoverability

The cumulative all-six disclosure condition has:

unrecoverability = 0.0801

therefore:

M4_privacy = 0.9199

The Pathogenic-only value:

1 - 0.2299 = 0.7701

is retained as supporting context.

The all-six cumulative condition is used as the principal current privacy-case
endpoint because the privacy case studies progressive genomic disclosure and
persistence.

This is a project model output, not a cryptographic impossibility measure.

---

# M5 — Containment Difficulty

Definition:

Residual difficulty containing downstream exposure after response controls are
applied.

Risk direction:

0 = easy/effective containment

1 = difficult/ineffective containment

For F11, no operational containment experiment was performed.

Therefore:

F11 M5 = UNMEASURED.

For privacy, B3 directly models containment.

However, containment performance depends strongly on attack origin.

The current evidence includes substantially different results for:

- low-degree/peripheral origin;
- mid-degree origin;
- high-degree/hub origin.

Therefore a single containment scalar must not be selected from the easiest
scenario.

C4.5 retains an M5 scenario envelope.

For the principal k=10 containment benchmark:

99.2 percent reduction corresponds to residual difficulty:

1 - 0.992 = 0.008

But attack-origin sensitivity demonstrates that this low residual is not
universal.

The scenario envelope is retained until later sensitivity analysis.

---

# Modifier and dimension correlation

Modifiers may share source evidence with dimensions.

Examples:

- F11 M1 and D2 both derive from controlled ALT-support loss.
- Privacy M4 and D5 both involve persistence/recoverability concepts.
- Privacy M5 and D4 mitigation evidence both derive from B3.

This correlation is explicitly recorded.

Modifiers must not be treated as statistically independent multipliers without
further justification.

---

# Missing-data rule

The following are prohibited:

UNMEASURED -> 0

APPLICABLE_BUT_UNQUANTIFIED -> 0

NOT_APPLICABLE -> 0

Missing and non-applicable modifiers remain structurally distinct from low-risk
values.

---

# Numerical status after C4.5

M1 F11: numerically resolved.

M2 F11: applicable but unquantified.

M3 F11: unmeasured.

M4 F11: unmeasured.

M5 F11: unmeasured.

M1 Privacy: not applicable.

M2 Privacy: not applicable.

M3 Privacy: model-supported numerical descriptor.

M4 Privacy: model-supported numerical descriptor.

M5 Privacy: scenario envelope; single scalar not yet selected.

No modifier is yet automatically applied to the base D1-D7 scores.

M6 evidence confidence is deferred to C4.6.

Final GRI remains uncomputed.

# C4.4 F11 D7 Structural Normalization

## Purpose

D7 represents Pipeline Exposure Risk:

the extent to which an upstream integrity failure survives through the genomic
processing pipeline and reaches downstream interpretation.

For the current F11 worked case, the relevant integrity path is:

S1 Raw Signal
-> S2 Basecalling
-> S3 Alignment
-> S4 Variant / Genotype Evidence
-> S5 Clinical Interpretation

S5 -> S6 storage propagation is retained separately as modelled lifecycle
extension and is not treated as directly observed pipeline exposure.

---

# Why D7 is structural

D7 is not naturally represented by a probability, count, or fold-change.

The principal observation is the terminal lifecycle stage at which the
integrity effect is still directly demonstrated.

Therefore D7 uses a semantic terminal-reach transform.

---

# Locked semantic path

The D7 pre-storage integrity path contains five ordered semantic milestones:

- S1: Raw Signal
- S2: Basecalling / Reads
- S3: Alignment / Evidence
- S4: Variant Calling / Genotype Evidence
- S5: Clinical Interpretation

These stages were defined before C4 numerical scoring.

The normalization denominator therefore comes from the locked lifecycle model,
not from the number of successful handoffs observed in this experiment.

---

# Terminal-reach normalization

Let:

- i = ordinal position of the furthest directly observed stage;
- i_min = 1 for S1;
- i_max = 5 for S5.

Then:

    D7_reach =
        (i - i_min) / (i_max - i_min)

This gives:

- terminal S1 -> 0.00
- terminal S2 -> 0.25
- terminal S3 -> 0.50
- terminal S4 -> 0.75
- terminal S5 -> 1.00

The transform is monotonic and bounded in [0,1].

---

# F11 observed reach

The locked F11 handoffs are:

- HF11_01: S1 -> S2, OBSERVED_EMPIRICAL
- HF11_02: S2 -> S3, OBSERVED_EMPIRICAL
- HF11_03: S3 -> S4, OBSERVED_EMPIRICAL
- HF11_04: S4 -> S5, OBSERVED_EMPIRICAL
- HF11_05: S5 -> S6, MODELLED_PROPAGATION

The furthest directly observed integrity stage is therefore S5.

Thus:

    F11 D7 = 1.00

HF11_05 does not increase this value.

---

# Why this is not raw handoff summation

D7 is not computed as:

    number_of_observed_handoffs / number_of_handoffs

Instead, the scalar is derived from the terminal semantic stage reached on the
pre-defined D7 integrity path.

Observed handoff continuity is used as validation that no intermediate semantic
stage was skipped.

---

# No S6 bonus

S6 Storage is not included in the directly observed D7 path for the F11 case.

The S5 -> S6 handoff is E5 modelled propagation.

It is recorded as:

MODELLED_EXTENSION_PRESENT

but contributes zero additional numeric D7 severity.

---

# Separation from D2

D2 and D7 are correlated but measure different concepts.

D2:
clinical interpretation / disease-related outcome severity.

D7:
downstream pipeline reach of the integrity failure.

D7 is not multiplied by D2.

D2 is not added into D7.

No claim of independence is made.

Their correlation must be examined in later ablation and sensitivity analysis.

---

# Boundary interpretation

A D7 value of 1.0 does NOT mean:

- universal pipeline vulnerability;
- 100 percent probability of clinical harm;
- successful compromise of every genomic pipeline;
- storage propagation was directly observed.

It means only:

within the controlled F11 worked case, the integrity effect remained directly
observable through the final semantic endpoint of the locked S1-S5 integrity
path.

---

# Status after C4.4

F11 D2: resolved.

F11 D7: resolved.

Privacy D1: resolved.

Privacy D3: resolved.

Privacy D4: no direct baseline severity anchor.

Privacy D5: resolved.

Privacy D6: resolved.

All primary dimension inputs required by the two worked cases are now
structurally resolved.

Dimension weights: NOT DEFINED.

Modifier values: NOT YET DEFINED.

Evidence weights: NOT DEFINED.

Final GRI: NOT COMPUTED.

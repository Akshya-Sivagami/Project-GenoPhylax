# C4.3b Temporal Scalarization and D5 Semantic Resolution

## Purpose

C4.3b resolves how the fully reproduced B2 lifetime-risk trajectories become
case-level normalized inputs for:

- D1 Identity Risk;
- D3 Familial Cascade Risk;
- D5 Persistence Risk.

This stage does not define final GRI aggregation weights.

---

# Candidate temporal summaries

The reproduced annual B2 trajectories support several possible scalar summaries:

1. terminal probability;
2. maximum probability;
3. arithmetic mean of annual probability samples;
4. horizon-normalized trapezoidal area under the probability trajectory.

Terminal and maximum probability are rejected as primary scalarizations because
they discard onset information.

For example, both re-identification and familial risk ultimately reach 1.0, but
they do not reach high-risk states at exactly the same time.

Using only terminal saturation would erase that distinction.

A selected individual year is also rejected because no single evaluation year
has an independently established semantic role in the current framework.

---

# Selected temporal scalarization

The primary scalarization for D1 and D3 is the horizon-normalized trapezoidal
area under the modeled probability trajectory.

For a trajectory p(t) on the model horizon [0,H]:

    TemporalSeverity =
        integral_0^H p(t) dt / H

For the annual discrete trajectory, the integral is calculated using the
trapezoidal rule.

Properties:

- bounded in [0,1] because p(t) is bounded in [0,1];
- higher values represent greater sustained lifetime risk;
- earlier onset increases the score;
- later onset decreases the score;
- terminal saturation alone does not dominate the result;
- the complete trajectory contributes to the result.

The model horizon is not used as an arbitrary risk denominator. It is the actual
integration interval of the committed lifetime model.

---

# Why not simple annual mean?

The annual arithmetic mean is retained as a sensitivity comparator.

For regularly spaced annual samples, mean probability and normalized
trapezoidal AUC should be close.

The trapezoidal form is preferred because it treats the trajectory as a
time-domain quantity and avoids giving the two boundary samples the same full
sample weight as interior years.

The choice will later be included in sensitivity analysis.

---

# D1

D1 uses the B2 re-identification trajectory.

Primary scalar:

    D1_temporal =
        normalized trapezoidal AUC of re-identification probability

---

# D3

D3 uses the B2 familial trajectory.

Primary scalar:

    D3_temporal =
        normalized trapezoidal AUC of familial probability

---

# D5 provenance restriction

The committed B2 model also contains a native composite:

    composite =
        (re-identification + disease inference + familial risk) / 3

That native composite is retained as model context but is NOT selected as the
GenoPhylax D5 scalar.

Reason:

The locked HPRIV_03 persistence handoff is sourced from B2_E02 and B2_E03:

- re-identification persistence;
- familial persistence.

Disease-inference trajectory evidence is not part of the locked HPRIV_03
evidence set.

Using the native composite would therefore introduce an additional evidence
channel into D5 after C3 had already frozen the handoff semantics.

---

# Selected D5 persistence scalar

D5 is defined from the two provenance-eligible persistent privacy channels:

- re-identification temporal severity;
- familial temporal severity.

Baseline D5:

    D5 =
        (D1_temporal + D3_temporal) / 2

This equal mean is an assumption-minimizing baseline.

It does NOT assert equal biological importance.

Alternative relative weighting between the two persistence channels must be
tested later under V7 sensitivity analysis.

---

# Double-counting interpretation

D5 is not treated as a third independent underlying event.

D1 and D3 describe WHAT privacy consequences occur.

D5 describes the TEMPORAL PERSISTENCE of the evidence channels.

Their correlation must be acknowledged during final GRI aggregation and
sensitivity analysis.

No claim of statistical independence is made.

---

# Disease trajectory

The reproduced disease trajectory remains available for:

- model reproduction;
- contextual analysis;
- sensitivity analysis;
- future framework extensions.

It does not enter the currently locked D5 baseline.

---

# Composite trajectory

The B2 native composite remains:

MODEL_NATIVE_CONTEXT_ONLY

It is not used as the GenoPhylax D5 baseline.

---

# Status after C4.3b

D1 temporal scalarization: DEFINED

D3 temporal scalarization: DEFINED

D5 persistence scalarization: DEFINED

F11 D2 severity: already resolved

Privacy D6 severity: already resolved

F11 D7 structural transform: NOT YET DEFINED

D4 baseline severity: NOT DEFINED

Dimension weights: NOT DEFINED

Evidence weights: NOT DEFINED

Final GRI: NOT COMPUTED

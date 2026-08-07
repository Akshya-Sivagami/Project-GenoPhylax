# C3.1 F11 Evidence-Tier Scope Clarification

## Decision

The F11 worked-case handoffs HF11_01 through HF11_04 are classified as E2
Controlled Direct Empirical Case Study evidence.

HF11_05 remains E5 Modelled Propagation.

## Why HF11_01 and HF11_02 are not E1

Module A2 contains E1 evidence for specific replicated claims:

- multi-seed Gaussian perturbation reproducibility;
- cross-locus replication of the W0 null target-state effect.

Those results support the general mechanism that nanopore raw-signal
perturbations can alter basecalling output and propagate through downstream
processing.

They do not constitute independent replication of the specific F11 attack
chain.

The F11 experiment remains limited to:

- one individual;
- one pathogenic locus;
- one principal basecaller;
- one principal targeted interpolation attack configuration.

Therefore the F11-specific handoff claim is E2 even when stronger replicated
A2 evidence supports the broader mechanism.

## Principle

Evidence tiers are assigned to the exact claim represented by a handoff.

Evidence strength must not be inherited automatically from another experiment
in the same module or from a broader mechanistic result.

## Final F11 handoff tier structure

- S1 -> S2: E2 OBSERVED_EMPIRICAL
- S2 -> S3: E2 OBSERVED_EMPIRICAL
- S3 -> S4: E2 OBSERVED_EMPIRICAL
- S4 -> S5: E2 OBSERVED_EMPIRICAL
- S5 -> S6: E5 MODELLED_PROPAGATION

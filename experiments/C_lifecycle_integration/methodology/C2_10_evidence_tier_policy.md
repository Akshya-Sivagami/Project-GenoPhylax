# C2.10 Evidence Tier Policy

## Purpose

Evidence tiers characterize the strength and externality of each individual
evidence claim in the GenoPhylax cross-module evidence registry.

Tiers are assigned per evidence row, not per module.

They are ordinal evidence categories. They are not numerical confidence
weights and must not yet be converted directly into GenoPhylax Risk Index
multipliers.

## Tier definitions

### E1 — Replicated direct empirical evidence

Direct experimental evidence for which the principal effect or null result
has been reproduced across independent seeds, loci, datasets, systems, or
other meaningful replication units.

### E2 — Controlled direct empirical case study

Directly observed experimental evidence obtained under controlled conditions,
but with scope limited to a particular dataset, locus, individual, model,
system, or principal experimental configuration.

### E3 — Calibrated simulation/model

Simulation or mathematical model for which one or more important parameters
or outputs have been quantitatively calibrated against an external empirical
reference or documented real-world target.

### E4 — Uncalibrated simulation/internal model/design benchmark

Internally generated simulation, synthetic model, architecture benchmark,
design decision, or project-generated benchmark that has not been externally
calibrated for the specific claim.

### E5 — Illustrative/hypothetical lifecycle propagation

A plausible downstream scenario or lifecycle propagation step that is used
to reason about consequences but was not directly observed in the project
and is not represented by a calibrated model.

## Source-pending evidence

A registry row whose authoritative provenance has not yet been recovered is
not assigned an E1–E5 tier.

Its tier status is `SOURCE_PENDING`.

This prevents apparently strong empirical claims from receiving a confidence
classification solely from remembered or secondary descriptions.

## Interpretation rules

1. Tiers apply to claims, not entire modules.
2. E1 does not imply clinical or population validation.
3. E2 may contain strong causal controls while still remaining a case study.
4. E3 means calibrated model, not validated real-world prediction.
5. E4 is valid evidence but carries stronger model-dependence.
6. E5 is scenario evidence and must be labelled as modelled or hypothetical.
7. Numerical confidence weights are intentionally not defined at this stage.
8. Evidence-adjusted GRI scoring must be designed separately and sensitivity-tested.

## Current A1 handling

Authoritative A1 provenance was recovered on 2026-08-09 and preserved through
a private forensic archive plus a sanitized provenance package committed under
`experiments/A1_memory_audit/provenance/`.

A1_E01 through A1_E04 are therefore no longer `SOURCE_PENDING`.

Each is assigned **E2 — Controlled direct empirical case study**:

- A1_E01: one principal preserved BWA/ASAN fuzzing configuration;
- A1_E02: direct root-cause analysis within that software audit;
- A1_E03: one directly observed `ksw_extend2` ASAN finding;
- A1_E04: one directly observed `mem_aln2sam` ASAN finding.

E1 is not assigned because meaningful independent replication of the same
principal finding/effect across independent systems, versions, datasets, or
other replication units was not demonstrated.

A1 remains `STANDALONE_NON_GRI`; source recovery does not make A1 part of the
existing F11 or Privacy quantitative GRI worked cases.

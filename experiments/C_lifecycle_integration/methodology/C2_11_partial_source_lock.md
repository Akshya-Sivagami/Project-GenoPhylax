# C2.11 Partial Evidence Source Lock

## Status

`PARTIAL_LOCK_FOR_C3`

The C2 evidence registry is sufficiently verified to support C3 lifecycle
integration for evidence rows whose authoritative sources have been verified
and whose row-level evidence tiers have been assigned.

## Locked scope

- Total C2 evidence rows: 20
- C3-eligible locked rows: 16
- Source-pending excluded rows: 4

The following modules are locked for C3 use:

- A2
- A3
- B1
- B2
- B3

## Excluded scope

A1_E01 through A1_E04 remain source-pending.

These claims remain documented in C2 but are excluded from:

- C3 worked-case handoff construction;
- evidence-adjusted scoring;
- C4 GRI computation;
- confidence weighting.

Recovering A1 provenance may upgrade the registry later without invalidating
the C3 cases defined from the already verified evidence.

## Methodological rule

Partial lock means:

1. verified evidence may progress into C3;
2. unresolved evidence cannot contribute to a scored handoff;
3. unresolved evidence cannot inherit a tier by assumption;
4. no numerical confidence weights are introduced by this lock;
5. C2 may later be upgraded to a full lock if A1 provenance is recovered.

## Worked cases permitted under this lock

### Case 1 — F11 integrity

Uses A2/A3 evidence for observed experimental stages and introduces an explicit
modelled S5→S6 propagation handoff only where storage/database entry was not
directly observed.

### Case 2 — Privacy amplification and containment

Uses B1/B2/B3 model evidence across S6→S10.

The modelled nature and tier of each handoff must remain visible in C3.

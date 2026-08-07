# C3.2 A1 Paper Role and GRI Scope

## Decision

Module A1 is retained as a standalone upstream software-integrity contribution
within Project GenoPhylax.

A1 is not currently included in quantitative GRI scoring.

## Rationale

The A1 BWA fuzzing experiment was completed historically, but the original
authoritative fuzzing and AddressSanitizer artifacts are not present in the
current provenance-locked repository state.

C2 therefore retains A1_E01 through A1_E04 as SOURCE_PENDING.

They are excluded from:

- C3 scored handoffs;
- GRI dimension calculation;
- evidence-confidence adjustment;
- quantitative integrated case-study scoring.

## Paper framing

A1 demonstrates that vulnerabilities may exist in genomic computational
software at an upstream lifecycle entry point.

The quantitative GenoPhylax GRI case studies are built from provenance-locked
A2, A3, B1, B2 and B3 evidence.

The paper must not imply that every named project module contributes
numerically to the GRI.

## Future upgrade

If authoritative A1 artifacts are recovered before final paper freeze, A1 may
be source-locked and independently evaluated for inclusion.

Failure to recover those artifacts does not invalidate the current F11 or
privacy GRI case studies.

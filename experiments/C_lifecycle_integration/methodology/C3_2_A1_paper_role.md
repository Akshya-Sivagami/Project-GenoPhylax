# C3.2 A1 Paper Role and GRI Scope

## Decision

Module A1 is retained as a **standalone upstream software-integrity
contribution** within Project GenoPhylax.

A1 is source-locked but remains:

`STANDALONE_NON_GRI`

A1 is not included in the existing quantitative F11 or Privacy GRI worked
cases.

## Provenance status

The original A1 environment was recovered on 2026-08-09.

A complete private forensic archive was created and verified before sanitized
public provenance was committed under:

`experiments/A1_memory_audit/provenance/`

The recovered evidence supports:

- one canonical preserved BWA ASAN campaign with 963,339 executions over
  23,120 seconds (~6.42 h), 15.44% AFL bitmap coverage, and 521 saved crash
  artifacts;
- two distinct ASAN-confirmed out-of-bounds-read root causes;
- `ksw_extend2` at `ksw.c:428`, classified as a heap-backed out-of-bounds
  READ / CWE-125;
- `mem_aln2sam` at `bwamem.c:906`, classified as a global/static-storage
  out-of-bounds READ / CWE-125.

A1_E01 through A1_E04 are therefore no longer `SOURCE_PENDING`.

Under the C2 evidence-tier policy they are E2 controlled direct empirical
case-study evidence.

## Why A1 remains outside Base GRI

The exclusion is now a **scope decision rather than a provenance deficiency**.

The existing quantitative GenoPhylax worked cases were intentionally defined
as:

1. F11 integrity — A2/A3;
2. Privacy amplification/containment — B1/B2/B3.

A1 demonstrates a separate upstream software-security attack surface but was
not represented as a worked lifecycle handoff in the validated C3 cases.

Source recovery therefore does not justify retroactively inserting A1 into:

- C3 scored handoffs;
- C4 Base GRI calculation;
- V6 ablation;
- V7 sensitivity;
- V8 publication-claim numerical locks.

## Paper framing

A1 demonstrates that genomic computational software itself can expose
memory-safety failure modes when processing malformed genomic input.

The recovered evidence establishes sanitizer-detected out-of-bounds READs.
It does not establish:

- arbitrary code execution;
- remote code execution;
- memory-write corruption;
- patient harm;
- clinical record poisoning;
- successful SAM poisoning.

The paper must not imply that every project module contributes numerically to
GRI.

## Future work

A separate A1 lifecycle worked case could be designed later, but doing so
would constitute a new analysis rather than a repair of the currently
validated F11/Privacy GRI.

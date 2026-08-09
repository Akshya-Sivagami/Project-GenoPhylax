# C2.13 A1 Authoritative Source Recovery

## Status

`A1_SOURCE_RECOVERED`

Date: 2026-08-09

## Recovery

The original Module A1 BWA fuzzing environment was recovered from the
historical VirtualBox research VM.

Before public integration, the recovered environment was preserved as a
private forensic archive with cryptographic checksum and archive-integrity
validation.

A sanitized provenance package was then committed to:

`experiments/A1_memory_audit/provenance/`

Raw crash-inducing inputs and trigger material remain private.

## Corrected A1 evidence

### A1_E01 — canonical BWA ASAN campaign

- BWA 0.7.19-r1273
- 963,339 executions
- 23,120 seconds (~6.42 h)
- 15.44% AFL bitmap coverage
- 521 saved crash artifacts

Historical ~2.5M aggregate executions are not canonical because surviving
campaign directories include restarts/backups and other targets.

Historical 17.69% BWA coverage is superseded.

Tier: **E2**

### A1_E02 — root-cause result

Recovered evidence supports:

**two distinct ASAN-confirmed source-level out-of-bounds-read root causes**

Saved crash artifacts and unique crash-input hashes are not interpreted as
distinct vulnerabilities.

Tier: **E2**

### A1_E03

- function: `ksw_extend2`
- source: `ksw.c:428`
- class: heap-backed out-of-bounds READ
- CWE-125

Tier: **E2**

### A1_E04

- function: `mem_aln2sam`
- source: `bwamem.c:906`
- class: global/static-storage out-of-bounds READ
- CWE-125

Tier: **E2**

## Tier rationale

The four rows are directly observed controlled experimental evidence, but
meaningful independent replication of each principal claim has not been
demonstrated.

Under C2.10 they therefore meet E2 rather than E1.

## GRI scope lock

A1 remains:

`STANDALONE_NON_GRI`

This source recovery must not alter the existing:

- F11 Base GRI = 1.0000000000;
- Privacy Base GRI = 0.9115102712;
- C3 F11/Privacy handoffs;
- C4 scoring architecture;
- V6 ablation;
- V7 sensitivity;
- V8 publication-claim numerical results.

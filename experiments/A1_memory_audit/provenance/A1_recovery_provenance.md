# Module A1 — Recovery Provenance

## Recovery event

The original Module A1 BWA fuzzing environment was recovered on 2026-08-09 from
the original VirtualBox research VM.

Before any public-facing correction or integration, a complete private forensic
snapshot was created.

Private archive SHA-256:

`40b8b1136beba55905dc7be48acbc998c3e424c5141e084a886845826de48beb`

The archive checksum, gzip integrity, and tar readability were independently
verified at archive creation.

## Recovered software identity

- Software: BWA
- Repository: `https://github.com/lh3/bwa.git`
- Git commit: `91fb301a50e64afee7653d312a9487c2ba0d452e`
- Git describe: `v0.7.19-1-g91fb301`
- Binary-reported version: `Version: 0.7.19-r1273`

## Recovered authoritative findings

Two sanitizer-confirmed root causes are retained as the canonical A1 findings:

### A1_F01

- function: `ksw_extend2`
- source: `ksw.c:428`
- observed sanitizer class: heap-buffer out-of-bounds READ
- public classification: CWE-125 Out-of-bounds Read

### A1_F02

- function: `mem_aln2sam`
- source: `bwamem.c:906`
- observed sanitizer class: global/static-storage out-of-bounds READ
- public classification: CWE-125 Out-of-bounds Read

## Provenance model

Raw evidence remains private.

The public package records hashes of the authoritative private files so later
integrity checks can demonstrate that the published interpretation corresponds
to the preserved recovery snapshot without distributing crash-inducing inputs.

## Relationship to GenoPhylax integration

A1 remains:

`STANDALONE_NON_GRI`

Recovery of A1 evidence is intended to resolve provenance for the C2 evidence
registry rows A1_E01 through A1_E04.

It does not modify the validated F11 or Privacy Base GRI mathematics and does not
require reopening C3, C4, V6, V7, or V8 numerical results.

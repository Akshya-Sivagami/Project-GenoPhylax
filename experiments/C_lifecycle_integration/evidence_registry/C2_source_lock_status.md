# C2 Authoritative Source-Lock Status

## Current status

`DRAFT_SOURCE_REVIEW_REQUIRED`

C2 is structurally valid and covers A1, A2, A3, B1, B2 and B3.

It contains 20 evidence records.

It is not yet authoritative-source locked.

---

## Strong candidate mappings

The first-pass resolver produced strong repository candidates for principal A2,
A3 and B1 evidence records.

These still require final human inspection before publication use, but they are
module-consistent and result-specific.

---

## Unresolved or unsuitable mappings

### A1_E01 through A1_E04

The automatic searches did not locate authoritative A1 result files using the
expected exact terms.

Proposed matches pointing into A2, A3 or third-party environment files are
invalid.

These rows remain unresolved until:

1. original A1 findings and ASAN summaries are located in Git;
2. small authoritative A1 summaries are recovered and committed;
3. or an evidence snapshot is reconstructed from retained original logs.

A1 findings must not be assigned to unrelated A2 or A3 files.

### B2_E01

The automatic resolver did not locate a clean textual result containing the
claimed unrecoverability value of 0.044.

The search also surfaced a different value of 0.215 in research notes.

The value 0.044 must therefore be reverified before final use.

### B2_E02 and B2_E03

The lifetime-risk implementation is a plausible computational source, but exact
year-threshold values should be regenerated into a compact machine-readable
results table.

### B3_E01 through B3_E03

Implementation scripts are plausible computational sources, but compact
machine-readable result tables should be regenerated before source lock.

The current search was contaminated by numeric substring matches in Python
environments and third-party packages.

---

## Search-quality limitation

Future source discovery must exclude:

- site-packages directories;
- environment directories;
- plotting environments;
- the POD5 environment;
- Python cache directories.

Searches must match numerical claims with semantic context rather than raw
numeric substrings.

---

## Migration decision

The Module C foundation may be committed and moved to local WSL while C2
remains explicitly marked as a draft.

Authoritative source locking will be completed locally using:

- Git-tracked evidence files;
- regenerated compact B2 and B3 result tables;
- recovered A1 evidence files or original source logs.

C3 Handoff Vector scoring and C4 GRI implementation must not begin before the
source lock is complete.

# A1 BWA Fuzzing — Recovered Campaign Reconstruction

## Recovery status

The original A1 fuzzing environment was recovered on 2026-08-09 from the
original VirtualBox research VM.

A complete private forensic snapshot was created and cryptographically verified
before this sanitized public provenance package was prepared.

The recovered environment contains multiple AFL/AFL++ campaign directories.
Their target attribution was determined from their surviving filesystem paths
and `fuzzer_stats` metadata.

---

## Canonical primary BWA ASAN campaign

The strongest preserved BWA AddressSanitizer campaign is:

`fuzz_output/bwa_asan/default/fuzzer_stats`

Recovered metadata:

- target: BWA
- instrumentation: AddressSanitizer
- executions: 963,339
- runtime: 23,120 seconds
- runtime: approximately 6.42 hours
- AFL bitmap coverage: 15.44%
- saved crash artifacts: 521
- stability: 99.50%

This is the canonical preserved campaign used when one representative A1 BWA
ASAN campaign statistic is required.

---

## Other preserved BWA campaigns

### Earlier / backup BWA ASAN state

`fuzz_output/bwa_asan_backup/default/fuzzer_stats`

- executions: 207,707
- runtime: 2,284 seconds
- AFL bitmap coverage: 14.93%
- saved crashes: 101

This is retained as supporting historical BWA ASAN metadata.

### BWA ASAN restart/fixed snapshot

`fuzz_output/bwa_asan_fixed/default/fuzzer_stats`

- executions: 3,567
- recorded runtime: 0 seconds
- AFL bitmap coverage: 13.27%
- saved crashes: 0

Because the preserved metadata reports zero runtime together with thousands of
executions and an implausible instantaneous execution rate, this row is treated
as a restart/fixed snapshot.

It must not be used to calculate campaign duration, throughput, or aggregate
execution-time statistics.

### Non-ASAN BWA campaign

`fuzz_output/bwa/default/fuzzer_stats`

- executions: 177,601
- runtime: 2,411 seconds
- AFL bitmap coverage: 15.38%
- saved crashes: 149

This is supporting non-ASAN BWA fuzzing evidence and is not interchangeable with
the canonical ASAN campaign.

---

## Non-BWA campaigns excluded from A1 BWA statistics

Two recovered `fuzzer_stats` files belong to Samtools:

- `fuzz_output/samtools/default/fuzzer_stats`
- `fuzz_output/samtools_fuzz/default/fuzzer_stats`

Their 0.52% bitmap coverage values are therefore not BWA coverage measurements.

They are preserved in the reconstruction table for provenance completeness but
are explicitly classified:

`EXCLUDED_NON_BWA`

They must not be used when reporting A1 BWA execution counts, runtime, coverage,
or crash statistics.

---

## Correction of historical BWA coverage

Earlier project notes reported:

`17.69% BWA coverage`

The recovered authoritative BWA campaign metadata does not support this value.

Preserved BWA bitmap coverage values are:

- 14.93% — earlier/backup BWA ASAN state
- 15.44% — canonical primary BWA ASAN campaign
- 13.27% — ASAN restart/fixed snapshot
- 15.38% — non-ASAN BWA campaign

Therefore:

**15.44% is the canonical preserved primary BWA ASAN bitmap coverage.**

The historical 17.69% value is superseded and must not be reported as canonical
BWA coverage.

---

## Historical aggregate execution count

Earlier notes reported approximately:

`2.5 million executions`

The recovered environment contains multiple campaign directories, restarts,
backups, and different targets.

These values must not simply be summed because doing so could combine:

- campaign restarts;
- earlier/backed-up states;
- overlapping corpus states;
- ASAN and non-ASAN experiments;
- non-BWA targets.

Therefore the approximately 2.5 million figure remains historical-only unless a
separate provenance-safe reconstruction demonstrates it independently.

For publication, the strongest directly preserved BWA ASAN campaign is reported
instead:

**963,339 executions over approximately 6.42 hours.**

---

## Crash artifacts versus root causes

AFL saved-crash counts are not equivalent to distinct vulnerabilities.

Similarly:

- crash files;
- unique crash-input hashes;
- sanitizer failures;
- source-level root causes;

are different quantities and must not be conflated.

The recovered evidence currently supports exactly:

**Two distinct ASAN-confirmed source-level out-of-bounds-read findings.**

Those two findings are the scientifically relevant A1 root-cause count.

Raw crash-inducing inputs remain private and are excluded from this public
provenance package.

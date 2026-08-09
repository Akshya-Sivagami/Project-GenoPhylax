# A1 — Publication Claims and Limitations

## Supported finding statement

The recovered A1 evidence supports two distinct AddressSanitizer-confirmed
out-of-bounds read findings in the tested BWA build:

1. `ksw_extend2` at `ksw.c:428`
   - heap-backed out-of-bounds read
   - ASAN reports a read access
   - appropriate weakness family: CWE-125

2. `mem_aln2sam` at `bwamem.c:906`
   - global/static-storage out-of-bounds read
   - ASAN reports a read access
   - appropriate weakness family: CWE-125

## Claims that are NOT established

The recovered evidence does not establish:

- arbitrary code execution;
- remote code execution;
- memory-write corruption;
- control-flow hijacking;
- exploitability beyond process failure / sanitizer-detected invalid read;
- patient harm;
- clinical record poisoning;
- successful SAM poisoning;
- compromise of a production sequencing system.

The findings therefore must not be described as demonstrated RCE or demonstrated
memory-write corruption.

## Terminology

Preferred:

- ASAN-confirmed out-of-bounds read
- memory-safety defect
- heap-backed out-of-bounds read
- global/static-storage out-of-bounds read
- CWE-125

Avoid unless independently established:

- exploitable vulnerability
- arbitrary code execution
- RCE
- memory corruption write
- CVE-class vulnerability
- patient-impacting exploit

No CVE identifier has been assigned by this provenance record.

## Novelty boundary

The appropriate novelty formulation is:

"To our knowledge, no prior public report was found for these exact two recovered
root causes as of 2026-08-09."

This statement applies only to the exact recovered source locations/root causes.

It does NOT claim:

- that BWA has never previously had vulnerabilities;
- that BWA has never previously been fuzzed;
- that `mem_aln2sam` has never appeared in another fuzzing report;
- that these are the first vulnerabilities ever discovered in BWA.

Novelty should be re-checked immediately before paper submission or public disclosure.

## Responsible-disclosure boundary

The public GenoPhylax repository may contain:

- sanitized finding classifications;
- software/version provenance;
- aggregate campaign metadata;
- cryptographic hashes of private evidence;
- methodological limitations;
- corrected publication wording.

It should NOT currently contain:

- raw crash-inducing inputs;
- exact triggering byte sequences;
- reproducer files;
- detailed exploit-development instructions;
- private raw ASAN trace files where those traces expose trigger/reproduction details.

The complete recovered evidence remains preserved privately pending disclosure decisions.

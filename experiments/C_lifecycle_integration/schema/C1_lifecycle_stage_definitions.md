# Module C1 — Canonical Lifecycle Stage Definitions

## Status

`LOCKED_FOR_C2_EVIDENCE_REGISTRY`

## Purpose

This document defines the canonical lifecycle stages used by Module C to connect the completed GenoPhylax A and B modules. It defines the integration vocabulary only; it does not assign GenoPhylax Risk Index weights or claim clinical validation.

## Canonical sequence

```text
S1 Raw Signal
  -> S2 Basecalling
  -> S3 Alignment
  -> S4 Variant Calling
  -> S5 Clinical Interpretation
  -> S6 Storage
  -> S7 Sharing
  -> S8 Graph Amplification
  -> S9 Lifetime Risk
  -> S10 Containment, Recovery and Audit
```

## Principal lifecycle handoff

The principal integrity-to-persistence handoff is **S5 -> S6**: an interpreted genomic result becomes a stored record governed by storage, access-control, disclosure and long-term persistence assumptions.

For the A3 F11 case, this is represented as a modelled transition from pathogenic-call suppression to possible storage of an apparently negative or incomplete result. The experiment did not place the corrupted result into a real clinical database and did not demonstrate patient harm.

## Stage definitions

### S1 — Sequencing and Raw-Signal Generation

**Domain:** Generation

**Primary assets:** biological sample; sequencer output; raw nanopore signal; POD5 or equivalent raw-signal files.

**Primary operations:** sample acquisition; sequencing; signal measurement; raw-data generation.

**Representative failures:** sample manipulation; malicious biological input; localized signal perturbation; raw-data corruption.

**Project evidence:** A2, A3.

**Security properties:** integrity; authenticity; provenance.

**Scope:** Begins when a biological sample or sequencer produces a digital raw-signal representation.

### S2 — Basecalling and Read Generation

**Domain:** Generation

**Primary assets:** basecalled reads; FASTQ; basecall quality values; move-table metadata.

**Primary operations:** signal-to-base translation; quality estimation; read segmentation.

**Representative failures:** base substitution; insertion; deletion; read splitting; adversarial basecall degradation.

**Project evidence:** A2, A3.

**Security properties:** integrity; traceability; reproducibility.

**Scope:** Covers transformation of raw sequencing signal into nucleotide reads.

### S3 — Alignment and Genomic Evidence Construction

**Domain:** Computation

**Primary assets:** SAM or BAM records; mapping coordinates; mapping quality; pileup evidence.

**Primary operations:** reference alignment; read placement; evidence aggregation.

**Representative failures:** memory-safety failure; incorrect alignment; evidence displacement; malformed-input processing.

**Project evidence:** A1, A2, A3.

**Security properties:** integrity; availability; memory safety.

**Scope:** Creates reference-relative evidence used by downstream variant callers.

### S4 — Variant Calling and Genotype Inference

**Domain:** Computation

**Primary assets:** VCF or BCF records; genotypes; allele support; variant quality.

**Primary operations:** variant detection; genotype inference; call filtering.

**Representative failures:** false-negative call; false-positive call; genotype alteration; call suppression.

**Project evidence:** A2, A3.

**Security properties:** integrity; correctness; provenance.

**Scope:** Produces discrete variant and genotype records from aligned evidence.

### S5 — Clinical Annotation and Interpretation

**Domain:** Interpretation

**Primary assets:** annotated variants; clinical significance; condition associations; interpretive reports.

**Primary operations:** database annotation; pathogenicity interpretation; clinical reporting.

**Representative failures:** missed pathogenic variant; incorrect clinical interpretation; false reassurance; unsupported disease inference.

**Project evidence:** A3.

**Security properties:** clinical integrity; semantic correctness; auditability.

**Scope:** Maps computational calls to clinical or biological meaning. Project evidence represents potential interpretation risk and not a demonstrated patient diagnosis.

### S6 — Storage and Access Control

**Domain:** Persistence

**Primary assets:** raw sequences; variant records; clinical annotations; derived genomic layers.

**Primary operations:** database entry; vault storage; access control; selective disclosure.

**Representative failures:** storage of corrupted records; unauthorized access; over-disclosure; insufficient unrecoverability.

**Project evidence:** B2, B3.

**Security properties:** confidentiality; integrity; unrecoverability; access control.

**Scope:** This is the principal handoff from generation-time integrity risk to persistent storage and privacy risk.

### S7 — Sharing and Secondary Use

**Domain:** Distribution

**Primary assets:** shared genomic records; derived reports; research datasets; relative-matching outputs.

**Primary operations:** data sharing; secondary analysis; platform disclosure; dataset replication.

**Representative failures:** uncontrolled replication; purpose expansion; metadata leakage; propagation of corrupted information.

**Project evidence:** B1, B2.

**Security properties:** confidentiality; consent; purpose limitation; provenance.

**Scope:** Covers movement of genomic information beyond its original storage or processing context.

### S8 — Familial and Population Amplification

**Domain:** Amplification

**Primary assets:** kinship links; relative records; population graphs; relationship inferences.

**Primary operations:** relative matching; kinship inference; graph traversal; population exposure propagation.

**Representative failures:** non-consensual familial exposure; graph-amplified breach; relationship inference; population-scale propagation.

**Project evidence:** B1, B3.

**Security properties:** collective privacy; containment; consent.

**Scope:** Represents risk expansion through biological relationships and platform graph structure.

### S9 — Long-Term Persistence and Re-identification

**Domain:** Persistence

**Primary assets:** replicated genomic data; identity linkages; historical disclosures; persistent biological identifiers.

**Primary operations:** long-term retention; future database linkage; re-identification; cumulative secondary use.

**Representative failures:** irreversible exposure; future re-identification; cumulative privacy loss; long-lived familial harm.

**Project evidence:** B2.

**Security properties:** persistence control; future privacy; revocability.

**Scope:** Models the time-dependent increase or persistence of genomic risk.

### S10 — Containment, Recovery and Audit

**Domain:** Response

**Primary assets:** audit logs; trusted source data; containment boundaries; authentication evidence.

**Primary operations:** detection; boundary isolation; access revocation; record recovery; provenance verification.

**Representative failures:** late detection; insufficient containment; loss of trusted provenance; irrecoverable corrupted record.

**Project evidence:** B3, A1, A2, A3.

**Security properties:** detectability; recoverability; accountability; resilience.

**Scope:** Represents preventive and corrective controls across the lifecycle.

## Schema constraints

- Stage IDs are stable and ordered from S1 through S10.
- Evidence records may map to one or more stages.
- Handoff records must identify both a source and destination stage.
- Experimental evidence and modelled propagation must remain distinguishable.
- No composite GRI score is valid until evidence normalization, confidence handling and sensitivity analysis are defined.

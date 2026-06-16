# Project GenoPhylax

**A Unified Cyber-Biosecurity Framework Across the Genomic Data Lifecycle**

*From Molecule to Population: Generation-Time Attacks, Storage Vaulting, and Graph-Amplified Breach Containment*

---

## Overview

Project GenoPhylax is a cyber-biosecurity research initiative focused on modeling genomic security risks across the complete lifecycle of genomic data.

Current genomic security research largely studies two domains independently:

1. Generation-time threats
    - Sequencing pipeline vulnerabilities
    - Memory-safety issues in bioinformatics software
    - Adversarial DNA attacks against ML-based basecallers and variant callers
2. Storage and sharing-time threats
    - Genomic privacy leakage
    - Re-identification attacks
    - Kinship graph amplification
    - Credential compromise and unauthorized access

GenoPhylax proposes a unified lifecycle framework that connects these traditionally separate threat surfaces into a single model.

The project introduces the **GenoPhylax Risk Index (GRI)**, a lifecycle-aware quantitative framework that evaluates genomic cyber-biosecurity risk across generation, processing, storage, sharing, and access-control stages.

---

## Research Objectives

### Objective 1

Identify vulnerabilities within genomic sequencing and bioinformatics pipelines.

### Objective 2

Evaluate adversarial manipulation risks in ML-based genomic workflows.

### Objective 3

Model graph-amplified exposure dynamics observed in large-scale genomic breaches.

### Objective 4

Design privacy-preserving storage and selective-disclosure mechanisms.

### Objective 5

Develop the GenoPhylax Risk Index (GRI).

### Objective 6

Create the first unified lifecycle-aware cyber-biosecurity framework spanning genomic data generation through population-scale exposure.

---

## Core Research Modules

### Module A1 — Memory Safety Audit

Static analysis and fuzzing of:

- BWA
- SAMtools
- GATK
- BLAST
- Minimap2

Deliverables:

- Vulnerability taxonomy
- Security assessment
- Potential CVE-class findings

---

### Module A2 — Adversarial DNA & ML Pipeline Attacks

Target systems:

- Bonito
- Guppy
- DeepVariant

Deliverables:

- Adversarial sequence library
- Attack benchmark results
- Model robustness evaluation

---

### Module A3 — Clinical Consequence Mapping

Deliverables:

- Variant-impact analysis
- ClinVar mapping
- ACMG classification impact
- Misdiagnosis case studies

---

### Module B1 — Graph Amplification Model

Deliverables:

- Kinship graph modeling
- Breach amplification analysis
- 23andMe calibration study

---

### Module B2 — Lifetime Risk & GenomicVault

Deliverables:

- Lifetime genomic risk framework
- Selective disclosure architecture
- Privacy proof methodology

---

### Module B3 — Graph-Aware Containment & Continuous Authentication

Deliverables:

- Exposure containment algorithms
- Genomic-specific authentication framework
- Credential-stuffing mitigation strategies

---

### Module C — Lifecycle Risk Synthesis & GRI

Deliverables:

- Unified lifecycle model
- GRI methodology
- Risk scoring framework
- Validation methodology
- Integrated cyber-biosecurity taxonomy

---

## GenoPhylax Risk Index (GRI)

GRI evaluates a:

(record, pipeline)

pair rather than a genomic record alone.

### Risk Dimensions

| ID | Dimension |
| --- | --- |
| D1 | Identity Risk |
| D2 | Disease Inference Risk |
| D3 | Familial Cascade Risk |
| D4 | Accessibility Risk |
| D5 | Persistence Risk |
| D6 | Amplification Risk |
| D7 | Pipeline Exposure Risk |

The final GRI framework will provide a unified quantitative measure of genomic cyber-biosecurity risk across the complete data lifecycle.

---

## Repository Structure

```
Project-GenoPhylax/

│
├── docs/
│   ├── roadmap/
│   ├── mentor_deliverables/
│   ├── literature_reviews/
│   ├── diagrams/
│   └── presentations/
│
├── research/
│   ├── genomic_privacy/
│   ├── dna_attacks/
│   ├── graph_models/
│   ├── risk_index/
│   └── notes/
│
├── datasets/
│   ├── metadata/
│   └── dataset_comparisons/
│
├── experiments/
│   ├── A1_memory_audit/
│   ├── A2_adversarial_dna/
│   ├── A3_clinical_mapping/
│   ├── B1_graph_amplification/
│   ├── B2_vault_design/
│   ├── B3_authentication/
│   └── GRI_validation/
│
├── paper/
│   ├── drafts/
│   ├── figures/
│   └── references/
│
└── README.md
```

---

## Current Status

### Mentor Roadmap Progress

- [ ]  Genomics Fundamentals
- [ ]  Cyber-Biosecurity Fundamentals
- [ ]  Genomic Privacy Survey
- [ ]  Genomic Leakage Survey
- [ ]  Dataset Analysis
- [ ]  Threat Modeling
- [ ]  Leakage Taxonomy
- [ ]  Gap Analysis
- [ ]  GenoPhylax Risk Index
- [ ]  GRI Validation
- [ ]  DNA Attack Survey
- [ ]  Sequencing Architecture
- [ ]  Attack Surface Model
- [ ]  Unified Lifecycle Framework
- [ ]  Final Problem Definition
- [ ]  Conference Paper Draft

---

## Target Outcomes

### Academic

- Conference submission
- Journal submission
- Research poster
- Technical report

### Technical

- GenoPhylax Risk Index (GRI)
- Graph Amplification Framework
- GenomicVault Prototype
- Threat Modeling Toolkit

### Open Source

- Research artifacts
- Diagrams
- Reproducible experiments
- Public documentation

---

## Disclaimer

This repository is intended for academic and defensive cyber-biosecurity research.

No work contained within this repository should be used against real-world genomic systems or healthcare infrastructure.

---

## Project Status

Active Research & Development
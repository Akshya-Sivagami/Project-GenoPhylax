# RESEARCH PROPOSAL: Project Genophylax

**A Unified Cyber-Biosecurity Framework Across the Genomic Data Lifecycle**

*From Molecule to Population: Generation-Time Attacks, Storage Vaulting, and Graph-Amplified Breach Containment*

- **Field:** Cyber-Biosecurity | Bioinformatics Security | Adversarial ML | Genomic Privacy | Applied Cryptography

## 1. Executive Summary

Genomic data is vulnerable at two very different moments, and existing research tends to treat them as unrelated problems. At the moment a sample is generated, the same kinds of weaknesses found in ordinary software exist inside the bioinformatics tools that turn raw sequencer signal into usable genetic data — memory-safety bugs in widely used pipeline tools, and machine-learning basecallers and variant callers that can be deliberately fed input designed to make them produce a wrong but plausible-looking result. Once genomic data exists in a database or sharing platform, it faces a second, very different category of risk: the 23andMe breach of 2023 is the clearest public example, where around 14,000 compromised accounts ended up exposing the genetic data of roughly 6.9 million people, because compromising one account exposes an entire network of biological relatives through kinship-sharing features.

These two risks are normally studied in isolation — generation-time software security on one side, breach and privacy research on the other — but they describe two ends of the same record's life. A variant call corrupted at the moment of generation doesn't just risk a misdiagnosis for one patient; it becomes a poisoned record that flows into storage and sharing infrastructure, where it is subject to exactly the same amplification dynamics as a record exposed through a conventional breach. No existing framework currently connects these two stages.

This project, Project Genophylax, proposes the first framework to model the complete genomic data lifecycle as a single, connected threat surface — from the physical DNA sample, through machine-learning-based sequencing, into storage and controlled disclosure, through relative-sharing features, to the authentication layer protecting access to all of it. 

To operationalize this lifecycle perspective, Project Genophylax introduces the **GenoPhylax Risk Index (GRI)**, a lifecycle-aware quantitative framework for assessing genomic cyber-biosecurity risk. Rather than scoring genomic records in isolation, GRI evaluates the risk associated with a genomic record moving through a specific processing, storage, and sharing pipeline, enabling risks from generation-time compromise and storage-time exposure to be assessed within a common framework.

Rather than treating generation-time security and storage-time privacy as two separate problems, Genophylax treats them as one problem viewed at two different points in time, and builds a single model spanning both.

## 2. The Core Insight

The output of a generation-time attack — a corrupted but plausible-looking genetic record — is structurally identical to the input of a storage-and-sharing-time breach: a record entering a database, being copied, shared with relatives, and protected (or not) by an authentication system. Whether a record reaches that storage layer because it was poisoned upstream or because an account was compromised downstream, it is subject to exactly the same graph-amplification dynamics once it gets there. Studying either half in isolation misses that handoff point entirely — closing that gap is what this project sets out to do.

## 2.1 The GenoPhylax Risk Index (GRI)

The GenoPhylax Risk Index (GRI) is the project's central quantitative framework.

Existing genomic privacy metrics typically focus on isolated dimensions such as re-identification risk or data leakage. GRI instead evaluates genomic cyber-biosecurity risk across the complete lifecycle of a genomic record, incorporating both generation-time compromise and storage-time exposure.

### Unit of Analysis

GRI evaluates a:

**(record, pipeline)**

pair rather than a genomic record alone.

The same genomic sequence may present radically different risk depending on how it is generated, processed, stored, shared, and protected.

### GRI Dimensions

### D1 — Identity Risk

Likelihood that an individual can be re-identified from genomic information.

Examples:

- genealogy matching
- demographic linkage
- public database correlation

---

### D2 — Disease Inference Risk

Ability to infer medical conditions, predispositions, or health traits.

Examples:

- pathogenic variants
- polygenic risk scores
- phenotype prediction

---

### D3 — Familial Cascade Risk

Intrinsic exposure risk inherited by biological relatives.

Examples:

- kinship inference
- inherited variants
- family-based re-identification

---

### D4 — Accessibility Risk

Ease with which unauthorized entities may gain access to genomic information.

Examples:

- credential compromise
- weak authentication
- access-control failures

---

### D5 — Persistence Risk

Difficulty of mitigating exposure once information has been disclosed.

Examples:

- immutable biology
- replicated datasets
- secondary sharing

---

### D6 — Amplification Risk

Exposure multiplier created by platform architecture.

Examples:

- DNA-relative matching
- kinship graph topology
- relationship-discovery features

This dimension is calibrated using Module B1 and real-world breach events such as 23andMe.

---

### D7 — Pipeline Exposure Risk

Probability that a genomic record was compromised during generation or processing.

Examples:

- memory-safety vulnerabilities
- adversarial DNA
- sequencing-pipeline attacks
- variant-calling manipulation

This dimension is informed by Modules A1 and A2.

### 2.2 The Genomic Data Lifecycle Threat Surface

| **Lifecycle Stage** | **What Happens** | **Why It Connects Forward** |
| --- | --- | --- |
| **1. Sample & Sequencing** | Physical DNA sample is sequenced; bioinformatics tools (BWA, SAMtools, GATK) process raw signal into reads. Memory-safety vulnerabilities can be triggered here. | A corrupted read at this stage propagates into every downstream record — it is the root of the chain. |
| **2. Basecalling & Variant Calling** | ML models (Bonito, DeepVariant) translate signal to bases and call variants. Adversarially designed DNA corrupts this translation, producing a wrong but plausible-looking variant call. | This corrupted record is now indistinguishable from a real variant call — it gets stored and shared as if legitimate. |
| **3. Clinical Interpretation** | The corrupted variant call leads to a misdiagnosis: pathogenic SNV called benign, cancer mutation suppressed, wrong pharmacogenomic dosage. | Patient-level harm is realised here — but the record itself now persists, poisoned, in downstream databases. |
| **4. Storage & Database Entry** | The (potentially poisoned) record enters storage. A selective disclosure vault would normally protect raw sequences — but a record corrupted upstream defeats data-quality assumptions the vault was not designed to catch. | **This is the handoff point:** attack output becomes data-integrity problem. |
| **5. Sharing & Kinship Graph** | Record (corrupted or legitimately breached) propagates through DTC kinship graphs (DNA Relatives-style features), exposing relatives who never consented. | Amplification factor compounds whatever entered the system — a poisoned record or a credential-stuffing breach both ride the same graph. |
| **6. Platform Access & Auth** | Credential stuffing or account takeover provides the entry point for graph-amplified breaches (23andMe ground truth). | Closes the loop: weak authentication is the access vector that activates the graph amplification risk modelled in Stage 5. |

> 💡 **The Hinge Point:** Stage 4 is where a generation-time attack becomes a storage-and-sharing problem. No paper in either the bioinformatics security or genomic privacy literature currently models this handoff.
> 

## 3. Integrated Novelty Assessment

Each module is independently novel, as established in the original proposals. The table below isolates what additional novelty emerges specifically from integration — this is the part that did not exist before today and is the actual case for merging.

| **Contribution** | **Individually Novel Because** | **Jointly Novel Because** |
| --- | --- | --- |
| **Dual-surface generation attack** | No paper audits production bioinformatics tools + attacks ML basecallers together | First work to show generation-time attacks don't just cause local misdiagnosis — they poison records that propagate through sharing infrastructure |
| **Graph amplification model** | No formal model of kinship-graph-mediated breach amplification exists, despite 23andMe being the largest genomic breach in history | First model to treat graph amplification as agnostic to root cause — equally describing a credential-stuffing breach AND an upstream data-poisoning attack |
| **Selective disclosure vault** | No vault design proves raw sequence unrecoverability while only exposing derived markers | First vault design that must also account for upstream record integrity — disclosure guarantees mean nothing if the underlying call was already corrupted at generation |
| **End-to-end threat taxonomy** | Neither generation-time security nor storage/sharing-time privacy has a unified taxonomy on its own | **THE central contribution:** first cyber-biosecurity framework spanning the full genomic data lifecycle from physical molecule to population-scale breach — defining a new field rather than patching one stage of it |

## 4. Proposed Methodology — Six Modules, One Framework

Modules A1-A3 and B1-B3 remain individually well-scoped and independently publishable as fallback positions. Module C is the connective theoretical work that transforms the project from a collection of modules into a unified cyber-biosecurity framework.

| **Mod.** | **Module** | **Core Work** | **Output** |
| --- | --- | --- | --- |
| **A1** | Memory Safety Audit | Static analysis + fuzzing (AFL++, Semgrep) on BWA, SAMtools, GATK, BLAST, Minimap2 for exploitable vulnerabilities via malicious DNA input | Vulnerability report; CVE-class findings; severity taxonomy |
| **A2** | Adversarial DNA + ML Pipeline Attack | Design biologically plausible adversarial DNA; attack Bonito/Guppy basecalling and DeepVariant variant calling; quantify corruption rate | Adversarial sequence library; attack success benchmarks |
| **A3** | Clinical Consequence Mapping | Map induced variant errors to ClinVar/ACMG pathogenicity classes; demonstrate concrete misdiagnosis scenarios | Clinical risk assessment; worked misdiagnosis case studies |
| **B1** | Graph Amplification Model | Formal model of kinship-graph breach amplification; calibrate against 23andMe ground truth (14K accounts to 6.9M exposed) | Validated amplification model; quantified blast-radius risk surface |
| **B2** | Lifetime Risk + Selective Disclosure Vault | Time-dependent privacy risk function; vault design exposing only derived markers, never raw sequence, with formal unrecoverability proof | Lifetime risk projections; open-source GenomicVault with privacy proof |
| **B3** | Graph-Aware Containment + Continuous Auth | Containment algorithm exploiting graph topology to minimise exposure; genomic-specific behavioural authentication defeating credential stuffing | Containment algorithm + simulation; auth framework with stuffing-detection benchmarks |
| **C** | Lifecycle Risk Synthesis & GRI Construction | Formal integration of generation-time compromise and storage-time exposure into a unified lifecycle-aware cyber-biosecurity framework. Develop the GenoPhylax Risk Index (GRI) as the quantitative instrument linking Modules A and B. | Unified lifecycle framework, GRI methodology, scoring model, validation methodology, and integrated cyber-biosecurity taxonomy |

### 4.1 Execution Order Recommendation

- **Parallel Execution:** A1 (audit) and B1 (graph model) can run in parallel from week one — neither depends on the other and both produce early concrete results, which matters for a 10-week mentor-credited timeline.
- **Sequential Follow-up:** A2-A3 and B2-B3 follow once tooling from A1/B1 is in place.
- **Iterative Work:** Module C — the integration — should be drafted iteratively throughout, not left to the end, since it is the section reviewers will scrutinise hardest.

## 5. Mapping to Mentor's Assigned Roadmap

Your mentor's 16-step roadmap and this merged paper are not competing tracks. The roadmap is the credentialed scaffolding; the paper is the destination her own Step 14 ("Connect Both Domains") already points to.

| **Step** | **Mentor's Roadmap Deliverable** | **Status** | **How It Maps to the Merged Paper** |
| --- | --- | --- | --- |
| **1** | Genomics fundamentals summary + presentation | To do — quick | Foundational; supports writing accessible background section for Nature-tier non-specialist readers |
| **2** | CyberBioSecurity basics presentation | To do — quick | Same — background section material |
| **3** | Literature survey: genomic privacy (10-15 papers) | Partially done | Already have: Harmanci & Gerstein 2018, Gymrek et al. 2013, Ayoz et al. 2021, NIST IR 8432. Need ~8-10 more for full coverage |
| **4** | Literature survey: genomic data leakage / re-ID / membership inference | Partially done | 23andMe breach corpus (ICO ruling, PIPEDA findings, regulatory filings) already gathered — strong real-world grounding |
| **5** | Dataset comparison sheet | To do | Maps directly to Resources section already drafted: 1000 Genomes, UK Biobank, ClinVar, PharmGKB, NCBI SRA |
| **6** | Threat modeling (assets, actors, attack surfaces) | Partially done | Covered by dual-surface taxonomy + graph/auth threat model — needs formatting into her requested diagram form |
| **7** | Leakage classification taxonomy (identity, disease, familial, metadata, AI) | To do — synthesis | Can be derived directly from existing novelty tables in both proposals; needs reformatting into her 5-category schema |
| **8** | Gap analysis document (2-3 pages) | Done — expand | Already produced in the Prior Work & Gap Analysis sections of both proposals — needs condensing to her format |
| **9** | GenoPhylax Risk Index (GRI)   | To do  | Central quantitative framework of the project. Synthesizes outputs from Modules A and B into a lifecycle-aware cyber-biosecurity metric spanning generation-time compromise and storage-time exposure. |
| **10** | Validate GRI using representative lifecycle scenarios. | To do | Validated using the 23andMe breach, adversarial sequencing scenarios, and integrated lifecycle simulations. |
| **11** | DNA attack papers survey (5-10 papers) | Done | UW 2017, Islam et al. 2022, FIMBA 2024, GenoArmory 2025 already identified and gap-analysed |
| **12** | Sequencing pipeline architecture diagram | To do | Maps directly to the Lifecycle Table (Section 3 of this document) — already conceptually built, needs visual diagram form |
| **13** | DNA attack surface model | Done | Covered by Modules A1-A3 |
| **14** | Connect both domains into unified model | **This IS the paper** | This is Module C — the central theoretical contribution of the merged paper. Her roadmap step 14 and your research goal are the same thing. |
| **15** | Final problem definition | Ready now | The Executive Summary + Problem Statement sections of this merged proposal directly satisfy this deliverable |
| **16** | Conference-ready paper draft | In progress | This merged proposal is the structural skeleton for that draft |

> 📊 **Net Position:** Roughly 5 of 16 steps are already substantially complete through the groundwork. The GenoPhylax Risk Index (GRI) now serves as the project's primary unifying deliverable, transforming the mentor's original scoring-framework requirement into a lifecycle-aware quantitative methodology that integrates outputs from all major modules. Rather than existing as a standalone rubric, GRI becomes the analytical bridge connecting generation-time compromise, storage-time exposure, and graph-amplified population risk.
> 
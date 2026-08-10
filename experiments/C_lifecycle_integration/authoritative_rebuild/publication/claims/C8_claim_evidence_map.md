# C8 Paper Claim–Evidence Map

Every claim below is derived from the authoritative C0–C5 rebuild.

## C5_F01

In the controlled HG002 F11 case, targeted PM2 perturbation reduced evaluable ALT-supporting parents from 14/14 in the clean condition to 0/14 on target, with downstream loss of the clinically relevant F11 variant call.

**Anchor:** 14/14 -> 0/14; downstream F11 call lost

**Evidence:** A3_E01|A3_E02|A3_E03|A3_E04|HF11_01|HF11_02

**Scope:** Single HG002 individual, one pathogenic F11 locus and one basecaller/perturbation configuration; no patient outcome was observed.

## C5_F02

The F11 experimental case scored D2=1.0 and D7=1.0 because the tested perturbation completely suppressed evaluable allele evidence and propagated through the observed S2->S4->S5 clinical-processing chain.

**Anchor:** F11 Base GRI=1.0000000000

**Evidence:** C4_normalized_dimensions|C4_base_gri

**Scope:** This is a case-level computational severity score, not a probability of clinical harm.

## C5_F03

The authoritative B2 model produced pathogenic-variant unrecoverability of 0.2299, 100% modelled re-identification by year 13 and 100% modelled familial exposure by year 15.

**Anchor:** unrecoverability=0.2299; re-ID=13y; familial=15y

**Evidence:** B2_E01|B2_E02|B2_E03

**Scope:** These are model-derived trajectories rather than observed longitudinal population outcomes.

## C5_F04

The authoritative B1 analysis used a 4,144-node graph with 1,657 registered nodes and produced calibrated mean familial amplification of 464.4x, corresponding to D6=0.898.

**Anchor:** 4144 nodes; 1657 registered; 464.4x; D6=0.898

**Evidence:** B1_E01|B1_E02

**Scope:** Amplification remains dependent on graph construction and calibration assumptions.

## C5_F05

Across applicable privacy dimensions D1, D3, D5 and D6, the authoritative Base GRI was 0.9373875000.

**Anchor:** D1=1.0000; D3=1.0000; D5=0.8516; D6=0.8980; Base=0.9373875000

**Evidence:** C4_normalized_dimensions|C4_base_gri

**Scope:** The score combines model-derived dimensions and should not be interpreted as an empirical population probability.

## C5_F06

When B2-derived dimensions were collapsed into one composite and weighted 50/50 against B1 amplification, the privacy sensitivity score remained high.

**Anchor:** 50/50 provenance sensitivity=0.9242583333

**Evidence:** C4_sensitivity_analysis

**Scope:** Sensitivity analysis is a robustness check and is not a confidence interval.

## C5_F07

B3 containment achieved 99.24% best reduction in the primary scenario, but fixed-k residual containment difficulty varied substantially by attack origin.

**Anchor:** M5 residual candidates at k=10: peripheral=0.008; mid-degree=0.795; hub=0.970

**Evidence:** B3_E01|B3_E02|HPRIV_04|C4_modifier_context

**Scope:** M5 values are scenario-specific residual candidates and are not multiplied into Base GRI.

## C5_F08

The final B3 credential-stuffing benchmark used threshold 3.6 and achieved F1=0.8387, but this performance is treated as access-control mitigation evidence rather than a direct measure of privacy-event detectability.

**Anchor:** threshold=3.6; F1=0.8387

**Evidence:** B3_E03|HPRIV_05|C4_modifier_context

**Scope:** Internal generated benchmark; M3 detectability remains UNMEASURED.

## C5_F09

A1 contributes standalone software-security evidence and A2 contributes supporting perturbation evidence, but neither is forced into the Base GRI where the required semantic mapping is not established.

**Anchor:** A1=STANDALONE_NON_GRI; A2=SUPPORTING_NON_GRI

**Evidence:** C2_authoritative_evidence_registry

**Scope:** Their exclusion from Base GRI is deliberate and should not be interpreted as lack of scientific relevance.

# GenoPhylax B1/B2 Validation Strengthening

Purpose:
Strengthen the existing frozen B1 and B2 model evidence without modifying
the authoritative experiments or their historical outputs.

## B1

Frozen authoritative result:
- calibrated mean amplification = 464.4x
- historical calibration target = 492.86x
- historical relative calibration error = 5.77%

Validation questions:
1. How variable is amplification across random seeds?
2. How sensitive is amplification to cousin probability?
3. How sensitive is amplification to registration rate?
4. How sensitive is amplification to propagation depth?
5. Does the reported 464.4x represent a stable region or a narrow fitted point?

Important:
The 464.4x result is a calibrated/modelled value, not a universal genomic
breach amplification factor.

## B2

Frozen authoritative outputs remain unchanged.

Validation questions:
1. How sensitive is unrecoverability to entropy-leakage assumptions?
2. How sensitive are lifetime horizons to database-growth assumptions?
3. How sensitive are lifetime horizons to inference-growth assumptions?
4. How stable is the year-50 D5 output across plausible parameter ranges?
5. Which assumptions dominate B2 output variance?

Important:
B2 lifetime horizons are model outputs, not observed real-world lifetimes.

## Rule

Nothing in this directory replaces or modifies:
- experiments/B1_graph_amplification
- experiments/B2_vault_design
- experiments/B_final_audit

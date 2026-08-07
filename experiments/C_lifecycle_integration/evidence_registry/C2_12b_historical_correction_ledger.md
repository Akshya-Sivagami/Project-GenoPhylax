# C2.12b Historical Correction Ledger

This ledger records retired GenoPhylax numerical claims that were corrected during the Module C evidence-source audit.

A retired value is not deleted from the project history. Instead, the correction reason, historical provenance status and authoritative replacement source are recorded explicitly.

## P01_B1_GRAPH_MISATTRIBUTION

- **module:** B1/B3
- **retired_claim:** B1 population graph reported as 3,303 nodes, 1,321 registered individuals and 786 baseline exposed.
- **retired_value:** 3303 nodes | 1321 registered | 786 exposed
- **current_claim:** Current committed B1 reproduction generates 4,144 nodes and 1,657 registered individuals. The 3,303 / 1,321 / 786 values belong to the B3 containment graph.
- **current_value:** B1: 4144 nodes | 1657 registered; B3: 3303 nodes | 1321 registered | 786 baseline exposed
- **retirement_reason:** Cross-module evidence misattribution.
- **historical_origin_status:** TRACED_TO_DIFFERENT_MODULE
- **due_diligence_performed:** Current repository and bounded Git-history audit performed; B1 and B3 authoritative reproductions compared directly.
- **supersession_basis:** The old values reproduce under B3, while the committed B1 analysis independently reproduces a different graph.
- **authoritative_source:** experiments/C_lifecycle_integration/evidence_registry/reproduced_results/B1_authoritative_results.tsv | experiments/C_lifecycle_integration/evidence_registry/reproduced_results/B3_reproduction_stdout.txt
- **date_corrected:** 2026-08-07

## P02_B2_UNRECOVERABILITY_0044

- **module:** B2
- **retired_claim:** Pathogenic Variants unrecoverability reported as 0.044.
- **retired_value:** 0.044
- **current_claim:** Current committed B2 model reproduces Pathogenic Variants single-tier unrecoverability as 0.2299.
- **current_value:** 0.2299
- **retirement_reason:** Retired value cannot be reproduced from the committed model.
- **historical_origin_status:** NOT_FOUND_IN_GIT_HISTORY
- **due_diligence_performed:** Current tracked B2 files searched; bounded Git pickaxe history searched for 0.044/.044; no source located.
- **supersession_basis:** Current committed implementation is reproducible and its parameters and outputs are archived under Module C.
- **authoritative_source:** experiments/C_lifecycle_integration/evidence_registry/reproduced_results/B2_authoritative_vault_results.tsv
- **date_corrected:** 2026-08-07

## P03_B2_REID_YEAR20

- **module:** B2
- **retired_claim:** Re-identification risk reported as reaching 100 percent by year 20.
- **retired_value:** 100% by year 20
- **current_claim:** Current committed B2 lifetime-risk model first reaches 100 percent re-identification at year 13.
- **current_value:** 100% first reached at year 13
- **retirement_reason:** Retired timing is not reproduced by the current committed lifetime-risk implementation.
- **historical_origin_status:** NOT_FOUND_IN_GIT_HISTORY
- **due_diligence_performed:** Current tracked B2 artifacts and bounded Git-history searches for the year-20 claim were performed; no source found.
- **supersession_basis:** Current lifetime-risk implementation reproduces the year-13 saturation threshold and preserves the full threshold trajectory.
- **authoritative_source:** experiments/C_lifecycle_integration/evidence_registry/reproduced_results/B2_authoritative_lifetime_results.tsv
- **date_corrected:** 2026-08-07

## P04_B3_AUTH_THRESHOLD

- **module:** B3
- **retired_claim:** Authentication threshold reported as 3.6 or 3.8 with older precision/recall/F1/accuracy metrics.
- **retired_value:** threshold 3.6/3.8 | F1 approximately 0.8409
- **current_claim:** Current committed B3 implementation uses threshold 4.5 with precision 1.0000, recall 0.9800, F1 0.9899 and accuracy 0.9960.
- **current_value:** threshold 4.5 | P=1.0000 | R=0.9800 | F1=0.9899 | Acc=0.9960
- **retirement_reason:** Retired threshold/metrics are not present in or reproduced by the current committed B3 implementation.
- **historical_origin_status:** NOT_FOUND_IN_GIT_HISTORY
- **due_diligence_performed:** Current B3 files and bounded Git-history searches for thresholds 3.6/3.8 and retired metrics were performed.
- **supersession_basis:** Current committed implementation and archived reproduction both produce threshold 4.5 and the current metric set.
- **authoritative_source:** experiments/C_lifecycle_integration/evidence_registry/reproduced_results/B3_authoritative_results.tsv
- **date_corrected:** 2026-08-07

## P05_B3_HUB_K20

- **module:** B3
- **retired_claim:** Hub-origin breaches were described as requiring k=20 for containment.
- **retired_value:** hub-origin requires k=20
- **current_claim:** Current attack-origin reproduction shows strong dependence on origin class and does not establish a universal k=20 requirement for hub-origin breaches.
- **current_value:** High-degree hub baseline=1077; k=10 reduction=2.0%; no universal k=20 requirement established
- **retirement_reason:** A historical top_k=20 implementation/default parameter was overinterpreted as an empirical requirement.
- **historical_origin_status:** TRACED_TO_OVERINTERPRETED_IMPLEMENTATION_PARAMETER
- **due_diligence_performed:** Git commit 75b5316 inspected; historical top_k=20 implementation context compared against current reproduced attack-origin results.
- **supersession_basis:** The implementation parameter is not itself evidence of a required containment threshold; current attack-origin analysis reports observed reductions by origin instead.
- **authoritative_source:** experiments/B3_authentication/containment_algorithm.py | experiments/C_lifecycle_integration/evidence_registry/reproduced_results/B3_reproduction_stdout.txt
- **date_corrected:** 2026-08-07


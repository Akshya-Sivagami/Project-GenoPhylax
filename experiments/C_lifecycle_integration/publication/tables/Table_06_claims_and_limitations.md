# Table 6 — Publication claims and limitations

| Claim | Evidence | Supported wording | Key limitation |
| --- | --- | --- | --- |
| A1 identified two source-level BWA out-of-bounds-read root causes. | E2 controlled empirical/software audit | Two ASAN-confirmed CWE-125 root causes | No RCE, arbitrary code execution, memory-write corruption or assigned CVE established. |
| Targeted F11 raw-signal perturbation suppressed ALT evidence in the tested worked case. | E2 controlled empirical case | All 14 clean ALT-supporting parents lost ALT under PM2; off-target sham retained 14/14. | Single locus/person/run/basecaller configuration; no external clinical validation. |
| Kinship can amplify genomic disclosure. | E3 calibrated model | 464.4× amplification in calibrated B1 model | Synthetic graph and configured calibration assumptions. |
| Genomic disclosure persists over long time horizons. | E4 internal model | Re-identification reached 100% by year 13 in the configured B2 simulation. | Model trajectory, not observed population incidence. |
| Containment can sharply reduce simulated exposure. | E4 internal model | k=10 reduced exposure from 786 to 6 in the principal B3 scenario. | Internal graph simulation; not real-world containment validation. |
| GRI synthesizes lifecycle severity with provenance retained. | Mixed E2/E3/E4 | F11 Base GRI=1.0000000000; Privacy Base GRI=0.9115102712. | GRI is severity representation, not probability of breach or patient harm. |

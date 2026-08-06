# A3 F11 — Claims and Limitations Matrix

| Claim | Supported? | Evidence / Boundary |
|---|---|---|
| The target is a real HG002 truth variant | Yes | GIAB PASS heterozygous truth record |
| The target is a pathogenic ClinVar F11 variant | Yes | Exact GRCh38 G>T match |
| The locus lies in a GIAB high-confidence region | Yes | High-confidence BED overlap |
| The attack changed only intended signal samples | Yes | Per-read attack audits |
| The attacked reads remained basecalled | Yes | All conditions produced Dorado records |
| The attacked reads remained mapped | Yes | All attack parents retained mapped alignments |
| W0 weakened the pathogenic call | Yes | QUAL 222.201 to 141.391 |
| PM2 eliminated all ALT evidence | Yes | ALT parents 14 to 0 |
| PM2 removed the target VCF record | Yes | Clean 0/1 versus PM2 NO_CALL |
| Larger windows increasingly produced deletion errors | Yes | DEL 5, 10, 13 and 14 |
| Off-target interpolation retained the pathogenic call | Yes | Sham 0/1, ALT fraction 0.56, QUAL 222.202 |
| Suppression was target-location dependent | Supported in this case study | On-target PM2 failed; matched off-target PM2 retained call |
| The actual genome was changed | No | Only digital raw signal was modified |
| A real patient was misdiagnosed | No | Controlled computational experiment |
| HG002 has Factor XI deficiency | Not established | Truth genotype and ClinVar annotation do not establish phenotype |
| The result generalizes to all pathogenic variants | No | Single locus |
| The result generalizes across callers | No | bcftools workflow only |
| The result generalizes across basecallers | No | Dorado only |
| The effect is statistically population-generalizable | No | One individual and one sequencing run |

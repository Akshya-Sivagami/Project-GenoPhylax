# B1 Validation Strengthening Summary

## Status

MODELLED / SENSITIVITY ANALYSIS

This analysis does not replace or modify the frozen historical B1 evidence.

## Historical frozen result

The historical calibration sweep selected cousin_prob=0.20 by minimizing
distance to the historical 23andMe amplification reference of 492.86x.

The resulting frozen calibrated mean was 464.4x, with a historical
calibration error of approximately 5.77%.

Because the same external value was used to select the parameter, this is
a calibration fit and must not be described as independent validation.

## Multi-seed finding

At the frozen structural configuration, single-entry breach simulations
were highly variable across random seeds.

30-seed experiment:
- mean amplification: 845.07x
- median amplification: 1197.50x
- sample SD: 517.70x
- range: 1x to 1357x
- 5th-95th percentile: 1x to 1302.70x

## Breach-entry Monte Carlo

Across 3,000 breach-entry realizations:
- mean amplification: 879.03x
- median amplification: 1122x
- range: 1x to 1395x
- 5th-95th percentile: 1x to 1337x
- fraction <=10x: 19.13%
- fraction >=500x: 80.13%

## Topology explanation

Across 30 independently generated registered graphs:
- mean giant-component fraction: 80.85%
- mean isolated-node fraction: 11.46%
- mean fraction in components of <=10 nodes: 19.15%
- mean 3-hop reach: 879.85 nodes

The approximately 19.15% of nodes in small components closely corresponds
to the approximately 19.13% of Monte Carlo breach entries producing <=10x
amplification.

This supports a topology/entry-point explanation for the bimodal exposure
behavior.

## Parameter sensitivity

Tested:
- cousin probability: 0.05, 0.10, 0.20, 0.30
- registration rate: 0.20, 0.40, 0.60
- propagation depth: 1, 2, 3 hops
- 5 graph seeds
- 50 breach-entry realizations per configuration

Total breach realizations: 9,000.

Lowest tested scenario mean:
- cousin_prob=0.05
- registration_rate=0.2
- hops=1
- mean amplification=4.35x

Highest tested scenario mean:
- cousin_prob=0.3
- registration_rate=0.6
- hops=3
- mean amplification=1621.63x

Historical-structure sensitivity configuration
(cousin_prob=0.20, registration=0.40, hops=3):
- mean amplification=944.04x
- median amplification=1178.50x
- 5th percentile=1.00x
- 95th percentile=1346.55x
- fraction >=500x=0.872

## Defensible conclusion

B1 demonstrates that exposure amplification can emerge from connectivity
in a synthetic registered kinship graph, but its magnitude is strongly
dependent on graph connectivity, platform registration, propagation depth,
and the initial breach entry point.

The historical 464.4x value is retained as a calibrated historical result.
It is not a universal amplification factor and is not treated as an
independent validation estimate.

The strengthened evidence therefore supports a RANGE- AND
TOPOLOGY-DEPENDENT amplification claim rather than a single universal
multiplier.

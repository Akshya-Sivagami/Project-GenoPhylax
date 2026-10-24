# GenoPhylax B3 Defense Validation Summary

## Status

PASS

Historical B3 files were not modified.

## Containment validation

Containment was evaluated across 20 explicitly seeded synthetic
kinship graphs using the historical B3 graph configuration.

### Peripheral-origin breaches

- >=99% reduction achieved in 20/20 seeds.
- Median minimum tested containment budget: k=4.
- Tested range: k=1-6.
- Mean reduction at k=10: 99.23%.

### Mid-degree-origin breaches

- >=99% reduction achieved in 20/20 seeds.
- Median minimum tested containment budget: k=10.
- Tested range: k=4-35.
- Mean reduction at k=10: 72.70%.

### Hub-origin breaches

- >=99% reduction achieved in 20/20 seeds.
- Median minimum tested containment budget: k=18.
- Tested range: k=12-22.
- Mean reduction at k=10: 1.91%.

### Containment interpretation

The validation does not support a universal containment threshold.

The required containment budget depends strongly on breach origin
and graph realization. Peripheral breaches were consistently
contained with small budgets, while hub-origin breaches required
substantially larger budgets.

The reported k ranges are model-validation ranges, not empirical
confidence intervals for real genomic platforms.

## Authentication validation

Authentication was evaluated across 100 independently generated
synthetic datasets.

Each session was assigned an anomaly score once. Threshold
selection was performed only on the development split and the
selected threshold was then evaluated on held-out sessions.

### Development-selected threshold

- Mean: 3.518
- Median: 3.500
- 5th-95th percentile: 3.100-3.900
- Range: 2.700-4.100

### Held-out performance

- Mean precision: 0.8840
- Mean recall: 0.8365
- Mean F1: 0.8555
- Mean accuracy: 0.9436

### Historical threshold 4.5

On the same held-out datasets:

- Mean precision: 0.9997
- Mean recall: 0.6825
- Mean F1: 0.8086

Threshold 4.5 therefore represents a conservative high-precision
operating point in this synthetic model, but it is not supported as
a universal or generally optimal threshold.

## Safe DEF CON framing

B3 demonstrates a modelled defensive concept: graph-aware
containment can sharply reduce simulated propagation, but the
required response budget depends on breach topology and origin.

The authentication component demonstrates an additional synthetic
detection control with a measurable precision-recall tradeoff.

These results are validation of the GenoPhylax simulation and
defense design. They are not measurements of production genomic
platforms and should not be presented as universal operational
performance.

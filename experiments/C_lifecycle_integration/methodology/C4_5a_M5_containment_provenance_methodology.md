# C4.5a M5 Containment Provenance Repair

## Reason for repair

The initial C4.5 modifier architecture correctly classified Privacy M5 as a
scenario envelope, but the generated numerical envelope contained only the
principal/peripheral 99.2 percent containment result.

That produced an apparent envelope of:

0.008 to 0.008 residual containment difficulty.

This did not represent the documented attack-origin heterogeneity.

## Correct interpretation

B3 containment performance depends strongly on attack origin.

The relevant scenarios are retained separately rather than collapsed into one
universal scalar.

For each scenario:

ResidualContainmentDifficulty =
    1 - containment_reduction_fraction

The resulting scenario values remain model-derived.

## No single M5 scalar

C4.5 does not select:

- the easiest scenario;
- the hardest scenario;
- the arithmetic mean;
- the median;
- any manually preferred scenario

as the universal Privacy M5 value.

The complete source-backed envelope is retained.

Later sensitivity analysis may evaluate how GRI conclusions change across this
range.

## Risk direction

0 = low residual containment difficulty

1 = high residual containment difficulty

## Correlation

Privacy M5 is related to B3 mitigation evidence already used for D4 context.

M5 is therefore not treated as an independent multiplier.

## Status

M5 scenario envelope: source-backed.

Single M5 scalar: NOT SELECTED.

M6: NOT DEFINED.

Final GRI: NOT COMPUTED.

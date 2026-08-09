# C4.3 Authoritative Source Extraction and Trajectory Reconstruction

## Purpose

C4.3 creates a machine-traceable numerical bridge between the locked C2/C3
evidence base and later GRI calculations.

The stage must not rely on manually re-entered remembered values when the
authoritative project artifact is available.

## Source hierarchy

Preferred sources are:

1. locked or reproduced authoritative numerical artifacts;
2. finalized experiment numerical summaries;
3. committed validated source outputs.

Narrative summaries are not preferred over numerical artifacts when both exist.

## Raw extraction

Each extracted value records:

- module;
- case;
- dimension;
- source file;
- raw value;
- unit;
- extraction status;
- source locator;
- interpretation note.

A value that cannot be resolved from the available authoritative source is
marked unresolved rather than silently substituted from memory.

## F11 D2

ALT-support loss is the primary severity metric.

The terminal genotype/call-loss endpoint is corroborating evidence only.

These measurements are not summed or averaged.

## B1 D6

The calibrated kinship amplification result is normalized relative to the
documented external calibration anchor using the C4.2 LOG_REFERENCE_RATIO.

The untuned/default B1 simulation result must not silently replace the
calibrated result.

## B2 lifetime trajectories

C4.3 attempts to reconstruct the complete annual probability trajectory from
the authoritative B2 lifetime artifact.

For each available trajectory, candidate summaries may be generated:

- terminal probability;
- maximum probability;
- mean probability;
- horizon-normalized trapezoidal area;
- first year at defined probability thresholds.

These are candidate descriptors only.

C4.3a does not select the final temporal scalarization.

## Temporal anti-cherry-picking rule

No single evaluation year may become the case-level severity because it gives a
preferred numerical result.

No terminal saturation value may automatically define severity.

The final temporal transform is selected only after complete trajectory
reconstruction and comparison.

## D7

F11 D7 remains structurally deferred.

Observed handoff count is not automatically converted to a risk score.

The eventual transform must distinguish:

- directly observed pipeline reach;
- terminal direct manifestation;
- modelled S5-to-S6 extension.

## Numerical status

F11 D2 normalized input: permitted when source extraction resolves.

Privacy D6 normalized input: permitted when calibrated B1 values resolve.

Privacy D1/D3/D5 temporal trajectories: reconstructed where source schema
permits.

Temporal scalarization: NOT SELECTED.

D7 scalarization: NOT SELECTED.

Dimension weights: NOT DEFINED.

Evidence weights: NOT DEFINED.

Final GRI: NOT COMPUTED.

# Experiment E — Cross-Locus Specificity Controls

## Objective

These controls tested whether the successful PM5 targeted raw-signal attack depended on:

1. sufficient local signal context around the target base; and
2. spatial proximity between the perturbed signal window and the intended genomic target.

The controls were performed at two independent heterozygous loci:

| Locus | Variant |
|---|---|
| L2 | chr1:20061156 A>T |
| L3 | chr4:40028853 A>G |

Each locus used ten clean ALT-supporting parent reads.

---

## Control 1 — W0 target-only perturbation

W0 modified only the raw-signal event assigned to the target nucleotide.

### Signal changes

| Locus | Reads | Changed samples | Changed percentage | Outside-window changes |
|---|---:|---:|---:|---:|
| L2 | 10 | 107 | 0.0036465% | 0 |
| L3 | 10 | 227 | 0.0075969% | 0 |

### Target effect

| Locus | Clean ALT parents | ALT retained | ALT changed |
|---|---:|---:|---:|
| L2 | 10 | 10 | 0 |
| L3 | 10 | 10 | 0 |

### Interpretation

A single target-base signal event was insufficient to alter Dorado's nucleotide prediction.

This supports the conclusion that nanopore basecalling depends on a local signal neighbourhood rather than one isolated event.

---

## Control 2 — Near off-target sham at +20 bases

The near sham used the same PM5-sized 11-base-event interpolation window but shifted its centre 20 bases downstream from the target.

The sham and target PM5 windows did not overlap. Their nearest edges were separated by nine base-events.

### Signal changes

| Locus | Reads | Changed samples | Changed percentage | Target-window overlaps |
|---|---:|---:|---:|---:|
| L2 | 10 | 1,350 | 0.0460076% | 0 |
| L3 | 10 | 1,172 | 0.0392226% | 0 |

### Target effect

| Locus | ALT retained | ALT changed | Result |
|---|---:|---:|---|
| L2 | 9 | 1 | One ALT-to-deletion transition |
| L3 | 10 | 0 | No effect |

### L2 audit

The changed L2 parent was:

`0dc565bd-d774-4920-a88a-a4c2ca842d02`

For this read:

- target base index: 9040;
- target PM5 base window: 9035–9045;
- sham centre: 9060;
- sham base window: 9055–9065;
- centre distance: 20 bases;
- nearest inter-window gap: 9 base-events;
- changed signal samples: 172;
- mapping remained MAPQ 60;
- the target changed from ALT to deletion.

The clean and sham alignments showed a local CIGAR reconfiguration while preserving the same high-confidence primary genomic mapping.

### Interpretation

The +20 sham was not a fully distant negative control.

The isolated L2 effect indicates that raw-signal perturbations can influence nearby sequence predictions beyond the exact edited base-event window. This is consistent with short-range basecalling context spillover.

---

## Control 3 — Distant off-target sham at +100 bases

The distant sham used the same 11-base-event interpolation mechanism but shifted its centre 100 bases away from the target.

### Signal changes

| Locus | Reads | Changed samples | Changed percentage | Target-window overlaps |
|---|---:|---:|---:|---:|
| L2 | 10 | 1,246 | 0.0424633% | 0 |
| L3 | 10 | 1,387 | 0.0464178% | 0 |

The signal-edit magnitude was comparable to the PM5-sized near sham, confirming that the distant control was not weaker merely because fewer signal samples were modified.

### Alignment preservation

| Locus | Primary records | Mapped primary records | MAPQ 60 primary records |
|---|---:|---:|---:|
| L2 | 10 | 10 | 10 |
| L3 | 10 | 10 | 10 |

L3 produced one additional supplementary alignment record, but all ten parent reads retained MAPQ 60 primary alignments.

### Target effect

| Locus | Clean ALT parents | ALT retained | ALT changed |
|---|---:|---:|---:|
| L2 | 10 | 10 | 0 |
| L3 | 10 | 10 | 0 |

No reads transitioned to:

- REF;
- deletion;
- another nucleotide;
- no coverage;
- unmapped status.

### Interpretation

The +100-base sham provides a clean spatial negative control.

A perturbation of comparable signal magnitude and identical window width had no effect on the intended target when positioned sufficiently far away.

---

## Combined interpretation

The three controls establish both a contextual and spatial boundary for the targeted signal attack.

| Condition | Window | Location | L2 target changes | L3 target changes |
|---|---|---|---:|---:|
| W0 | 1 base-event | target | 0/10 | 0/10 |
| Near sham | 11 base-events | +20 bases | 1/10 | 0/10 |
| Distant sham | 11 base-events | +100 bases | 0/10 | 0/10 |
| PM5 attack | 11 base-events | centred on target | 10/10 | 10/10 |

These results show:

1. the attack requires more than the isolated target event;
2. an 11-base local signal neighbourhood is sufficient when centred on the target;
3. short-range spillover can occur within nearby contextual sequence;
4. an equally strong perturbation 100 bases away does not affect the target;
5. the PM5 effect is therefore localized and spatially specific rather than a nonspecific consequence of signal corruption.

---

## Final conclusion

The cross-locus controls strengthen the Experiment E claim substantially.

The targeted basecalling attack is:

- context-dependent;
- spatially localized;
- reproducible across independent loci;
- capable of altering all attacked ALT-supporting reads when centred on the target;
- ineffective when reduced to a single target event;
- ineffective when displaced 100 bases away;
- capable of limited short-range spillover when positioned only 20 bases away.

**Final status: COMPLETE**

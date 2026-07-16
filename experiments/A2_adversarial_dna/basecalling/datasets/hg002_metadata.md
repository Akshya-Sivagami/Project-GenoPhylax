# HG002 Nanopore Dataset Metadata

## Dataset

- Sample: HG002 / GM24385
- Source: Oxford Nanopore Technologies Open Data
- Release: GIAB 2023.05
- Sequencing chemistry: R10.4.1
- Raw signal format: POD5
- Reference sample: NIST Genome in a Bottle HG002
- Expected reference genome: GRCh38

## Source Flowcell

- Flowcell ID: PAO89685
- Run path:
  `s3://ont-open-data/giab_2023.05/flowcells/hg002/20230424_1302_3H_PAO89685_2264ba8c/`

## Experiment A Subset

The complete `pod5_pass` directory contains approximately 1.2 TiB across 1,912 POD5 files. A three-file subset was selected for baseline GPU basecalling validation.

Selected files:

1. `PAO89685_pass__2264ba8c_afee3a87_0.pod5`
2. `PAO89685_pass__2264ba8c_afee3a87_1.pod5`
3. `PAO89685_pass__2264ba8c_afee3a87_10.pod5`

## Server Storage Location

`~/datasets/hg002/pod5/`

Raw POD5 files are intentionally stored outside the Git repository because they are large, public, and reproducibly downloadable.

## Scientific Rationale

HG002 was selected because it is an official ONT dataset generated using modern R10.4.1 chemistry and has an established GIAB truth set. This enables both clean basecalling evaluation and later comparison of downstream variant calls against known truth.

HG002 is independent from the NA12878 sample used in the earlier DeepVariant experiments. Results will therefore be framed as independent demonstrations of related pipeline attack mechanisms rather than a coordinate-matched same-sample comparison.

# Experiment A — Clean Nanopore Basecalling Baseline

## Objective

Establish a reproducible clean-signal GPU basecalling baseline on the NVIDIA GB10 platform before introducing adversarial or controlled raw-signal perturbations.

## Research Question

Can modern Nanopore raw signal be basecalled reproducibly on the ARM64 NVIDIA GB10 platform using a production basecaller, while collecting accuracy and performance measurements suitable for later adversarial comparisons?

## Hardware Environment

- GPU: NVIDIA GB10
- Architecture: ARM64 / aarch64
- CUDA: 13.0
- Compute capability: 12.1
- Unified system memory: 119 GiB
- CPU cores: 20
- Storage: 3.6 TiB NVMe

Detailed environment information is stored in:

`../environment/gb10_environment.txt`

## Dataset

- Sample: HG002 / GM24385
- Source: ONT Open Data
- Chemistry: R10.4.1
- Format: POD5
- Subset: Three POD5 files
- Raw data location: `~/datasets/hg002/pod5/`

See:

`../datasets/hg002_metadata.md`

## Planned Basecaller

Dorado will be used as the production baseline because it is the current Oxford Nanopore basecaller and supports ARM64 GB10 systems.

## Planned Metrics

### Basecalling Performance

- Total runtime
- Number of reads processed
- Reads per second
- Samples per second, where available
- GPU utilization
- CPU utilization

### Basecalling and Alignment Quality

- Mean read Q-score
- Alignment rate
- Mean read identity
- Substitution count
- Insertion count
- Deletion count
- Read-length distribution

## Experimental Status

- GPU environment validation: Complete
- Dataset selection: Complete
- Dataset download: Pending verification
- Dorado installation: Not started
- Clean basecalling run: Not started
- Alignment: Not started
- Metrics extraction: Not started

## Observations

To be completed during execution.

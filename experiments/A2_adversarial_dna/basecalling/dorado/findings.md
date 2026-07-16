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

## Clean Baseline Results

Dorado successfully completed HAC basecalling of the selected three-file HG002
POD5 subset using the NVIDIA GB10 GPU.

### Execution Results

- Input POD5 files: 3
- Approximate raw-signal input size: 2.3 GiB
- Input reads basecalled: 11,999
- Output BAM records: 12,703
- Dorado pipeline time: 106.779 seconds
- Total wall-clock time: 132.75 seconds
- Reported throughput: 25.42 million samples per second
- Maximum resident memory: approximately 4.79 GiB
- Swap activity: none
- Exit status: 0
[200~cat >> "$BASE_DIR/findings.md" <<'EOF'

## Clean Baseline Results

Dorado successfully completed HAC basecalling of the selected three-file HG002
POD5 subset using the NVIDIA GB10 GPU.

### Execution Results

- Input POD5 files: 3
- Approximate raw-signal input size: 2.3 GiB
- Input reads basecalled: 11,999
- Output BAM records: 12,703
- Dorado pipeline time: 106.779 seconds
- Total wall-clock time: 132.75 seconds
- Reported throughput: 25.42 million samples per second
- Maximum resident memory: approximately 4.79 GiB
- Swap activity: none
- Exit status: 0

The BAM contains 704 more output records than the number of raw reads reported
as basecalled. This is consistent with Dorado's default read-splitting behavior:
a single input POD5 read containing concatenated molecules can be separated into
multiple output subreads.

GPU monitoring showed sustained high compute activity during basecalling, with
the active phase frequently reaching approximately 95-96% SM utilization.
The initial apparent delay was therefore not caused by GPU underutilization. It
was primarily attributable to automatic batch-size optimization and the size of
the raw-signal workload.

### Baseline Conclusion

The ARM64 CUDA 13 Dorado build is compatible with the NVIDIA GB10 and provides
a stable, high-utilization clean basecalling baseline. This baseline can now be
used as the unperturbed control for later raw-signal manipulation experiments.

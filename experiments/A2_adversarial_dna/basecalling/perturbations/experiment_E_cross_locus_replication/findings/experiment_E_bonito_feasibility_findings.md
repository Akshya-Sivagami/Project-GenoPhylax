# Experiment E — Bonito Cross-Model Transferability Feasibility

## Objective

The planned extension aimed to test whether the targeted PM5 raw-signal attack developed and validated using Dorado could also affect the Bonito research basecaller.

The intended comparison was:

```text
L2 and L3 clean POD5
        versus
L2 and L3 PM5 POD5
        ↓
Bonito basecalling
        ↓
Alignment
        ↓
Per-read target-state comparison
```

The main research question was:

```text
Does a targeted raw-signal perturbation validated against Dorado transfer to Bonito?
```

## Available machine

The available GPU system was:

* NVIDIA GB10;
* Linux AArch64;
* CUDA 13.0 driver environment;
* Python 3.12;
* GPU compute capability 12.1.

Bonito was tested inside a new isolated virtual environment:

```text
bonito_transferability/environment/bonito_env
```

The existing Dorado installation and the established `pod5_env` environment were not modified.

## Initial installation attempt

The initial Bonito installation attempted to install:

```text
ont-bonito[cu130]
```

Pip successfully downloaded Bonito metadata and several dependencies. However, dependency resolution repeatedly backtracked through older Bonito releases and eventually failed while evaluating an outdated package version.

This first failure was caused by dependency resolution and package compatibility rather than network connectivity.

## Pinned PyTorch installation

A second installation attempt recreated the isolated Bonito environment and installed a pinned PyTorch CUDA build before installing Bonito.

The following package installed successfully:

```text
torch 2.10.0+cu130
```

PyTorch successfully detected:

```text
GPU: NVIDIA GB10
CUDA available: True
GPU compute capability: 12.1
```

A basic CUDA tensor calculation completed successfully:

```text
cuda_tensor_test: 90.0
PYTORCH CUDA VALIDATION: PASS
```

This established that basic PyTorch CUDA execution was possible on the system.

## PyTorch compatibility warning

During initialization, PyTorch emitted the following compatibility warning:

```text
Found GPU0 NVIDIA GB10 which is of CUDA capability 12.1.

Minimum and maximum CUDA capability supported by this version of PyTorch:
8.0 to 12.0
```

Therefore, although the basic tensor test succeeded, the installed PyTorch build did not officially declare support for the GB10’s compute capability 12.1.

This meant that successful execution of all Bonito-specific GPU kernels could not be assumed.

## Bonito installation result

The exact Bonito release tested was:

```text
ont-bonito==1.1.0
```

Bonito’s ordinary Python dependencies were available for Linux AArch64, including:

* edlib;
* fast-ctc-decode;
* mappy;
* NumPy;
* pandas;
* parasail;
* POD5;
* pysam.

However, Bonito also required:

```text
ont-koi==0.6.5
```

No compatible `ont-koi` distribution was available for Linux AArch64.

The installer returned:

```text
ERROR: Could not find a version that satisfies the requirement ont-koi==0.6.5
ERROR: No matching distribution found for ont-koi==0.6.5
```

## Network assessment

The installation failure was not caused by the college Wi-Fi.

During the installation:

* PyTorch downloaded successfully;
* CUDA runtime packages downloaded successfully;
* cuDNN downloaded successfully;
* cuBLAS downloaded successfully;
* Bonito package metadata downloaded successfully;
* multiple Bonito dependencies were located successfully.

The failure occurred only when pip attempted to resolve the required `ont-koi` package for AArch64.

A network-related failure would normally produce errors such as:

```text
Connection timed out
Connection reset
Temporary failure in name resolution
Max retries exceeded
```

None of these network errors caused the final failure.

## Decision

An unofficial source port or architecture workaround was not attempted.

This decision was made because:

1. the required `ont-koi` release was unavailable for Linux AArch64;
2. the standard package installer could not provide the required backend;
3. the available PyTorch build warned that compute capability 12.1 exceeded its officially declared support range;
4. an unofficial backend build could produce behaviour different from the supported Bonito release;
5. such a custom build would weaken the fairness and reproducibility of a Dorado-versus-Bonito comparison;
6. Dorado already operated successfully as the supported production basecaller on the NVIDIA GB10 system.

## Scientific interpretation

Bonito transferability remains unresolved.

This result must not be interpreted as:

* failure of the PM5 attack against Bonito;
* evidence that the attack is Dorado-specific;
* evidence that Bonito is resistant to the perturbation.

The experiment was not executed because the required Bonito backend was unavailable for the machine architecture.

A scientifically valid Bonito transferability experiment would require an officially supported Linux x86-64 NVIDIA CUDA system using the same clean and PM5 POD5 inputs.

## Inputs preserved for future testing

The existing cross-locus inputs remain available for later testing on a compatible system:

```text
target_pod5/L2_chr1_20061156_A_T.pod5
target_pod5/L3_chr4_40028853_A_G.pod5

attacked_pod5/PM5/L2_chr1_20061156_A_T.PM5.pod5
attacked_pod5/PM5/L3_chr4_40028853_A_G.PM5.pod5
```

The W0 and distant-sham controls are also available if a future compatible Bonito system is obtained.

## Effect on the Dorado findings

The Bonito feasibility limitation does not change the completed Dorado result.

The final Dorado cross-locus comparison remains:

| Condition                  | L2 changes | L3 changes | Combined |
| -------------------------- | ---------: | ---------: | -------: |
| W0 target-only             |       0/10 |       0/10 |     0/20 |
| Near sham at +20 bases     |       1/10 |       0/10 |     1/20 |
| Distant sham at +100 bases |       0/10 |       0/10 |     0/20 |
| Target-centred PM5         |      10/10 |      10/10 |    20/20 |

All primary attacked reads remained mapped at MAPQ 60.

The PM5 attack therefore demonstrated:

* context dependence;
* spatial specificity;
* short-range contextual spillover;
* cross-locus reproducibility;
* preservation of gross genomic alignment;
* substantial suppression of ALT-supporting evidence.

## Limitation for publication

The final publication must state that:

* Dorado was the only basecaller experimentally evaluated;
* Bonito transferability was planned but could not be executed on the available AArch64 system;
* Bonito’s required KOI backend was unavailable for Linux AArch64;
* cross-model transferability therefore remains future work;
* no claim of model-agnostic transferability is made.

## Final status

```text
BONITO FEASIBILITY AUDIT: COMPLETE
PYTORCH CUDA TEST: COMPLETE
BONITO INSTALLATION: BLOCKED BY AARCH64 PACKAGE AVAILABILITY
BONITO TRANSFERABILITY: NOT EXECUTED
DORADO EXPERIMENT E: COMPLETE
```

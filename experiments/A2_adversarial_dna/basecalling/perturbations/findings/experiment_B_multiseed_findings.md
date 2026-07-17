# Experiment B — Multi-Seed Gaussian Perturbation Replication

## Objective

Experiment B tested whether the Gaussian raw-signal dose-response observed in Experiment A was reproducible across independent random seeds.

The same 100 HG002 nanopore reads were tested at:

- GN01: sigma fraction 0.01
- GN05: sigma fraction 0.05
- GN10: sigma fraction 0.10

Seeds 1, 2, 3, 4, and 5 were used, producing 15 experimental conditions.

## Validation

All 15 perturbation and Dorado basecalling runs completed successfully.

All generated BAM files passed `samtools quickcheck -u`.

The BAM records remained unmapped, as expected for Dorado unaligned BAM output.

## Reproducibility result

For all five seeds, increasing Gaussian noise produced:

- decreasing mean sequence identity;
- increasing mean edit distance;
- increasingly negative mean Q-score change.

The ordering was consistently:

GN01 -> GN05 -> GN10

This confirms that the dose-response was reproducible and was not unique to seed 42.

## Observed ranges

### GN01

- Mean sequence identity: approximately 98.29% to 99.24%
- Mean edit distance: approximately 12.48 to 17.36
- Mean Q-score change: approximately -0.184 to -0.083

### GN05

- Mean sequence identity: approximately 97.15% to 97.69%
- Mean edit distance: approximately 40.71 to 44.12
- Mean Q-score change: approximately -2.374 to -2.154

### GN10

- Mean sequence identity: approximately 93.56% to 93.95%
- Mean edit distance: approximately 112.38 to 115.20
- Mean Q-score change: approximately -10.435 to -10.270

## Read-splitting event

GN01 seed 5 produced 101 BAM records from 100 raw reads.

Two child records shared the same Dorado parent identifier through the `pi` tag and had different `sp` signal-start positions. This confirmed that one parent read was split into two child basecalls.

The original 101-record BAM was preserved as the operational output.

For parent-level paired comparison, the two children were ordered by `sp`, concatenated, and restored to the original parent read ID. The normalized comparison BAM contained 100 records and matched all clean read IDs.

This demonstrates that raw-signal perturbation can alter both nucleotide output and Dorado read-segmentation behavior.

## Conclusion

Experiment B confirms that increasing raw-signal Gaussian noise consistently causes:

- lower sequence identity;
- higher edit distance;
- greater basecalling-confidence loss;
- occasional changes in read segmentation.

Dorado still completed successfully and produced structurally valid files.

Successful pipeline execution and valid file structure therefore do not guarantee genomic data integrity.

## Status

Experiment B is complete.

The next phase is Experiment C: larger-scale validation using a larger paired read set.

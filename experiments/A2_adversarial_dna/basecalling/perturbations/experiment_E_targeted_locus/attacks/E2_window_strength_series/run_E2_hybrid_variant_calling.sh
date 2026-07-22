#!/usr/bin/env bash

set -Eeuo pipefail

cd ~/Project-GenoPhylax

source \
  experiments/A2_adversarial_dna/basecalling/environment/pod5_env/bin/activate

EXP_E_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_targeted_locus"
E2_DIR="$EXP_E_DIR/attacks/E2_window_strength_series"

E1_SOURCE="$EXP_E_DIR/genotype_consequence/local_interpolation_pm5"
E1_CONTROL="$EXP_E_DIR/genotype_consequence/E1_controlled_comparison"

REF="$HOME/datasets/GenoPhylax/references/GRCh38_GIAB/GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta"

BACKGROUND_BAM="$E1_SOURCE/original_background.bam"
CLEAN_HYBRID="$E1_CONTROL/clean_dorado_hybrid.sorted.bam"
PM5_HYBRID="$E1_SOURCE/attacked_hybrid.sorted.bam"

TARGET_CHROM="chr20"
TARGET_POS="10003468"
CALL_REGION="chr20:9995000-10008000"

SUMMARY="$E2_DIR/E2_variant_calling_summary.tsv"
DONE_MARKER="$E2_DIR/E2_HYBRID_VARIANT_CALLING.COMPLETE"

rm -f "$DONE_MARKER"

echo "============================================================"
echo "EXPERIMENT E2 — HYBRID CONSTRUCTION AND VARIANT CALLING"
echo "Started: $(date -Is)"
echo "============================================================"

for FILE in \
  "$REF" \
  "$BACKGROUND_BAM" \
  "$CLEAN_HYBRID" \
  "$PM5_HYBRID"
do
  [[ -f "$FILE" ]] || {
    echo "ERROR: Missing required file:"
    echo "$FILE"
    exit 1
  }
done

BACKGROUND_COUNT=$(samtools view -c "$BACKGROUND_BAM")

[[ "$BACKGROUND_COUNT" -eq 51 ]] || {
  echo "ERROR: Expected 51 background records; got $BACKGROUND_COUNT."
  exit 1
}

printf \
"condition\tcontext_bases\tchanged_samples\tchanged_fraction\thybrid_records\ttarget_overlapping_records\tGT\tQUAL\tINFO_DP\tREF_DP4\tALT_DP4\tDP4\tstatus\n" \
> "$SUMMARY"

call_condition() {
  CONDITION="$1"
  CONTEXT="$2"
  CHANGED_SAMPLES="$3"
  CHANGED_FRACTION="$4"
  HYBRID_BAM="$5"

  CONDITION_DIR="$E2_DIR/$CONDITION"
  CALL_DIR="$CONDITION_DIR/variant_consequence"
  VCF="$CALL_DIR/${CONDITION}.vcf"

  mkdir -p "$CALL_DIR"

  [[ -s "$HYBRID_BAM" ]] || {
    echo "ERROR: Missing hybrid BAM for $CONDITION:"
    echo "$HYBRID_BAM"
    exit 1
  }

  HYBRID_RECORDS=$(samtools view -c "$HYBRID_BAM")

  TARGET_RECORDS=$(
    samtools view -c \
      "$HYBRID_BAM" \
      "${TARGET_CHROM}:${TARGET_POS}-${TARGET_POS}"
  )

  bcftools mpileup \
    -f "$REF" \
    -r "$CALL_REGION" \
    -Ou \
    "$HYBRID_BAM" \
    2> "$CALL_DIR/${CONDITION}_mpileup.log" \
  | bcftools call \
      -mv \
      -Ov \
      -o "$VCF"

  TARGET_LINE=$(
    awk -F'\t' \
      -v pos="$TARGET_POS" \
      '!/^#/ && $1=="chr20" && $2==pos {print}' \
      "$VCF"
  )

  if [[ -z "$TARGET_LINE" ]]; then
    printf \
      "%s\t%s\t%s\t%s\t%s\t%s\tNO_CALL\t.\t.\t.\t.\t.\tPASS\n" \
      "$CONDITION" \
      "$CONTEXT" \
      "$CHANGED_SAMPLES" \
      "$CHANGED_FRACTION" \
      "$HYBRID_RECORDS" \
      "$TARGET_RECORDS" \
      >> "$SUMMARY"

    echo "$CONDITION: no target variant record"
    return
  fi

  echo "$TARGET_LINE" \
  | awk -F'\t' \
      -v OFS='\t' \
      -v condition="$CONDITION" \
      -v context="$CONTEXT" \
      -v changed="$CHANGED_SAMPLES" \
      -v fraction="$CHANGED_FRACTION" \
      -v hybrid_records="$HYBRID_RECORDS" \
      -v target_records="$TARGET_RECORDS" '
      {
        info_dp="."
        dp4="."

        split($8, info, ";")

        for(i in info){
          if(info[i] ~ /^DP=/){
            split(info[i], x, "=")
            info_dp=x[2]
          }

          if(info[i] ~ /^DP4=/){
            split(info[i], x, "=")
            dp4=x[2]
          }
        }

        split(dp4, d, ",")
        ref_depth=d[1]+d[2]
        alt_depth=d[3]+d[4]

        split($10, sample, ":")
        gt=sample[1]

        print condition,
              context,
              changed,
              fraction,
              hybrid_records,
              target_records,
              gt,
              $6,
              info_dp,
              ref_depth,
              alt_depth,
              dp4,
              "PASS"
      }
    ' \
  >> "$SUMMARY"
}

build_hybrid() {
  CONDITION="$1"

  CONDITION_DIR="$E2_DIR/$CONDITION"
  RESULT_DIR="$CONDITION_DIR/dorado_results"
  CALL_DIR="$CONDITION_DIR/variant_consequence"

  ALIGNED_BAM="$RESULT_DIR/${CONDITION}.aligned.sorted.bam"
  REPLACEMENT_BAM="$CALL_DIR/${CONDITION}_replacement_reads.bam"
  UNSORTED_HYBRID="$CALL_DIR/${CONDITION}_hybrid.unsorted.bam"
  SORTED_HYBRID="$CALL_DIR/${CONDITION}_hybrid.sorted.bam"
  COMPLETE_MARKER="$CALL_DIR/${CONDITION}_HYBRID.COMPLETE"

  mkdir -p "$CALL_DIR"

  [[ -s "$ALIGNED_BAM" ]] || {
    echo "ERROR: Missing aligned BAM:"
    echo "$ALIGNED_BAM"
    exit 1
  }

  if [[ -f "$COMPLETE_MARKER" ]] \
    && [[ -s "$SORTED_HYBRID" ]]
  then
    echo "$CONDITION hybrid already exists; reusing."
  else
    rm -f "$COMPLETE_MARKER"

    samtools view \
      -h \
      "$ALIGNED_BAM" \
      "$CALL_REGION" \
    | samtools view \
        -b \
        -o "$REPLACEMENT_BAM" -

    REPLACEMENT_COUNT=$(samtools view -c "$REPLACEMENT_BAM")

    [[ "$REPLACEMENT_COUNT" -eq 12 ]] || {
      echo "ERROR: Expected 12 replacement records for $CONDITION; got $REPLACEMENT_COUNT."
      exit 1
    }

    samtools merge \
      -f \
      "$UNSORTED_HYBRID" \
      "$BACKGROUND_BAM" \
      "$REPLACEMENT_BAM"

    samtools sort \
      -@ 4 \
      -o "$SORTED_HYBRID" \
      "$UNSORTED_HYBRID"

    samtools index "$SORTED_HYBRID"

    HYBRID_COUNT=$(samtools view -c "$SORTED_HYBRID")

    [[ "$HYBRID_COUNT" -eq 63 ]] || {
      echo "ERROR: Expected 63 hybrid records for $CONDITION; got $HYBRID_COUNT."
      exit 1
    }

    touch "$COMPLETE_MARKER"
    echo "$CONDITION hybrid construction: PASS"
  fi
}

for CONDITION in E2_W0 E2_PM2 E2_PM10 E2_PM20; do
  echo
  echo "------------------------------------------------------------"
  echo "Building $CONDITION hybrid"
  echo "------------------------------------------------------------"
  build_hybrid "$CONDITION"
done

echo
echo "============================================================"
echo "RUN CONTROLLED VARIANT CALLS"
echo "============================================================"

call_condition \
  "CLEAN" \
  "-1" \
  "0" \
  "0" \
  "$CLEAN_HYBRID"

call_condition \
  "E2_W0" \
  "0" \
  "280" \
  "0.0000661730" \
  "$E2_DIR/E2_W0/variant_consequence/E2_W0_hybrid.sorted.bam"

call_condition \
  "E2_PM2" \
  "2" \
  "776" \
  "0.0001833939" \
  "$E2_DIR/E2_PM2/variant_consequence/E2_PM2_hybrid.sorted.bam"

call_condition \
  "E1_PM5" \
  "5" \
  "1599" \
  "0.0003778954" \
  "$PM5_HYBRID"

call_condition \
  "E2_PM10" \
  "10" \
  "2982" \
  "0.0007047430" \
  "$E2_DIR/E2_PM10/variant_consequence/E2_PM10_hybrid.sorted.bam"

call_condition \
  "E2_PM20" \
  "20" \
  "5862" \
  "0.0013853800" \
  "$E2_DIR/E2_PM20/variant_consequence/E2_PM20_hybrid.sorted.bam"

echo
echo "============================================================"
echo "E2 VARIANT-CALLING SUMMARY"
echo "============================================================"

column -t -s $'\t' "$SUMMARY"

touch "$DONE_MARKER"

echo
echo "Finished: $(date -Is)"
echo "E2 hybrid variant calling: COMPLETE"

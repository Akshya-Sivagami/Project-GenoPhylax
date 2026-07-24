#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

NEXT_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication"

COHORT_DIR="$NEXT_DIR/final_cohorts"
DOWNLOAD_DIR="$NEXT_DIR/source_pod5/downloaded_shards"
MARKER_DIR="$NEXT_DIR/markers"

MANIFEST="$COHORT_DIR/combined_L2_L3_pod5_download_manifest.tsv"

S3_ROOT="https://ont-open-data.s3.amazonaws.com"

DONE_MARKER="$MARKER_DIR/pod5_download.done"
FAIL_MARKER="$MARKER_DIR/pod5_download.failed"
VALIDATION="$DOWNLOAD_DIR/download_validation.tsv"
SUMMARY="$DOWNLOAD_DIR/download_summary.txt"

mkdir -p "$DOWNLOAD_DIR" "$MARKER_DIR"

rm -f "$DONE_MARKER" "$FAIL_MARKER"

if [[ ! -s "$MANIFEST" ]]; then
    echo "ERROR: Missing manifest: $MANIFEST"
    touch "$FAIL_MARKER"
    exit 1
fi

printf \
"filename\texpected_bytes\tactual_bytes\tstatus\n" \
> "$VALIDATION"

download_one() {
    local filename="$1"
    local expected_size="$2"
    local remote_path="$3"

    local output="$DOWNLOAD_DIR/$filename"
    local url="$S3_ROOT/$remote_path"

    echo
    echo "START: $filename"
    echo "URL:   $url"

    if [[ -f "$output" ]]; then
        local current_size
        current_size=$(stat -c '%s' "$output")

        if [[ "$current_size" -eq "$expected_size" ]]; then
            echo "SKIP: already complete bytes=$current_size"
            return 0
        fi

        if [[ "$current_size" -gt "$expected_size" ]]; then
            echo "Existing file is oversized; deleting:"
            echo "$output"
            rm -f "$output"
        else
            echo "RESUME: existing bytes=$current_size"
        fi
    fi

    curl \
        -L \
        --fail \
        --retry 10 \
        --retry-delay 5 \
        --retry-all-errors \
        -C - \
        --silent \
        --show-error \
        -o "$output" \
        "$url"

    local actual_size
    actual_size=$(stat -c '%s' "$output")

    if [[ "$actual_size" -ne "$expected_size" ]]; then
        echo "ERROR: size mismatch"
        echo "Expected: $expected_size"
        echo "Actual:   $actual_size"
        return 1
    fi

    echo "PASS: $filename bytes=$actual_size"
}

export -f download_one
export DOWNLOAD_DIR
export S3_ROOT

tail -n +2 "$MANIFEST" \
| xargs \
    -P 4 \
    -d '\n' \
    -I '{}' \
    bash -c '
        line="$1"

        filename=$(printf "%s\n" "$line" | cut -f1)
        expected_size=$(printf "%s\n" "$line" | cut -f2)
        remote_path=$(printf "%s\n" "$line" | cut -f3)

        download_one \
            "$filename" \
            "$expected_size" \
            "$remote_path"
    ' _ '{}'

python - \
    "$MANIFEST" \
    "$DOWNLOAD_DIR" \
    "$VALIDATION" \
    "$SUMMARY" \
    <<'PY'
from __future__ import annotations

import csv
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
download_dir = Path(sys.argv[2])
validation_path = Path(sys.argv[3])
summary_path = Path(sys.argv[4])

with manifest_path.open(
    "rt",
    encoding="utf-8",
    newline="",
) as handle:
    rows = list(
        csv.DictReader(
            handle,
            delimiter="\t",
        )
    )

validation_rows = []
errors = []
total_expected = 0
total_actual = 0

for row in rows:
    filename = row["filename"]
    expected = int(row["size_bytes"])
    path = download_dir / filename

    total_expected += expected

    if not path.exists():
        actual = 0
        status = "MISSING"
        errors.append(filename)
    else:
        actual = path.stat().st_size
        total_actual += actual

        if actual == expected:
            status = "PASS"
        else:
            status = "SIZE_MISMATCH"
            errors.append(filename)

    validation_rows.append(
        {
            "filename": filename,
            "expected_bytes": expected,
            "actual_bytes": actual,
            "status": status,
        }
    )

with validation_path.open(
    "wt",
    encoding="utf-8",
    newline="",
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "filename",
            "expected_bytes",
            "actual_bytes",
            "status",
        ],
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(validation_rows)

summary_lines = [
    f"manifest_files={len(rows)}",
    f"validated_files={sum(row['status'] == 'PASS' for row in validation_rows)}",
    f"failed_files={len(errors)}",
    f"expected_bytes={total_expected}",
    f"actual_bytes={total_actual}",
    f"expected_GiB={total_expected / 1024**3:.6f}",
    f"actual_GiB={total_actual / 1024**3:.6f}",
    f"status={'PASS' if not errors else 'FAIL'}",
]

summary_path.write_text(
    "\n".join(summary_lines) + "\n",
    encoding="utf-8",
)

print("\n".join(summary_lines))

if errors:
    raise SystemExit(
        "Download validation failed for: "
        + ", ".join(errors)
    )
PY

touch "$DONE_MARKER"

echo
echo "============================================================"
echo "CROSS-LOCUS POD5 DOWNLOAD COMPLETE"
echo "============================================================"

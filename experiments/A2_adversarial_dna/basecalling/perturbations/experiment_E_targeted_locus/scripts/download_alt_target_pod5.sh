#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

EXP_E_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_targeted_locus"
MAP_DIR="$EXP_E_DIR/read_mapping"
DOWNLOAD_DIR="$EXP_E_DIR/source_pod5/alt_files"

MANIFEST="$MAP_DIR/alt_pod5_download_manifest.tsv"

S3_ROOT="https://ont-open-data.s3.amazonaws.com/giab_2023.05/flowcells/hg002/20230424_1302_3H_PAO89685_2264ba8c/pod5_pass"

mkdir -p "$DOWNLOAD_DIR"

download_one() {
    local filename="$1"
    local expected_size="$2"
    local output="$DOWNLOAD_DIR/$filename"
    local url="$S3_ROOT/$filename"

    echo "START  $filename"

    curl -L \
      --fail \
      --retry 8 \
      --retry-delay 5 \
      --retry-all-errors \
      -C - \
      --silent \
      --show-error \
      -o "$output" \
      "$url"

    actual_size="$(stat -c '%s' "$output")"

    if [[ "$actual_size" -ne "$expected_size" ]]; then
        echo "ERROR  $filename expected=$expected_size actual=$actual_size"
        return 1
    fi

    echo "PASS   $filename bytes=$actual_size"
}

export -f download_one
export DOWNLOAD_DIR
export S3_ROOT

tail -n +2 "$MANIFEST" \
  | cut -f1,2 \
  | xargs -P 4 -n 2 bash -c '
        download_one "$1" "$2"
    ' _

echo
echo "All downloads completed."

python - "$MANIFEST" "$DOWNLOAD_DIR" <<'PY'
from __future__ import annotations

import csv
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
download_dir = Path(sys.argv[2])

rows = []

with manifest_path.open("rt", encoding="utf-8") as handle:
    reader = csv.DictReader(handle, delimiter="\t")
    rows.extend(reader)

errors = []

for row in rows:
    filename = row["filename"]
    expected = int(row["size_bytes"])
    path = download_dir / filename

    if not path.exists():
        errors.append(f"MISSING\t{filename}")
        continue

    actual = path.stat().st_size

    if actual != expected:
        errors.append(
            f"SIZE_MISMATCH\t{filename}\t"
            f"expected={expected}\tactual={actual}"
        )

if errors:
    print("Download validation: FAIL")
    for error in errors:
        print(error)
    raise SystemExit(1)

print("Download validation: PASS")
print(f"Validated files: {len(rows)}")
print(
    "Validated GiB: "
    f"{sum(int(row['size_bytes']) for row in rows) / 1024**3:.2f}"
)
PY

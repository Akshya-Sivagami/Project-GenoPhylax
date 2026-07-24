#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

CROSS_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication"
BONITO_DIR="$CROSS_DIR/bonito_transferability"

ENV_DIR="$BONITO_DIR/environment/bonito_env"
LOG_DIR="$BONITO_DIR/logs"
MARKER_DIR="$BONITO_DIR/markers"
RESULTS_DIR="$BONITO_DIR/results"

mkdir -p \
    "$BONITO_DIR/environment" \
    "$LOG_DIR" \
    "$MARKER_DIR" \
    "$RESULTS_DIR" \
    "$BONITO_DIR/models"

rm -f \
    "$MARKER_DIR/BONITO_REPAIR_INSTALL.COMPLETE" \
    "$MARKER_DIR/BONITO_REPAIR_INSTALL.FAILED" \
    "$MARKER_DIR/BONITO_INSTALL.COMPLETE" \
    "$MARKER_DIR/BONITO_INSTALL.FAILED"

trap '
    status=$?
    echo
    echo "============================================================"
    echo "BONITO REPAIR INSTALLATION FAILED"
    echo "Exit status: $status"
    echo "Finished: $(date -Is)"
    echo "============================================================"
    touch "$MARKER_DIR/BONITO_REPAIR_INSTALL.FAILED"
    exit "$status"
' ERR

echo "============================================================"
echo "EXPERIMENT E — BONITO REPAIR INSTALLATION"
echo "Started: $(date -Is)"
echo "============================================================"

echo
echo "[1/9] Validate machine"

echo "Architecture: $(uname -m)"
echo "System Python: $(python3 --version 2>&1)"

if [ "$(uname -m)" != "aarch64" ]; then
    echo "ERROR: Expected aarch64 architecture"
    exit 1
fi

command -v nvidia-smi
nvidia-smi

echo
echo "[2/9] Remove only the failed isolated Bonito environment"

if [ -d "$ENV_DIR" ]; then
    echo "Removing:"
    echo "$ENV_DIR"
    rm -rf "$ENV_DIR"
fi

if [ -e "$ENV_DIR" ]; then
    echo "ERROR: Failed to remove old Bonito environment"
    exit 1
fi

echo
echo "[3/9] Create fresh isolated environment"

python3 -m venv "$ENV_DIR"

source "$ENV_DIR/bin/activate"

echo "Active environment: $VIRTUAL_ENV"
echo "Python executable: $(command -v python)"
python --version

if [ "$VIRTUAL_ENV" != "$HOME/Project-GenoPhylax/$ENV_DIR" ]; then
    echo "ERROR: Unexpected virtual environment:"
    echo "$VIRTUAL_ENV"
    exit 1
fi

echo
echo "[4/9] Upgrade packaging tools"

python -m pip install --upgrade \
    pip \
    setuptools \
    wheel \
    packaging

echo
echo "[5/9] Install pinned PyTorch CUDA 13.0 build"

python -m pip install \
    --index-url https://download.pytorch.org/whl/cu130 \
    "torch==2.10.0"

echo
echo "[6/9] Validate PyTorch before Bonito"

python - <<'PY'
import platform
import torch

print("architecture:", platform.machine())
print("torch_version:", torch.__version__)
print("torch_cuda_build:", torch.version.cuda)
print("cuda_available:", torch.cuda.is_available())
print("cuda_device_count:", torch.cuda.device_count())

if not torch.cuda.is_available():
    raise SystemExit("ERROR: CUDA is unavailable through PyTorch")

for index in range(torch.cuda.device_count()):
    print("cuda_device", index, torch.cuda.get_device_name(index))
    print(
        "cuda_capability",
        index,
        torch.cuda.get_device_capability(index),
    )

device = torch.device("cuda:0")
test_tensor = torch.arange(10, dtype=torch.float32, device=device)
result = (test_tensor * 2).sum().item()

print("cuda_tensor_test:", result)

if result != 90.0:
    raise SystemExit("ERROR: CUDA tensor calculation returned unexpected result")

print("PYTORCH CUDA VALIDATION: PASS")
PY

echo
echo "[7/9] Install exact Bonito release"

python -m pip install \
    --extra-index-url https://download.pytorch.org/whl/cu130 \
    "ont-bonito==1.1.0"

echo
echo "[8/9] Validate Bonito and dependency environment"

command -v bonito
bonito --help 2>&1 | head -100

python - <<'PY'
import importlib.metadata
import platform
import sys

import bonito
import pod5
import torch

print("python_version:", sys.version.replace("\n", " "))
print("python_executable:", sys.executable)
print("architecture:", platform.machine())

for package in [
    "ont-bonito",
    "torch",
    "pod5",
    "numpy",
    "pandas",
    "pysam",
    "edlib",
    "mappy",
    "parasail",
]:
    try:
        print(package, importlib.metadata.version(package))
    except Exception as exc:
        print(package, "VERSION_NOT_FOUND", repr(exc))

print("bonito_module:", bonito.__file__)
print("pod5_module:", pod5.__file__)
print("torch_version:", torch.__version__)
print("torch_cuda_build:", torch.version.cuda)
print("cuda_available:", torch.cuda.is_available())

if importlib.metadata.version("ont-bonito") != "1.1.0":
    raise SystemExit("ERROR: Incorrect Bonito version installed")

if not torch.cuda.is_available():
    raise SystemExit("ERROR: CUDA became unavailable after Bonito installation")

print("BONITO IMPORT AND CUDA VALIDATION: PASS")
PY

echo
echo "--- pip dependency check ---"

python -m pip check

echo
echo "--- Bonito basecaller help ---"

bonito basecaller --help 2>&1 | head -180

echo
echo "--- Bonito download help ---"

bonito download --help 2>&1 | head -140

echo
echo "[9/9] List compatible models"

bonito download --models --show \
    > "$RESULTS_DIR/bonito_available_models.txt"

grep -iE \
    "dna_r10[._]4[._]1.*e8[._]2.*400bps.*hac" \
    "$RESULTS_DIR/bonito_available_models.txt" \
    | tee "$RESULTS_DIR/bonito_compatible_hac_models.txt" \
    || true

echo
echo "--- Matching model count ---"

MATCH_COUNT=$(
    grep -icE \
        "dna_r10[._]4[._]1.*e8[._]2.*400bps.*hac" \
        "$RESULTS_DIR/bonito_available_models.txt" \
        || true
)

echo "MATCH_COUNT=$MATCH_COUNT"

if [ "$MATCH_COUNT" -lt 1 ]; then
    echo "ERROR: No compatible R10.4.1 E8.2 400-bps HAC model was listed"
    exit 1
fi

python -m pip freeze \
    > "$RESULTS_DIR/bonito_environment_freeze.txt"

touch "$MARKER_DIR/BONITO_REPAIR_INSTALL.COMPLETE"

echo
echo "============================================================"
echo "BONITO REPAIR INSTALLATION: COMPLETE"
echo "Finished: $(date -Is)"
echo "============================================================"

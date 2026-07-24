#!/usr/bin/env bash

set -Eeuo pipefail

cd "$HOME/Project-GenoPhylax"

CROSS_DIR="experiments/A2_adversarial_dna/basecalling/perturbations/experiment_E_cross_locus_replication"
BONITO_DIR="$CROSS_DIR/bonito_transferability"

ENV_DIR="$BONITO_DIR/environment/bonito_env"
LOG_DIR="$BONITO_DIR/logs"
MARKER_DIR="$BONITO_DIR/markers"

mkdir -p \
    "$BONITO_DIR/environment" \
    "$LOG_DIR" \
    "$MARKER_DIR" \
    "$BONITO_DIR/results" \
    "$BONITO_DIR/models"

rm -f \
    "$MARKER_DIR/BONITO_INSTALL.COMPLETE" \
    "$MARKER_DIR/BONITO_INSTALL.FAILED"

trap '
    status=$?
    echo
    echo "BONITO INSTALLATION FAILED"
    echo "Exit status: $status"
    touch "$MARKER_DIR/BONITO_INSTALL.FAILED"
    exit "$status"
' ERR

echo "============================================================"
echo "EXPERIMENT E — ISOLATED BONITO INSTALLATION"
echo "Started: $(date -Is)"
echo "============================================================"

echo
echo "[1/7] System validation"

echo "Architecture: $(uname -m)"
echo "Python:"
python3 --version

if [ "$(uname -m)" != "aarch64" ]; then
    echo "WARNING: Expected aarch64 but found $(uname -m)"
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi is unavailable"
    exit 1
fi

nvidia-smi

echo
echo "[2/7] Inspect previous Bonito directories"

for OLD_DIR in \
    "$HOME/genophylax_gpu/bonito" \
    "$HOME/Project-GenoPhylax/experiments/A2_adversarial_dna/basecalling/bonito"
do
    echo
    echo "--- $OLD_DIR ---"

    if [ -e "$OLD_DIR" ]; then
        ls -la "$OLD_DIR" | head -40 || true

        if [ -d "$OLD_DIR/.git" ]; then
            git -C "$OLD_DIR" status --short --branch || true
            git -C "$OLD_DIR" log -1 --oneline || true
        fi

        find "$OLD_DIR" \
            -maxdepth 3 \
            -type f \
            \( -name "activate" \
            -o -name "pyvenv.cfg" \
            -o -name "bonito" \) \
            -print 2>/dev/null \
            | head -50 || true
    else
        echo "Not present"
    fi
done

echo
echo "[3/7] Create isolated Bonito virtual environment"

if [ ! -x "$ENV_DIR/bin/python" ]; then
    python3 -m venv "$ENV_DIR"
else
    echo "Existing environment found; reusing it."
fi

source "$ENV_DIR/bin/activate"

echo "Environment: $VIRTUAL_ENV"
echo "Python: $(command -v python)"
python --version

echo
echo "[4/7] Upgrade packaging tools"

python -m pip install --upgrade \
    pip \
    setuptools \
    wheel

echo
echo "[5/7] Install Bonito with CUDA 13.0 PyTorch dependencies"

python -m pip install \
    "ont-bonito[cu130]" \
    --extra-index-url https://download.pytorch.org/whl/cu130

echo
echo "[6/7] Validate installation"

echo
echo "--- Executables ---"
command -v python
command -v bonito

echo
echo "--- Package versions ---"

python - <<'PY'
import importlib
import importlib.metadata
import platform
import sys

print("python:", sys.version.replace("\n", " "))
print("executable:", sys.executable)
print("architecture:", platform.machine())

for package in ["ont-bonito", "torch", "pod5", "numpy", "pysam"]:
    try:
        print(package, importlib.metadata.version(package))
    except Exception as exc:
        print(package, "VERSION_NOT_FOUND", repr(exc))

import bonito
import torch

print("bonito_import:", bonito.__file__)
print("torch_version:", torch.__version__)
print("torch_cuda_build:", torch.version.cuda)
print("cuda_available:", torch.cuda.is_available())
print("cuda_device_count:", torch.cuda.device_count())

if torch.cuda.is_available():
    for index in range(torch.cuda.device_count()):
        print("cuda_device", index, torch.cuda.get_device_name(index))
        print(
            "cuda_capability",
            index,
            torch.cuda.get_device_capability(index),
        )
PY

echo
echo "--- Bonito version/help ---"

bonito --version 2>&1 || true
bonito --help 2>&1 | head -100
bonito basecaller --help 2>&1 | head -160
bonito download --help 2>&1 | head -120

echo
echo "[7/7] List compatible downloadable models"

bonito download --models --show \
    > "$BONITO_DIR/results/bonito_available_models.txt"

grep -iE \
    "r10[._]4[._]1|e8[._]2|400bps|hac" \
    "$BONITO_DIR/results/bonito_available_models.txt" \
    | tee "$BONITO_DIR/results/bonito_r10_models.txt" \
    || true

if ! command -v bonito >/dev/null 2>&1; then
    echo "ERROR: Bonito executable missing after installation"
    exit 1
fi

python - <<'PY'
import torch

if not torch.cuda.is_available():
    raise SystemExit(
        "ERROR: Bonito installed, but CUDA is not available through PyTorch"
    )

print("CUDA validation: PASS")
PY

touch "$MARKER_DIR/BONITO_INSTALL.COMPLETE"

echo
echo "============================================================"
echo "BONITO INSTALLATION: COMPLETE"
echo "Finished: $(date -Is)"
echo "============================================================"

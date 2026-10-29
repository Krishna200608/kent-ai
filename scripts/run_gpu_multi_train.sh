#!/usr/bin/env bash
# ==============================================================================
# Kent-AI: Automated Multi-Model Fine-Tuning Pipeline on College GPU Cluster
# Target: Comparative Study across PubMedBERT, BioLinkBERT, and DeBERTa-v3
# Hardware: NVIDIA RTX 5000 Ada (32GB VRAM)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

mkdir -p logs data/models

echo "=================================================================="
echo "  KENT-AI: MULTI-MODEL GPU COMPARATIVE TRAINING PIPELINE"
echo "=================================================================="
echo "Repository Root : ${PROJECT_ROOT}"
echo "Current Time    : $(date)"

# 1. Environment & GPU Verification
if [ -d ".venv" ]; then
    echo "[✓] Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif command -v python3 &>/dev/null; then
    echo "[!] .venv not found. Using system python3."
else
    echo "[✗] Python3 not found. Please activate environment first."
    exit 1
fi

if command -v nvidia-smi &>/dev/null; then
    echo "[✓] NVIDIA GPU Detected:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
    echo "[!] Warning: nvidia-smi not found. Training will run on CPU (very slow)."
fi

# 2. Check Dataset Splits
TRAIN_FILE="data/processed/train.jsonl"
VAL_FILE="data/processed/val.jsonl"
TEST_FILE="data/processed/test.jsonl"

if [ ! -f "${TRAIN_FILE}" ] || [ ! -f "${VAL_FILE}" ]; then
    echo "[✗] Required dataset files not found at ${TRAIN_FILE} or ${VAL_FILE}."
    echo "    Please verify dataset partitioning first."
    exit 1
fi

echo "[✓] Training corpus verified: $(wc -l < ${TRAIN_FILE}) train cases, $(wc -l < ${VAL_FILE}) val cases."

# 3. Model Training Function
train_model() {
    local MODEL_ID="$1"
    local OUT_DIR="$2"
    local LOG_FILE="$3"
    local DISPLAY_NAME="$4"

    echo ""
    echo "------------------------------------------------------------------"
    echo "  [TRAINING] ${DISPLAY_NAME}"
    echo "  Model ID  : ${MODEL_ID}"
    echo "  Output Dir: ${OUT_DIR}"
    echo "  Log File  : ${LOG_FILE}"
    echo "  Start Time: $(date)"
    echo "------------------------------------------------------------------"

    python scripts/train_ner.py \
        --model-name "${MODEL_ID}" \
        --output-dir "${OUT_DIR}" \
        --train-file "${TRAIN_FILE}" \
        --val-file "${VAL_FILE}" \
        --batch-size 32 \
        --epochs 8 \
        2>&1 | tee "${LOG_FILE}"

    echo "[✓] Completed training ${DISPLAY_NAME} at $(date)"
}

# ==============================================================================
# Model 1: PubMedBERT (Microsoft BiomedNLP) — Top Recommendation / BLURB #1
# ==============================================================================
train_model \
    "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext" \
    "data/models/pubmedbert_homeoNER" \
    "logs/train_pubmedbert.log" \
    "PubMedBERT (BiomedNLP)"

# ==============================================================================
# Model 2: BioLinkBERT (Stanford) — Citation-Graph Link Pretraining
# ==============================================================================
train_model \
    "michiyasunaga/BioLinkBERT-base" \
    "data/models/biolinkbert_homeoNER" \
    "logs/train_biolinkbert.log" \
    "BioLinkBERT (Stanford)"

# ==============================================================================
# Model 3: DeBERTa-v3 (Microsoft) — Disentangled Attention & RTD Objective
# ==============================================================================
train_model \
    "microsoft/deberta-v3-base" \
    "data/models/deberta_homeoNER" \
    "logs/train_deberta.log" \
    "DeBERTa-v3 (Microsoft)"

echo ""
echo "=================================================================="
echo "  ALL MULTI-MODEL TRAINING RUNS COMPLETED SUCCESSFULLY!"
echo "=================================================================="
echo "Saved Models in data/models/:"
ls -lh data/models/
echo ""
echo "To evaluate on held-out test split (test.jsonl):"
echo "  python scripts/evaluate.py --test-file data/processed/test.jsonl"
echo "=================================================================="

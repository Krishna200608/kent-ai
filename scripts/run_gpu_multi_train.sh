#!/usr/bin/env bash
# ==============================================================================
# Kent-AI: Automated Multi-Model Fine-Tuning Pipeline on College GPU Cluster
# Target: Comparative Study across PubMedBERT, BioLinkBERT, and DeBERTa-v3
# Hardware: NVIDIA RTX 5000 Ada (32GB VRAM)
# ==============================================================================

set -euo pipefail
export HF_HUB_DISABLE_XET=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

mkdir -p logs data/models
echo $$ > logs/multi_train.pid

echo "=================================================================="
echo "  KENT-AI: MULTI-MODEL GPU COMPARATIVE TRAINING PIPELINE"
echo "=================================================================="
echo "Repository Root : ${PROJECT_ROOT}"
echo "Current Time    : $(date)"

# 1. Environment & GPU Verification
PYTHON_EXEC="python3"
if [ -d ".venv" ]; then
    echo "[✓] Using virtual environment (.venv)..."
    PYTHON_EXEC="${PROJECT_ROOT}/.venv/bin/python"
    source .venv/bin/activate
elif command -v python3 &>/dev/null; then
    echo "[!] .venv not found. Using system python3."
    PYTHON_EXEC="python3"
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

    if [ -f "${OUT_DIR}/model.safetensors" ] || [ -f "${OUT_DIR}/pytorch_model.bin" ]; then
        echo ""
        echo "[✓] ${DISPLAY_NAME} already trained at ${OUT_DIR}. Skipping training to preserve checkpoints."
        return 0
    fi

    echo ""
    echo "------------------------------------------------------------------"
    echo "  [TRAINING] ${DISPLAY_NAME}"
    echo "  Model ID  : ${MODEL_ID}"
    echo "  Output Dir: ${OUT_DIR}"
    echo "  Log File  : ${LOG_FILE}"
    echo "  Start Time: $(date)"
    echo "------------------------------------------------------------------"

    "${PYTHON_EXEC}" scripts/train_ner.py \
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

# ==============================================================================
# Step 4: Comprehensive Academic Evaluation on Held-Out Test Split (test.jsonl)
# ==============================================================================
echo "=================================================================="
echo "  STARTING EVALUATION BENCHMARK ON TEST SPLIT (1,973 CASES)"
echo "=================================================================="
mkdir -p docs/Evaluation

evaluate_model() {
    local MODEL_DIR="$1"
    local JSON_OUT="$2"
    local MD_OUT="$3"
    local DISPLAY_NAME="$4"

    if [ -f "${MD_OUT}" ] && [ -f "${JSON_OUT}" ]; then
        echo ""
        echo "[✓] ${DISPLAY_NAME} already evaluated. Report exists at ${MD_OUT}. Skipping."
        return 0
    fi

    echo ""
    echo "------------------------------------------------------------------"
    echo "  [EVALUATION] ${DISPLAY_NAME}"
    echo "  Model Path: ${MODEL_DIR}"
    echo "  Output MD : ${MD_OUT}"
    echo "  Start Time: $(date)"
    echo "------------------------------------------------------------------"

    "${PYTHON_EXEC}" scripts/evaluate.py \
        --model-path "${MODEL_DIR}" \
        --test-file "${TEST_FILE}" \
        --output-json "${JSON_OUT}" \
        --output-md "${MD_OUT}" \
        --device "cuda"

    echo "[✓] Evaluated ${DISPLAY_NAME} successfully."
}

# 1. Evaluate Bio_ClinicalBERT (Reference Baseline)
if [ -d "data/models/clinicalbert_homeoNER" ]; then
    evaluate_model "data/models/clinicalbert_homeoNER" "data/eval_metrics_clinicalbert.json" "docs/Evaluation/eval_clinicalbert.md" "Bio_ClinicalBERT (Baseline)"
fi

# 2. Evaluate PubMedBERT
if [ -d "data/models/pubmedbert_homeoNER" ]; then
    evaluate_model "data/models/pubmedbert_homeoNER" "data/eval_metrics_pubmedbert.json" "docs/Evaluation/eval_pubmedbert.md" "PubMedBERT (BiomedNLP)"
fi

# 3. Evaluate BioLinkBERT
if [ -d "data/models/biolinkbert_homeoNER" ]; then
    evaluate_model "data/models/biolinkbert_homeoNER" "data/eval_metrics_biolinkbert.json" "docs/Evaluation/eval_biolinkbert.md" "BioLinkBERT (Stanford)"
fi

# 4. Evaluate DeBERTa-v3
if [ -d "data/models/deberta_homeoNER" ]; then
    evaluate_model "data/models/deberta_homeoNER" "data/eval_metrics_deberta.json" "docs/Evaluation/eval_deberta.md" "DeBERTa-v3 (Microsoft)"
fi

echo ""
echo "=================================================================="
echo "  MULTI-MODEL COMPARATIVE STUDY PIPELINE COMPLETE!"
echo "  Evaluation reports saved in docs/Evaluation/"
echo "=================================================================="


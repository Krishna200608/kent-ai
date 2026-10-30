#!/usr/bin/env bash
# ==============================================================================
# Kent-AI Week 2: Production QLoRA Fine-Tuning Pipeline for Qwen 2.5 7B Instruct
# Hardware: NVIDIA RTX 5000 Ada (32GB VRAM, Server 172.20.70.80)
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# 1. Environment and Storage Redirection (/DATA has 2.8TB free)
export HF_HOME="/DATA/narya/cache/huggingface"
export TRANSFORMERS_CACHE="/DATA/narya/cache/huggingface"
export TMPDIR="/DATA/narya/tmp"
export HF_HUB_DISABLE_XET=1

mkdir -p "$HF_HOME" "$TMPDIR" logs data/models/qwen_homeoQLoRA

LOG_FILE="logs/train_qwen_qlora.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================================================"
echo "Starting Kent-AI Week 2: Qwen 2.5 7B QLoRA Fine-Tuning"
echo "Timestamp: $(date -Iseconds)"
echo "Host: $(hostname)"
echo "GPU Device: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo 'Unknown')"
echo "Storage HF_HOME: $HF_HOME ($(df -h "$HF_HOME" | awk 'NR==2 {print $4}') available)"
echo "========================================================================"

# 2. Execute Training Run (Batch size 2 x Grad Accum 8 = Effective Batch 16, ~6.8GB VRAM)
.venv/bin/python scripts/train_llm_peft.py \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --output-dir data/models/qwen_homeoQLoRA \
  --train-file data/processed/train.jsonl \
  --val-file data/processed/val.jsonl \
  --epochs 3 \
  --batch-size 2 \
  --grad-accum 8 \
  --lr 2e-4 \
  --max-seq-length 512 \
  --lora-r 16 \
  --lora-alpha 32 \
  --lora-dropout 0.05 \
  --eval-steps 200 \
  --save-steps 400

echo "========================================================================"
echo "Training finished at $(date -Iseconds)"
echo "Adapter files saved to data/models/qwen_homeoQLoRA"
echo "========================================================================"

# 3. Execute Held-Out Test Set Evaluation
echo "Beginning Quantitative Benchmark on test.jsonl (1,973 cases)..."
.venv/bin/python scripts/evaluate_llm.py \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --adapter-dir data/models/qwen_homeoQLoRA \
  --test-file data/processed/test.jsonl \
  --output-report docs/Evaluation/eval_qwen_7b.md \
  --output-json data/eval_metrics_qwen_7b.json

echo "========================================================================"
echo "Week 2 Qwen 2.5 7B Training & Evaluation Pipeline Complete!"
echo "Timestamp: $(date -Iseconds)"
echo "========================================================================"

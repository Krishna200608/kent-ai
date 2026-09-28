#!/bin/bash
# ==============================================================================
# Kent-AI: Phase 1 Production Case Generation (College GPU Server)
# Target: 22,200 synthetic clinical training cases across 4,933 MIND rubrics
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=================================================================="
echo "Kent-AI: Synthetic Case Generation Production Runner"
echo "Project Root: $PROJECT_ROOT"
echo "Target: 22,200 Cases (4-5 variations per Kent MIND rubric)"
echo "=================================================================="

# 1. Check Python environment
if [ -d ".venv" ]; then
    echo "[✓] Activating Python virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -n "$VIRTUAL_ENV" ]; then
    echo "[✓] Using active virtual environment: $VIRTUAL_ENV"
else
    echo "[!] Warning: No virtual environment detected. Using system Python."
fi

# 2. Check GPU Telemetry
if command -v nvidia-smi &> /dev/null; then
    echo "[✓] NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
else
    echo "[!] No nvidia-smi found. Running in CPU mode or containerized environment."
fi

# 3. Check Ollama Service & Model Availability
OLLAMA_HOST="${OLLAMA_API_BASE:-http://localhost:11434}"
echo "[*] Checking Ollama service at $OLLAMA_HOST..."

if curl -s -f "$OLLAMA_HOST/api/tags" &> /dev/null; then
    echo "[✓] Ollama service is reachable."
else
    echo "[!] Ollama service not responding. Starting ollama in background..."
    if command -v ollama &> /dev/null; then
        ollama serve &
        sleep 5
    else
        echo "[✗] Error: 'ollama' binary not found. Please install Ollama or start the service."
        exit 1
    fi
fi

# Verify llama3:8b is pulled
echo "[*] Ensuring 'llama3:8b' model is available in Ollama..."
ollama pull llama3:8b

# 4. Prepare directories
mkdir -p logs data/processed

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/case_generation_${TIMESTAMP}.log"

echo "=================================================================="
echo "Launching Case Generation with Crash-Safe Checkpointing..."
echo "Log file: $LOG_FILE"
echo "To monitor live progress, run:"
echo "  tail -f $LOG_FILE"
echo "=================================================================="

# 5. Run generation pipeline
# Note: --resume ensures automatic recovery from the last checkpoint if interrupted.
# Note: --split automatically partitions into 80% train, 10% val, 10% test upon completion.

python scripts/generate_cases.py \
    --config configs/generation.yaml \
    --cases-per-rubric 4 \
    --resume \
    --split 2>&1 | tee "$LOG_FILE"

EXIT_STATUS=${PIPESTATUS[0]}

if [ $EXIT_STATUS -eq 0 ]; then
    echo "=================================================================="
    echo "[✓] Production case generation completed successfully!"
    echo "Output files created:"
    ls -lh data/processed/*.jsonl
    echo "Ready for Phase 3 ClinicalBERT fine-tuning."
    echo "=================================================================="
else
    echo "[✗] Generation exited with status code $EXIT_STATUS. Check $LOG_FILE for details."
    exit $EXIT_STATUS
fi

#!/usr/bin/env bash
# ==============================================================================
# Kent-AI: Automated Production Case Generation on College GPU Cluster
# Target: 22,200 Synthetic Clinical Cases (4 variations x 4,933 MIND Rubrics)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

mkdir -p logs data/processed

echo "=================================================================="
echo "  KENT-AI: PRODUCTION GPU CASE GENERATION PIPELINE"
echo "=================================================================="
echo "Repository Root : ${PROJECT_ROOT}"
echo "Current Time    : $(date)"

# 1. Check Python Environment
if [ -d ".venv" ]; then
    echo "[✓] Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif command -v python3 &>/dev/null; then
    echo "[!] .venv not found. Using system python3."
else
    echo "[✗] Python3 is not installed. Please set up Python first."
    exit 1
fi

# 2. Check GPU Acceleration
if command -v nvidia-smi &>/dev/null; then
    echo "[✓] NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
    echo "[!] Warning: nvidia-smi not found. Generation will default to CPU (much slower)."
fi

# 3. Check and Start Ollama Daemon
echo "[*] Checking Ollama service..."
if ! command -v ollama &>/dev/null; then
    echo "[✗] Ollama is not installed. Install via: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo "[*] Starting Ollama daemon in background..."
    nohup ollama serve > logs/ollama.log 2>&1 &
    sleep 4
fi

if curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo "[✓] Ollama daemon is active on port 11434."
else
    echo "[✗] Could not connect to Ollama daemon. Check logs/ollama.log."
    exit 1
fi

# 4. Ensure LLaMA 3 Model is Pulled
echo "[*] Ensuring llama3:8b model is available in Ollama..."
ollama pull llama3:8b

# 5. Launch Case Generation in Background with nohup
LOG_FILE="${PROJECT_ROOT}/logs/generation.log"
PID_FILE="${PROJECT_ROOT}/logs/generation.pid"

if [ -f "${PID_FILE}" ] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
    echo "[!] Generation is ALREADY RUNNING (PID: $(cat "${PID_FILE}"))."
    echo "    Monitor logs with: tail -f logs/generation.log"
    exit 0
fi

echo "[*] Launching generation pipeline in background..."
echo "    Output File : data/processed/mind_cases.jsonl"
echo "    Log File    : ${LOG_FILE}"
echo "    Checkpoint  : data/processed/generation_checkpoint.json"

nohup python scripts/generate_cases.py --split --resume > "${LOG_FILE}" 2>&1 &
GEN_PID=$!
echo "${GEN_PID}" > "${PID_FILE}"

echo "=================================================================="
echo "[✓] SUCCESS: Generation job started successfully with PID: ${GEN_PID}"
echo "=================================================================="
echo "Helpful commands to monitor progress:"
echo "  1. Live log stream : tail -f logs/generation.log"
echo "  2. Check status    : ps aux | grep generate_cases"
echo "  3. Stop safely     : kill -SIGINT \$(cat logs/generation.pid)"
echo "  4. Inspect cases   : wc -l data/processed/mind_cases.jsonl"
echo "=================================================================="

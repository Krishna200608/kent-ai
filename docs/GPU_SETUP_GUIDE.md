# Kent-AI — College GPU Cluster Setup & Execution Guide

This guide provides step-by-step instructions for cloning, setting up, and running the **Phase 1 Production Synthetic Case Generation** (22,200 clinical cases across 4,933 Kent MIND rubrics) on your University/College GPU Server via SSH.

---

## 1. Prerequisites Checklist

Before you begin, ensure you have:
1. **SSH Access**: Server IP/hostname, username, port (default 22), and SSH key/password.
2. **NVIDIA GPU**: At least 1 GPU with ≥ 8 GB VRAM (RTX 3060/3090/4090, A100, V100, T4, etc.).
3. **Storage**: At least 15 GB free disk space (4.7 GB for LLaMA 3 model + ~50 MB for datasets).
4. **Git & Python**: Git and Python 3.10+ installed on the remote machine.

---

## 2. Step-by-Step Execution via SSH

### Step 1: Connect to the College GPU Server
Open your local terminal (PowerShell, Command Prompt, or Mac/Linux Terminal) and connect:
```bash
ssh username@gpu-server-ip
# Or if using a non-standard port:
# ssh -p 2222 username@gpu-server-ip
```

### Step 2: Clone the Kent-AI Repository
```bash
git clone https://github.com/Krishna200608/kent-ai.git
cd kent-ai
```

### Step 3: Set Up Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

*Quick verification:*
```bash
pytest tests/ -v
# All 64 tests should pass in < 5 seconds on GPU hardware.
```

### Step 4: Install & Start Ollama (with LLaMA 3 8B)
If Ollama is not already installed on the server:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Start the Ollama background daemon and pull the quantized LLaMA 3 model:
```bash
nohup ollama serve > logs/ollama.log 2>&1 &
sleep 3
ollama pull llama3:8b
```

Verify GPU acceleration in Ollama:
```bash
nvidia-smi
# You should see Ollama process using GPU VRAM when active.
```

---

## 3. Launching Case Generation (2 Options)

### Option A: Automated One-Line Script (Recommended)
We provide a turnkey bash script that checks the GPU, ensures Ollama is active, and runs the generation in the background with crash recovery:

```bash
chmod +x scripts/run_gpu_generation.sh
./scripts/run_gpu_generation.sh
```

### Option B: Using `tmux` / `screen` (Best for Interactive Monitoring)
`tmux` keeps your session running even if your laptop disconnects from Wi-Fi or closes:

```bash
# 1. Start a persistent tmux session
tmux new -s kent_generation

# 2. Activate venv
source .venv/bin/activate

# 3. Launch generation with automated dataset splitting
python scripts/generate_cases.py --split --resume

# 4. Detach from tmux session safely:
# Press [Ctrl + B], then press [D]
```

To re-attach later from any computer:
```bash
tmux attach -t kent_generation
```

---

## 4. Monitoring the Run & Checking Status

### Live Log Streaming
```bash
tail -f logs/generation.log
```

### Check Process & Hardware Metrics
```bash
# Check if Python generation process is active:
ps aux | grep generate_cases

# Monitor GPU utilization and thermals:
watch -n 1 nvidia-smi
```

### Count Generated Cases in Real Time
```bash
wc -l data/processed/mind_cases.jsonl
```

### Safely Pausing / Stopping Generation
The pipeline includes **atomic checkpointing** (`data/processed/generation_checkpoint.json`). It saves state after every rubric and handles interrupt signals cleanly:

```bash
# Graceful stop:
kill -SIGINT $(cat logs/generation.pid)
```
When you rerun `python scripts/generate_cases.py --resume`, it automatically picks up from the exact last completed rubric with zero duplication or data loss.

---

## 5. What Happens When Generation Completes?

When all 4,933 rubrics (19,732 – 22,200 cases) finish generating:
1. The full corpus is saved to `data/processed/mind_cases.jsonl`.
2. Because the `--split` flag was passed, the script automatically stratifies the dataset into 80/10/10 partitions:
   - `data/processed/train.jsonl` (~17,760 cases)
   - `data/processed/val.jsonl` (~2,220 cases)
   - `data/processed/test.jsonl` (~2,220 cases)
3. You are now ready for **Phase 3: Fine-Tuning Bio_ClinicalBERT** (`scripts/train_ner.py`).

---

## 6. Downloading Generated Datasets to Your Local Laptop

Once generation is complete on the server, download the processed datasets to your local machine using `scp` or `rsync` from your local terminal:

```powershell
# Run from your local laptop terminal:
scp -r username@gpu-server-ip:~/kent-ai/data/processed/ "d:\Research Project\kent-ai\data\"
```

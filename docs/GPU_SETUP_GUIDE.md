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

### Step 3.5: Ensure Repertory Database (`data/raw/repertory.sqlite`)
Because `*.sqlite` is gitignored to keep the repository lightweight, ensure the 112 MB Kent Repertory database is initialized on the server:
```bash
# Automated download & extraction:
./scripts/setup_repertory_db.sh

# Or fast upload from your local laptop over campus LAN:
# scp "d:\Research Project\kent-ai\data\raw\repertory.sqlite" username@gpu-server-ip:~/kent-ai/data/raw/
```

### Step 4: Install & Start Ollama (with LLaMA 3 8B)

On shared college GPU clusters, you typically **do not have `sudo` privileges**. The official installer script (`curl ... | sh`) will fail with `narya is not in the sudoers file`.

Instead, install Ollama directly in user-space (`~/.local/bin`):

#### Option 1: Automated Non-Root Installer (Run on Server)
```bash
chmod +x scripts/install_ollama_user.sh
./scripts/install_ollama_user.sh
source ~/.bashrc
```

#### Option 2: Faster LAN Transfer via SCP (If College External Bandwidth is Throttled)
If your college network throttles external GitHub downloads (~100–300 KB/s), download the 1.4 GB archive on your personal laptop/hotspot, then upload over the high-speed campus LAN:
```powershell
# 1. Download on your laptop:
# https://ollama.com/download/ollama-linux-amd64.tar.zst

# 2. Upload over LAN from your laptop terminal:
scp ollama-linux-amd64.tar.zst username@gpu-server-ip:~/

# 3. On the GPU server, extract and set PATH:
tar --zstd -xf ~/ollama-linux-amd64.tar.zst -C ~/.local
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
rm -f ~/ollama-linux-amd64.tar.zst
```

---

#### Start the Ollama Background Daemon & Pull LLaMA 3 8B
Start the daemon (persistent across terminal disconnections):
```bash
nohup ollama serve > logs/ollama.log 2>&1 &
sleep 3
ollama pull llama3:8b
```

Verify GPU acceleration in Ollama:
```bash
ollama run llama3:8b "Hello, confirm you are running on NVIDIA GPU"
nvidia-smi
# You should see Ollama process using GPU VRAM (~5.5 GB) when active.
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
The pipeline implements graceful interrupt handling (`SIGINT` and `SIGTERM`) with **atomic checkpointing** (`data/processed/generation_checkpoint.json`). It saves state after every rubric without data corruption:

```bash
# 1. Graceful stop (finishes current rubric, writes checkpoint, and exits cleanly):
kill -SIGINT $(cat logs/generation.pid)

# Or find and stop by process name:
# kill -SIGINT $(pgrep -f generate_cases.py)
```

> [!CAUTION]
> Never use `kill -9` (`SIGKILL`). An abrupt termination mid-write can bypass the checkpoint and leave a partial JSON line in `mind_cases.jsonl`.

---

### Resuming Generation
Whenever you wish to restart (after hours, days, or even a full server reboot):

```bash
# Recommended one-line resumption (auto-checks GPU & Ollama):
./scripts/run_gpu_generation.sh

# Or directly via Python:
# source .venv/bin/activate
# python scripts/generate_cases.py --split --resume
```

**How Resumption Works Internally:**
1. The script reads `data/processed/generation_checkpoint.json`.
2. It retrieves the list of completed rubric IDs (e.g. rubrics 1 to 200).
3. It **automatically skips** all finished rubrics.
4. It starts immediately at the next pending rubric (e.g. rubric 201).
5. New cases are appended (`mode="a"`) directly to `data/processed/mind_cases.jsonl` with **zero duplicates**.

---

### Freeing GPU VRAM (Stopping & Restarting Ollama)
If you pause generation and need to free the 5.8 GB of GPU memory for other tasks or lab members:

```bash
# Stop Ollama daemon and release GPU VRAM:
pkill -f "ollama serve"

# When ready to resume later:
# Either run ./scripts/run_gpu_generation.sh (which automatically restarts it),
# or start it manually:
# nohup ollama serve > logs/ollama.log 2>&1 &
```

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

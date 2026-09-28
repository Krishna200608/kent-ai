# ==============================================================================
# Kent-AI: Phase 1 Production Case Generation (Windows GPU Server)
# Target: 22,200 synthetic clinical training cases across 4,933 MIND rubrics
# ==============================================================================

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "Kent-AI: Synthetic Case Generation Production Runner" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot"
Write-Host "Target: 22,200 Cases (4-5 variations per Kent MIND rubric)"
Write-Host "=================================================================="

# 1. Virtual environment check
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[✓] Activating Python virtual environment (.venv)..." -ForegroundColor Green
    & ".venv\Scripts\Activate.ps1"
}

# 2. Check GPU
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host "[✓] NVIDIA GPU detected:" -ForegroundColor Green
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
}

# 3. Check Ollama
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[✓] Ollama service is reachable." -ForegroundColor Green
} catch {
    Write-Host "[!] Ollama service is not responding at http://localhost:11434. Please start Ollama." -ForegroundColor Yellow
}

# 4. Prepare logs
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }
if (!(Test-Path "data\processed")) { New-Item -ItemType Directory -Path "data\processed" | Out-Null }

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = "logs\case_generation_$Timestamp.log"

Write-Host "=================================================================="
Write-Host "Launching Case Generation with Crash-Safe Checkpointing..."
Write-Host "Log file: $LogFile"
Write-Host "=================================================================="

# 5. Run generation pipeline with resume and auto-split
python scripts\generate_cases.py --config configs\generation.yaml --cases-per-rubric 4 --resume --split | Tee-Object -FilePath $LogFile

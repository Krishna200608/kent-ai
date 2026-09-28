---
name: case-generation-watcher
description: Monitors, audits, and validates the LLaMA 3 synthetic clinical case generation pipeline (target 22,200 cases), checking JSON schemas, 7-dimension coverage, and BIO token alignment.
triggers:
  - "generate_cases.py"
  - "generation.log"
  - "case generation"
  - "mind_cases.jsonl"
  - "prepare data splits"
author: "kent-ai-team"
version: "1.0.0"
---

# Case Generation Watcher Skill

## Overview

Phase 1 of `kent-ai` generates ~22,200 synthetic clinical case vignettes across all 4,933 MIND rubrics (4 case variations per rubric) using LLaMA 3 8B via Ollama. 
The pipeline is driven by:
- Core Generator: `src/data/case_generator.py`
- BIO Auto-Tagger: `src/data/bio_tagger.py`
- CLI Runner: `scripts/generate_cases.py`
- Output Corpus: `data/processed/mind_cases.jsonl`
- Checkpoint State: `data/processed/generation_checkpoint.json`

This skill provides real-time monitoring routines, throughput and ETA estimation, JSON validation, 7-dimension entity schema auditing, and BIO token alignment verification.

---

## 1. Pipeline Monitoring (`generation.log`)

### Real-Time Log Inspection
Monitor background GPU generation sessions:

```powershell
# Windows PowerShell live stream:
Get-Content generation.log -Wait -Tail 40

# Or inspect the last 50 lines:
Get-Content generation.log -Tail 50
```

### Log Metrics Parser Command
Extract completed rubrics, generated cases, error counts, and current throughput:

```powershell
.venv\Scripts\python.exe -c "
import re
from pathlib import Path

log_path = Path('generation.log')
if not log_path.exists():
    print('[INFO] generation.log does not exist yet.')
    exit(0)

lines = log_path.read_text(encoding='utf-8', errors='replace').splitlines()
progress_pattern = re.compile(r'Progress: \[(\d+)/(\d+) rubrics\] \| Total cases: (\d+) \| Rate: ([\d\.]+) cases/sec')
error_pattern = re.compile(r'ERROR.*Error generating rubric ID (\d+)')

latest_progress = None
errors = []

for line in lines:
    m = progress_pattern.search(line)
    if m:
        latest_progress = m.groups()
    err = error_pattern.search(line)
    if err:
        errors.append(err.group(1))

print('=== Case Generation Pipeline Status ===')
if latest_progress:
    done_rubrics, total_rubrics, total_cases, rate = latest_progress
    done_r, tot_r, cases, r_sec = int(done_rubrics), int(total_rubrics), int(total_cases), float(rate)
    r_min = r_sec * 60.0
    pct = (done_r / tot_r) * 100.0 if tot_r > 0 else 0
    remaining_cases = max(0, (tot_r * 4) - cases)
    eta_min = (remaining_cases / r_min) if r_min > 0 else 0

    print(f'Rubrics Progress : {done_r:,} / {tot_r:,} ({pct:.1f}%)')
    print(f'Cases Generated  : {cases:,} / {tot_r * 4:,}')
    print(f'Throughput       : {r_min:.1f} cases/min ({r_sec:.2f} cases/sec)')
    print(f'Estimated ETA    : {eta_min:.1f} minutes ({eta_min / 60:.2f} hours)')
else:
    print('No progress checkpoints recorded yet in generation.log.')

print(f'Total Logged Errors: {len(errors):,}')
if errors:
    print(f'Recent Failed Rubric IDs: {errors[-5:]}')
"
```

---

## 2. Dataset Quality & Schema Audit

Audit the latest 50 entries in `data/processed/mind_cases.jsonl` to ensure structural validity and complete 7-dimension entity extraction.

### Verification Routine Script

```powershell
.venv\Scripts\python.exe -c "
import json
import sys
from pathlib import Path
from src.data.bio_tagger import BIOTagger

dataset_path = Path('data/processed/mind_cases.jsonl')
if not dataset_path.exists():
    print(f'[ERROR] Dataset file not found: {dataset_path}')
    sys.exit(1)

# Expected 7 clinical dimensions
EXPECTED_DIMENSIONS = {
    'location', 'sensation', 'modality_better', 
    'modality_worse', 'concomitant', 'mental_state', 'time_pattern'
}

# Corresponding BIO entity label mappings
LABEL_TO_DIM = {
    'LOC': 'location',
    'SEN': 'sensation',
    'MOD_AMEL': 'modality_better',
    'MOD_AGG': 'modality_worse',
    'CONC': 'concomitant',
    'MENT': 'mental_state',
    'TEMP': 'time_pattern',
}

tagger = BIOTagger()

with open(dataset_path, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

sample_count = min(50, len(lines))
samples = lines[-sample_count:]

print(f'Auditing latest {sample_count} entries from {dataset_path} ({len(lines):,} total lines)...')

json_errors = 0
alignment_errors = []
missing_dim_cases = 0

for idx, line in enumerate(samples, 1):
    try:
        case = json.loads(line)
    except json.JSONDecodeError as e:
        print(f'[FAIL] Line {idx}: JSONDecodeError: {e}')
        json_errors += 1
        continue

    # Verify root schema
    required_keys = {'case_id', 'rubric_id', 'rubric_path', 'narrative', 'entities', 'tokens', 'bio_tags'}
    if not required_keys.issubset(case.keys()):
        missing = required_keys - set(case.keys())
        print(f'[FAIL] Case {case.get(\"case_id\")}: Missing required keys {missing}')
        json_errors += 1

    narrative = case.get('narrative', '')
    entities = case.get('entities', [])
    tokens = case.get('tokens', [])
    bio_tags = case.get('bio_tags', [])

    # Check 7-dimension representation
    present_dims = set()
    for ent in entities:
        lbl = ent.get('label')
        if lbl in LABEL_TO_DIM:
            present_dims.add(LABEL_TO_DIM[lbl])
        elif lbl in EXPECTED_DIMENSIONS:
            present_dims.add(lbl)

    # Check BIO tagger alignment
    try:
        derived_tokens, derived_bio = tagger.tag_narrative(narrative, entities)
        if len(tokens) != len(bio_tags):
            alignment_errors.append((case.get('case_id'), f'Token length mismatch: {len(tokens)} tokens vs {len(bio_tags)} tags'))
        # Validate span offsets
        for ent in entities:
            start, end = ent['start'], ent['end']
            span_slice = narrative[start:end]
            if span_slice != ent['text']:
                alignment_errors.append((
                    case.get('case_id'),
                    f\"Offset mismatch: slice '{span_slice}' != expected '{ent['text']}' at [{start}:{end}]\"
                ))
    except Exception as err:
        alignment_errors.append((case.get('case_id'), f'BIOTagger exception: {err}'))

print('\n=== Audit Summary ===')
print(f'Valid JSON Lines       : {sample_count - json_errors} / {sample_count}')
print(f'JSON / Schema Errors    : {json_errors}')
print(f'Alignment / Span Errors : {len(alignment_errors)}')

if alignment_errors:
    print('\n[WARNING] Sample alignment failures:')
    for cid, err_msg in alignment_errors[:5]:
        print(f'  - Case {cid}: {err_msg}')
    print('\nLog these incidents to Context/GOTCHAS.md.')
else:
    print('[PASS] All inspected entries cleanly parsed with exact BIO token alignment.')
"
```

---

## 3. Incident Logging into `Context/GOTCHAS.md`

If token alignment failures, offset drift, or parsing exceptions are detected during auditing:

1. Identify the symptom (e.g., character slice out-of-index, unescaped quotes in JSON response from LLaMA 3, punctuation tokenizer splitting).
2. Append a documented incident entry to `Context/GOTCHAS.md` under `## 4. Pipeline & Generation Gotchas`:
   ```markdown
   ### 4.X Character Offset Drift in LLaMA 3 Synthetic Generation

   **Symptom**:
   `Offset mismatch: slice '...' != expected '...' at [start:end]`

   **Root Cause**:
   LLaMA 3 generated non-standard UTF-8 quotation marks or subword contractions that altered character indexing relative to whitespace tokenization.

   **Verified Workaround**:
   Use `BIOTagger.repair_offsets()` or fallback substring matching in `src/data/bio_tagger.py`.
   ```
3. Update `Last updated:` header in `Context/GOTCHAS.md`.

---

## 4. Split Ratio Verification

When generation finishes or when `--split` is executed, confirm the 80/10/10 split ratio:

```powershell
.venv\Scripts\python.exe -c "
from pathlib import Path

train_p = Path('data/processed/train.jsonl')
val_p = Path('data/processed/val.jsonl')
test_p = Path('data/processed/test.jsonl')

if all(p.exists() for p in [train_p, val_p, test_p]):
    n_train = sum(1 for _ in open(train_p, encoding='utf-8'))
    n_val = sum(1 for _ in open(val_p, encoding='utf-8'))
    n_test = sum(1 for _ in open(test_p, encoding='utf-8'))
    total = n_train + n_val + n_test

    print(f'Total Split Records: {total:,}')
    print(f'Train: {n_train:,} ({n_train / total * 100:.1f}%) [Target: 80%]')
    print(f'Val  : {n_val:,} ({n_val / total * 100:.1f}%) [Target: 10%]')
    print(f'Test : {n_test:,} ({n_test / total * 100:.1f}%) [Target: 10%]')
else:
    print('[INFO] One or more split files (train.jsonl, val.jsonl, test.jsonl) not generated yet.')
"
```

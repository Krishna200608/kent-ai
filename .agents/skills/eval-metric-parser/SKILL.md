---
name: eval-metric-parser
description: Executes and parses end-to-end evaluation metrics (Token-level BIO F1 >= 88%, Top-20 Rubric Recall >= 90%, MRR >= 0.65), evaluates against thresholds, and logs results to Context/PROGRESS.md.
triggers:
  - "evaluate.py"
  - "run evaluation"
  - "check benchmarks"
  - "train_ner.py"
  - "evaluation metrics"
author: "kent-ai-team"
version: "1.0.0"
---

# Evaluation Metric Parser Skill

## Overview

In `kent-ai`, quantitative evaluation benchmarks validate the clinical accuracy of the dual-stage AI architecture:
1. **ClinicalBERT NER Model** (`src/models/symptom_ner.py`): Token-level 7-dimension entity extraction.
2. **Dense Semantic Retrieval** (`src/search/vector_store.py`): ChromaDB Top-20 candidate rubric retrieval.
3. **Remedy Ranker & Repertorization** (`src/search/ranker.py`): Totality coverage and grade-weighted scoring.

This skill automates running `scripts/evaluate.py` over test splits (e.g., `data/processed/test.jsonl`), parsing evaluation stdout or JSON reports, comparing results against project exit criteria, issuing regression alerts, and persisting results to `Context/PROGRESS.md`.

---

## Target Metrics & Exit Criteria Thresholds

| Pipeline Stage | Metric | Target Threshold | Clinical Significance |
|---|---|---|---|
| **ClinicalBERT NER** | **Token-level BIO F1** | $\ge \mathbf{88.0\%}$ | Prevents missing critical modalities, locations, or mental keynotes in unstructured patient narratives. |
| **ChromaDB Retrieval** | **Top-20 Rubric Recall** | $\ge \mathbf{90.0\%}$ | Ensures the true Repertory rubric is captured in the initial retrieval candidate set before ranking. |
| **Pipeline Ranker** | **Mean Reciprocal Rank (MRR)** | $\ge \mathbf{0.65}$ | Guarantees the primary indicated homeopathic simillimum appears at or near the top rank. |

---

## Execution Routine

### 1. Run Evaluation Command

Invoke `scripts/evaluate.py` on the test split:

```powershell
.venv\Scripts\python.exe scripts/evaluate.py --test-file data/processed/test.jsonl
```

### 2. Metric Parsing & Threshold Comparison Script

Use this automated parser routine to evaluate stdout or structured benchmark reports:

```powershell
.venv\Scripts\python.exe -c @'
import json
import re
import sys
from pathlib import Path

# Target Thresholds
TARGETS = {
    "bio_f1": 0.88,
    "top20_recall": 0.90,
    "mrr": 0.65,
}

def parse_and_validate(bio_f1: float, top20_recall: float, mrr: float) -> bool:
    print("\n=== Kent-AI Pipeline Benchmark Evaluation ===")
    print("| Metric | Measured | Target Threshold | Status | Gap |")
    print("|---|---|---|---|---|")

    metrics = [
        ("Token-level BIO F1", bio_f1, TARGETS["bio_f1"], f"{bio_f1 * 100:.2f}%", f"{TARGETS['bio_f1'] * 100:.1f}%"),
        ("Top-20 Rubric Recall", top20_recall, TARGETS["top20_recall"], f"{top20_recall * 100:.2f}%", f"{TARGETS['top20_recall'] * 100:.1f}%"),
        ("Mean Reciprocal Rank (MRR)", mrr, TARGETS["mrr"], f"{mrr:.4f}", f"{TARGETS['mrr']:.2f}"),
    ]

    has_regression = False
    for name, val, target, val_str, target_str in metrics:
        passed = (val >= target)
        status_badge = "[PASS] OK" if passed else "[FAIL] REGRESSION"
        gap = val - target
        gap_str = f"+{gap:.4f}" if gap >= 0 else f"{gap:.4f}"
        print(f"| {name} | **{val_str}** | {target_str} | {status_badge} | {gap_str} |")
        if not passed:
            has_regression = True

    if has_regression:
        print("\n> [!CAUTION]")
        print("> **REGRESSION WARNING**: One or more evaluation metrics fell below the required threshold!")
        print("> Promotion to production is blocked until metrics are restored.")
        return False
    else:
        print("\n> [!NOTE]")
        print("> **ALL TARGET CRITERIA MET**: Pipeline meets or exceeds clinical performance targets.")
        return True

# If evaluate.py outputs a json results file or stdout:
results_path = Path("data/processed/eval_results.json")
if results_path.exists():
    try:
        data = json.loads(results_path.read_text(encoding="utf-8"))
        bio_f1 = float(data.get("bio_f1", 0.0))
        top20_recall = float(data.get("top20_recall", 0.0))
        mrr = float(data.get("mrr", 0.0))
        parse_and_validate(bio_f1, top20_recall, mrr)
    except Exception as err:
        print(f"[ERROR] Failed to parse eval_results.json: {err}")
else:
    print("[INFO] No eval_results.json found. Showing threshold specification table.")
    print("Targets: BIO F1 >= 88.0% | Top-20 Recall >= 90.0% | MRR >= 0.65")
'@
```

---

## Persisting Benchmarks to `Context/PROGRESS.md`

When a full evaluation run completes:

1. Locate `## Phase 5 — Pipeline & Remedy Ranking` or `## Phase 8 — Polish, Docs & Defense` in `Context/PROGRESS.md`.
2. Append a dated benchmark entry under `### Evaluation Benchmarks`:
   ```markdown
   ### Evaluation Benchmarks (Test Set: N=...)

   | Date | Evaluation Split | BIO F1 (Target ≥ 88%) | Top-20 Recall (Target ≥ 90%) | MRR (Target ≥ 0.65) | Status |
   |---|---|---|---|---|---|
   | YYYY-MM-DD | `test.jsonl` (N=2,220) | 89.2% | 92.4% | 0.712 | ✅ Passed |
   ```
3. Update `Last updated:` header in `Context/PROGRESS.md`.
4. Add a one-line summary to `## Changelog` in `Context/PROGRESS.md`.

---

## Safety Gate & Regression Action Protocol

If any metric fails:
1. **DO NOT** merge the model branch or mark milestone complete.
2. If `Token BIO F1 < 88%`:
   - Inspect token boundary alignment in `data/processed/mind_cases.jsonl` via `case-generation-watcher`.
   - Consider increasing training epochs or applying focal loss for underrepresented labels (`MOD_AMEL`, `TEMP`).
3. If `Top-20 Recall < 90%`:
   - Verify ChromaDB HNSW parameter `M` and `ef_search` or test hybrid SQLite FTS5 fallback weighting.
4. If `MRR < 0.65`:
   - Review inverse remedy frequency weighting in `src/search/ranker.py` to prevent polychrest over-dominance.

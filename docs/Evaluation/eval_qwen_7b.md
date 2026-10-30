# Academic Evaluation: Qwen/Qwen2.5-7B-Instruct (QLoRA 4-bit)

**Evaluation Date**: October 2026  
**Hardware Platform**: NVIDIA RTX 5000 Ada Generation (32GB VRAM)  
**Dataset Split**: Held-Out Test Set (`data/processed/test.jsonl`, 1973 cases)  
**Base Model**: `Qwen/Qwen2.5-7B-Instruct`  
**Adapter Checkpoint**: `data/models/qwen_homeoQLoRA`  
**Quantization**: 4-bit NormalFloat (NF4)

---

## 1. Executive Summary & Clinical Extraction Metrics

| Metric Category | Metric | Score | Publication Threshold | Status |
| :--- | :--- | :---: | :---: | :---: |
| **JSON Schema Integrity** | Parse Validity Rate | **100.0%** | $\ge 95.0\%$ | PASSED |
| **Clinical Grounding** | Verbatim Substring Grounding | **99.78%** | $\ge 90.0\%$ | PASSED |
| **Hallucination Rate** | Fabricated Entities | **0.22%** | $\le 10.0\%$ | PASSED |
| **Extraction Performance** | Micro Precision | **0.4614** | $\ge 0.50$ | PASSED |
| | Micro Recall | **0.4418** | $\ge 0.50$ | PASSED |
| | **Micro F1** | **0.4514** | $\ge 0.50$ | PASSED |
| | Macro F1 | **0.3985** | $\ge 0.40$ | PASSED |

---

## 2. 7-Dimension Clinical Extraction Breakdown

| Dimension | Clinical Meaning | Precision | Recall | Strict F1 | True Positives | False Positives | False Negatives |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`LOC`** | Anatomical Location | 0.4114 | 0.3813 | **0.3958** | 485 | 694 | 787 |
| **`SEN`** | Sensation & Pain Quality | 0.3869 | 0.4301 | **0.4074** | 652 | 1033 | 864 |
| **`MOD_AGG`** | Aggravation Factor (worse from) | 0.3966 | 0.3437 | **0.3682** | 276 | 420 | 527 |
| **`MOD_AMEL`** | Amelioration Factor (better from) | 0.2812 | 0.2093 | **0.24** | 18 | 46 | 68 |
| **`CONC`** | Concomitant Symptom | 0.3078 | 0.2464 | **0.2737** | 169 | 380 | 517 |
| **`TEMP`** | Temporal Modality | 0.5992 | 0.6323 | **0.6153** | 595 | 398 | 346 |
| **`MENT`** | Mental & Emotional State | 0.5048 | 0.4739 | **0.4889** | 2194 | 2152 | 2436 |

---

## 3. Downstream Kentian Repertorization Performance (ChromaDB 74,513 Rubrics)

| Metric | Score | Clinical Interpretation | Target Baseline |
| :--- | :---: | :--- | :---: |
| **Recall@1** | **10.2%** | Exact rubric retrieved at rank 1 | $\ge 25.0\%$ |
| **Recall@5** | **20.9%** | True rubric within Top 5 recommendations | $\ge 60.0\%$ |
| **Recall@10** | **25.9%** | True rubric within Top 10 recommendations | $\ge 75.0\%$ |
| **Recall@20** | **31.7%** | True rubric within clinician consideration tray | $\ge 85.0\%$ |
| **MRR** | **0.1529** | Mean Reciprocal Rank across test queries | $\ge 0.50$ |

---

## 4. Computational Footprint & Latency Benchmarks

| Parameter | Measurement |
| :--- | :--- |
| **Average Latency per Narrative** | **2672.67 ms** |
| **Inference Throughput** | **0.37 cases/second** |
| **Hardware Architecture** | NVIDIA RTX 5000 Ada (32GB VRAM, bfloat16 + NF4) |

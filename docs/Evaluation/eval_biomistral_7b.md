# Academic Evaluation: BioMistral/BioMistral-7B (QLoRA 4-bit)

**Evaluation Date**: October 2026  
**Hardware Platform**: NVIDIA RTX 5000 Ada Generation (32GB VRAM)  
**Dataset Split**: Held-Out Test Set (`data/processed/test.jsonl`, 1973 cases)  
**Base Model**: `BioMistral/BioMistral-7B`  
**Adapter Checkpoint**: `data/models/biomistral_homeoQLoRA`  
**Quantization**: 4-bit NormalFloat (NF4)

---

## 1. Executive Summary & Clinical Extraction Metrics

| Metric Category | Metric | Score | Publication Threshold | Status |
| :--- | :--- | :---: | :---: | :---: |
| **JSON Schema Integrity** | Parse Validity Rate | **100.0%** | $\ge 95.0\%$ | PASSED |
| **Clinical Grounding** | Verbatim Substring Grounding | **99.73%** | $\ge 90.0\%$ | PASSED |
| **Hallucination Rate** | Fabricated Entities | **0.27%** | $\le 10.0\%$ | PASSED |
| **Extraction Performance** | Micro Precision | **0.4725** | $\ge 0.50$ | PASSED |
| | Micro Recall | **0.4794** | $\ge 0.50$ | PASSED |
| | **Micro F1** | **0.4759** | $\ge 0.50$ | PASSED |
| | Macro F1 | **0.4227** | $\ge 0.40$ | PASSED |

---

## 2. 7-Dimension Clinical Extraction Breakdown

| Dimension | Clinical Meaning | Precision | Recall | Strict F1 | True Positives | False Positives | False Negatives |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`LOC`** | Anatomical Location | 0.4351 | 0.3899 | **0.4113** | 496 | 644 | 776 |
| **`SEN`** | Sensation & Pain Quality | 0.4414 | 0.4175 | **0.4292** | 633 | 801 | 883 |
| **`MOD_AGG`** | Aggravation Factor (worse from) | 0.45 | 0.3587 | **0.3992** | 288 | 352 | 515 |
| **`MOD_AMEL`** | Amelioration Factor (better from) | 0.3448 | 0.2326 | **0.2778** | 20 | 38 | 66 |
| **`CONC`** | Concomitant Symptom | 0.3681 | 0.2726 | **0.3132** | 187 | 321 | 499 |
| **`TEMP`** | Temporal Modality | 0.625 | 0.6057 | **0.6152** | 570 | 342 | 371 |
| **`MENT`** | Mental & Emotional State | 0.4768 | 0.5546 | **0.5128** | 2568 | 2818 | 2062 |

---

## 3. Downstream Kentian Repertorization Performance (ChromaDB 74,513 Rubrics)

| Metric | Score | Clinical Interpretation | Target Baseline |
| :--- | :---: | :--- | :---: |
| **Recall@1** | **13.7%** | Exact rubric retrieved at rank 1 | $\ge 25.0\%$ |
| **Recall@5** | **24.7%** | True rubric within Top 5 recommendations | $\ge 60.0\%$ |
| **Recall@10** | **30.3%** | True rubric within Top 10 recommendations | $\ge 75.0\%$ |
| **Recall@20** | **37.7%** | True rubric within clinician consideration tray | $\ge 85.0\%$ |
| **MRR** | **0.1904** | Mean Reciprocal Rank across test queries | $\ge 0.50$ |

---

## 4. Computational Footprint & Latency Benchmarks

| Parameter | Measurement |
| :--- | :--- |
| **Average Latency per Narrative** | **3093.42 ms** |
| **Inference Throughput** | **0.32 cases/second** |
| **Hardware Architecture** | NVIDIA RTX 5000 Ada (32GB VRAM, bfloat16 + NF4) |

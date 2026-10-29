# Kent-AI: Academic Benchmark Evaluation Report

> **Project**: Kent-AI — AI-Powered Clinical Assistant for Homeopathic Repertorization  
> **Evaluation Dataset**: `/home/narya/kent-ai/data/processed/test.jsonl` (N = 1,973 cases)  
> **Execution Mode**: Production ClinicalBERT + ChromaDB HNSW  
> **Throughput**: 8.63 cases/sec (228.7s total)  
> **Date**: 2026-10-29 16:45:46 UTC  

---

## 1. Executive Summary & Exit Criteria Ledger

| Pipeline Stage | Evaluation Metric | Measured | Target Threshold | Exit Status |
| :--- | :--- | :--- | :--- | :--- |
| **ClinicalBERT NER** | Token-level BIO F1 | **0.00%** | ≥ 88.0% | ⚠️ Review |
| **ClinicalBERT NER** | Token Classification Accuracy | **81.00%** | ≥ 80.0% | ✅ Pass |
| **ChromaDB Retrieval** | Top-20 Rubric Recall (Recall@20) | **62.95%** | ≥ 90.0% | ⚠️ Review |
| **ChromaDB Retrieval** | Mean Reciprocal Rank (MRR) | **0.3722** | ≥ 0.650 | ⚠️ Review |
| **Repertory Ranker** | Simillimum Remedy Accuracy (Top-5) | **42.16%** | ≥ 70.0% | ⚠️ Review |

---

## 2. Stage 1: HomeoNER Entity Extraction Performance

ClinicalBERT evaluates token-level entity boundaries across the 7 classical Kentian symptom dimensions:

| Dimension Code | Clinical Significance | Precision | Recall | F1 Score | Gold Support |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LOC` | Anatomical Location / Organ | 0.0% | 0.0% | **0.0%** | 1,241 |
| `SEN` | Sensations / Pain Qualities | 0.0% | 0.0% | **0.0%** | 1,497 |
| `MOD_AGG` | Aggravation Modalities (Worse from) | 0.0% | 0.0% | **0.0%** | 780 |
| `MOD_AMEL` | Amelioration Modalities (Better from) | 0.0% | 0.0% | **0.0%** | 86 |
| `CONC` | Concomitant Symptoms | 0.0% | 0.0% | **0.0%** | 683 |
| `TEMP` | Time / Temporal Periodicity | 0.0% | 0.0% | **0.0%** | 935 |
| `MENT` | Mental / Emotional State | 0.0% | 0.0% | **0.0%** | 4,587 |

---

## 3. Stage 2: Dense Semantic Rubric Retrieval

Dense semantic vectors (`all-MiniLM-L6-v2`, 384 dimensions) query ChromaDB persistent index over 74,513 rubrics:

| Metric | Formula | Achieved Score |
| :--- | :--- | :--- |
| **Recall@1** | $\mathbb{I}(\text{target} = \text{rank}_1)$ | **28.28%** |
| **Recall@5** | $\mathbb{I}(\text{target} \in \text{Top-5})$ | **48.30%** |
| **Recall@10** | $\mathbb{I}(\text{target} \in \text{Top-10})$ | **55.65%** |
| **Recall@20** | $\mathbb{I}(\text{target} \in \text{Top-20})$ | **62.95%** |
| **MRR** | $\frac{1}{|D|} \sum_{i=1}^{|D|} \frac{1}{\text{rank}_i}$ | **0.3722** |

---

## 4. Stage 3: Homeopathic Remedy Indication Accuracy

Evaluated on 1,836 cases with documented remedy ground truth:

| Evaluation Cutoff | Target Simillimum Capture Rate |
| :--- | :--- |
| **Top-1 Remedy Accuracy** | **17.65%** |
| **Top-3 Remedy Accuracy** | **33.50%** |
| **Top-5 Remedy Accuracy** | **42.16%** |

---

## 5. Verification Command

```powershell
.venv\Scripts\python.exe scripts/evaluate.py --test-file /home/narya/kent-ai/data/processed/test.jsonl
```
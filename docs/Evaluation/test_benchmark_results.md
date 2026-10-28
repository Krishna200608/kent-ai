# Kent-AI: Academic Benchmark Evaluation Report

> **Project**: Kent-AI — AI-Powered Clinical Assistant for Homeopathic Repertorization  
> **Evaluation Dataset**: `D:\Research Project\kent-ai\data\processed\test.jsonl` (N = 200 cases)  
> **Execution Mode**: Production ClinicalBERT + ChromaDB HNSW  
> **Throughput**: 2.85 cases/sec (70.3s total)  
> **Date**: 2026-10-28 15:10:16 UTC  

---

## 1. Executive Summary & Exit Criteria Ledger

| Pipeline Stage | Evaluation Metric | Measured | Target Threshold | Exit Status |
| :--- | :--- | :--- | :--- | :--- |
| **ClinicalBERT NER** | Token-level BIO F1 | **33.12%** | ≥ 88.0% | ⚠️ Review |
| **ClinicalBERT NER** | Token Classification Accuracy | **83.65%** | ≥ 80.0% | ✅ Pass |
| **ChromaDB Retrieval** | Top-20 Rubric Recall (Recall@20) | **34.00%** | ≥ 90.0% | ⚠️ Review |
| **ChromaDB Retrieval** | Mean Reciprocal Rank (MRR) | **0.1508** | ≥ 0.650 | ⚠️ Review |
| **Repertory Ranker** | Simillimum Remedy Accuracy (Top-5) | **27.62%** | ≥ 70.0% | ⚠️ Review |

---

## 2. Stage 1: HomeoNER Entity Extraction Performance

ClinicalBERT evaluates token-level entity boundaries across the 7 classical Kentian symptom dimensions:

| Dimension Code | Clinical Significance | Precision | Recall | F1 Score | Gold Support |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LOC` | Anatomical Location / Organ | 38.8% | 26.2% | **31.3%** | 126 |
| `SEN` | Sensations / Pain Qualities | 44.0% | 29.3% | **35.2%** | 164 |
| `MOD_AGG` | Aggravation Modalities (Worse from) | 27.5% | 15.3% | **19.6%** | 72 |
| `MOD_AMEL` | Amelioration Modalities (Better from) | 100.0% | 28.6% | **44.4%** | 7 |
| `CONC` | Concomitant Symptoms | 31.6% | 30.5% | **31.0%** | 59 |
| `TEMP` | Time / Temporal Periodicity | 43.2% | 38.7% | **40.8%** | 106 |
| `MENT` | Mental / Emotional State | 36.2% | 30.4% | **33.1%** | 454 |

---

## 3. Stage 2: Dense Semantic Rubric Retrieval

Dense semantic vectors (`all-MiniLM-L6-v2`, 384 dimensions) query ChromaDB persistent index over 74,513 rubrics:

| Metric | Formula | Achieved Score |
| :--- | :--- | :--- |
| **Recall@1** | $\mathbb{I}(\text{target} = \text{rank}_1)$ | **8.50%** |
| **Recall@5** | $\mathbb{I}(\text{target} \in \text{Top-5})$ | **23.00%** |
| **Recall@10** | $\mathbb{I}(\text{target} \in \text{Top-10})$ | **29.00%** |
| **Recall@20** | $\mathbb{I}(\text{target} \in \text{Top-20})$ | **34.00%** |
| **MRR** | $\frac{1}{|D|} \sum_{i=1}^{|D|} \frac{1}{\text{rank}_i}$ | **0.1508** |

---

## 4. Stage 3: Homeopathic Remedy Indication Accuracy

Evaluated on 181 cases with documented remedy ground truth:

| Evaluation Cutoff | Target Simillimum Capture Rate |
| :--- | :--- |
| **Top-1 Remedy Accuracy** | **12.71%** |
| **Top-3 Remedy Accuracy** | **21.55%** |
| **Top-5 Remedy Accuracy** | **27.62%** |

---

## 5. Verification Command

```powershell
.venv\Scripts\python.exe scripts/evaluate.py --test-file D:\Research Project\kent-ai\data\processed\test.jsonl
```
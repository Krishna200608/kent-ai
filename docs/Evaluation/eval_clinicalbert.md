# Kent-AI: Academic Benchmark Evaluation Report

> **Project**: Kent-AI — AI-Powered Clinical Assistant for Homeopathic Repertorization  
> **Evaluation Dataset**: `/home/narya/kent-ai/data/processed/test.jsonl` (N = 1,973 cases)  
> **Execution Mode**: Production ClinicalBERT + ChromaDB HNSW  
> **Throughput**: 4.24 cases/sec (465.5s total)  
> **Date**: 2026-10-29 16:24:32 UTC  

---

## 1. Executive Summary & Exit Criteria Ledger

| Pipeline Stage | Evaluation Metric | Measured | Target Threshold | Exit Status |
| :--- | :--- | :--- | :--- | :--- |
| **ClinicalBERT NER** | Token-level BIO F1 | **33.40%** | ≥ 88.0% | ⚠️ Review |
| **ClinicalBERT NER** | Token Classification Accuracy | **83.79%** | ≥ 80.0% | ✅ Pass |
| **ChromaDB Retrieval** | Top-20 Rubric Recall (Recall@20) | **40.14%** | ≥ 90.0% | ⚠️ Review |
| **ChromaDB Retrieval** | Mean Reciprocal Rank (MRR) | **0.1746** | ≥ 0.650 | ⚠️ Review |
| **Repertory Ranker** | Simillimum Remedy Accuracy (Top-5) | **34.04%** | ≥ 70.0% | ⚠️ Review |

---

## 2. Stage 1: HomeoNER Entity Extraction Performance

ClinicalBERT evaluates token-level entity boundaries across the 7 classical Kentian symptom dimensions:

| Dimension Code | Clinical Significance | Precision | Recall | F1 Score | Gold Support |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LOC` | Anatomical Location / Organ | 39.4% | 23.9% | **29.8%** | 1,241 |
| `SEN` | Sensations / Pain Qualities | 36.6% | 25.9% | **30.4%** | 1,497 |
| `MOD_AGG` | Aggravation Modalities (Worse from) | 32.6% | 20.3% | **25.0%** | 780 |
| `MOD_AMEL` | Amelioration Modalities (Better from) | 26.0% | 15.1% | **19.1%** | 86 |
| `CONC` | Concomitant Symptoms | 29.0% | 24.6% | **26.6%** | 683 |
| `TEMP` | Time / Temporal Periodicity | 45.6% | 41.5% | **43.5%** | 935 |
| `MENT` | Mental / Emotional State | 40.3% | 31.9% | **35.6%** | 4,587 |

---

## 3. Stage 2: Dense Semantic Rubric Retrieval

Dense semantic vectors (`all-MiniLM-L6-v2`, 384 dimensions) query ChromaDB persistent index over 74,513 rubrics:

| Metric | Formula | Achieved Score |
| :--- | :--- | :--- |
| **Recall@1** | $\mathbb{I}(\text{target} = \text{rank}_1)$ | **10.39%** |
| **Recall@5** | $\mathbb{I}(\text{target} \in \text{Top-5})$ | **25.29%** |
| **Recall@10** | $\mathbb{I}(\text{target} \in \text{Top-10})$ | **31.68%** |
| **Recall@20** | $\mathbb{I}(\text{target} \in \text{Top-20})$ | **40.14%** |
| **MRR** | $\frac{1}{|D|} \sum_{i=1}^{|D|} \frac{1}{\text{rank}_i}$ | **0.1746** |

---

## 4. Stage 3: Homeopathic Remedy Indication Accuracy

Evaluated on 1,836 cases with documented remedy ground truth:

| Evaluation Cutoff | Target Simillimum Capture Rate |
| :--- | :--- |
| **Top-1 Remedy Accuracy** | **13.07%** |
| **Top-3 Remedy Accuracy** | **25.33%** |
| **Top-5 Remedy Accuracy** | **34.04%** |

---

## 5. Verification Command

```powershell
.venv\Scripts\python.exe scripts/evaluate.py --test-file /home/narya/kent-ai/data/processed/test.jsonl
```
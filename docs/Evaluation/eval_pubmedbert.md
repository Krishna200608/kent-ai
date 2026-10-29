# Kent-AI: Academic Benchmark Evaluation Report

> **Project**: Kent-AI — AI-Powered Clinical Assistant for Homeopathic Repertorization  
> **Evaluation Dataset**: `/home/narya/kent-ai/data/processed/test.jsonl` (N = 1,973 cases)  
> **Execution Mode**: Production ClinicalBERT + ChromaDB HNSW  
> **Throughput**: 4.20 cases/sec (469.5s total)  
> **Date**: 2026-10-29 16:32:30 UTC  

---

## 1. Executive Summary & Exit Criteria Ledger

| Pipeline Stage | Evaluation Metric | Measured | Target Threshold | Exit Status |
| :--- | :--- | :--- | :--- | :--- |
| **ClinicalBERT NER** | Token-level BIO F1 | **34.72%** | ≥ 88.0% | ⚠️ Review |
| **ClinicalBERT NER** | Token Classification Accuracy | **83.80%** | ≥ 80.0% | ✅ Pass |
| **ChromaDB Retrieval** | Top-20 Rubric Recall (Recall@20) | **41.56%** | ≥ 90.0% | ⚠️ Review |
| **ChromaDB Retrieval** | Mean Reciprocal Rank (MRR) | **0.1815** | ≥ 0.650 | ⚠️ Review |
| **Repertory Ranker** | Simillimum Remedy Accuracy (Top-5) | **35.02%** | ≥ 70.0% | ⚠️ Review |

---

## 2. Stage 1: HomeoNER Entity Extraction Performance

ClinicalBERT evaluates token-level entity boundaries across the 7 classical Kentian symptom dimensions:

| Dimension Code | Clinical Significance | Precision | Recall | F1 Score | Gold Support |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LOC` | Anatomical Location / Organ | 40.5% | 29.0% | **33.8%** | 1,241 |
| `SEN` | Sensations / Pain Qualities | 35.4% | 29.9% | **32.4%** | 1,497 |
| `MOD_AGG` | Aggravation Modalities (Worse from) | 35.3% | 19.9% | **25.4%** | 780 |
| `MOD_AMEL` | Amelioration Modalities (Better from) | 21.4% | 10.5% | **14.1%** | 86 |
| `CONC` | Concomitant Symptoms | 28.6% | 20.5% | **23.9%** | 683 |
| `TEMP` | Time / Temporal Periodicity | 48.2% | 40.1% | **43.8%** | 935 |
| `MENT` | Mental / Emotional State | 42.4% | 33.0% | **37.1%** | 4,587 |

---

## 3. Stage 2: Dense Semantic Rubric Retrieval

Dense semantic vectors (`all-MiniLM-L6-v2`, 384 dimensions) query ChromaDB persistent index over 74,513 rubrics:

| Metric | Formula | Achieved Score |
| :--- | :--- | :--- |
| **Recall@1** | $\mathbb{I}(\text{target} = \text{rank}_1)$ | **10.69%** |
| **Recall@5** | $\mathbb{I}(\text{target} \in \text{Top-5})$ | **26.46%** |
| **Recall@10** | $\mathbb{I}(\text{target} \in \text{Top-10})$ | **33.40%** |
| **Recall@20** | $\mathbb{I}(\text{target} \in \text{Top-20})$ | **41.56%** |
| **MRR** | $\frac{1}{|D|} \sum_{i=1}^{|D|} \frac{1}{\text{rank}_i}$ | **0.1815** |

---

## 4. Stage 3: Homeopathic Remedy Indication Accuracy

Evaluated on 1,836 cases with documented remedy ground truth:

| Evaluation Cutoff | Target Simillimum Capture Rate |
| :--- | :--- |
| **Top-1 Remedy Accuracy** | **13.02%** |
| **Top-3 Remedy Accuracy** | **26.42%** |
| **Top-5 Remedy Accuracy** | **35.02%** |

---

## 5. Verification Command

```powershell
.venv\Scripts\python.exe scripts/evaluate.py --test-file /home/narya/kent-ai/data/processed/test.jsonl
```
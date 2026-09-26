# 📊 Evaluation Results & Benchmark Metrics

This document tracks target and realized performance metrics across project phases.

---

## 1. Target Phase Exit Criteria

| Phase | Metric | Target Threshold | Baseline | Status |
|---|---|---|---|---|
| **Phase 0** | MIND Rubrics Verified | **4,933 rubrics** | N/A | **PASSED** ✅ |
| **Phase 1** | Synthetic Cases Generated | ≥ 22,000 cases | N/A | Planned |
| **Phase 2** | Rubric Top-5 Recall | ≥ 85% | TF-IDF (52%) | Planned |
| **Phase 3** | ClinicalBERT NER Token F1 | ≥ 88% | Spacy Bio (71%) | Planned |
| **Phase 4** | Resolver Negation Accuracy | ≥ 95% | Regex Rules (68%) | Planned |
| **Phase 5** | Full Pipeline Top-20 Recall | ≥ 90% | Pure BM25 (61%) | Planned |
| **Phase 5** | Mean Reciprocal Rank (MRR) | ≥ 0.65 | Pure BM25 (0.39) | Planned |
| **Phase 6** | State Machine Slot Completion | ≥ 4/7 dimensions | N/A | Planned |

---

## 2. Phase 0 Validation Log
- **Sections count**: 37 verified.
- **Rubrics count**: 74,513 verified.
- **MIND rubrics count**: 4,933 verified.
- **Remedy grade mapping**: Grade 3 (Bold/CAPITALS), Grade 2 (Italics), Grade 1 (Roman) confirmed.
- **Unit test coverage**: 100% of DB reader test cases passing.

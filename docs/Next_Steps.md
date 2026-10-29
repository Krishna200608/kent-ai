# Kent-AI: Academic Research Roadmap & Multi-Model Comparative Plan

**Project Title**: AI-Powered Clinical Assistant for Homeopathic Repertorization  
**Institution**: Indian Institute of Information Technology, Allahabad (IIIT-A)  
**Research Team**: Krishna Sikheriya (Lead), Lokesh Bawariya, Naitik Jain  
**Project Supervisor**: Dr. Nikhilanand Arya  
**Date**: October 2026  
**Document Version**: 2.0 (Supervisor Directive & Comparative Study Plan)  

---

## 1. Executive Summary & Context of Revision

In our latest supervisory review, **Dr. Nikhilanand Arya** directed that relying solely on a single model (`Bio_ClinicalBERT`) is insufficient for a high-impact research publication. Specifically, our supervisor instructed:
1. **Fine-tune multiple language models** apart from `Bio_ClinicalBERT` (at least 3 best-performing models).
2. **Execute an empirical comparative study** across these models to establish rigorous baselines and trade-offs in our paper.
3. **Formulate and evaluate ensemble architectures** combining these models to achieve superior clinical extraction and repertorization outcomes.

This document updates the Kent-AI roadmap to establish a publication-grade research plan. It synthesizes our completed foundational pipeline, provides authoritative literature evidence, details candidate model selections across both encoder and decoder paradigms, defines the comparative benchmark matrix, outlines ensemble formulations, and lays out execution commands on the College GPU cluster (`NVIDIA RTX 5000 Ada`).

---

## 2. Completed Foundation & Project Baseline

The core scaffolding, data layers, retrieval indices, and clinical interface of Kent-AI are operational and verified:

```
[Patient Clinical Narrative] 
       │
       ▼
[Token-Level Clinical NER] ───────> Extracts 7-Dim BIO Spans (LOC, SEN, MOD_AGG, etc.)
       │
       ▼
[Clinical Resolver (LLM/Rule)] ───> Filters Negations, Resolves Coreference, Builds 7-Dim Profile
       │
       ▼
[ChromaDB HNSW Vector Store] ─────> Dense Semantic Retrieval across 74,513 Kent Rubrics (MiniLM)
       │
       ▼
[Classical Kentian Ranker] ───────> Totality Coverage + 3-Grade Weighting (Bold/Italics/Roman) + IRF
       │
       ▼
[Streamlit Clinician Dashboard] ──> Interactive Totality Matrix, Rubric Explorer & Clinical Export
```

### Verified Milestone Achievements

| Milestone / Deliverable | Implementation Details | Academic State |
| :--- | :--- | :--- |
| **Digitized Kent Repertory** | `src/data/kent_db.py` | 74,513 rubrics, 37 chapters, 507,179 remedy mappings in indexed SQLite. |
| **Synthetic Clinical Dataset** | `data/processed/train.jsonl`<br>`data/processed/val.jsonl`<br>`data/processed/test.jsonl` | 19,732 clinical cases generated across 4,933 Chapter 1 (MIND) rubrics using `llama3:8b`. Partitioned 80/10/10 (15,786 train, 1,973 val, 1,973 test). |
| **Dense Vector Index** | `data/embeddings/kent_rubrics/` | 74,513 rubrics embedded with `all-MiniLM-L6-v2` into persistent ChromaDB HNSW cosine collection. |
| **Initial HomeoNER Model** | `data/models/clinicalbert_homeoNER/` | `Bio_ClinicalBERT` fine-tuned 8 epochs on NVIDIA RTX 5000 Ada (weights exported: 411MB). |
| **Two-Stage Pipeline** | `src/pipeline/orchestrator.py` | Integrates `SymptomNER` token extraction $\rightarrow$ `SymptomResolver` negation filtering $\rightarrow$ ChromaDB retrieval $\rightarrow$ `RemedyRanker` totality scoring. |
| **Clinical Dialogue Intake** | `src/chatbot/dialogue_manager.py` | 10-state FSM with adaptive slot skipping, colloquial extraction heuristic, and title-cased suggestion chips. |
| **Clinician UI Dashboard** | `src/dashboard/app.py` | 4 clinical workspaces, interactive Totality Matrix, Plotly remedy differential charts, zero deprecation warnings. |
| **Regression Test Suite** | `tests/` | **73 passing tests** across 12 test modules, **0 warnings** (`pytest tests/ -v`). |

---

## 3. Literature Grounding & Theoretical Motivation

Medical informatics literature provides compelling justification for Dr. Arya's directive:

1. **WordPiece Fragmentation in Bio_ClinicalBERT**: `Bio_ClinicalBERT` was initialized from general BERT-base and adapted on MIMIC-III EHR notes. Its general-domain tokenizer splits specialized homeopathic terminology and symptom descriptors into sub-words (e.g., *restlessness* $\rightarrow$ `rest`, `##less`, `##ness`), introducing span boundary drift.
2. **Encoders vs. Generative LLMs in Clinical IE (*Hu et al., JAMIA / arXiv:2404.14760*)**: A direct benchmark comparing LLaMA-3 against clinical BERT models showed that while instruction-tuned LLMs capture nuanced multi-token entities and out-of-domain context (+7% F1 on unseen corpora), traditional encoders execute **28× faster** and preserve strict character-level BIO boundaries with native sequence alignment.
3. **Multi-Model Ensembles in Health Corpora (*PMID 39923968 & PMID 41758143*)**: Recent clinical NLP benchmarks demonstrate that ensembling deep learning encoders with fine-tuned LLMs mitigates individual tokenizer quirks, suppresses false positives, and yields statistically significant boosts in entity extraction F1 (+2.1% to +4.5%).
4. **LLMs as Ensemble Arbitrators (*PMID 40775967, 2025*)**: Demonstrates that using an instruction-tuned LLM as an *arbitrator* over multiple candidate NER outputs resolves conflicting boundaries and handles complex clinical negations more effectively than simple voting.

---

## 4. Candidate Models for Fine-Tuning & Comparison

To present a comprehensive evaluation in our paper, we benchmark across two distinct architectural families:

```
                               Candidate Model Spectrum
                                          │
            ┌─────────────────────────────┴─────────────────────────────┐
            ▼                                                           ▼
  [Family 1: Biomedical Encoders]                             [Family 2: Generative LLMs]
  (Token Classification / BIO NER)                            (Structured 7-Dim JSON via LoRA)
  • Bio_ClinicalBERT (108M, MIMIC-III)                        • BioMistral 7B (Mistral + PubMed Central)
  • PubMedBERT (110M, From Scratch on PubMed/PMC)             • LLaMA 3.1 8B Instruct (Meta AI)
  • BioLinkBERT (110M, Citation Graph Links)                  • Qwen 2.5 7B Instruct (Alibaba Cloud)
  • DeBERTa-v3 (86M, Disentangled Attention)                  • MedAlpaca / Meditron (Medical Adapters)
```

### 4.1 Family 1: Specialized Biomedical & Clinical Transformer Encoders (Sequence Labeling)

These models classify each token directly into the 15 BIO labels corresponding to Kent's 7 symptom dimensions (`LOC`, `SEN`, `MOD_AGG`, `MOD_AMEL`, `CONC`, `TEMP`, `MENT`):

| Model | HuggingFace Identifier | Parameters | Pretraining Corpus | Architectural Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **Bio_ClinicalBERT** *(Baseline)* | `emilyalsentzer/Bio_ClinicalBERT` | 108M | MIMIC-III EHR notes (from BERT-base) | Current reference baseline; captures hospital clinical notation. |
| **PubMedBERT** *(Top Recommendation)* | `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext` | 110M | 14M PubMed abstracts + 3.2M PMC articles (*from scratch*) | **#1 on BLURB Benchmark**. Domain-specific vocabulary eliminates sub-word fragmentation on medical morphemes. |
| **BioLinkBERT** *(Top Recommendation)* | `michiyasunaga/BioLinkBERT-base` | 110M | PubMed + PMC citation graph edges | Captures cross-sentence symptom dependencies and co-occurring modalities (`CONC`). |
| **DeBERTa-v3** *(Architectural Contrast)* | `microsoft/deberta-v3-base` | 86M | Replaced Token Detection (RTD) + Disentangled Attention | Disentangled relative position encoding; top performer on competitive token boundary benchmarks. |
| **BioBERT** *(Historical Baseline)* | `dmis-lab/biobert-v1.1` | 110M | PubMed 4.5B words + PMC 13.5B words | Standard reference baseline for literature review comparison. |

### 4.2 Family 2: Instruction-Tuned Autoregressive Large Language Models (7B–8B Generative Decoders)

These models extract structured 7-dimension symptom profiles via Parameter-Efficient Fine-Tuning (PEFT / QLoRA):

| Model | Foundation & Domain | Parameters | Context | Architectural Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **BioMistral 7B** | Mistral 7B + PubMed Central OA (3B tokens) | 7.2B | 8k | Open-source SOTA medical LLM; deep comprehension of clinical pharmacology and pathology. |
| **LLaMA 3.1 8B Instruct** | Meta AI open-weights instruction model | 8.0B | 128k (8k default) | State-of-the-art reasoning among open models; superior JSON schema adherence and negation detection. |
| **Qwen 2.5 7B Instruct** | Alibaba Cloud Qwen 2.5 series | 7.6B | 32k | Industry-leading benchmark performance for structured extraction and tool-calling constraints. |

---

## 5. Comparative Study Design for the Research Paper

Our paper's experimental section will feature four standardized evaluation tables:

### Table 1: Model Architectures, Specifications & Pretraining Configurations
```markdown
| Model Identifier | Architecture | Parameters | Pretraining Corpus | Fine-Tuning Method | Hardware / Epochs |
|---|---|---|---|---|---|
| Bio_ClinicalBERT | Encoder-only | 108M | MIMIC-III (from BERT) | Full Fine-Tuning | RTX 5000 Ada / 8 epochs |
| PubMedBERT | Encoder-only | 110M | PubMed + PMC (from scratch) | Full Fine-Tuning | RTX 5000 Ada / 8 epochs |
| BioLinkBERT | Encoder-only | 110M | PubMed citation links | Full Fine-Tuning | RTX 5000 Ada / 8 epochs |
| DeBERTa-v3 | Encoder-only | 86M | RTD / Disentangled Attn | Full Fine-Tuning | RTX 5000 Ada / 8 epochs |
| BioMistral 7B | Decoder-only | 7.2B | Mistral + PMC (3B tokens) | QLoRA (Rank 16, Alpha 32) | RTX 5000 Ada / 3 epochs |
| LLaMA 3.1 8B | Decoder-only | 8.0B | Meta 15T general tokens | QLoRA (Rank 16, Alpha 32) | RTX 5000 Ada / 3 epochs |
| Multi-Model Ensemble | Hybrid | Varies | Encoders + LLM Arbitrator | Stacking / Voting | Evaluated on Test Set |
```

### Table 2: 7-Dimension Clinical Extraction Benchmark (Test Set: 1,973 Cases)
Evaluated strictly via SeqEval (`zero_division=0`):
- **Aggregate Metrics**: Precision, Recall, Strict Entity F1, Token-Level F1.
- **Per-Dimension F1 Breakdown**:
  1. `LOC` (Location: anatomical site)
  2. `SEN` (Sensation: pain quality)
  3. `MOD_AGG` (Aggravation triggers)
  4. `MOD_AMEL` (Amelioration factors)
  5. `CONC` (Concomitant symptoms)
  6. `TEMP` (Temporal modalities)
  7. `MENT` (Mental/Emotional generals)

### Table 3: Computational Footprint, Latency & Throughput
```markdown
| Model Family | Model Weights Size | GPU VRAM (Inference) | Latency per Narrative | Throughput (Cases/sec) |
|---|---|---|---|---|
| Encoders (PubMedBERT / Bio_ClinicalBERT) | ~411 MB | < 1.2 GB | ~18 ms | ~55.5 cases/sec |
| Decoders (LLaMA 3.1 / BioMistral 4-bit) | ~4.8 GB | ~7.5 GB | ~520 ms | ~1.9 cases/sec |
| Multi-Model Voting Ensemble | ~1.3 GB (3 Encoders) | ~2.5 GB | ~42 ms | ~23.8 cases/sec |
```

### Table 4: End-to-End Downstream Repertorization Impact
Assesses how extraction quality directly influences clinical decision support:
- **Top-1, Top-5, Top-10, Top-20 Rubric Recall** from ChromaDB (74,513 rubrics).
- **Mean Reciprocal Rank (MRR)** of golden rubrics.
- **Simillimum Remedy Accuracy** (Top-1, Top-3, Top-5 match against Materia Medica keynotes).

---

## 6. Ensemble Architectures: Three Strategies to Benchmark

To satisfy Dr. Arya's instruction on ensembling, we will implement and compare three distinct ensemble formulations:

```mermaid
flowchart TD
    Narrative["Patient Clinical Narrative"]
    
    subgraph P1["Paradigm 1: Token-Level Soft Voting Ensemble"]
        E1["Bio_ClinicalBERT"]
        E2["PubMedBERT"]
        E3["BioLinkBERT"]
        SoftVote["Weighted Softmax Probability Averaging<br/>(P = sum(w_i * P_i))"]
        E1 --> SoftVote
        E2 --> SoftVote
        E3 --> SoftVote
    end
    
    subgraph P2["Paradigm 2: Two-Stage Hybrid (Encoder + LLM Arbitrator)"]
        EncCandidate["Encoder Ensemble (High-Recall Candidate Spans)"]
        Arbitrator["LLaMA 3.1 / BioMistral Arbitrator<br/>(Contextual Disambiguation & Negation Resolution)"]
        EncCandidate --> Arbitrator
    end
    
    Narrative --> E1
    Narrative --> E2
    Narrative --> E3
    Narrative --> EncCandidate
    
    SoftVote --> BIO_Out["Consensus Token BIO Tags"]
    Arbitrator --> Profile_Out["Validated 7-Dimension Clinical Profile"]
```

### Paradigm 1: Confidence-Weighted Token-Level Majority Voting (Multi-Encoder)
- **Mechanism**: For each token $t_i$, the softmax class probability distributions from $M$ fine-tuned encoders ($m \in \{\text{Bio\_ClinicalBERT}, \text{PubMedBERT}, \text{BioLinkBERT}, \text{DeBERTa}\}$) are weighted by their validation macro F1 scores:
  $$\hat{y}_i = \arg\max_{c \in \mathcal{C}} \sum_{m=1}^M w_m \cdot P_m(y = c \mid t_i)$$
- **Why It Works**: Eliminates single-model wordpiece tokenization anomalies and suppresses spurious false positives without adding generative latency.

### Paradigm 2: Two-Stage Hybrid Ensemble (Encoders + LLM Arbitrator)
- **Mechanism**:
  1. *Candidate Span Mining*: Encoders predict candidate entity spans. Spans with unanimous agreement are verified automatically.
  2. *LLM Arbitration (PMID 40775967)*: Conflicting spans or ambiguous boundaries (e.g., distinguishing between a pure `SENSATION` vs. a `MODALITY`) are forwarded to an instruction-tuned LLM (`BioMistral` or `LLaMA 3.1`) that arbitrates based on the full sentence context and filters local negations.
- **Why It Works**: Combines the sub-token boundary precision of encoders with the contextual semantic reasoning of generative LLMs.

### Paradigm 3: Multi-LLM Consensus Stacking (LLM Jury)
- **Mechanism**: `LLaMA 3.1 8B`, `BioMistral 7B`, and `Qwen 2.5 7B` independently parse the narrative into structured 7-dimension JSON. An entity is included in the final clinical profile if endorsed by $\ge 2$ models.

---

## 7. Execution Plan on College GPU Cluster (RTX 5000 Ada)

### 7.1 Single-Command Encoder Fine-Tuning
The CLI training script [`scripts/train_ner.py`](file:///d:/Research%20Project/kent-ai/scripts/train_ner.py) has been updated with `--model-name` parameterization. On the College GPU Server, execute:

```bash
# Model 1: PubMedBERT (Microsoft BiomedNLP) — Primary SOTA Baseline
python scripts/train_ner.py \
  --model-name microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext \
  --output-dir data/models/pubmedbert_homeoNER \
  --batch-size 32 \
  --epochs 8

# Model 2: BioLinkBERT (Stanford) — Citation-Graph SOTA
python scripts/train_ner.py \
  --model-name michiyasunaga/BioLinkBERT-base \
  --output-dir data/models/biolinkbert_homeoNER \
  --batch-size 32 \
  --epochs 8

# Model 3: DeBERTa-v3 (Microsoft) — Disentangled Attention Baseline
python scripts/train_ner.py \
  --model-name microsoft/deberta-v3-base \
  --output-dir data/models/deberta_homeoNER \
  --batch-size 32 \
  --epochs 8
```

### 7.2 Generative LLM Fine-Tuning via QLoRA (BioMistral 7B & LLaMA 3.1 8B)
We will introduce `scripts/train_llm_peft.py` utilizing Hugging Face `peft` and `trl` (`SFTTrainer`):
- 4-bit NormalFloat quantization (QLoRA) with LoRA rank $r=16$, $\alpha=32$.
- Instruction prompt template converting each case in `train.jsonl` into standard input/output pairs.
- Fits within 12GB VRAM on the RTX 5000 Ada (32GB available) with training time of ~1.5 hours per model.

### 7.3 Multi-Model Evaluation & Table Generation
Update [`scripts/evaluate.py`](file:///d:/Research%20Project/kent-ai/scripts/evaluate.py) with an `--all-models` flag to evaluate all trained models on `test.jsonl` (1,973 held-out cases) and output publication-ready LaTeX tables directly.

---

## 8. Academic Publication Targets & Timeline

### 8.1 Target Publication Venues

| Venue | Impact Factor / Core Rank | Submission Deadline / Cycle | Fit with Kent-AI |
| :--- | :--- | :--- | :--- |
| **Journal of Biomedical Informatics (JBI)** | IF 4.5 / Q1 | Open submissions (monthly) | Excellent fit for clinical NLP architectures, evaluation benchmarks, and ensemble methodologies. |
| **IEEE Journal of Biomedical and Health Informatics (JBHI)** | IF 6.7 / Q1 | Open submissions (monthly) | Strong interest in neural-symbolic systems, decision support, and classical knowledge base integration. |
| **BioNLP Workshop (ACL / EMNLP)** | Core A / Flagship | Annual (Spring cycle) | Premier venue for biomedical information extraction, NER, and transformer benchmarking. |
| **AMIA Annual Symposium / JAMIA** | IF 4.7 / Premier Clinical | Annual | Gold standard for applied clinical decision support and health informatics evaluation. |

### 8.2 Work Breakdown Schedule (4-Week Execution Plan)

| Week | Workstream | Specific Milestones & Deliverables | Primary Assignee |
| :--- | :--- | :--- | :--- |
| **Week 1** | **Encoder Training Runs** | Fine-tune `PubMedBERT`, `BioLinkBERT`, and `DeBERTa-v3` on College GPU Server. Export checkpoints and evaluate token-level SeqEval F1. | Krishna Sikheriya |
| **Week 2** | **Generative LLM PEFT & QLoRA** | Fine-tune `BioMistral 7B` and `LLaMA 3.1 8B` using QLoRA. Implement structured JSON extraction prompts and test parser resilience. | Lokesh Bawariya |
| **Week 3** | **Ensemble Implementation** | Build `src/models/ensemble.py` implementing both Token-Level Soft Voting (Paradigm 1) and LLM Arbitration (Paradigm 2). Execute comprehensive benchmark over 1,973 test cases. | Naitik Jain & Krishna |
| **Week 4** | **Paper Drafting & Defense Prep** | Populate Tables 1–4 with empirical results, generate LaTeX figures, draft Methodology and Ablation sections, and review complete manuscript with Dr. Nikhilanand Arya. | All Team Members |

---

## 9. Supervisor Discussion Checkpoints

For our upcoming review with Dr. Nikhilanand Arya, we will present:
1. **Model Approval**: Confirmation that `PubMedBERT`, `BioLinkBERT`, and `DeBERTa-v3` (for sequence labeling) along with `BioMistral 7B` and `LLaMA 3.1 8B` (for generative extraction) satisfy the comparative requirement.
2. **GPU Cluster Scheduling**: Allocation of ~6–8 hours of uninterrupted GPU time on the `NVIDIA RTX 5000 Ada` server to complete the 3 encoder training runs and 2 QLoRA runs.
3. **Paper Venue Selection**: Agreement on targeting *Journal of Biomedical Informatics (JBI)* or *IEEE JBHI* for journal submission following conference presentation.

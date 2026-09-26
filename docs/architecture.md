# 📐 System Architecture

**Kent-AI: AI-Powered Clinical Assistant for Homeopathic Repertorization**

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Input ["Patient Intake Layer"]
        A[Patient Chat Utterance] --> B[Conversational Intake Agent / State Machine]
        B --> C[Full Consultation Transcript]
    end

    subgraph Extraction ["Clinical Information Extraction Layer"]
        C --> D[Bio_ClinicalBERT NER Model]
        D -->|BIO Token Spans| E[LLaMA 3 Clinical Resolver]
        E -->|Negation Handling & Coreference| F[Structured 7-Dimension Clinical Profile]
    end

    subgraph Retrieval ["Hybrid Rubric Matching Engine"]
        F --> G[Sentence-Transformers all-MiniLM-L6-v2]
        G --> H[(ChromaDB Vector Store\n74,513 Kent Rubrics)]
        F --> I[(SQLite FTS5 Full-Text Index)]
        H --> J[Candidate Rubric Union & Deduplication]
        I --> J
    end

    subgraph Repertorization ["Remedy Ranking & Provenance Layer"]
        J --> K[Repertory Intersection Ranker]
        K -->|Grade 3 / 2 / 1 Weighting| L[Ranked Remedy Differential]
        L --> M[(Kent Repertory SQLite DB\nPages & Citations)]
    end

    subgraph Presentation ["Clinical Presentation Layer"]
        M --> N[Patient Report Generator]
        N --> O[Streamlit Clinician Dashboard]
    end
```

---

## 2. Kent's 7 Symptom Dimensions

| Dimension | Description | Example Entities |
|---|---|---|
| **Location (LOC)** | Anatomical organ, tissue, or lateral side | *Right temple, epigastrium, occiput* |
| **Sensation (SEN)** | Quality or character of discomfort | *Throbbing, burning, stitching, stitching like splinters* |
| **Modality: Worse (MOD_AGG)** | Factors that trigger or aggravate symptoms | *Cold drafts, motion, stepping hard, evening* |
| **Modality: Better (MOD_AMEL)** | Factors that soothe or relieve symptoms | *Warm wraps, lying down, hard pressure, fresh air* |
| **Concomitants (CONC)** | Unrelated symptoms co-occurring simultaneously | *Nausea with headache, perspiration during chill* |
| **Temporal (TEMP)** | Exact circadian timing of recurrence | *Aggravation at 3 AM, periodicity every 7 days* |
| **Mental/Emotional (MENT)** | Psychological and dispositional state | *Fear of dark, weeping when spoken to, restlessness* |

---

## 3. Database & Storage Architecture
- **Raw Layer**: `data/raw/repertory.sqlite` contains 37 sections, 74,513 rubrics, 500,000+ remedy links, and OCR bounding boxes.
- **Vector Layer**: `data/embeddings/kent_rubrics` persistent ChromaDB HNSW collection with cosine distance.
- **Processed Layer**: `data/processed/` contains partitioned JSONL sets for fine-tuning and evaluation.

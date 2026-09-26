# 🌿 Kent-AI

**AI-Powered Clinical Assistant for Homeopathic Repertorization**

---

## 📖 Overview

**Kent-AI** bridges classical homeopathic repertorization with modern Natural Language Processing and information retrieval. Utilizing Dr. James Tyler Kent’s *Repertory of the Homoeopathic Materia Medica*, Kent-AI extracts 7-dimensional clinical symptom profiles from conversational patient narratives, maps them into hierarchical repertory rubrics, and ranks candidate remedies with full provenance.

### Core Objectives
1. **Empathetic Symptom Elicitation**: Conversational state machine guiding patient intake across Kent's 7 symptom dimensions (*Location, Sensation, Modality (Worse/Better), Concomitants, Temporal, Mental/Emotional*).
2. **Clinical Information Extraction**: Domain fine-tuned Bio_ClinicalBERT for token-level symptom span detection (BIO tagging).
3. **Semantic Rubric Matching**: Dual-retrieval engine utilizing ChromaDB dense embeddings (`all-MiniLM-L6-v2`) and SQLite FTS5 for precision matching across 74,513 Kent rubrics.
4. **Transparent Remedy Ranking**: Grade-weighted intersection scoring (Grade 3 Bold, Grade 2 Italic, Grade 1 Roman) linking remedies directly to source pages in Kent's Repertory.
5. **Doctor-in-the-Loop Dashboard**: Interactive Streamlit UI for clinicians to review extracted dimensions, inspect candidate rubrics, and explore repertory trees.

---

## 🏗️ Repository Architecture

```
kent-ai/
├── configs/               # Hyperparameter and model configuration files
│   ├── model.yaml         # ClinicalBERT NER settings and 7-dim label schema
│   ├── generation.yaml    # LLaMA 3 synthetic case generation params
│   ├── chromadb.yaml      # ChromaDB collection & embedding configuration
│   └── chatbot.yaml       # Patient intake state machine rules
├── data/
│   ├── raw/               # Immutable source repertory database (repertory.sqlite)
│   ├── processed/         # Synthetic cases, train/val/test splits (jsonl)
│   └── embeddings/        # Persistent ChromaDB rubric vectors
├── src/
│   ├── data/              # Kent DB reader, synthetic case generator, BIO tagger, splitter
│   ├── models/            # ClinicalBERT NER wrapper, trainer, and LLaMA resolver
│   ├── search/            # Sentence embedder, vector store, and remedy ranker
│   ├── chatbot/           # State machine, dialogue manager, prompts
│   ├── pipeline/          # End-to-end transcript-to-report orchestrator
│   └── dashboard/         # Streamlit clinical dashboard and components
├── scripts/               # Standalone execution pipelines (generation, training, eval)
├── notebooks/             # Exploratory analysis & Colab training notebooks
├── tests/                 # Comprehensive unit and integration test suite
└── docs/                  # Architecture specs, API reference, proposals
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- SQLite 3 with FTS5 support (included with standard Python)

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-username/kent-ai.git
cd kent-ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Verify Database Reader (Phase 0 Milestone)
```bash
python -c "from src.data.kent_db import get_mind_rubrics; print(f'MIND Rubrics loaded: {len(get_mind_rubrics())}')"
# Expected output: MIND Rubrics loaded: 4933
```

### 4. Run Unit Tests
```bash
pytest tests/ -v
```

---

## 🗺️ Project Roadmap

- [x] **Phase 0: Scaffolding & Data Layer** — Directory skeleton, SQLite database connector, configs, unit tests.
- [ ] **Phase 1: Synthetic Case Generation** — LLaMA 3 prompt pipeline generating 22,200 MIND clinical cases with BIO tags.
- [ ] **Phase 2: ChromaDB Rubric Index** — Dense vector index over 74,513 Kent rubrics (`all-MiniLM-L6-v2`).
- [ ] **Phase 3: ClinicalBERT NER Training** — Fine-tuning Bio_ClinicalBERT for 7-dimension symptom span extraction.
- [ ] **Phase 4: LLaMA 3 Post-Processor** — Negation handling, coreference resolution, structured 7-dim JSON extraction.
- [ ] **Phase 5: Pipeline & Remedy Ranking** — End-to-end transcript-to-report pipeline with grade-weighted remedy scoring.
- [ ] **Phase 6: Conversational Chatbot** — Empathetic clinical intake agent with finite-state dialogue manager.
- [ ] **Phase 7: Streamlit Doctor Dashboard** — Multi-page clinical review interface and repertory browser.
- [ ] **Phase 8: Polish & Defense** — Comprehensive documentation, benchmarking, and defense preparation.

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
Kent Repertory digitized data is maintained under open research terms.

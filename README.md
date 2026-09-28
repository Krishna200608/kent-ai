# 🌿 Kent-AI: AI-Powered Clinical Assistant for Homeopathic Repertorization

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Tests Passing](https://img.shields.io/badge/tests-64%20passed-brightgreen.svg)](tests/)
[![ChromaDB Indexed](https://img.shields.io/badge/ChromaDB-74%2C513%20rubrics-emerald.svg)](data/embeddings/kent_rubrics/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Institution: IIIT Allahabad](https://img.shields.io/badge/IIIT%20Allahabad-Department%20of%20IT-red.svg)](https://www.iiita.ac.in/)

> **Kent-AI** bridges 19th-century classical homeopathic repertorization with 21st-century Natural Language Processing and dense vector retrieval. Based on Dr. James Tyler Kent’s *Repertory of the Homoeopathic Materia Medica*, Kent-AI extracts 7-dimensional clinical symptom profiles from conversational patient intake transcripts, matches them against a hierarchical repertory of 74,513 rubrics using dense semantic search, and computes transparent, grade-weighted remedy rankings with complete clinical provenance.

---

## 🏛️ Academic & Project Metadata

| Attribute | Details |
| :--- | :--- |
| **Institution** | Indian Institute of Information Technology, Allahabad (IIIT Allahabad) |
| **Department** | Department of Information Technology |
| **Academic Program** | B.Tech Semester Project (Seventh Semester) — Mid-Semester Evaluation |
| **Project Title** | **Kent-AI: An AI-Powered Conversational Clinical Assistant for Homeopathic Case-Taking and Dense Semantic Repertorization** |
| **Project Supervisor** | **Dr. Nikhilanand Arya**, Assistant Professor, Department of IT, IIIT Allahabad |
| **Team Members** | **Krishna Sikheriya** (IIT2023139) — *Team Lead*<br>**Lokesh Bawariya** (IIT2023138) — *Team Member*<br>**Naitik Jain** (IIB2023036) — *Team Member* |
| **Source Repository** | [GitHub: Krishna200608/kent-ai](https://github.com/Krishna200608/kent-ai) |

---

## 📖 System Overview & Core Capabilities

Classical homeopathic case-taking requires eliciting an individualized, holistic totality of symptoms across multiple distinct clinical dimensions. Kent-AI automates this labor-intensive process while maintaining strict doctor-in-the-loop oversight:

```
[Patient Conversation]
         │
         ▼
[1. Conversational Chatbot]  ──> Finite-state intake machine exploring Kent's 7 Dimensions
         │
         ▼
[2. ClinicalBERT NER]        ──> Token-level BIO span detection (MENT, SEN, LOC, MOD, etc.)
         │
         ▼
[3. LLaMA 3 Post-Processor]  ──> Resolves negations, coreferences, and structured JSON slots
         │
         ▼
[4. Semantic Retrieval]      ──> Dense ChromaDB HNSW cosine index over 74,513 Kent rubrics
         │
         ▼
[5. Remedy Ranking Engine]   ──> Grade-weighted intersection totality scoring (Grades 3, 2, 1)
         │
         ▼
[6. Doctor Dashboard]        ──> Streamlit clinical portal with Materia Medica keynote lookup
```

### The 7 Kent Symptom Dimensions
1. **Location (`LOC`)**: Specific anatomical organ, side, or tissue (e.g., *forehead, right temple, epigastrium*).
2. **Sensation (`SEN`)**: Qualitative perception (e.g., *throbbing, burning, stitching, dull ache*).
3. **Modality — Aggravation (`MOD_AGG`)**: Factors worsening discomfort (e.g., *worse from noise, worse at 3 AM*).
4. **Modality — Amelioration (`MOD_AMEL`)**: Factors relieving discomfort (e.g., *better from hard pressure, fresh air*).
5. **Concomitant (`CONC`)**: Co-occurring clinical phenomena (e.g., *headache accompanied by nausea and chills*).
6. **Temporal (`TEMP`)**: Diurnal periodicity and clock modalities (e.g., *morning on waking, twilight, midnight*).
7. **Mental / Emotional (`MENT`)**: Disposition and psyche (e.g., *anxiety about health, tearful mood, restlessness*).

---

## 📊 Validated Milestones & Benchmarks

| Milestone / Evaluation Axis | Status | Key Metric / Verification Result |
| :--- | :--- | :--- |
| **Phase 0: Database & DAL** | ✅ Complete | **74,513 rubrics**, 679 remedies, 507,179 associations parsed from Kent's SQLite |
| **Phase 1: Synthetic Case Pilot** | ✅ Complete | **100 cases / 25 rubrics**: **100% JSON parse validity**, **100.00% BIO slice accuracy** (576/576 spans, 0 drift), **86.9% lexical diversity** |
| **Phase 2: ChromaDB Rubric Index** | ✅ Complete | **74,513 rubrics indexed** in 931s (80.0 rubrics/sec) with `all-MiniLM-L6-v2` (384-dim HNSW cosine index) |
| **Phase 6: Clinical Dialogue Manager** | ✅ Complete | Finite-state intake machine with dynamic LLaMA 3 quick-reply suggestions |
| **Phase 7: Doctor Dashboard** | ✅ Complete | 4-Workspace Streamlit portal (`src/dashboard/app.py`) following Google Stitch glassmorphic theme |
| **Test Suite Coverage** | ✅ Complete | **64 unit & integration tests passing** in ~23 seconds (`pytest tests/`) |

---

## 🏗️ Repository Structure

```
kent-ai/
├── Context/                    # Self-contained project memory for AI assistants & developers
│   ├── ARCHITECTURE.md         # End-to-end 6-phase pipeline & data flow specifications
│   ├── CONVENTIONS.md          # Coding style, strict typing, and test standards
│   ├── DATA.md                 # SQLite DDLs, SyntheticCase JSON schema, and BIO label space
│   ├── GOTCHAS.md              # 15+ hard-won architectural & database traps solved
│   ├── PROGRESS.md             # Real-time task tracker, deliverables, and benchmark metrics
│   └── PROJECT.md              # High-level mission and homeopathic domain requirements
├── configs/                    # Declarative YAML hyperparameter and model configs
│   ├── chatbot.yaml            # Dialogue manager state transition rules
│   ├── chromadb.yaml           # ChromaDB HNSW cosine index configuration
│   ├── generation.yaml         # LLaMA 3 synthetic case generation settings
│   └── model.yaml              # Bio_ClinicalBERT NER hyperparameters & BIO tag set
├── data/
│   ├── raw/                    # Immutable source repertory database (repertory.sqlite)
│   ├── processed/              # Pilot cases (pilot_100_cases.jsonl) & generation checkpoints
│   └── embeddings/             # Persistent ChromaDB rubric vectors (74,513 indexed)
├── docs/                       # Architecture documentation, design system, and setup guides
│   ├── DESIGN.md               # Google Stitch UI/UX design tokens & glassmorphism theme
│   ├── GPU_SETUP_GUIDE.md      # Step-by-step SSH & College GPU cluster execution guide
│   └── Report/Content.md       # Master report & 20-slide defense presentation blueprint
├── logs/                       # Runtime logs (git-ignored, e.g., pilot_generation.log)
├── notebooks/                  # Exploratory data analysis & validation notebooks
├── reports/                    # Formal evaluation reports
│   └── pilot_100_cases_evaluation.md # Statistical audit report of the 100-case pilot run
├── scripts/                    # Production execution pipelines
│   ├── audit_pilot.py          # Statistical auditor (BIO slice accuracy, Jaccard overlap)
│   ├── build_embeddings.py     # ChromaDB batch indexer across 74,513 rubrics
│   ├── generate_cases.py       # Full production LLaMA 3 generator with 80/10/10 split
│   ├── generate_pilot_sample.py# Stratified 100-case pilot generator
│   └── run_gpu_generation.sh   # Turnkey bash runner for College GPU deployment
├── src/                        # Core Python package
│   ├── chatbot/                # State machine, dialogue manager, prompts
│   ├── dashboard/              # Streamlit doctor interface (Stitch CSS, components)
│   ├── data/                   # Kent SQLite DAL, CaseGenerator, BIOTagger, Splitter
│   ├── models/                 # Bio_ClinicalBERT wrapper, NER trainer, LLaMA resolver
│   ├── pipeline/               # End-to-end transcript-to-remedy orchestrator
│   └── search/                 # RubricEmbedder, RubricVectorStore, RemedyRanker
└── tests/                      # Comprehensive pytest test suite (64 passing tests)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- SQLite 3 with FTS5 support (bundled with standard Python distributions)
- Optional: [Ollama](https://ollama.com/) with `llama3:8b` for live local LLM inference

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/Krishna200608/kent-ai.git
cd kent-ai

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# Install package in editable mode with development dependencies
pip install -e ".[dev]"
```

### 3. Verify Database Reader & Run Unit Tests
```bash
# Verify SQLite reader loads 4,933 MIND rubrics
python -c "from src.data.kent_db import get_mind_rubrics; print(f'MIND Rubrics loaded: {len(get_mind_rubrics())}')"

# Run the complete test suite (all 64 unit & integration tests)
make test      # Or: pytest tests/ -v
```

### 4. Launch the Streamlit Clinical Dashboard
```bash
make serve     # Or: streamlit run src/dashboard/app.py
```
Open your browser at `http://localhost:8501` to explore:
- **Intake Consultation**: Live conversational symptom collection with dynamic quick suggestions.
- **Instant Repertorization**: Multi-rubric totality matrix with grade-weighted remedy scoring.
- **74k Rubric Explorer**: Semantic search across Kent's entire hierarchical repertory.
- **Materia Medica Keynotes**: Grade 3 characteristic symptom inspection.

---

## 🖥️ Production Generation on College GPU Cluster

For generating the full **22,200 synthetic clinical training cases** across all 4,933 MIND rubrics on your university GPU server:

```bash
# Connect to your GPU server via SSH
ssh username@gpu-server-ip

# Clone and navigate
git clone https://github.com/Krishna200608/kent-ai.git
cd kent-ai

# Set up environment
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Launch background generation job with automatic Ollama management:
chmod +x scripts/run_gpu_generation.sh
./scripts/run_gpu_generation.sh

# Monitor progress in real time:
tail -f logs/generation.log
```

> For comprehensive SSH setup, `tmux` persistent sessions, and crash recovery, consult the [College GPU Setup Guide](docs/GPU_SETUP_GUIDE.md).

---

## 🗺️ Project Roadmap & Phase Tracker

| Phase | Milestone Description | Status |
| :--- | :--- | :--- |
| **Phase 0** | **Scaffolding & Data Layer** — SQLite DAL over 74,513 rubrics, packaging, tests | ✅ **Complete** |
| **Phase 1** | **Synthetic Case Generation** — LLaMA 3 pipeline; 100-case pilot audited (86.9% diversity) | 🔄 **Pilot Audited / GPU Scale-up Ready** |
| **Phase 2** | **ChromaDB Rubric Index** — 74,513 rubrics indexed with `all-MiniLM-L6-v2` | ✅ **Complete** |
| **Phase 3** | **ClinicalBERT NER Fine-Tuning** — 7-dimension token span extraction | ⏳ *Scheduled post-GPU generation* |
| **Phase 4** | **LLaMA 3 Clinical Resolver** — Negation handling, coreference, JSON slot assembly | ✅ **Core Prompts & Architecture Complete** |
| **Phase 5** | **Remedy Ranking & Totality Engine** — Grade-weighted provenance scoring | ✅ **Core Engine Implemented** |
| **Phase 6** | **Conversational Intake Chatbot** — State machine with dynamic quick suggestions | ✅ **Complete** |
| **Phase 7** | **Doctor Dashboard** — 4-Workspace Streamlit portal adhering to Google Stitch UI/UX | ✅ **Complete** |
| **Phase 8** | **Mid-Semester Defense & Benchmarking** — Evaluation report, LaTeX thesis, PPT | 🔄 **In Progress** |

---

## 📄 License & Attribution

This project is licensed under the [MIT License](LICENSE).  
The digitized Kent Repertory database is utilized under open academic and research terms.

**Developed at**:  
**Department of Information Technology**  
**Indian Institute of Information Technology, Allahabad (IIIT Allahabad)**  
Prayagraj, Uttar Pradesh, India — 211015

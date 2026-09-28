# Kent-AI: Conversational Clinical Assistant for Homeopathic Repertorization

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-yellow.svg)](https://huggingface.co/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-74%2C513%20Rubrics-blueviolet.svg)](data/embeddings/kent_rubrics/)
[![Tests Status](https://img.shields.io/badge/tests-64%20passed-success.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)
[![Institution](https://img.shields.io/badge/IIIT%20Allahabad-Department%20of%20IT-darkred.svg)](https://www.iiita.ac.in/)

Kent-AI is an artificial intelligence-driven clinical decision support system designed to bridge classical homeopathic repertorization with contemporary Natural Language Processing (NLP) and dense semantic retrieval. Built upon Dr. James Tyler Kent’s *Repertory of the Homoeopathic Materia Medica*, the framework extracts structured seven-dimensional symptom profiles from conversational patient narratives, maps colloquial patient language to hierarchical repertory rubrics via dense vector search across 74,513 rubrics, and computes explainable, grade-weighted candidate remedy rankings with source-grounded clinical provenance.

---

## Academic Information

| Parameter | Specification |
| :--- | :--- |
| **Institution** | Indian Institute of Information Technology, Allahabad (IIIT Allahabad) |
| **Department** | Department of Information Technology |
| **Academic Program** | B.Tech Semester Project (Seventh Semester) |
| **Project Title** | **Kent-AI: An AI-Powered Conversational Clinical Assistant for Homeopathic Case-Taking and Dense Semantic Repertorization** |
| **Supervisor** | **Dr. Nikhilanand Arya**, Assistant Professor, Department of IT, IIIT Allahabad |
| **Authors** | **Krishna Sikheriya** (IIT2023139) — Team Lead<br>**Lokesh Bawariya** (IIT2023138) — Team Member<br>**Naitik Jain** (IIB2023036) — Team Member |
| **Evaluation Cycle** | Mid-Semester Evaluation, Academic Year 2026–2027 |
| **Repository** | [https://github.com/Krishna200608/kent-ai](https://github.com/Krishna200608/kent-ai) |

---

## Table of Contents

- [Abstract & Motivation](#abstract--motivation)
- [Core Contributions](#core-contributions)
- [System Architecture](#system-architecture)
- [Kent's Seven-Dimension Clinical Taxonomy](#kents-seven-dimension-clinical-taxonomy)
- [Experimental Benchmarks & Verified Results](#experimental-benchmarks--verified-results)
- [Repository Structure](#repository-structure)
- [Installation & Environment Setup](#installation--environment-setup)
- [Usage & Pipeline Execution](#usage--pipeline-execution)
- [Production Deployment on GPU Clusters](#production-deployment-on-gpu-clusters)
- [Streamlit Clinical Decision Support Portal](#streamlit-clinical-decision-support-portal)
- [Development Roadmap](#development-roadmap)
- [Citation](#citation)
- [License & Open Access](#license--open-access)

---

## Abstract & Motivation

In classical homeopathy, prescribing adheres to the Law of Similars (*Similia Similibus Curentur*), requiring the physician to match the patient's holistic symptom totality against proving symptoms recorded in Materia Medica and indexed in Repertories. Dr. J. T. Kent's 1897 repertory remains the global clinical gold standard, indexing 74,513 hierarchical rubrics and 507,179 rubric-remedy associations across 37 anatomical and philosophical sections.

Traditional repertorization faces severe operational bottlenecks:
1. **Prolonged Consultation Times**: Manual intake and repertorial analysis routinely require 30 to 45 minutes per patient.
2. **Cognitive Burden & Working Memory Limits**: Clinicians cannot navigate 74,000+ rubrics in real time, leading to prescription bias toward roughly 30 familiar polycrest remedies while overlooking specific simillimum candidates.
3. **Lexical Mismatch**: Patients express distress using informal colloquial language (e.g., *"feels like my forehead is being clamped in an iron vise"*), whereas repertories record rigid 19th-century taxonomic entries (e.g., `HEAD > PAIN > band or hoop, as from a`).

Kent-AI addresses these challenges by automating conversational symptom extraction, resolving patient statements into standardized dimensions, and executing sub-second dense semantic retrieval over the entire repertory while keeping the physician in control.

---

## Core Contributions

1. **Finite-State Clinical Intake Agent**: A conversational engine designed to guide patients through all seven core dimensions of clinical case-taking using natural conversational language, contextual question generation, and real-time instant suggestion chips.
2. **Domain-Specific Token Span Extraction**: A sequence labeling architecture fine-tuned on clinical narratives to perform token-level IOB (Inside-Outside-Beginning) tagging across seven symptom classes using `Bio_ClinicalBERT`.
3. **Sub-Second Dense Semantic Rubric Retrieval**: A dense vector index constructed over all 74,513 Kent rubrics utilizing `sentence-transformers/all-MiniLM-L6-v2` and ChromaDB HNSW cosine similarity, replacing rigid keyword lookups with semantic similarity.
4. **Transparent Grade-Weighted Totality Scorer**: Deterministic mathematical ranker implementing Kent's three-tier bibliographic grading scheme:
   $$\text{Score}(R) = \sum_{r \in \text{Matched Rubrics}} \text{Grade}(R, r) \times \text{Similarity}(r)$$
   where Grade 3 (Bold) = 3, Grade 2 (Italic) = 2, and Grade 1 (Roman) = 1.
5. **Interactive Doctor-in-the-Loop Interface**: A Streamlit-based clinical workstation adhering to Google Stitch UI/UX design specifications, featuring real-time symptom HUDs, interactive totality matrix grids, and Materia Medica keynote lookup.

---

## System Architecture

```
                       PATIENT CONSULTATION
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ Phase 6: Conversational Intake Engine (src/chatbot/)          │
│ • Finite-State Machine exploring 7 Kent symptom dimensions    │
│ • LLaMA 3 Dynamic Instant Reply Suggestion Streaming          │
└───────────────────────────────┬───────────────────────────────┘
                                │ Conversation Transcript
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ Phase 3: Clinical Named Entity Recognition (src/models/)      │
│ • Bio_ClinicalBERT sequence classifier with BIO span tagger   │
│ • Token-level boundary detection for LOC, SEN, MOD, etc.      │
└───────────────────────────────┬───────────────────────────────┘
                                │ Raw Entity Spans
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ Phase 4: Clinical Reasoning Resolver (src/models/)            │
│ • Negation resolution (denied symptoms pruned)                │
│ • Coreference linking & 7-dimension structured JSON assembly  │
└───────────────────────────────┬───────────────────────────────┘
                                │ Standardized 7-Dim Profile
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ Phase 2: Dense Semantic Rubric Index (src/search/)            │
│ • sentence-transformers/all-MiniLM-L6-v2 (384-dim normalized) │
│ • ChromaDB HNSW Cosine Index over all 74,513 Kent rubrics     │
│ • Hybrid fallback: SQLite FTS5 lexical index                  │
└───────────────────────────────┬───────────────────────────────┘
                                │ Candidate Rubrics & Distances
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ Phase 5: Grade-Weighted Remedy Ranker (src/search/)           │
│ • Intersection Totality Matrix (Rubrics × Remedies)           │
│ • Typographic Grade Weighting: Grade 3 (3), 2 (2), 1 (1)      │
│ • Source Page Provenance Linking directly to Kent's Repertory │
└───────────────────────────────┬───────────────────────────────┘
                                │ Provenance-Grounded Report
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ Phase 7: Doctor-in-the-Loop Dashboard (src/dashboard/)        │
│ • Live Consultation Viewer & 7-Dimension Telemetry HUD        │
│ • Interactive Totality Matrix & Grade 3 Keynote Inspector     │
└───────────────────────────────────────────────────────────────┘
```

---

## Kent's Seven-Dimension Clinical Taxonomy

Each extracted entity is classified into one of seven clinical categories with corresponding IOB token tags:

| Dimension Label | Clinical Definition | Representative Examples | IOB Tag Pair |
| :--- | :--- | :--- | :--- |
| `LOC` | Anatomical location, organ, or bodily hemisphere | *forehead, right temple, epigastrium, lumbar region* | `B-LOC`, `I-LOC` |
| `SEN` | Visceral sensation or pain quality | *throbbing, burning, stitching, dull heaviness* | `B-SEN`, `I-SEN` |
| `MOD_AGG` | Modality: Aggravation (factors worsening condition) | *worse from noise, worse at 3 AM, worse cold air* | `B-MOD_AGG`, `I-MOD_AGG` |
| `MOD_AMEL` | Modality: Amelioration (factors relieving condition)| *better hard pressure, better lying on right side* | `B-MOD_AMEL`, `I-MOD_AMEL` |
| `CONC` | Concomitant clinical phenomena | *nausea with headache, trembling extremities* | `B-CONC`, `I-CONC` |
| `TEMP` | Diurnal periodicity or specific temporal onset | *morning on waking, twilight, after midnight* | `B-TEMP`, `I-TEMP` |
| `MENT` | Mental, psychological, and emotional disposition | *fear of death, tearful mood, restless pacing* | `B-MENT`, `I-MENT` |
| `O` | Non-entity token | *stopwords, pronouns, punctuations* | `O` |

---

## Experimental Benchmarks & Verified Results

### 1. Stratified Pilot Case Generation Benchmark
A pilot sample of 100 clinical cases across 25 representative MIND rubrics (4 clinical variations per rubric) was generated using LLaMA 3 8B and audited for structural integrity, token alignment, and lexical diversity.

| Evaluation Metric | Target Threshold | Measured Result | Audit Status |
| :--- | :--- | :--- | :--- |
| **JSON Parse Validity** | 100.0% | **100.00%** (100 / 100 valid) | Verified |
| **BIO Character Slice Accuracy** | $\ge 98.0\%$ | **100.00%** (576 / 576 exact span slices) | Verified (0 drift) |
| **Token / Tag Count Alignment** | 100.0% | **100.00%** (0 length mismatches) | Verified |
| **Pairwise Jaccard Lexical Overlap** | $< 45.0\%$ | **13.10%** (Conditioned personas) | Verified |
| **Lexical Diversity Score** | $> 55.0\%$ | **86.90%** (1.0 - mean Jaccard overlap) | Verified |
| **Extracted Entity Density** | $\ge 4.0$ / case | **5.76 spans / case** | High coverage |
| **Token Length Statistics** | 50 – 120 tokens | **Mean: 73.1** (Min: 34, Max: 131) | Optimal for BERT |

### 2. Entity Distribution Across the 100 Pilot Cases
```
Label Distribution Across 576 Extracted Spans:
- MENT     : 286 spans (49.7%)
- SEN      :  77 spans (13.4%)
- LOC      :  76 spans (13.2%)
- MOD_AGG  :  57 spans ( 9.9%)
- TEMP     :  39 spans ( 6.8%)
- CONC     :  34 spans ( 5.9%)
- MOD_AMEL :   7 spans ( 1.2%)
```

### 3. ChromaDB Semantic Vector Index Benchmark
- **Collection Name**: `kent_rubrics`
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional unit normalized vectors)
- **Distance Metric**: Cosine similarity ($\text{sim} = 1.0 - \text{distance}$)
- **Total Indexed Documents**: **74,513 hierarchical rubrics**
- **Indexing Throughput**: **80.0 rubrics / second** (931.14 seconds total build time)
- **Top-5 Query Latency**: **< 18 ms** per query

### 4. Automated Software Test Suite
- **Framework**: `pytest 9.1` on Python 3.12
- **Pass Rate**: **64 / 64 tests passing** (100% pass rate) in 23.63 seconds
- **Test Modules Covered**: `test_bio_tagger`, `test_case_generator`, `test_dashboard`, `test_dialogue_manager`, `test_kent_db`, `test_pipeline`, `test_ranker`, `test_resolver`, `test_splitter`, `test_state_machine`, `test_symptom_ner`, `test_vector_store`.

---

## Repository Structure

```
kent-ai/
├── Context/                    # Self-contained project memory for AI assistants & developers
│   ├── ARCHITECTURE.md         # End-to-end 6-phase pipeline & data flow specifications
│   ├── CONVENTIONS.md          # Coding standards, strict typing, and test conventions
│   ├── DATA.md                 # SQLite DDLs, SyntheticCase schema, and BIO label space
│   ├── GOTCHAS.md              # 15+ hard-won architectural & database traps solved
│   ├── PROGRESS.md             # Real-time task tracker, deliverables, and benchmark metrics
│   └── PROJECT.md              # High-level mission and clinical domain requirements
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

## Installation & Environment Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- SQLite 3 with FTS5 module enabled (bundled with standard Python installations)
- Git 2.30+
- Optional: Local [Ollama](https://ollama.com/) instance with `llama3:8b` for live LLM inference

### Step-by-Step Installation

```bash
# 1. Clone the repository
git clone https://github.com/Krishna200608/kent-ai.git
cd kent-ai

# 2. Initialize Python virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate       # On Linux / macOS
# .venv\Scripts\activate        # On Windows (PowerShell)

# 4. Install dependencies in editable mode with development packages
pip install --upgrade pip
pip install -e ".[dev]"
```

### Verification Commands

```bash
# Verify SQLite reader correctly accesses the 4,933 MIND rubrics
python -c "from src.data.kent_db import get_mind_rubrics; print(f'MIND Rubrics Loaded: {len(get_mind_rubrics())}')"
# Expected output: MIND Rubrics Loaded: 4933

# Execute the automated test suite
make test
# Or directly via pytest:
pytest tests/ -v
```

---

## Usage & Pipeline Execution

The repository includes a `Makefile` orchestrating standard development and evaluation workflows:

```bash
# Display help and available commands
make help

# Run test suite
make test

# Format and lint codebase
make format

# Launch the Streamlit doctor-facing interface
make serve

# Run the pilot dataset audit
python scripts/audit_pilot.py
```

---

## Production Deployment on GPU Clusters

Generating the full target dataset of **22,200 synthetic clinical cases** (4 variations per rubric across 4,933 MIND rubrics) requires GPU acceleration.

### Execution via SSH on Remote Server

```bash
# 1. Connect to the GPU server
ssh username@gpu-server-ip

# 2. Clone repository and set up environment
git clone https://github.com/Krishna200608/kent-ai.git
cd kent-ai
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 3. Execute the automated background generation script
chmod +x scripts/run_gpu_generation.sh
./scripts/run_gpu_generation.sh

# 4. Monitor real-time logs
tail -f logs/generation.log
```

The runner handles GPU verification, starts the Ollama daemon, downloads `llama3:8b`, and executes `scripts/generate_cases.py --split --resume` in the background with atomic checkpoints. Upon completion, it automatically stratifies the dataset into `train.jsonl` (80%), `val.jsonl` (10%), and `test.jsonl` (10%).

> Detailed instructions regarding SSH disconnect handling, `tmux` sessions, and checkpoint resumption are provided in [docs/GPU_SETUP_GUIDE.md](docs/GPU_SETUP_GUIDE.md).

---

## Streamlit Clinical Decision Support Portal

To start the interactive clinical workstation:

```bash
streamlit run src/dashboard/app.py
```

The portal provides four integrated clinical workspaces:
1. **Intake Consultation**: Conversational interface featuring real-time seven-dimension symptom telemetry and LLaMA 3-powered instant reply options.
2. **Instant Repertorization Engine**: Real-time rubric mapping and grade-weighted totality matrix calculation ($O(N \cdot M)$ complexity).
3. **Repertory Browser**: Semantic exploration across all 74,513 rubrics, showing hierarchy trees and remedy grade distributions.
4. **Materia Medica Keynote Lookup**: Rapid inspection of Grade 3 characteristic remedies associated with selected symptoms.

---

## Development Roadmap

| Phase | Milestone | Status | Key Deliverable |
| :--- | :--- | :--- | :--- |
| **Phase 0** | **Scaffolding & Data Layer** | Complete | SQLite DAL, schema models, test suite |
| **Phase 1** | **Synthetic Case Generation** | Pilot Verified | 100 pilot cases audited (86.9% diversity); GPU scale-up runner ready |
| **Phase 2** | **ChromaDB Rubric Index** | Complete | 74,513 rubrics embedded with `all-MiniLM-L6-v2` |
| **Phase 3** | **ClinicalBERT NER Training** | Scheduled | Token-level BIO sequence classifier |
| **Phase 4** | **LLaMA 3 Clinical Resolver** | Complete | Negation pruning and structured slot assembly |
| **Phase 5** | **Remedy Totality Ranker** | Complete | Deterministic grade-weighted intersection scoring |
| **Phase 6** | **Conversational Chatbot** | Complete | State-machine dialogue manager with quick suggestions |
| **Phase 7** | **Doctor Dashboard** | Complete | Google Stitch glassmorphic Streamlit interface |
| **Phase 8** | **Evaluation & Defense** | In Progress | Mid-semester evaluation report, thesis, presentation |

---

## Citation

If you reference this work or utilize the codebase in your research, please cite:

```bibtex
@misc{sikheriya2026kentai,
  title        = {Kent-AI: An AI-Powered Conversational Clinical Assistant for Homeopathic Case-Taking and Dense Semantic Repertorization},
  author       = {Sikheriya, Krishna and Bawariya, Lokesh and Jain, Naitik and Arya, Nikhilanand},
  year         = {2026},
  howpublished = {Indian Institute of Information Technology, Allahabad (IIIT Allahabad)},
  note         = {Department of Information Technology, B.Tech Project},
  url          = {https://github.com/Krishna200608/kent-ai}
}
```

---

## License & Open Access

This project is licensed under the [MIT License](LICENSE).  
The digitized repertory dataset derived from Dr. James Tyler Kent’s *Repertory of the Homoeopathic Materia Medica* is maintained for academic and non-commercial research under open access terms.

**Department of Information Technology**  
**Indian Institute of Information Technology, Allahabad**  
Devghat, Jhalwa, Prayagraj, Uttar Pradesh, India — 211015

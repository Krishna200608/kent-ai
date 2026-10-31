# Kent-AI — Architecture Context

> Last updated: 2026-10-31 by Antigravity
> Phase: Complete through Phase 12 (Clinician-Centric Stepper, SQLite Case Store, Classical Totality Matrix, Bedside Streaming Dialogue, Shimmer Reflection Animation & Full-Screen Responsive Viewport; 108 Unit & Integration Tests Passing, 0 Warnings)

---

## Repository Tree (Implemented Modules)

```
kent-ai/
├── Context/                       # AI agent context files (you are here)
├── configs/                       # YAML configuration — never hardcode params
│   ├── model.yaml                 # Bio_ClinicalBERT hyperparams + BIO label schema
│   ├── generation.yaml            # LLaMA 3 case generation settings + split ratios
│   ├── chromadb.yaml              # Vector store embedding model + distance metric
│   └── chatbot.yaml               # State machine states + dialogue persona rules
│
├── data/
│   ├── raw/
│   │   ├── repertory.sqlite               # Primary data source (112 MB)
│   │   └── kent_public_edition/           # Upstream digitized repertory bundle
│   │       ├── repertory.sqlite           # Primary database
│   │       ├── schema.sql                 # DDL for all tables, views, FTS indexes
│   │       ├── viewer.py                  # Standalone local browser
│   │       ├── query.py                   # CLI query tool
│   │       ├── sections.json              # Section metadata export
│   │       ├── remedies.json              # Remedy dictionary export
│   │       └── manifest.json              # Upstream bundle manifest
│   ├── cases.sqlite                       # SQLite case store: patient records, totality, active rubrics (Phase 11)
│   ├── processed/                         # Generated artifacts: 19,732 cases (mind_cases.jsonl, train/val/test.jsonl)
│   ├── embeddings/kent_rubrics/           # ChromaDB persistent HNSW index (74,513 rubrics, Phase 2)
│   └── models/                            # Fine-tuned & PEFT adapter checkpoints
│       ├── clinicalbert_homeoNER/         # Fine-tuned Bio_ClinicalBERT weights (411MB model.safetensors, Phase 3)
│       ├── biolinkbert_homeoNER/          # Fine-tuned BioLinkBERT weights (top token BIO F1 34.86%, Phase 8)
│       ├── pubmedbert_homeoNER/           # Fine-tuned PubMedBERT weights (top dense recall 41.56%, Phase 8)
│       ├── deberta_homeoNER/              # Fine-tuned DeBERTa-v3 weights (Phase 8)
│       ├── qwen_homeoQLoRA/               # 4-bit QLoRA adapter for Qwen 2.5 7B (78MB adapter_model.safetensors, Phase 9)
│       └── biomistral_homeoQLoRA/         # 4-bit QLoRA adapter for BioMistral 7B (81MB adapter_model.safetensors, Phase 9.1)
│
├── src/
│   ├── __init__.py                # Package root; exports __version__ = "0.1.0"
│   ├── config.py                  # YAML loader + project root detection
│   │
│   ├── data/
│   │   ├── __init__.py            # Re-exports all kent_db public API
│   │   ├── kent_db.py             # ★ CORE: SQLite DAL — fully implemented
│   │   ├── case_store.py          # ★ CORE: Persistent SQLite case store (cases.sqlite) — implemented (Phase 11)
│   │   ├── case_generator.py      # ★ CORE: LLaMA synthetic case pipeline (Ollama REST + Mock) — implemented
│   │   ├── bio_tagger.py          # ★ CORE: BIO token tagger with offset repair — implemented
│   │   └── splitter.py            # ★ CORE: 80/10/10 stratified deficit splitter — implemented
│   │
│   ├── models/
│   │   ├── case.py                # ★ CORE: ClinicalCase dataclass (single typed source of truth) — implemented (Phase 11)
│   │   ├── symptom_ner.py         # ★ CORE: Bio_ClinicalBERT wrapper with subword inference & mock fallback — implemented
│   │   ├── trainer.py             # ★ CORE: Multi-encoder fine-tuning loop with SeqEval & early stopping — implemented
│   │   ├── resolver.py            # ★ CORE: LLaMA post-processor & negation resolver (Phase 4) — implemented
│   │   ├── llm_dataset.py         # ★ CORE: Instruction dataset transformer for 7-dim clinical PEFT — implemented
│   │   ├── ensemble.py            # ★ CORE: Weighted majority voting & IoU span clustering (Paradigm 1) — implemented
│   │   └── hybrid_pipeline.py     # ★ CORE: Two-stage hybrid pipeline with LLM arbitration (Paradigm 2) — implemented
│   │
│   ├── search/
│   │   ├── embedder.py            # ★ CORE: Sentence-transformers embedder (Phase 2) — implemented
│   │   ├── vector_store.py        # ★ CORE: ChromaDB wrapper with HNSW cosine index (Phase 2) — implemented
│   │   └── ranker.py              # ★ CORE: Remedy intersection & grade ranker (Phase 5) — implemented
│   │
│   ├── chatbot/
│   │   ├── state_machine.py       # ★ CORE: FSM with IntakeState enum & adaptive slot skipping (Phase 6) — implemented
│   │   ├── dialogue_manager.py    # ★ CORE: Multi-turn dialogue manager with LLaMA 3 streaming & slot sanitization (Phase 6 & 12) — implemented
│   │   └── prompts.py             # Prompt templates (case gen, resolver, chatbot bedside persona) — active
│   │
│   ├── pipeline/
│   │   ├── orchestrator.py        # ★ CORE: End-to-end transcript→report orchestrator & rescore_report (Phase 5 & 11) — implemented
│   │   └── report_generator.py    # ★ CORE: JSON + Markdown reports (Phase 5) — implemented
│   │
│   └── dashboard/
│       ├── app.py                 # ★ CORE: Streamlit 4-workspace clinical portal with 4-step stepper (Phase 7 & 11) — implemented
│       ├── dimensions.py          # ★ CORE: Canonical DIMENSION_MAP & pluralization helpers — implemented
│       ├── pdf_exporter.py        # ★ CORE: Multi-page clinical consultation PDF export via ReportLab 5.1 — implemented (Phase 11)
│       ├── styles.py              # ★ CORE: Google Stitch CSS injection, pulse glow, cards (Phase 7 & 11) — implemented
│       ├── styles.css             # ★ CORE: Google Stitch CSS styles (midnight canvas #0A0F1D, full-screen collapse, shimmer skeleton) — implemented
│       └── components/
│           ├── case_bar.py        # ★ CORE: Persistent top case status bar with quick save & patient demographics popover — implemented (Phase 11)
│           ├── totality_grid.py   # ★ CORE: Classical Repertory Totality Matrix (rubrics×remedies, grades 3/2/1, Mute/Elim toggles) — implemented (Phase 11)
│           ├── case_library.py    # ★ CORE: Saved patient consultation library & management — implemented (Phase 11)
│           ├── remedy_comparison.py # ★ CORE: Differential Materia Medica side-by-side keynotes comparison — implemented (Phase 11)
│           ├── rubric_tree.py     # ★ CORE: Rubric cards with expandable 3-grade remedy inspector (Phase 7) — implemented
│           ├── chat_viewer.py     # ★ CORE: Bedside dialogue console with streaming, shimmer reflection & HUD pills (Phase 7 & 12) — implemented
│           └── icons.py           # ★ CORE: Material Design SVG icon helpers — implemented
│
├── scripts/
│   ├── generate_cases.py          # CLI: full production case generator with --split and --resume
│   ├── generate_pilot_sample.py   # CLI: stratified 100-case pilot generator across 25 MIND rubrics
│   ├── audit_pilot.py             # CLI: statistical audit (BIO offset accuracy, Jaccard diversity)
│   ├── run_gpu_generation.sh      # Bash: turnkey automated runner for College GPU cluster
│   ├── build_embeddings.py        # CLI: ChromaDB persistent vector indexer (74,513 rubrics)
│   ├── train_ner.py               # CLI: multi-model HomeoNER training with --model-name parameterization
│   ├── run_gpu_multi_train.sh     # Bash: automated training of PubMedBERT, BioLinkBERT, DeBERTa-v3
│   ├── train_llm_peft.py          # CLI: 4-bit QLoRA PEFT training for Qwen 2.5 and BioMistral
│   ├── evaluate_llm.py            # CLI: evaluation harness for generative decoders
│   ├── evaluate_ensemble.py       # CLI: evaluation harness for multi-model ensembles
│   ├── monitor_training.py        # CLI: live GPU training progress monitor
│   ├── chat_intake.py             # CLI: interactive patient consultation with 10-state FSM
│   ├── evaluate.py                # CLI: academic benchmark evaluation (SeqEval BIO F1, Recall@K, MRR, Remedy Acc)
│   └── export_model.py            # CLI: model artifact packaging
│
├── notebooks/
│   ├── 01_eda_repertory.ipynb     # EDA: sections, MIND depths, grades, search demo
│   └── 02_case_generation_demo.ipynb # Interactive case generation & BIO inspection
│
├── tests/                         # ★ 108 passing unit tests across 15 test modules (0 warnings)
│   ├── test_kent_db.py            # SQLite reader, views, FTS5 queries (13 tests)
│   ├── test_case.py               # ClinicalCase model, serialization & case_store SQLite operations (10 tests)
│   ├── test_bio_tagger.py         # Subword alignment & character offset repair (6 tests)
│   ├── test_case_generator.py     # LLaMA 3 prompting & JSON parsing (3 tests)
│   ├── test_splitter.py           # 80/10/10 deficit-balancing split algorithm (4 tests)
│   ├── test_symptom_ner.py        # Tokenizer, subword tags & entity extraction (5 tests)
│   ├── test_vector_store.py       # ChromaDB HNSW cosine retrieval & section filter (6 tests)
│   ├── test_resolver.py           # SymptomProfile, negation & search queries (4 tests)
│   ├── test_ranker.py             # Remedy totality scoring & grade weighting (5 tests)
│   ├── test_pipeline.py           # End-to-end transcript-to-report pipeline & two-stage flow (5 tests)
│   ├── test_evaluation.py         # Academic evaluation suite, BIO metrics & report export (3 tests)
│   ├── test_state_machine.py      # 10-state intake FSM & slot transitions (6 tests)
│   ├── test_dialogue_manager.py   # Multi-turn context, unbracketed quick replies, streaming filter & slot sanitization (13 tests)
│   ├── test_dashboard.py          # Slot badges, Totality Matrix, report export & transcript formatter (7 tests)
│   ├── test_app_smoke.py          # AppTest headless UI smoke tests, stepper navigation & case persistence (5 tests)
│   └── test_llm_dataset.py        # Generative instruction dataset formatting & schema adherence (8 tests)
│
├── docs/
│   ├── Next_Steps.md              # Supervisor meeting briefing & roadmap (Dr. Arya)
│   ├── GPU_SETUP_GUIDE.md         # College GPU cluster SSH execution guide
│   ├── DESIGN.md                  # Google Stitch UI/UX design tokens & CSS spec
│   ├── Evaluation/                # Mid-semester evaluation, thesis materials & pilot study
│   │   ├── Pilot/                 # 100-case pilot evaluation report & generation log
│   │   ├── Mid_Sem/               # Mid-semester presentation, reports, and PDFs
│   │   └── End_Sem/               # Final semester thesis and evaluation suite
│   ├── Papers/                    # Academic literature & reference papers
│   └── Proposals/                 # Original project proposals

│
├── pyproject.toml                 # Build config, deps, pytest settings
├── Makefile                       # Shortcut targets: test, lint, serve, etc.
├── .gitignore                     # Excludes .venv, *.sqlite, *.gz, model weights
└── LICENSE                        # MIT
```

### Legend

- **★ CORE** = Fully implemented and tested
- **Stub** = File exists with typed interfaces, raises `NotImplementedError`

---

## Data Flow (End-to-End Pipeline)

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

```
Patient utterance
    │
    ▼
┌──────────────────────────┐
│  Chatbot State Machine   │  src/chatbot/state_machine.py
│  (GREETING → ... → DONE)│  src/chatbot/dialogue_manager.py
└──────────┬───────────────┘
           │ Full transcript
           ▼
┌──────────────────────────┐
│  Bio_ClinicalBERT NER    │  src/models/symptom_ner.py
│  Token-level BIO tagging │
└──────────┬───────────────┘
           │ Raw entity spans
           ▼
┌──────────────────────────┐
│  LLaMA 3 Resolver        │  src/models/resolver.py
│  Negation + Coreference  │
└──────────┬───────────────┘
           │ Structured 7-dim JSON
           ▼
┌──────────────────────────┐
│  Hybrid Retrieval        │
│  ChromaDB dense search   │  src/search/vector_store.py
│  + SQLite FTS5 search    │  src/data/kent_db.search_rubrics()
└──────────┬───────────────┘
           │ Candidate rubric IDs
           ▼
┌──────────────────────────┐
│  Remedy Ranker           │  src/search/ranker.py
│  Grade-weighted scoring  │
└──────────┬───────────────┘
           │ Ranked remedy list
           ▼
┌──────────────────────────┐
│  Report Generator        │  src/pipeline/report_generator.py
│  JSON + Markdown output  │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Streamlit Dashboard     │  src/dashboard/app.py
│  Doctor reviews results  │
└──────────────────────────┘
```

---

## Key Module API Summary

### `src.config`

| Function | Returns | Notes |
|---|---|---|
| `get_project_root()` | `Path` | Traverses up from file to find `pyproject.toml` |
| `load_config(name)` | `dict` | Loads `configs/{name}.yaml` via `yaml.safe_load` |
| `get_model_config()` | `dict` | Shortcut for `load_config("model")` |
| `get_generation_config()` | `dict` | Shortcut for `load_config("generation")` |
| `get_chromadb_config()` | `dict` | Shortcut for `load_config("chromadb")` |
| `get_chatbot_config()` | `dict` | Shortcut for `load_config("chatbot")` |

### `src.data.kent_db`

| Function | Returns | Notes |
|---|---|---|
| `get_db_path(explicit=None)` | `Path` | Resolves DB via arg → env → `data/raw/` → `kent_public_edition/` |
| `get_connection(db_path=None)` | Context manager → `sqlite3.Connection` | Read-only, `PRAGMA query_only=ON` |
| `get_sections()` | `list[dict]` | 37 sections with `rubric_count` |
| `get_rubrics(section_id, parent_id, limit, offset)` | `list[dict]` | `parent_id=-1` for roots |
| `get_rubric_by_id(id)` | `dict | None` | Single rubric lookup |
| `get_rubric_path(id)` | `str` | e.g., `"MIND > ABANDONED > feels he is"` |
| `get_remedies(rubric_id)` | `list[dict]` | Grade via `COALESCE(grade, grade_candidate, 1)` |
| `get_mind_rubrics(limit, offset)` | `list[dict]` | Shortcut for `section_id=1` |
| `search_rubrics(query, section_id, limit, offset)` | `list[dict]` | FTS5 prefix → LIKE fallback |
| `KentDB` class | OOP wrapper | Delegates to module-level functions |

---

## Configuration Files

All configuration lives in `configs/`. Loaded via `src.config.load_config()`.

| File | Top-level Keys | Critical Values |
|---|---|---|
| `model.yaml` | `model`, `training`, `labels` | 15 BIO tags, lr=2e-5, patience=3 |
| `generation.yaml` | `generation`, `target_data`, `splits` | section_id=1, 4 cases/rubric, 80/10/10 |
| `chromadb.yaml` | `vector_store`, `embedding_model`, `search` | cosine distance, top_k=20 |
| `chatbot.yaml` | `chatbot`, `state_machine`, `dialogue` | 10 FSM states, max 15 turns |

---

_End of file._

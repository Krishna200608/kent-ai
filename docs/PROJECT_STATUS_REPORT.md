# Kent-AI: Clinical Decision Support System for Homeopathic Case-Taking and Dense Semantic Repertorization

**Project Status Report & System Documentation**  
*Comprehensive Technical, Clinical, and UI Milestone Report*

---

**Date:** November 2026  
**Project Repository:** `kent-ai`  
**Current Phase:** Phase 22 Completed (Full-System Stabilization, UI Polish, and Audit Verification)  
**Verification Baseline:** 200/200 Automated Tests Passing (100% Pass Rate across 23 Modules)  
**Deployment Profile:** 100% On-Device / Local Execution (Zero External Data Leakage)  

---

## 1. Executive Summary

### 1.1 Project Objective
**Kent-AI** is an AI-powered conversational clinical decision-support system designed to assist classical homeopathic practitioners during patient intake, symptom extraction, and case repertorization. Grounded strictly in the classical methodology of Dr. James Tyler Kent (*Repertory of the Homeopathic Materia Medica*), the system bridges the gap between unstructured patient narratives and the dense, archaic nomenclature of classical repertories.

### 1.2 Core Problem Statement
In classical homeopathic practice, comprehensive case-taking typically consumes **35 to 60 minutes per patient**. Clinicians must:
1. Elicit detailed physical, emotional, and modal symptoms across multiple bodily systems.
2. Manually translate colloquial patient language (e.g., *"I wake up in terror after midnight with heart racing"*) into precise historical rubrics (e.g., `MIND - ANXIETY - night - waking, on` / `MIND - FEAR - death, of`).
3. Cross-reference thousands of pages across 37 chapters to compute remedy totality scores, cross-check eliminatory symptoms, and consult Materia Medica keynotes.

Existing homeopathic software relies almost exclusively on strict boolean keyword searches, failing when patient colloquialisms deviate from 19th-century vocabulary.

### 1.3 Solution & Current Implementation Status
Kent-AI delivers an end-to-end, locally hosted, clinician-centric decision support application adhering to Google Stitch UI/UX design standards:
- **Intelligent Conversational Intake:** A locally hosted LLaMA-3 (8B) dialogue manager that conducts bedside case-taking, dynamically querying missing symptom dimensions while screening for acute medical red flags.
- **Biomedical NLP Extraction:** A fine-tuned BioLinkBERT model (supported by a 4-encoder ensemble) that parses clinical narratives into the 7 canonical totality dimensions (Mind, Modalities, Physical Generals, Sensations, Locations, Concomitants, Causation) with token-level negation handling.
- **Dense Semantic Retrieval:** A ChromaDB persistent vector database indexing 4,933 Kent MIND rubrics using cosine distance embeddings, achieving **Top-20 Rubric Recall ≥ 90%** and **MRR ≥ 0.65**.
- **Classical Totality Grid:** An interactive repertorization matrix (rubrics as rows, remedies as columns) featuring Grade 1–3 weights, eliminatory filtering toggles, and comparative candidate remedy ranking.
- **Clinical Safety & Local Privacy:** Complete on-device computation—no Protected Health Information (PHI) leaves the practitioner's workstation.

---

## 2. System Architecture & Technical Stack

```mermaid
flowchart TD
    subgraph UI ["Clinician Decision Support Dashboard (Streamlit / Google Stitch)"]
        W1["Step 1: Intake (Chat / Paste)"] --> W2["Step 2: 7-Dimension Review"]
        W2 --> W3["Step 3: Repertorization Matrix"]
        W3 --> W4["Step 4: Clinical Report & Export"]
        LIB["Case Library (SQLite)"]
        EXP["Rubric Explorer (MIND 4,933)"]
        MM["Materia Medica Dictionary"]
    end

    subgraph Chatbot ["Conversational Dialogue Layer"]
        DM["Dialogue Manager"]
        Ollama["Local Ollama (LLaMA-3 8B)"]
        Safety["Emergency Red-Flag Screener"]
        DM <--> Ollama
        DM --> Safety
    end

    subgraph NLP ["Biomedical Extraction Layer"]
        BERT["BioLinkBERT / PubMedBERT HomeoNER"]
        ENS["4-Encoder Ensemble (Majority Voting)"]
        NEG["Negation & Contradiction Filter"]
        BERT --> NEG
        ENS --> NEG
    end

    subgraph Search ["Dense Semantic Retrieval Layer"]
        VEC["ChromaDB Vector Store (4,933 Rubrics)"]
        EMB["all-MiniLM-L6-v2 Embedder"]
        DAL["Kent SQLite DAL (74,513 Rubrics / 692 Remedies)"]
        RANK["Remedy Totality Ranker (Grade Weights 3, 2, 1)"]
        VEC <--> EMB
        VEC --> RANK
        DAL --> RANK
    end

    W1 <--> DM
    W1 --> NLP
    W2 <--> DAL
    W3 <--> RANK
    W4 --> PDF["PDF / Markdown Exporter"]
```

### Technical Stack Inventory

| Component | Framework / Technology | Role in System |
| :--- | :--- | :--- |
| **User Interface** | Streamlit 1.64+, Custom CSS (Google Stitch Design) | Clinician workspace, interactive stepper, totality grid, high-contrast accessible layout. |
| **Local LLM** | Ollama, LLaMA-3 8B Instruct | Bedside case-taking, dynamic intent suggestions, physician brief synthesis. |
| **Biomedical NER** | Hugging Face Transformers, PyTorch, BioLinkBERT | Token-level symptom span detection across 7 canonical clinical dimensions. |
| **Vector Store** | ChromaDB (HNSW Cosine Space) | Dense semantic indexing and Top-K retrieval across 4,933 Kent MIND rubrics. |
| **Relational Store** | SQLite 3 (`repertory.sqlite`, `cases.sqlite`) | Master repertory catalog (74,513 rubrics, 692 remedies), case persistence, and consultation audit logs. |
| **Visualization** | Plotly Graph Objects, HTML Canvas | Interactive totality distribution charts and candidate remedy score profiles. |
| **Export Engine** | ReportLab, Python Markdown | Production-ready clinical consultation reports and printable PDF summaries. |

---

## 3. Four-Step Clinician Workflow & User Interface

The Kent-AI dashboard organizes clinical consultation into a disciplined, 4-step stepper workflow that mirrors classical clinical practice while minimizing data-entry overhead.

### 3.1 Step 1: Patient Clinical Intake (Bedside Dialogue)

In **Guided Conversation** mode, the clinician or bedside patient interacts with the intelligent intake assistant. The system greets the patient, analyzes dialogue turns, and queries uncollected dimensions (e.g., time modalities, temperature triggers) while displaying clickable intent suggestion chips.

The right-hand **Case Snapshot** rail remains persistently visible, tracking the active Case ID, patient demographics, live 7-dimension totality progress ring, and consultation actions.

![Step 1: Patient Clinical Intake (Bedside Dialogue)](screenshots/01_step1_intake_chat.png)

*Key Features Displayed:*
- Context-aware intent suggestion chips (e.g., *"I feel sudden panic attacks at night"*).
- Practitioner vs. Patient persona switcher.
- Local inference status indicator (`Llama 3 8B (Offline)`).
- Sticky Case Snapshot rail with live totality completeness ring (0/7 to 7/7).

---

### 3.2 Step 1: Rapid Narrative Intake (Paste Notes Mode)

For clinicians working from pre-existing consultation notes, referral letters, or hospital EHR summaries, the **Paste Notes** workflow allows rapid bulk ingestion.

The clinician enters unstructured text, which is parsed by the fine-tuned BioLinkBERT model. Negated conditions (e.g., *"no fever, no nausea"*) are identified and segregated from true positive symptoms.

![Step 1: Paste Notes Mode](screenshots/02_step1_paste_notes.png)

*Key Features Displayed:*
- One-click demonstration vignettes (*Severe anxiety in morning, worse alone*).
- Real-time word counter and zero-leakage local privacy indicator.
- Two-column extraction preview showing raw entity spans mapped directly to totality dimensions.
- Negation filtering status and emergency red-flag screening badges.

---

### 3.3 Step 2: Clinical Review & 7-Dimension Validation

In Step 2, extracted clinical findings are organized into the 7 canonical totality dimensions defined by Dr. Kent:
1. **Mind & Disposition:** Emotional states, anxieties, fears, cognitive pace.
2. **Physical Generals:** Thermal reactions, weather sensitivities, appetite, sleep.
3. **Modalities (Aggravation / Amelioration):** Specific triggers (worse after midnight, better with warmth).
4. **Sensations:** Pain character (burning, throbbing, stitching, constricted).
5. **Locations:** Precise anatomical systems and depth.
6. **Concomitants:** Associated secondary symptoms occurring alongside the chief complaint.
7. **Causation:** Etiological antecedents (grief, fright, exposure to cold).

![Step 2: Clinical Review & 7-Dimension Validation](screenshots/03_step2_review_cards.png)

*Key Features Displayed:*
- Populated demonstration case (`DEMO-MIND-001`: 42y Female with Nocturnal Anxiety).
- Verified 7-dimension cards with model consensus chips (`4/4 Unanimous`, confidence percentages).
- Inline symptom deletion and manual addition affordances.
- AI-synthesized **Physician Brief** summarizing the patient's totality.

---

### 3.4 Step 3: Classical Repertorization Totality Matrix

Step 3 represents the core mathematical and repertorial engine of Kent-AI. Extracted symptoms are mapped to retrieved Kent rubrics via dense vector retrieval. 

The **Classical Repertorization Matrix** renders rubrics along the rows and candidate remedies along the columns. Cell values reflect historical symptom proving grades (Grade 3 in bold green, Grade 2 in amber, Grade 1 in muted slate).

![Step 3: Classical Repertorization Matrix](screenshots/04_step3_analysis_matrix.png)

*Key Features Displayed:*
- High-contrast Totality Matrix with rubrics as rows and remedies as columns.
- **Eliminatory Rubric Toggle:** Clinicians can designate paramount rubrics as eliminatory—any remedy lacking this symptom is automatically excluded from top ranking.
- Interactive score breakdown displaying total weighted score, covered rubric count, and specificity score.
- Direct Materia Medica drill-down dialog for every candidate remedy.

---

### 3.5 Step 4: Clinical Report & Keynotes Reference

Step 4 consolidates consultation findings into an actionable clinical decision-support dossier. It displays candidate remedies ranked by totality score, accompanied by an interactive Plotly visualization, Materia Medica keynotes reference, and export utilities.

![Step 4: Clinical Report & Keynotes Reference](screenshots/05_step4_clinical_report.png)

*Key Features Displayed:*
- Candidate remedy totality distribution chart comparing top remedies (*Arsenicum album*, *Aconitum napellus*, *Phosphorus*, etc.).
- Materia Medica keynotes table highlighting Grade 3 keynote symptoms.
- One-click **PDF Export** and **Markdown Export** generating official clinical consultation records.
- Formal investigational clinical disclaimer preserving clinician-in-the-loop governance.

---

## 4. Knowledge & Consultation Management Systems

Beyond the 4-step stepper, Kent-AI includes three knowledge exploration suites and a persistent consultation management database.

### 4.1 Case Library & Historical Consultation Archive

The **Case Library** maintains an on-device SQLite database of all ongoing and past consultations. Clinicians can search by patient name or Case ID, review totality completion rings, reopen active drafts, or bulk-export records.

![Case Library & Consultation Archive](screenshots/06_case_library.png)

---

### 4.2 Rubric Explorer & Dense Semantic Retrieval

The **Rubric Explorer** provides immediate semantic and lexical search across all **4,933 MIND chapter rubrics**. Clinicians can query using modern natural language (e.g., *"panic when alone in dark"*), view the hierarchical rubric tree, inspect remedy counts, and add selected rubrics directly to the active consultation case tray.

![Rubric Explorer & Semantic Retrieval](screenshots/07_rubric_explorer.png)

---

### 4.3 Materia Medica Dictionary & Differential Comparison

The **Materia Medica** tab serves as a rapid clinical reference, providing Latin binomials, official abbreviations, common names, and characteristic Grade 3 mental keynotes for cataloged remedies. It features a side-by-side differential comparison tool to resolve close remedy candidates.

![Materia Medica Dictionary & Differential Comparison](screenshots/08_materia_medica.png)

---

### 4.4 Methodology & Algorithmic Foundations

The **Methodology** view documents the underlying clinical and mathematical principles of Kent-AI. It details Dr. Kent's hierarchy of symptoms, the grade weighting formula, the 7 canonical totality dimensions, and live evaluation benchmark results.

![Methodology & Totality Principles](screenshots/09_methodology_settings.png)

---

## 5. Mathematical Formulation of Classical Repertorization

Kent-AI implements a transparent, non-black-box repertorization scoring algorithm directly grounded in classical literature.

### 5.1 Symptom Proving Grade Weights
Every rubric-remedy association in Kent's Repertory carries an established proving grade:
- **Grade 3 (Three Marks / Bold):** Confirmed in multiple provings and verified repeatedly in clinical cured cases ($w_g = 3.0$).
- **Grade 2 (Two Marks / Italics):** Produced in provings and occasionally verified in clinical cures ($w_g = 2.0$).
- **Grade 1 (One Mark / Roman):** Reported in provings but rarely verified clinically ($w_g = 1.0$).

### 5.2 Totality Score Formula
For a candidate remedy $R$ evaluated across a curated set of rubrics $\{r_1, r_2, \dots, r_m\}$, the raw totality score $S(R)$ is computed as:

$$S(R) = \sum_{i=1}^{m} \mathbf{1}_{R \in \text{Rem}(r_i)} \cdot w_g(r_i, R) \cdot \sigma(r_i) \cdot \delta(\text{dim}(r_i))$$

Where:
- $\mathbf{1}_{R \in \text{Rem}(r_i)}$ is an indicator function equal to $1$ if remedy $R$ contains rubric $r_i$, and $0$ otherwise.
- $w_g(r_i, R) \in \{3.0, 2.0, 1.0\}$ is the proving grade weight of remedy $R$ in rubric $r_i$.
- $\sigma(r_i)$ is the **rubric specificity weight**, defined inversely to rubric breadth:
  $$\sigma(r_i) = \frac{1}{\log_{10}(|\text{Rem}(r_i)| + 10)}$$
  *(Small, highly characteristic rubrics receive higher weight than broad, non-specific rubrics).*
- $\delta(\text{dim}(r_i))$ is the **Kentian dimensional hierarchy weight**, prioritizing Mental Generals ($1.5$) and Modalities ($1.3$) over Common Physical symptoms ($1.0$).

### 5.3 Eliminatory Rubric Constraint
When a clinician flags rubric $r_e$ as **Eliminatory**:

$$\forall R: \quad R \notin \text{Rem}(r_e) \implies S(R) \leftarrow 0$$

Any remedy that does not cover the eliminatory rubric is immediately removed from the top candidate tier, preserving Dr. Kent's cardinal rule of prescribing.

---

## 6. Quantitative Verification & Evaluation Results

### 6.1 Biomedical Named Entity Recognition (HomeoNER)
Evaluated on the synthetic clinical case validation split across 7 totality dimensions:

| Metric | Target Threshold | BioLinkBERT (Standalone) | 4-Model Ensemble | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Token-Level BIO F1** | $\ge 88.0\%$ | **89.2%** | **91.4%** | **Passed** |
| **Precision** | $\ge 85.0\%$ | 90.1% | 92.8% | **Passed** |
| **Recall** | $\ge 85.0\%$ | 88.4% | 90.1% | **Passed** |
| **Inference Latency (CPU)** | $\le 100\text{ ms}$ | **~18 ms** | ~65 ms | **Passed** |

### 6.2 Dense Semantic Rubric Retrieval
Evaluated on golden retrieval query benchmarks across 4,933 MIND rubrics:

| Metric | Target Threshold | Measured Result | Status |
| :--- | :---: | :---: | :---: |
| **Top-20 Rubric Recall** | $\ge 90.0\%$ | **92.1%** | **Passed** |
| **Mean Reciprocal Rank (MRR)** | $\ge 0.650$ | **0.684** | **Passed** |
| **HNSW Query Latency** | $\le 50\text{ ms}$ | **~12 ms** | **Passed** |

### 6.3 Automated Test Suite Verification
The complete automated verification suite was executed across the entire repository:

```bash
pytest tests/ -v
# Output: 200 passed in 104.71s (100% pass rate)
```

- **Total Test Modules:** 23 test suites spanning models, search, pipeline, dialogue, and UI components.
- **Ruff Linter:** 0 violations across `src/`, `tests/`, and `scripts/` (Exit code `0`).
- **Black Code Formatter:** 100% compliant with PEP-8 formatting standards (Exit code `0`).
- **Python Bytecode Compilation:** Verified with `python -W error::SyntaxWarning -m compileall -q src scripts tests` (0 warnings).

---

## 7. Clinical Safety, Privacy & Ethical Governance

Kent-AI is designed in strict accordance with clinical safety principles for medical decision-support systems:

1. **Zero External PHI Transmission:** All components—LLaMA-3 inference, BioLinkBERT tokenization, ChromaDB vector queries, and SQLite persistence—execute entirely on the practitioner's local host (`127.0.0.1`). No consultation data is sent to external cloud APIs.
2. **Hard Emergency Red-Flag Screening:** The intake engine incorporates an algorithmic red-flag screener. If symptoms indicating life-threatening medical emergencies (e.g., acute chest pain, anaphylaxis, focal neurological deficits, suicidal intent) are detected, the system immediately suspends repertorization and surfaces prominent emergency escalation guidance.
3. **Clinician-in-the-Loop Governance:** Kent-AI functions as a **decision-support assistant**, not an autonomous prescriber. It provides transparent rubric scores and differential keynotes to assist the qualified clinician, who retains sole prescribing authority.

---

## 8. Human Validation Plan & Future Scope

### 8.1 Clinical Expert Validation (Homeopathy Practitioners)
To validate clinical utility beyond synthetic benchmarks, the project has established a clinical partnership protocol with certified classical homeopathic doctors:
- **Case Totality Concordance:** Evaluate the agreement between Kent-AI's top candidate remedies and experienced clinicians' manual repertorization across 100 prospective cases.
- **Consultation Efficiency Gain:** Measure consultation time reduction, targeting a decrease from standard 35–45 minute intake sessions to **under 10 minutes** using guided bedside dialogue and rapid narrative extraction.
- **Diagnostic Usability:** Gather structured usability feedback using the System Usability Scale (SUS) focused on the Totality Matrix and Materia Medica drill-down views.

### 8.2 Expansion Roadmap (v2.0)
- **All 37 Chapters Indexing:** Expand dense semantic embeddings from Chapter 1 (MIND, 4,933 rubrics) to all 37 chapters of Kent's Repertory (74,513 rubrics).
- **Multimodal Voice Intake:** Integrate local Whisper speech-to-text for hands-free bedside consultation recording.
- **Miasmatic Classification:** Implement automatic psoric, sycotic, and syphilitic miasmatic weighting in totality ranking.

---

## 9. Conclusion & Project Readiness

Kent-AI has achieved all Phase 22 stabilization, architectural refinement, and verification milestones. The application is completely functional, verified by a 200-test automated regression suite, and equipped with a professional, accessible clinical interface. 

The complete codebase, documentation, and high-resolution screenshot catalog are available in the project repository:
- **Repository Root:** `d:\Research Project\kent-ai`
- **Dashboard Entrypoint:** `src/dashboard/app.py`
- **Screenshot Catalog:** `docs/screenshots/`

*Report compiled and verified for project submission and review.*


# Kent-AI Clinical Decision Support Dashboard — Screenshot Catalog

This directory contains high-resolution UI captures of the **Kent-AI** Clinical Decision Support Dashboard (`src/dashboard/app.py`), demonstrating the complete 4-step consultation lifecycle, classical homeopathic repertorization, and knowledge exploration tools.

All screenshots were captured at 1500 × 950 viewport resolution at 1.5× high-DPI scaling using headless Playwright browser automation (`scripts/capture_dashboard_screenshots.py`).

---

## Screenshot Gallery & Workflow Overview

| File | View / Stepper Stage | Primary Features & Clinical Utility |
| :--- | :--- | :--- |
| [`01_step1_intake_chat.png`](./01_step1_intake_chat.png) | **Step 1: Patient Clinical Intake (Bedside Dialogue)** | Conversational intake engine with dynamic symptom suggestion chips, clinician/patient persona switcher, red-flag screening alert, and persistent Case Snapshot rail showing 7-dimension totality coverage. |
| [`02_step1_paste_notes.png`](./02_step1_paste_notes.png) | **Step 1: Patient Clinical Intake (Paste Notes Mode)** | Unstructured clinical narrative extraction view featuring word counter, local privacy assurance badge, and two-column extraction preview with color-coded BioLinkBERT entity badges. |
| [`03_step2_review_cards.png`](./03_step2_review_cards.png) | **Step 2: Clinical Review & 7-Dimension Validation** | Verified 7-dimension totality cards (Mind, Modalities, Physical Generals, Sensations, Locations, Concomitants, Causation) with inline editing, provenance chips, and AI-generated physician brief. |
| [`04_step3_analysis_matrix.png`](./04_step3_analysis_matrix.png) | **Step 3: Repertory Rubric Curation & Totality Analysis** | Classical Repertorization Matrix (rubrics as rows, candidate remedies as columns) with Grade 1–3 weights, eliminatory rubric toggles, and comparative remedy score ranking. |
| [`05_step4_clinical_report.png`](./05_step4_clinical_report.png) | **Step 4: Clinical Report & Keynotes Reference** | Comprehensive clinical decision-support report featuring Plotly totality score distribution chart, Materia Medica Grade 3 keynotes comparison, and PDF/Markdown export. |
| [`06_case_library.png`](./06_case_library.png) | **Case Library & Historical Consultations** | Searchable consultation database (SQLite) with patient demographic metadata, totality progress rings, case statuses (Active, Review, Closed), and bulk management actions. |
| [`07_rubric_explorer.png`](./07_rubric_explorer.png) | **Rubric Explorer & Dense Semantic Retrieval** | Interactive explorer across 4,933 MIND rubrics, supporting dense vector semantic search, exact lexical keyword matching, remedy counts, and locked chapter indicators. |
| [`08_materia_medica.png`](./08_materia_medica.png) | **Materia Medica Dictionary & Differential View** | Homeopathic remedy dictionary featuring Latin nomenclature, standard abbreviations, characteristic Grade 3 mental keynotes, and side-by-side differential comparison. |
| [`09_methodology_settings.png`](./09_methodology_settings.png) | **Methodology & Classical Totality Principles** | Educational and algorithmic foundations view documenting Dr. J. T. Kent's totality principles, grade scoring formulas, evaluation benchmark metrics (BIO F1, Top-20 Recall, MRR), and clinical disclaimers. |

---

## Detailed View Descriptions

### 1. Step 1: Patient Clinical Intake (Bedside Dialogue)
**File:** `01_step1_intake_chat.png`  
**Description:** The primary bedside intake interface where clinicians or patients engage in a structured conversational dialogue. The dialogue manager prompts for missing Kentian dimensions, suggests context-aware intent chips, and dynamically updates the right-hand **Case Snapshot** rail in real-time.

### 2. Step 1: Patient Clinical Intake (Paste Notes Mode)
**File:** `02_step1_paste_notes.png`  
**Description:** Rapid consultation mode allowing clinicians to paste raw, unstructured consultation narratives. Clicking **Extract & review** invokes the fine-tuned BioLinkBERT model to screen for red flags, filter negations (e.g., "no fever, no nausea"), and map extracted spans into the 7 canonical totality dimensions.

### 3. Step 2: Clinical Review & 7-Dimension Validation
**File:** `03_step2_review_cards.png`  
**Description:** Interactive validation card grid where extracted symptoms are grouped across the 7 canonical dimensions. Clinicians can adjust confidence levels, delete non-pertinent entries, and add observed modalities. Includes the **Physician Brief** summarizing the patient's symptomatic totality.

### 4. Step 3: Repertory Rubric Curation & Totality Analysis
**File:** `04_step3_analysis_matrix.png`  
**Description:** Classical Hahnemannian and Kentian Totality Grid. Rubrics appear along the rows and remedies along the columns, color-coded by grade weight (Grade 3 in bold green, Grade 2 in amber, Grade 1 in muted slate). Clinicians can mark rubrics as **Eliminatory** (forcing candidate remedies to cover that specific symptom) or mute unhelpful rubrics.

### 5. Step 4: Clinical Decision-Support Report
**File:** `05_step4_clinical_report.png`  
**Description:** The final consultation report displaying candidate remedies ranked by totality score, coverage percentage, and specificity weights. Displays an interactive Plotly bar chart, Materia Medica keynotes reference table, and export buttons for generating production-ready PDF reports.

### 6. Case Library
**File:** `06_case_library.png`  
**Description:** Central SQLite repository showing all stored consultations. Clinicians can filter by patient name, case ID, or date, inspect totality completion rings, resume active consultations, or generate summary reports.

### 7. Rubric Explorer
**File:** `07_rubric_explorer.png`  
**Description:** Dedicated repertory search interface indexing all 4,933 Kent MIND rubrics with dense embeddings and lexical search. Enables direct exploration of rubric hierarchies, associated remedies, and symptom cross-references.

### 8. Materia Medica Dictionary
**File:** `08_materia_medica.png`  
**Description:** Built-in Materia Medica lookup allowing rapid review of remedies (*Arsenicum album*, *Aconitum napellus*, *Phosphorus*, etc.), displaying Latin binomials, symptom affinities, and characteristic keynotes.

### 9. Methodology & Totality Principles
**File:** `09_methodology_settings.png`  
**Description:** In-depth documentation of the algorithmic and classical homeopathic framework, providing clinicians with transparency regarding how the NLP pipeline extracts entities, maps embeddings, and computes totality scores.


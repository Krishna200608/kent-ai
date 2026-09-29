# Kent-AI: Master Glossary of Full Forms, Acronyms & Domain Jargon

**Project Title**: Kent-AI: An AI-Powered Conversational Clinical Assistant for Homeopathic Case-Taking and Dense Semantic Repertorization  
**Institution**: Indian Institute of Information Technology, Allahabad (IIIT-A)  
**Evaluation Milestone**: B.Tech IT Seventh Semester — Mid-Semester Evaluation  
**Related Documents**: [Presentation Deck (`Kent-AI Midsem.pdf`)](file:///d:/Research%20Project/kent-ai/docs/Evaluation/Mid_Sem/Kent-AI%20Midsem.pdf) | [Presentation Script (`Mid-sem-ppt-content.md`)](file:///d:/Research%20Project/kent-ai/docs/Evaluation/Mid_Sem/Mid-sem-ppt-content.md) | [Speaker Notes (`Speaker_Notes.md`)](file:///d:/Research%20Project/kent-ai/docs/Evaluation/Mid_Sem/Speaker_Notes.md) | [Thesis Report (`MidSem-Report/`)](file:///d:/Research%20Project/kent-ai/docs/Evaluation/Mid_Sem/MidSem-Report)

---

## Table of Contents
1. [Homeopathic & Clinical Medical Terminology](#1-homeopathic--clinical-medical-terminology)
2. [7 Symptom Dimensions & Token Sequence Tagging (HomeoNER)](#2-7-symptom-dimensions--token-sequence-tagging-homeoner)
3. [AI, NLP & Software Engineering Architecture](#3-ai-nlp--software-engineering-architecture)
4. [Mathematical Formulations, Metrics & Statistical Symbols](#4-mathematical-formulations-metrics--statistical-symbols)
5. [Key Software Frameworks, Models & Infrastructure](#5-key-software-frameworks-models--infrastructure)
6. [Alphabetical Quick-Lookup Index for Viva & Oral Exam](#6-alphabetical-quick-lookup-index-for-viva--oral-exam)

---

## 1. Homeopathic & Clinical Medical Terminology

| Acronym / Term | Full Form / Latin Origin | Classical Definition & Role in Kent-AI |
|---|---|---|
| **Simillimum** | *Simillimum* (Latin: "The most similar") | The single indicated homeopathic remedy that most closely matches the complete physical, mental, and modal symptom totality of the patient. The primary goal of Kent-AI is to compute totality scores across candidate remedies to present the top simillimum options to the physician. |
| **Repertorization** | Repertorial Analysis / Totality Synthesis | The systematic, mathematical process of converting patient complaints into rubrics, aggregating remedy proving weights, and ranking candidate remedies. Kent-AI automates this in $<15$ ms using relational SQL joins. |
| **Rubric** | Repertorial Rubric (Standard Heading) | A standardized medical symptom taxonomy entry in a repertory (e.g., `HEAD > PAIN > stooping, from`) under which remedies are listed with proving grades. Kent-AI indexes all **74,513 rubrics** across Kent's Repertory. |
| **Proving** | Pathogenetic Trial (Human Drug Proving) | Systematic clinical trial where potentized substances are administered to healthy human volunteers to record all physical, emotional, and cognitive symptoms elicited, forming the empirical foundation of the Materia Medica. |
| **Prover** | Human Drug Proving Volunteer | A healthy human participant in a homeopathic proving trial who meticulously records all subjective and objective alterations. |
| **Polycrest** | Polychrest Remedy (Greek: *polychrestos* = "useful for many") | Broad-acting constitutional remedies with extensive proving histories that appear under thousands of rubrics (e.g., *Sulphur, Lycopodium, Calcarea carb, Arsenicum*). Kent-AI's Inverse Remedy Frequency (IRF) metric penalizes polycrests to prevent them from overpowering specific remedies. |
| **Keynote** | Characteristic Keynote Symptom | A striking, singular, or idiosyncratic symptom that uniquely differentiates a remedy from all others. Kent-AI provides a dedicated Materia Medica Keynote reverse lookup tab in the clinician dashboard. |
| **Modality** | Modifying Factors (Aggravation / Amelioration) | Environmental, postural, thermal, temporal, or psychological conditions that worsen (**Aggravation / `MOD_AGG`**) or relieve (**Amelioration / `MOD_AMEL`**) a symptom (e.g., *worse from direct sunlight*, *better hard pressure*). |
| **Concomitant** | Concomitant Symptom (`CONC`) | An accompanying symptom occurring simultaneously alongside the chief complaint without a direct physiological or pathological relationship (e.g., nausea accompanying a temporal migraine). |
| **Materia Medica** | Materia Medica (Latin: "Medical Materials") | Encyclopedic pharmaceutical literature compiling verified proving records, toxicological data, and clinical cured cases for all 679 homeopathic remedies. |
| **Repertory** | Clinical Symptom Index | An inverted taxonomy arranging symptoms anatomically and psychologically, referencing every remedy confirmed to treat each symptom. Kent-AI digitizes Dr. James Tyler Kent's 1897 Repertory. |
| **3-Tier Grading** | Kent's Typographic Proving Hierarchy | Kent's clinical confidence scale: **Grade 3** (Bold Capitals, weight 3.0, verified across multiple provers and clinical cures), **Grade 2** (Italics, weight 2.0, confirmed in multiple provers), **Grade 1** (Plain Roman, weight 1.0, solitary proving or occasional clinical cure). |
| **Law of Similars** | *Similia Similibus Curentur* | Fundamental homeopathic axiom: "Let like be cured by like"—a substance that causes symptoms in healthy humans cures similar symptoms in diseased patients. |
| **AYUSH** | Ministry of Ayurveda, Yoga & Naturopathy, Unani, Siddha, and Homoeopathy | Ministry in the Government of India overseeing indigenous and complementary medical education, research, and healthcare delivery. |
| **PHC / OPD** | Primary Health Centre / Outpatient Department | High-volume public healthcare facilities where physician consultation time is constrained (8–12 patients/day), targeted by Kent-AI's $<10$-minute consultation reduction. |
| **CAM** | Complementary and Alternative Medicine | Broad healthcare domain encompassing homeopathy, traditional Indian systems, and integrative health approaches. |
| **OSCE** | Objective Structured Clinical Examination | Standardized global examination testing clinician diagnostic, history-taking, and communication competency (used in the Google AMIE 2024 trials). |
| **HOHM** | HOHM Foundation | Research foundation that authored the landmark April 2026 MDPI *Healthcare* study evaluating ChatGPT-4, Claude 3, Copilot, and Gemini across 100 acute clinical cases (proving only 36.5% agreement and severe stochastic instability). |

---

## 2. 7 Symptom Dimensions & Token Sequence Tagging (HomeoNER)

| Acronym / Tag | Dimension / Concept | Clinical Meaning & Example Span |
|---|---|---|
| **7D** | Seven Symptom Dimensions | The 7 core clinical axes required in classical Kentian homeopathy for complete case individualization. |
| **`LOC`** | Location | Anatomical site, laterality, and radiation of complaint (e.g., *"right temple"*, *"occiput"*, *"above right eye"*). |
| **`SEN`** | Sensation | Subjective character of pain or sensory pathology (e.g., *"throbbing"*, *"bursting"*, *"as if in a vise"*, *"burning"*). |
| **`MOD_AGG`** | Modality — Aggravation | Triggers, postures, or environmental circumstances worsening the symptom (e.g., *"sun exposure"*, *"stooping"*, *"cold draft"*, *"motion"*). |
| **`MOD_AMEL`** | Modality — Amelioration | Circumstances or actions that relieve the symptom (e.g., *"hard pressure"*, *"dark room"*, *"warm drinks"*, *"rest"*). |
| **`CONC`** | Concomitants | Co-occurring secondary symptoms accompanying the chief complaint (e.g., *"sweating"*, *"visual aura"*, *"nausea"*). |
| **`TEMP`** | Temporal Modality | Diurnal rhythms, periodicity, or onset times (e.g., *"morning"*, *"at 3 AM"*, *"every 7 days"*). |
| **`MENT`** | Mental / Emotional | Psychological traits, disposition, and affective state (e.g., *"anxiety"*, *"fear of being alone"*, *"weeping mood"*, *"grief"*). |
| **BIO Scheme** | Beginning, Inside, Outside Tagging | Standard sequence labeling token format: `B-` marks the first token of an entity span, `I-` marks subsequent tokens, and `O` marks non-entity tokens. |
| **15 BIO Classes** | 15-Class Tagset | $7 \text{ dimensions} \times 2 \ (\text{B-} / \text{I-}) + 1 \ (\text{O}) = 15$ token classification classes trained on `Bio_ClinicalBERT`. |
| **Offset Drift** | Character Offset Drift | The spatial shift (by $\pm 1$ to $\pm 3$ characters) between LLM-reported JSON indices and raw narrative strings caused by BPE subword tokenization and whitespace. Repaired via Kent-AI's 4-tier ladder. |
| **4-Tier Ladder** | 4-Tier Drift Repair Ladder | Algorithmic cascade in `src/data/bio_tagger.py`: **Tier 1** (Exact Slice) $\to$ **Tier 2** (Local Window $\pm 15$ chars) $\to$ **Tier 3** (Global Substring Search) $\to$ **Tier 4** (Case-Insensitive Word Boundary Regex). Achieved 100% string alignment. |
| **HomeoNER** | Homeopathic Named Entity Recognition Corpus | The synthetic benchmark dataset of ~22,200 clinical patient cases generated across Kent's 4,933 MIND rubrics with verified 15-class BIO alignments. |

---

## 3. AI, NLP & Software Engineering Architecture

| Acronym / Jargon | Full Form / Technical Definition | Role in Kent-AI Architecture |
|---|---|---|
| **FSM** | Finite State Machine | A mathematical model of computation consisting of states, inputs, and transition functions. Kent-AI uses a 10-state FSM (`src/chatbot/state_machine.py`) to govern patient intake dialogue sequentially from Greeting to Done. |
| **TOD / DST** | Task-Oriented Dialogue / Dialogue State Tracking | Conversational framework where an agent elicits specific information slots to achieve a clinical goal. Based on MediTOD (EMNLP 2024). |
| **Slot Tracker** | 7-Dimension Clinical Slot Tracker | An internal state vector $\Phi \in [0, 1]^7$ monitoring fulfillment of the 7 dimensions, dynamically skipping redundant FSM questions when multiple attributes are volunteered spontaneously. |
| **NER** | Named Entity Recognition | Natural language processing subtask that locates and classifies named entities in unstructured text into predefined categories. Executed via `Bio_ClinicalBERT`. |
| **RAG** | Retrieval-Augmented Generation | AI framework combining vector information retrieval with generative LLM prompt injection. Evaluated and rejected for remedy ranking due to arithmetic failures and hallucinations (HomeoCure analysis). |
| **LLM** | Large Language Model | Autoregressive transformer neural network pre-trained on massive text corpora (e.g., Meta LLaMA 3 8B, ChatGPT-4, Claude 3). |
| **BERT** | Bidirectional Encoder Representations from Transformers | Masked language model architecture pre-trained with bidirectional self-attention, ideal for token classification and sequence tagging. |
| **`Bio_ClinicalBERT`** | Domain-Specific Clinical BERT | A 110-million parameter transformer pre-trained on PubMed biomedical abstracts and 2+ million MIMIC-III EHR clinical notes. Backs Kent-AI's 15-class token classification head. |
| **MIMIC-III** | Medical Information Mart for Intensive Care III | Publicly accessible, de-identified clinical critical-care database developed by MIT Lab for Computational Physiology, used to pre-train Bio_ClinicalBERT. |
| **MedNLI** | Medical Natural Language Inference | Gold-standard benchmark testing clinical reasoning and sentence entailment across patient notes. |
| **SBERT / MiniLM** | Sentence-BERT / `all-MiniLM-L6-v2` | A 384-dimensional Siamese bi-encoder mapping sentences into dense semantic vector space. Used to embed all 74,513 Kent rubrics for sub-15 ms cosine search. |
| **HNSW** | Hierarchical Navigable Small World | Fast, approximate nearest neighbor (ANN) graph algorithm providing sub-linear vector retrieval latency. Powers Kent-AI's ChromaDB index. |
| **ChromaDB** | Chroma Vector Database | Persistent, local-first on-disk vector database storing 74,513 unit-normalized 384-dimensional rubric embeddings with zero cloud dependencies. |
| **DAL** | Data Access Layer | Architectural boundary module (`src/data/kent_db.py`, 448 lines) enforcing strict read-only execution (`PRAGMA query_only = ON`) and grade coalescing over SQLite. |
| **FTS5** | Full-Text Search 5 | SQLite virtual table module supporting BM25-based keyword ranking, used as a lexical fallback. |
| **BPE** | Byte-Pair Encoding | Subword tokenization algorithm that iteratively merges frequent character pairs, responsible for character offset counting errors in generative LLM JSON mode. |
| **Jaccard Overlap** | Jaccard Similarity Index | Set similarity metric $J(A, B) = \frac{\|A \cap B\|}{\|A \cup B\|}$ computed across vocabulary bags to measure lexical overlap. Kent-AI achieved 13.10% overlap (86.90% diversity). |
| **AMIE** | Articulate Medical Intelligence Explorer | Google Research & DeepMind conversational diagnostic agent trained via self-play dialogue (Tu et al., *Nature* / arXiv 2024). |
| **MediTOD** | Medical Task-Oriented Dialogue | History-taking clinical dataset with comprehensive attribute annotations presented at EMNLP 2024 (Saley et al.). |
| **Note2Chat** | Note-Guided Dialogue Framework | Clinical reasoning architecture structuring conversational transitions to optimize EHR intake (Chen et al., 2026). |
| **Synthea** | Synthetic Patient Population Simulator | Open-source allopathic synthetic EHR simulator generating realistic patient disease histories without exposing real patient records. |
| **PHI** | Protected Health Information | Individually identifiable health information protected under law. Kent-AI prevents PHI transmission by operating 100% locally on the clinic PC. |
| **HIPAA / DISHA** | Health Insurance Portability and Accountability Act / Digital Information Security in Healthcare Act | US and Indian healthcare data privacy and cybersecurity regulations mandating zero unauthorized cloud transmission of patient medical text. |
| **HUD** | Heads-Up Display | Visual UI telemetry widget in Kent-AI's consultation workspace displaying real-time 7-dimension slot fulfillment progress. |

---

## 4. Mathematical Formulations, Equations & Symbol-by-Symbol Reference (Slide 11)

This section provides an exhaustive symbol-by-symbol breakdown of the four core equations presented in **Slide 11: Formal Mathematical Problem Formulation**.

---

### 4.1 Equation 1: Intake State Transition (Finite State Machine)

$$\mathbf{S_{t+1} = \delta(S_t, u_t, \Phi_t), \quad S_t \in \mathcal{S}_{\text{intake}}, \quad \Phi_t \in [0, 1]^7}$$

* **Plain English Meaning**: Decides which clinical question the conversational agent asks next, based on the current step, the patient's reply, and which of the 7 symptom dimensions have already been answered.

| Symbol | Name / Type | Mathematical & Clinical Role in Kent-AI |
|:---:|---|---|
| **$t$** | Time-step / Turn index | Represents the dialogue turn counter ($t = 0, 1, 2, \dots$). |
| **$S_t$** | Current dialogue state | The active state of the 10-state FSM at turn $t$ (e.g., currently asking for Location). |
| **$S_{t+1}$** | Next dialogue state | The target state the bot transitions to for the next question (e.g., transitioning to Sensation). |
| **$\delta$** | Transition function (*Delta*) | The deterministic state transition logic $\delta: \mathcal{S} \times \mathcal{U} \times \Phi \to \mathcal{S}$ that governs dialogue flow and executes adaptive state-skipping. |
| **$u_t$** | Patient utterance | The raw colloquial text string entered by the patient at turn $t$ (e.g., *"Severe burning pain in my temple"*). |
| **$\Phi_t$** | 7D Slot Tracker vector (*Phi*) | Internal state vector tracking fulfillment across the 7 dimensions: $\Phi_t = [\phi_{\text{LOC}}, \phi_{\text{SEN}}, \phi_{\text{MOD\_AGG}}, \phi_{\text{MOD\_AMEL}}, \phi_{\text{CONC}}, \phi_{\text{TEMP}}, \phi_{\text{MENT}}]^T$. |
| **$\mathcal{S}_{\text{intake}}$** | Intake State Space | The finite set of all 10 conversation states: $\{\text{Greeting}, \text{Chief Complaint}, \text{Location}, \text{Sensation}, \text{Worse From}, \text{Better From}, \text{Associated Symptoms}, \text{Mind \& Mood}, \text{Review}, \text{Done}\}$. |
| **$\in$** | Set membership | Indicates that $S_t$ must be an element of the valid defined state space $\mathcal{S}_{\text{intake}}$. |
| **$[0, 1]^7$** | 7-Dimensional Binary Space | Indicates that each of the 7 slots is either $0$ (unfilled/missing) or $1$ (fulfilled/extracted). If a patient provides multiple attributes at once, multiple flags turn to $1$, allowing $\delta$ to skip redundant questions. |

---

### 4.2 Equation 2: Token-Level Entity Recognition (Bio_ClinicalBERT)

$$\mathbf{\hat{y}_i = \arg\max_{c \in \mathcal{Y}} P(y_i = c \mid \mathbf{x}; \boldsymbol{\theta}^{\text{BERT}}), \quad |\mathcal{Y}| = 15 \text{ BIO Tags}}$$

* **Plain English Meaning**: Predicts the exact clinical entity label for each individual word/token in the patient's sentence using `Bio_ClinicalBERT`.

| Symbol | Name / Type | Mathematical & Clinical Role in Kent-AI |
|:---:|---|---|
| **$i$** | Token index | The positional index of the word or subword token in the patient's sentence ($i = 1, 2, \dots, N$). |
| **$\mathbf{x}$** | Input token sequence | The complete tokenized patient sentence $\mathbf{x} = [x_1, x_2, \dots, x_N]$ fed into the transformer. |
| **$\hat{y}_i$** | Predicted label (*y-hat*) | The final output tag assigned to token $i$ (e.g., $\hat{y}_i = \text{B-SEN}$). The hat ($\hat{}$) denotes an estimated/predicted value. |
| **$\arg\max_{c \in \mathcal{Y}}$** | Argument of the maximum | Mathematical operator that selects the tag $c$ from label set $\mathcal{Y}$ that maximizes the probability score. |
| **$c$** | Candidate class / tag | A single candidate BIO label from the tagset (e.g., `B-LOC`, `I-SEN`, `O`). |
| **$\mathcal{Y}$** | Tagset / Label space | The complete set of 15 possible classification classes. |
| **$|\mathcal{Y}| = 15$** | Set cardinality | Size of the label space: 7 dimensions $\times$ 2 (`B-` / `I-`) $+$ 1 (`O`) $= 15$ tags. |
| **$P(\dots)$** | Conditional probability | The Softmax output probability computed by `Bio_ClinicalBERT` for class $c$ on token $i$. |
| **$y_i$** | True label | The underlying target tag for the $i$-th token. |
| **$\boldsymbol{\theta}^{\text{BERT}}$** | Model parameters (*Theta*) | The 110 million learned weight matrices and bias vectors of fine-tuned `Bio_ClinicalBERT`. |
| **`BIO`** | Tagging scheme | **B-** (Beginning of entity span), **I-** (Inside continuation of entity span), **O** (Outside of any clinical entity). |

---

### 4.3 Equation 3: Dense Semantic Retrieval (ChromaDB Vector Store)

$$\mathbf{\text{Sim}(\mathbf{q}_k, \mathbf{e}_r) = \frac{\mathbf{q}_k \cdot \mathbf{e}_r}{\|\mathbf{q}_k\|_2 \|\mathbf{e}_r\|_2}, \quad r \in \mathcal{R}_{74,513}}$$

* **Plain English Meaning**: Measures the semantic similarity (geometric cosine angle) between the patient's symptom query and all 74,513 Kent repertory rubrics to find the best medical matches in $<15$ milliseconds.

| Symbol | Name / Type | Mathematical & Clinical Role in Kent-AI |
|:---:|---|---|
| **$\text{Sim}(\cdot, \cdot)$** | Cosine similarity function | Computes geometric angular alignment between two high-dimensional dense vectors (normalized dot product, range $[-1, +1]$). |
| **$k$** | Query index | Index of the patient's extracted symptom component ($k = 1, 2, \dots, K$). |
| **$\mathbf{q}_k$** | Query embedding vector | 384-dimensional dense semantic representation of symptom query $k$ generated by `all-MiniLM-L6-v2`. |
| **$r$** | Rubric instance | A specific rubric candidate from Kent's Repertory (e.g., `HEAD > PAIN > sun, from exposure to`). |
| **$\mathbf{e}_r$** | Rubric embedding vector | Pre-computed 384-dimensional dense vector of rubric $r$, stored persistently in ChromaDB's HNSW index. |
| **$\cdot$** | Vector dot product | Inner product: $\mathbf{q}_k \cdot \mathbf{e}_r = \sum_{d=1}^{384} q_{k,d} \cdot e_{r,d}$. |
| **$\|\mathbf{q}_k\|_2$** | $L_2$ Euclidean norm | Length of vector $\mathbf{q}_k$: $\sqrt{\sum_{d=1}^{384} q_{k,d}^2}$. Since vectors are unit-normalized, $\|\mathbf{q}_k\|_2 = 1.0$. |
| **$\|\mathbf{e}_r\|_2$** | $L_2$ Euclidean norm | Length of rubric vector $\mathbf{e}_r$: $\sqrt{\sum_{d=1}^{384} e_{r,d}^2} = 1.0$. (Thus the formula simplifies to $\mathbf{q}_k \cdot \mathbf{e}_r$ for instant computation). |
| **$\mathcal{R}_{74,513}$** | Total Rubric Taxonomy | The full digitized repository of all **74,513 rubrics** spanning all 37 anatomical chapters of Kent's Repertory. |
| **$r \in \mathcal{R}_{74,513}$** | Rubric space membership | Formally specifies that candidate rubric $r$ is searched across the complete 74,513-rubric index. |

---

### 4.4 Equation 4: Kentian Totality Scoring (Repertorization Ranker)

$$\mathbf{\text{Score}(m \mid \mathcal{R}^*) = \sum_{r \in \mathcal{R}^*} \mathbb{I}(m \in \mathcal{M}_r) \cdot w(g_{r,m}) \cdot \text{IRF}(r) \cdot \text{Sim}(q_r, r)}$$

* **Plain English Meaning**: Calculates the final holistic prescription score for each candidate remedy by multiplying historical database presence ($\mathbb{I}$), clinical proving grade ($w=3, 2, 1$), rubric specificity ($\text{IRF}$), and semantic retrieval confidence ($\text{Sim}$), then summing across all patient rubrics.

| Symbol | Name / Type | Mathematical & Clinical Role in Kent-AI |
|:---:|---|---|
| **$m$** | Candidate remedy | A specific homeopathic remedy being evaluated (e.g., *Belladonna, Glonoinum, Bryonia* from the 679 remedies in the database). |
| **$\mathcal{R}^*$** | Matched rubric set | The subset of candidate rubrics retrieved by vector search that passed the confidence threshold ($\text{Sim} \ge 0.52$). |
| **$\text{Score}(m \mid \mathcal{R}^*)$** | Remedy Totality Score | The final aggregated ranking score for remedy $m$ conditioned on the patient's rubric set $\mathcal{R}^*$. Highest score = primary Simillimum recommendation. |
| **$\sum_{r \in \mathcal{R}^*}$** | Summation operator | Sums the individual weighted score contributions across all matched rubrics $r$. |
| **$\mathbb{I}(\dots)$** | Indicator Function | Binary filter ensuring **zero hallucinations**: $\mathbb{I}(m \in \mathcal{M}_r) = 1$ if remedy $m$ is verified in Kent's database for rubric $r$; otherwise $0$. If a remedy is not in the database, its contribution is strictly zero. |
| **$\mathcal{M}_r$** | Rubric remedy set | The set of all remedies historically confirmed to treat rubric $r$ in Kent's Repertory. |
| **$g_{r,m}$** | Proving grade | The classical typographic proving grade assigned to remedy $m$ under rubric $r$ in Kent's 1897 Repertory. |
| **$w(g_{r,m})$** | Proving weight multiplier | Discrete weight function mapping Kent's proving hierarchy: **3.0** for Grade 3 (Bold Capitals), **2.0** for Grade 2 (Italics), **1.0** for Grade 1 (Plain Roman). |
| **$\text{IRF}(r)$** | Inverse Remedy Frequency | Specificity penalty metric: $\text{IRF}(r) = \ln\left(1 + \frac{|\mathcal{M}_{\text{total}}|}{|\mathcal{M}_r|}\right)$. Penalizes ubiquitous polycrest remedies (e.g., *Sulphur* in 400+ rubrics) and rewards rare, characteristic keynote rubrics. |
| **$|\mathcal{M}_{\text{total}}|$** | Total remedy count | Total number of distinct remedies in Kent's Repertory ($|\mathcal{M}_{\text{total}}| = 679$). |
| **$|\mathcal{M}_r|$** | Rubric remedy count | Number of remedies documented under rubric $r$. |
| **$\text{Sim}(q_r, r)$** | Retrieval confidence weight | The cosine similarity score from Equation 3, scaling remedy points by how closely the patient's words matched the rubric. |

---

### 4.5 Global Benchmark Evaluation Metrics Reference Table

| Metric / Term | Formula / Definition | Target Threshold | Clinical & Statistical Significance |
|---|---|:---:|---|
| **MRR** | $\frac{1}{\|Q\|}\sum_{i=1}^{\|Q\|} \frac{1}{\text{rank}_i}$ | $\ge 0.65$ | **Mean Reciprocal Rank**: Evaluates the position of the first correct rubric in search results. |
| **Recall@20** | $\frac{\sum_{q} \mathbb{I}(\text{true\_rubric} \in \text{Top20}(q))}{\|Q\|}$ | $\ge 90.0\%$ | **Top-20 Rubric Recall**: Percentage of clinical queries where the true rubric is retrieved within the top 20 candidates. |
| **BIO F1 Score** | $2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$ | $\ge 88.0\%$ | **Harmonic Mean of Precision & Recall**: Strict token-level classification accuracy across all 15 BIO classes. |
| **Schema Validity** | $\frac{\text{Valid JSON Cases}}{\text{Total Cases}}$ | $100.0\%$ | Proportion of synthetic clinical cases passing strict Pydantic parsing without syntax errors (100/100 pilot). |
| **Entropy Seeding** | $\text{Seed} = \text{Seed}_0 + (\text{idx} \times 137)$ | Deterministic | Dynamic pseudo-random seed permutation eliminating LLM repetition while maintaining experimental reproducibility. |
| **Zero-Quota Distortion** | Deficit-Balancing Allocation | 0 empty sets | Mathematical property ensuring small rubric clusters ($k=4$) never yield 0 samples in Validation/Test splits. |

---

## 5. Key Software Frameworks, Models & Infrastructure

| Component / Library | Version / Type | Exact Purpose in Kent-AI Pipeline |
|---|---|---|
| **Ollama** | Local LLM Server | Hosts and serves 4-bit/8-bit quantized `llama3:8b-instruct` on localhost port 11434 with 0 external network requests. |
| **`LLaMA 3 8B`** | Meta Foundation Model | Executes multi-archetype synthetic narrative generation (`case_generator.py`) and contextual negation filtering (`resolver.py`). |
| **ChromaDB** | Vector Database Engine | Manages persistent local SQLite metadata and DuckDB/HNSW vector embeddings under `data/embeddings/kent_rubrics/`. |
| **SQLite 3** | Relational Database Engine | Houses digitized Kent's Repertory (`data/raw/repertory.sqlite`, 112 MB) with strict read-only execution. |
| **Streamlit** | Web Application Framework | Implements doctor-facing portal (`src/dashboard/app.py`) featuring live chat console, slot HUD, and Totality Matrix. |
| **PyTorch (`torch`)** | Deep Learning Framework | Executes forward inference and sequence classification for Bio_ClinicalBERT token tagging. |
| **Hugging Face (`transformers`)** | Transformer Library | Provides tokenizers and model loading utilities for `emilyalsentzer/Bio_ClinicalBERT`. |
| **`sentence-transformers`** | Neural Embedding Framework | Computes 384-dimensional dense semantic representations using `all-MiniLM-L6-v2`. |
| **Pydantic** | Data Validation Library | Enforces strict type schemas for all synthetic case generation JSON objects (`ClinicalCase`, `EntitySpan`). |
| **`pytest`** | Automated Testing Framework | Executes Kent-AI's 60 automated unit and integration tests across 6 phases in 4.05 seconds. |

---

## 6. Alphabetical Quick-Lookup Index for Viva & Oral Exam

* **7D**: Seven Symptom Dimensions (Location, Sensation, Modality Aggravation, Modality Amelioration, Concomitant, Temporal, Mental).
* **AMIE**: Articulate Medical Intelligence Explorer (Google DeepMind diagnostic dialogue agent).
* **AYUSH**: Ministry of Ayurveda, Yoga & Naturopathy, Unani, Siddha, and Homoeopathy.
* **BERT**: Bidirectional Encoder Representations from Transformers.
* **`Bio_ClinicalBERT`**: 110M parameter clinical transformer pre-trained on PubMed and MIMIC-III.
* **BIO Tagging**: Beginning, Inside, Outside sequence labeling scheme (15 classes in Kent-AI).
* **BPE**: Byte-Pair Encoding (subword tokenizer causing character offset drift in LLMs).
* **CAM**: Complementary and Alternative Medicine.
* **ChromaDB**: In-process persistent dense neural vector database.
* **DAL**: Data Access Layer (`src/data/kent_db.py`).
* **DISHA**: Digital Information Security in Healthcare Act (India).
* **DST**: Dialogue State Tracking.
* **FSM**: Finite State Machine (10-state consultation controller).
* **FTS5**: SQLite Full-Text Search 5 virtual table extension.
* **HIPAA**: Health Insurance Portability and Accountability Act.
* **HNSW**: Hierarchical Navigable Small World (approximate nearest neighbor vector index).
* **HOHM**: HOHM Foundation (authors of 2026 MDPI *Healthcare* study showing 36.5% LLM remedy concordance).
* **HomeoNER**: Synthetic gold-standard clinical case corpus (~22,200 cases).
* **HUD**: Heads-Up Display (slot progress tracking widget).
* **IRF**: Inverse Remedy Frequency ($\text{IRF}(r) = \ln(1 + |\mathcal{M}_{\text{total}}| / |\mathcal{M}_r|)$).
* **Jaccard Overlap**: Word-level set similarity metric (Kent-AI achieved 13.10% overlap / 86.90% diversity).
* **Keynote**: A distinctive, idiosyncratic symptom uniquely identifying a remedy.
* **Law of Similars**: *Similia Similibus Curentur* ("Like cures like").
* **LLM**: Large Language Model.
* **`LOC`**: Location symptom dimension.
* **Materia Medica**: Pharmacological encyclopedia documenting proving symptoms for all 679 remedies.
* **MedNLI**: Medical Natural Language Inference benchmark.
* **MediTOD**: Task-oriented medical dialogue dataset (EMNLP 2024).
* **`MENT`**: Mental / Emotional symptom dimension.
* **MIMIC-III**: MIT de-identified ICU electronic health records database.
* **MiniLM**: 384-dimensional bi-encoder embedding model (`all-MiniLM-L6-v2`).
* **`MOD_AGG`**: Modality — Aggravation symptom dimension.
* **`MOD_AMEL`**: Modality — Amelioration symptom dimension.
* **MRR**: Mean Reciprocal Rank (retrieval metric target $\ge 0.65$).
* **NER**: Named Entity Recognition.
* **NLP / NLU**: Natural Language Processing / Natural Language Understanding.
* **Note2Chat**: Note-guided clinical intake framework (2026).
* **OPD**: Outpatient Department.
* **OSCE**: Objective Structured Clinical Examination.
* **PHC**: Primary Health Centre.
* **PHI**: Protected Health Information.
* **Polycrest**: Wide-acting constitutional remedy appearing in thousands of rubrics.
* **Prover**: Healthy volunteer in a homeopathic drug proving trial.
* **Proving**: Systematic trial recording symptoms produced by potentized remedies in healthy humans.
* **RAG**: Retrieval-Augmented Generation.
* **Recall@20**: Proportion of queries with true rubric in top-20 retrieved candidates (target $\ge 90.0\%$).
* **Repertorization**: Systematic mapping of symptoms to rubrics to calculate candidate remedy totality scores.
* **Rubric**: Standardized symptom category in Kent's Repertory (74,513 total rubrics).
* **`SEN`**: Sensation symptom dimension.
* **Simillimum**: The single most indicated curative remedy matching the patient's symptom totality.
* **Slot Tracker**: State vector $\Phi \in [0, 1]^7$ monitoring symptom dimension fulfillment.
* **Synthea**: Open-source synthetic electronic health record population simulator.
* **`TEMP`**: Temporal Modality symptom dimension.
* **TOD**: Task-Oriented Dialogue.
* **$w(g)$**: Typographic proving grade weight (Grade 3 = 3.0, Grade 2 = 2.0, Grade 1 = 1.0).

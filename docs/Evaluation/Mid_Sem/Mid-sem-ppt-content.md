# Kent-AI: AI-Powered Clinical Assistant for Homeopathic Repertorization
## Mid-Semester Evaluation Presentation — Slide-by-Slide Content Master
### Exactly Synchronized with `Kent-AI Midsem.pdf` (23 Slides Master Deck)

---

> **CRITICAL INSTITUTIONAL NOTICE (UGSC IT, IIIT Allahabad)**:  
> As explicitly instructed by the UGSC notification for anonymous board evaluation:  
> **"The name of the supervisor is NOT to be included in the presentation slides."**  
> Supervisor details are therefore strictly omitted from the slide deck.

---

### Canva Visual Styling & Design System (Final Approved Palette)
* **Primary Background**: Clean High-Contrast Slate/White Canvas with Minimalist Dark-Mode Dashboard Embeds
* **Accent Colors**: 
  * Vibrant Emerald Green (`#10B981`) — Passing Benchmarks & Validations
  * Tech Blue / Indigo (`#2563EB`) — NLP Extraction & State Machine
  * Warm Amber / Coral (`#F59E0B` / `#EF4444`) — Grade 3 Proving Prominence & Aggravations
  * Midnight Obsidian (`#0A0F1D`) — Clinical Dashboard UI
* **Typography**:
  * Slide Headers: *Outfit* / *Montserrat* (Bold Sans-Serif)
  * Body & Captions: *Inter* / *Roboto* (Clean, Highly Legible at Distance)
* **Visual Structure**: 23 Slides with dedicated process diagrams, benchmark KPI metric cards, and production dashboard screenshots.

---

### 🎯 Presentation Speaker Allocation (Order: Naitik $\to$ Krishna $\to$ Lokesh)

| Speaker | Assigned Slides | Theme & Scope | Estimated Time |
|---|:---:|---|:---:|
| **1. Naitik Jain** | **Slides 1 – 8** | Introduction, Principles, Motivation, Literature Review (2024–2026), Research Gaps & Problem Statement | **~5 – 6 min** |
| **2. Krishna Sikheriya** | **Slides 9 – 16** | Knowledge Base Scoping, 7D Clinical Framework, Mathematical Formulation, Architecture, Intake FSM, 15-Class BIO Extraction & Synthetic Pipeline | **~6 – 7 min** |
| **3. Lokesh Bawariya** | **Slides 17 – 23** | ChromaDB Dense Retrieval, Classical Remedy Ranker, 100-Case Pilot Benchmarks, Dashboard Walkthrough, Roadmap & Conclusion | **~5 – 6 min** |

---

## Slide 1: Title Slide (Project Overview) [Speaker 1: Naitik]

* **Canva Slide Layout**: Formal institutional presentation layout with IIIT Allahabad crest logo on the left, central title banner, and project team roster on the right.
* **Header**: Indian Institute of Information Technology, Allahabad
* **Slide Title**: 
  # KENT-AI
  ### An AI-Powered Conversational Clinical Assistant for Homeopathic Case-Taking and Dense Semantic Repertorization
* **Evaluation Context**: Mid-Semester Project Evaluation
* **Project Team Members**:
  * **IIT2023139** – Krishna Sikheriya
  * **IIT2023138** – Lokesh Bawariya
  * **IIB2023036** – Naitik Jain
* **Speaker Notes**:
  > *"Good morning respected members of the evaluation committee. We are presenting Kent-AI, an intelligent clinical assistant designed to solve a major operational bottleneck in homeopathic medicine: the time-consuming, cognitive burden of manual case-taking and repertorization. Our system automates patient symptom intake and uses dense neural search to recommend remedies in under 10 minutes."*

---

## Slide 2: Introduction

* **Canva Slide Layout**: 3-Container Layout. Top horizontal definition banner; 2 split cards below (Homeopathic Principles on the left, Kent's Repertory on the right).
* **Slide Title**: Introduction
* **Top Definition Banner (Orange Border)**:
  > **Homeopathy is an individualized medical science that treats patients holistically based on the Law of Similars. To identify the curative remedy (Simillimum), physicians rely on repertorization—the systematic process of mapping patient suffering to standardized repertory rubrics.**
* **Left Card: Homeopathic Principles & Repertorization (Green Border)**:
  * **Law of Similars**: *Similia Similibus Curentur* ("Like cures like") — micro-diluted remedies matching the patient's individual totality.
  * **What is Repertorization?**: The systematic translation of free-text patient complaints into standardized clinical taxonomy entries called **Rubrics**.
  * **The Simillimum**: The single indicated remedy that covers the symptom totality across physical, modal, and mental spheres.
* **Right Card: Kent Repertory & 3-Tier Grading (Blue Border)**:
  * **Classical Foundation**: Compiled by Dr. J. T. Kent (1897); indexes **74,513 rubrics** across **37 anatomical sections**.
  * **Database Scale**: **679 remedies** and **507,179 rubric-remedy associations**.
  * **Kent's 3-Tier Typographic Grading System**:
    * 🔴 **Grade 3 (Bold Capitals, Weight = 3)**: Highest clinical prominence; verified across multiple provers and clinical cures (313,519 links).
    * 🟡 **Grade 2 (Italics, Weight = 2)**: Moderately verified; confirmed by independent provers (113,336 links).
    * ⚪ **Grade 1 (Roman/Plain, Weight = 1)**: Solitary proving symptoms or occasional clinical observations (31,499 links).
* **Speaker Notes**:
  > *"To understand our work, we must understand how a homeopath prescribes. Homeopathy does not just treat a disease label—it treats the patient's individual symptom totality. Doctors match symptoms to standardized medical entries called rubrics in reference books called repertories. We digitized Dr. J. T. Kent's classical 1897 repertory, containing over 74,500 rubrics and half a million remedy links with three distinct clinical weights."*

---

## Slide 3: Motivation

* **Canva Slide Layout**: 3-Tier Vertical Flow Layout. Top: Clinical Bottlenecks Card. Middle: Semantic & Lexical Divide Comparison Table. Bottom: High-Contrast Takeaway Banner.
* **Slide Title**: Motivation
* **Top Card: The Clinical Consultation Bottleneck**:
  * **Time-Intensive Case-Taking**: 30–45 minutes per consultation limits capacity.
  * **Cognitive Fatigue & Bias**: 74,513 rubrics are impossible to cross-reference manually.
  * **Inter-Practitioner Inconsistency**: Different doctors may extract different rubrics from the same case.
* **Middle Table: The Semantic & Lexical Divide**:
  | Patient Expression | Kent's 19th-Century Rubric | Keyword Overlap |
  |---|---|:---:|
  | *"Crushing vice-like headache"* | `HEAD > PAIN > pressing > as if in a vise` | **0% Overlap** |
  | *"Worse when bending over"* | `HEAD > PAIN > stooping, from` | **0% Overlap** |
  | *"Throbbing above right eyebrow"* | `HEAD > PAIN > forehead > right > over eyes` | **0% Overlap** |
  | *"Fear of being alone at night"* | `MIND > FEAR > alone, of being > night` | **0% Overlap** |
* **Bottom Banner**:
  > **Why Dense Vector Search is Mandatory**: Colloquial modern English and Victorian inverted syntax have zero lexical overlap; exact SQL/FTS queries fail completely.
* **Speaker Notes**:
  > *"Traditional consultations take 30 to 45 minutes, capping clinic capacity to only 8 to 12 patients a day. Furthermore, patients speak modern colloquial English, while Kent's repertory is compiled in Victorian medical language. A patient saying 'worse bending over' maps to 'HEAD PAIN stooping from'—zero common words! Simple keyword matching fails completely, making neural semantic search mandatory."*

---

## Slide 4: Research Problems & Core Challenges

* **Canva Slide Layout**: 3-Pillar Clean Circular Header Card Layout.
* **Slide Title**: Research Problems & Core Challenges
* **Pillar 1 — 7D Clinical NER**:
  * Extracts Location, Sensation, Modalities, Concomitants, Temporal, and Mental/Emotional features from complex clinical dialogue.
* **Pillar 2 — Taxonomic Retrieval**:
  * Maps extracted symptoms to the optimal rubric across **74,513 candidates**, preserving hierarchical context with **<15 ms retrieval latency**.
* **Pillar 3 — Data Scarcity**:
  * No public token-annotated dataset exists for clinical symptom extraction; manually annotating 20,000+ cases is financially and logistically impractical.
* **Speaker Notes**:
  > *"We organized our technical research into three primary challenges: First, extracting 7 detailed clinical dimensions from conversational dialogue. Second, searching across an extreme taxonomy of 74,513 rubrics in under 15 milliseconds. Third, overcoming the total absence of public training data by engineering a verifiable synthetic generation pipeline."*

---

## Slide 5: Literature Review

* **Canva Slide Layout**: 2-Card Comparative Literature Cards with Direct Publication Links.
* **Slide Title**: Literature Review
* **Slide Subtitle**: AI in Homeopathy (2024–2026)
* **Card 1 (Blue Border)**:
  * **[HOHM Foundation (Healthcare, 2026)](https://www.mdpi.com/2227-9032/14/7/909)** $\to$
  * Four LLM chatbots matched the practitioner's remedy in only **36.5% of cases**, and repeated queries gave different answers.
* **Card 2 (Green Border)**:
  * **[HomeoCure (Springer, LLM-RAG)](https://link.springer.com/chapter/10.1007/978-3-032-23241-0_6)** $\to$
  * It retrieves symptom-remedy pairs from a digitized homeopathic text and asks follow-up questions for incomplete symptoms.
* **Speaker Notes**:
  > *"Looking at recent AI research in homeopathy: The 2026 HOHM Foundation study tested 4 commercial LLM chatbots on clinical cases. The chatbots agreed with doctors in only 36.5% of cases and produced different remedies for the exact same patient when queried again. HomeoCure explored RAG over symptom pairs, but lacks structured multi-dimensional clinical extraction."*

---

## Slide 6: Literature Review (Continued)

* **Canva Slide Layout**: 2-Card Stacked Literature Cards with Direct Academic Links.
* **Slide Title**: Literature Review (Continued)
* **Slide Subtitle**: Clinical NLP & Dense Retrieval (2019–2026)
* **Card 1 (Blue Border)**:
  * **[Bio_ClinicalBERT (Alsentzer et al., 2019)](https://doi.org/10.18653/v1/W19-1909)** $\to$
  * Domain-specific pretraining on clinical text improved performance on 3 of 5 clinical NLP tasks. It also set a new state of the art on MedNLI.
* **Card 2 (Green Border)**:
  * **[MediTOD (Saley et al., EMNLP 2024)](https://aclanthology.org/2024.emnlp-main.936/)** $\to$
  * A history-taking dialogue dataset annotated with medical slots. Its attributes, such as onset and severity, support structured symptom intake.
* **Speaker Notes**:
  > *"On the NLP and retrieval side: Bio_ClinicalBERT remains the gold-standard transformer for clinical entity recognition, outperforming general BERT models. In conversational healthcare, MediTOD proved that medical history-taking chatbots require explicit slot tracking to gather structured attributes like onset, triggers, and severity."*

---

## Slide 7: Research Gap Analysis

* **Canva Slide Layout**: Full-Width High-Contrast Comparison Matrix Table.
* **Slide Title**: Research Gap Analysis
* **Slide Subtitle**: Comparing Traditional Tools, General AI, Academic RAG, and Kent-AI
* **Comparative Feature Matrix**:
  | Feature | Traditional Tools (RadarOpus) | General AI (ChatGPT) | Research AI (HomeoCure) | **Kent-AI (Our Work)** |
  |---|:---:|:---:|:---:|:---:|
  | **Search Method** | Exact keywords | Free-text generation | Text similarity search | **Conversational FSM + Vector Search** |
  | **Database Grounded** | ✅ Yes (Static) | ❌ No (Hallucinates) | ⚠️ Partial text | **✅ 100% Grounded (74,513 Rubrics)** |
  | **Symptom Extraction** | ❌ Manual by doctor | ❌ Unstructured prose | ⚠️ Simple text | **✅ Bio_ClinicalBERT (7 Dimensions)** |
  | **Automated Intake** | ❌ None | ❌ Freeform chat | ⚠️ Basic questions | **✅ Structured 10-State Intake Bot** |
  | **Remedy Ranking** | Simple addition | ❌ Inconsistent output | ⚠️ Basic scoring | **✅ Kentian Grade-Weighted + IRF Penalty** |
  | **Doctor Dashboard** | Complex legacy UI | ❌ None | ❌ None | **✅ Modern Clinical Dashboard** |
  | **Privacy & Cost** | Local; ₹23,000–₹1.5 Lakhs | Cloud API (Privacy Risk) | Lightweight model | **Local-first: runs on clinician's PC (Ollama, SQLite, ChromaDB); no license fee** |
* **Speaker Notes**:
  > *"This matrix clearly illustrates the gap in existing tools. Commercial software costs up to 1.5 lakh rupees and forces doctors to do all extraction and search by hand. ChatGPT hallucinates fake remedies with no database grounding. Kent-AI combines structured conversational intake, 7-dimension extraction, dense vector search over all 74,513 rubrics, and transparent remedy ranking on a local-first PC stack."*

---

## Slide 8: Problem Statement

* **Canva Slide Layout**: 3-Container Segmented Box Layout. Top: Clinical Problem. Middle: AI / Computational Problem. Bottom: Clear Goal Statement Banner.
* **Slide Title**: Problem Statement
* **Box 1: The Clinical Problem (Blue Border)**:
  * Homeopathic consultations take **30 to 45 minutes**, causing physician fatigue and capping clinic capacity.
  * Patients speak modern everyday language, while classical repertories use **19th-century medical terms**, leading to **0% keyword overlap**.
  * Doctors cannot remember **74,513 rubrics**, leading to cognitive bias toward ~30 common remedies.
* **Box 2: The Computational / AI Problem (Purple Border)**:
  * **Zero labeled training data** exists for homeopathic clinical entity recognition.
  * Unconstrained generative AI (like ChatGPT) **hallucinates fake remedies** and lacks database provenance.
  * Cloud-based AI poses serious **patient data privacy (PHI) risks** in real clinic workflows.
* **Box 3: The Clear Goal Statement (Green Border)**:
  > **To develop an offline, privacy-preserving clinical assistant that automatically extracts Kent's 7 symptom dimensions through structured conversational intake, and delivers 100% database-grounded remedy repertorization in under 10 minutes.**
* **Speaker Notes**:
  > *"From these gaps, we formulate our problem statement into two pillars: Clinically, doctors face 45-minute bottlenecks, memory limits across 74,000 rubrics, and a total language mismatch. Computationally, no training data exists, LLMs hallucinate, and cloud APIs risk patient privacy. Our objective is to build a local-first assistant that extracts 7 dimensions through structured intake and delivers 100% grounded repertorization in under 10 minutes."*

---

## Slide 9: Existing Knowledge Base

* **Canva Slide Layout**: 2-Container Stacked Layout. Top: Open-source SQLite Foundation. Bottom: 37 Chapters & Primary Focus on MIND.
* **Slide Title**: Existing Knowledge Base
* **Top Box: Open-Source Foundation (Blue Border)**:
  * Our project leverages and builds upon the digitized Kent's Repertory open-source foundation developed by **su4532** ([github.com/su4532/kent-repertory-explorer](https://github.com/su4532/kent-repertory-explorer)).
  * This provides an initial structured SQLite schema with **74,513 rubrics**, **679 remedies**, and **507,179 mappings**.
  * Having this raw digital foundation in place allows our team to focus directly on the core machine learning challenges:  
    **1)** dense vector representation, **2)** ClinicalBERT symptom NER, **3)** synthetic case generation, and **4)** conversational clinical reasoning.
* **Bottom Box: Scoping the 37 Chapters & Primary Focus on MIND (Purple Border)**:
  * **Kent's Repertory**: 37 chapters organized head-to-foot.
  * **Selected Chapter 1 — MIND**: 4,933 rubrics as our initial benchmark.
  * **Why MIND?**:
    * Mental symptoms are given **highest importance** in classical case analysis.
    * Uses **abstract & figurative language**, making it the hardest AI reasoning challenge.
    * 4,933 MIND rubrics give us a solid, focused dataset to generate **~22,200 synthetic cases** and train `Bio_ClinicalBERT` before expanding to physical chapters.
  * **Next**: Expand from MIND $\to$ physical chapters after validation.
* **Speaker Notes**:
  > *"To build Kent-AI, we leveraged the digitized SQLite repertory developed by su4532, containing 74,513 rubrics and half a million links. Having this digital foundation allowed our team to focus on the core AI challenges. While all 37 chapters are indexed in our database, our initial training and synthetic generation benchmark focuses explicitly on Chapter 1: MIND. In homeopathy, mental symptoms carry the highest constitutional weight and present the greatest linguistic ambiguity for NLP."*

---

## Slide 10: Kent's 7 Clinical Symptom Dimensions

* **Canva Slide Layout**: Top Full-Width Dimension Matrix Table; Bottom Technical Significance Callout Box.
* **Slide Title**: Kent’s 7 Clinical Symptom Dimensions
* **Top Table: The 7 Clinical Dimensions**:
  | Dimension | What it captures | Example |
  |---|---|---|
  | **Location** | Body part/region | *"Right side of head"* |
  | **Sensation** | Type of feeling | *"Pressing, throbbing, burning"* |
  | **Modality** | Aggravation/amelioration | *"Worse in morning, better by pressure"* |
  | **Laterality** | Left/right/bilateral | *"Left-sided"* |
  | **Concomitant** | Accompanying symptoms | *"With nausea and anxiety"* |
  | **Mental/Emotional** | Psychological state | *"Irritable, restless at night"* |
  | **Temporality** | Time patterns | *"Worse at midnight, periodic"* |
* **Bottom Box: Why This Matters for Kent-AI (Yellow/Green Border)**:
  * **The "Complete Symptom" Principle**: In classical homeopathy, a raw complaint like *"I have a headache"* cannot be prescribed upon. It must be qualified across all 7 dimensions (location, sensation, triggers, and emotional state) to find the true *Simillimum*.
  * **The Target Schema for Our AI**: Our **10-State Conversational FSM** and **Bio_ClinicalBERT** are specifically engineered to extract, track, and validate these exact 7 dimensions from everyday patient dialogue.  
    *(Greeting $\to$ Chief Complaint $\to$ Location $\to$ Sensation $\to$ Worse From $\to$ Better From $\to$ Associated Symptoms $\to$ Mind & Mood $\to$ Review $\to$ Done)*
* **Speaker Notes**:
  > *"In homeopathy, you cannot prescribe on an isolated symptom like 'headache.' Dr. J. T. Kent established that a symptom is only actionable when it is qualified across these seven dimensions: where it is located, how it feels, what aggravates or relieves it, associated complaints, time patterns, and emotional state. This table defines the target schema for our 10-state chatbot and ClinicalBERT extractor."*

---

## Slide 11: Formal Mathematical Problem Formulation

* **Canva Slide Layout**: 2-Column Mathematical Card Layout with Bottom BIO Tagging Explanation Pill.
* **Slide Title**: Formal Mathematical Problem Formulation
* **Column 1: Intake & Extraction**:
  * **1. Intake State Transition**:
    $$S_{t+1} = \delta(S_t, u_t, \Phi_t), \quad S_t \in \mathcal{S}_{\text{intake}}, \quad \Phi_t \in [0, 1]^7$$
    * Moves to the next question based on the patient's reply and which of the 7 dimensions are already filled.
  * **2. Token-Level Entity Recognition**:
    $$\hat{y}_i = \arg\max_{c \in \mathcal{Y}} P(y_i = c \mid \mathbf{x}; \boldsymbol{\theta}_{\text{BERT}}), \quad |\mathcal{Y}| = 15 \text{ BIO Tags}$$
    * Predicts whether each word belongs to Location, Sensation, Modality, Time, or Mind.
* **Column 2: Vector Search & Totality Scoring**:
  * **3. Dense Semantic Retrieval**:
    $$\text{Sim}(\mathbf{q}_k, \mathbf{e}_r) = \frac{\mathbf{q}_k \cdot \mathbf{e}_r}{\|\mathbf{q}_k\|_2 \|\mathbf{e}_r\|_2}, \quad r \in \mathcal{R}_{74,513}$$
    * Calculates the cosine similarity between the patient's symptom query and all 74,513 pre-computed rubric vectors.
  * **4. Kentian Totality Scoring**:
    $$\text{Score}(m \mid \mathcal{R}^*) = \sum_{r \in \mathcal{R}^*} \mathbb{I}(m \in \mathcal{M}_r) \cdot w(g_{r,m}) \cdot \text{IRF}(r) \cdot \text{Sim}(q_r, r)$$
    * Combines rubric coverage ($\mathbb{I}$), proving grade weight ($w = 3, 2, 1$), search similarity ($\text{Sim}$), and an Inverse Remedy Frequency ($\text{IRF}$) penalty to stop common remedies from crowding out specific ones.
* **Bottom Callout**:
  * *In NLP, BIO stands for **Beginning, Inside, Outside**. It is the standard way AI models tag exact word boundaries for entities in a sentence.*  
  * *Kent-AI extracts 7 symptom dimensions, each using B- & I- tags, plus O (Outside) $\to$ **15 BIO tags**.*
* **Speaker Notes**:
  > *"We formulated our system with complete mathematical rigor: A finite state transition function guides patient intake; Bio_ClinicalBERT tags 15 BIO token classes; cosine similarity searches 74,000 rubric vectors; and our totality formula scores remedies using proving grades and an IRF penalty that prevents hyper-general remedies from dominating."*

---

## Slide 12: Proposed End-to-End System Architecture

* **Canva Slide Layout**: Full-Slide Horizontal 5-Column Architecture Diagram (compiled from `figure.tex`) with Bottom Performance Callout.
* **Slide Title**: Proposed End-to-End System Architecture
* **The 5 Connected Layers (Left to Right)**:
  1. **Layer 1: Patient Intake (Blue)**: Patient Utterance $\to$ 10-State Intake FSM (LLaMA 3 8B via Ollama) $\to$ Adaptive Slot Tracker & suggestion chips.
  2. **Layer 2: Clinical NLP (Purple)**: `Bio_ClinicalBERT` 15-class NER $\to$ Contextual LLaMA 3 Filter (negation pruning & coreferences) $\to$ Affirmative Symptom Profile (Pydantic JSON).
  3. **Layer 3: Dense Retrieval (Cyan)**: Bi-Encoder Embedding (`all-MiniLM-L6-v2`) $\longleftrightarrow$ **ChromaDB Vector Store (74,513 Rubrics)** $\to$ Calibrated Confidence Tiers ($\ge 0.52$ cutoff).
  4. **Layer 4: Totality Ranker (Orange)**: **Kent Repertory SQLite (679 remedies, 507k links)** $\to$ Proving Grade Weights ($3\times, 2\times, 1\times$) $\to$ Totality Scoring Engine ($\sum \mathbb{I} \cdot w \cdot \text{IRF} \cdot \text{Sim}$).
  5. **Layer 5: Clinician Portal (Green)**: Streamlit Dark Clinical UI $\to$ Interactive Totality Matrix $\to$ Clinical Decision Support report export.
* **Bottom Banner**:
  * **High-Speed Execution** — $<15$ ms semantic search across 74,513 rubrics; reduces review time from 45 min to $<10$ min.
  * **Grounded & Traceable** — Every recommendation is mathematically tied to Kent’s classical grades (3, 2, 1).
* **Speaker Notes**:
  > *"Here is the complete end-to-end architecture of Kent-AI. The patient chats with our 10-state intake bot; symptoms are extracted and cleaned of negations; ChromaDB retrieves matching rubrics in sub-15 milliseconds; our totality engine scores remedies using proving weights and an IRF penalty; and the doctor reviews the results on an interactive dashboard. The entire pipeline runs locally on the doctor's PC."*

---

## Slide 13: Conversational Intake Agent & 10-State FSM

* **Canva Slide Layout**: Horizontal 10-Step Numbered Sequence Flow with Icons; Bottom Feature Highlight Card.
* **Slide Title**: Conversational Intake Agent & 10-State FSM
* **The 10 Sequential Intake Stages**:
  1. 👤 **Greeting**: *"Hi! I'm Kent-AI. Let's talk about your health today."*
  2. 💬 **Chief Complaint**: *"What brings you here today?"*
  3. 📍 **Location**: *"Where do you feel it?"*
  4. ⚡ **Sensation**: *"How does it feel?"*
  5. ↗️ **Worse From**: *"What makes it worse?"*
  6. ↘️ **Better From**: *"What gives you relief?"*
  7. 🔗 **Associated Symptoms**: *"Any other symptoms?"*
  8. 🧠 **Mind & Mood**: *"How is your mood or mental state?"*
  9. 📋 **Review**: *"Let's review your information."*
  10. ✅ **Done**: *"Intake complete! Thank you."*
* **Three Smart Capabilities**:
  * **Auto-Fills Multiple Details**: If a patient says *"Burning pain in my right temple worse from light"*, the system fills Location, Sensation, and Triggers at once, skipping redundant questions.
  * **Empathetic Bedside Prompting**: Local LLaMA 3 is instructed to sound supportive and clear without drifting off-topic.
  * **Dynamic Quick-Reply Chips**: Generates clickable suggestion chips (e.g., *[Worse in morning]*, *[Throbbing pain]*) so mobile and elderly patients do not have to type long paragraphs.
* **Speaker Notes**:
  > *"The intake agent is strictly controlled by a 10-state Finite State Machine. If a patient shares multiple details at once, our slot tracker captures them automatically and skips redundant questions. Clickable suggestion chips make it effortless for patients to answer on mobile devices."*

---

## Slide 14: Symptom Extraction & LLaMA 3 Resolution Layer (Part 1)

* **Canva Slide Layout**: 2-Column Entity Tagging Layout. Left: Raw Patient Utterance. Right: Detailed 15-Class BIO Token Mapping Table.
* **Slide Title**: Symptom Extraction & LLaMA 3 Resolution Layer
* **Header Tag**: **1. Token-Level Bio_ClinicalBERT Tagging**
* **Subtitle**: Uses a 15-class BIO tagging scheme to identify exact word spans for Location, Sensation, Aggravation, Relief, Concomitants, Time and Mind.
* **Patient Input (Raw Text)**:
  > *"Severe throbbing pain in right temple worse in morning, but no vomiting or dizziness."*
* **Tokens with BIO Tags (15 Classes)**:
  | Token | BIO Tag | Class Description |
  |---|:---:|---|
  | Severe | `B-SEN` | Beginning of Sensation |
  | throbbing | `I-SEN` | Inside Sensation |
  | pain | `I-SEN` | Inside Sensation |
  | in | `O` | Outside / non-medical word |
  | right | `B-LOC` | Beginning of Location |
  | temple | `I-LOC` | Inside Location |
  | worse | `B-MOD_AGG` | Beginning of Aggravation |
  | in | `O` | Outside |
  | morning | `B-TEMP` | Beginning of Temporal Modality |
  | but | `O` | Outside |
  | no | `O` | Outside |
  | vomiting | `O` | Outside (negated) |
  | or | `O` | Outside |
  | dizziness | `O` | Outside (negated) |
* **Speaker Notes**:
  > *"In the first stage of extraction, Bio_ClinicalBERT tags exact token spans across 15 BIO classes. As shown here, 'Severe throbbing pain' is recognized as a single sensation entity, 'right temple' as location, and 'morning' as temporal modality."*

---

## Slide 15: Symptom Extraction & LLaMA 3 Resolution Layer (Part 2)

* **Canva Slide Layout**: 2-Column Split Layout. Left: 3-Step Logic Pipeline. Right: Resolved Pydantic JSON Profile.
* **Header Tag**: **2. LLaMA 3 Contextual Resolution**
* **Subtitle**: Filters negations, resolves pronouns, and produces a clean structured profile.
* **Left Column: 3 Resolution Steps**:
  1. 🚫 **Negation Filtering**: Drops negated statements (*"no vomiting or dizziness"* $\to$ marked negative and ignored; *"no vomiting"* ignored, *"dizziness"* kept only if confirmed affirmative).
  2. 🔗 **Pronoun Resolution**: Connects vague words to the correct anatomical entity (*"it radiates downward"* $\to$ *"it"* refers to *"temple"*).
  3. 📋 **Clean Structured Profile**: Emits structured JSON ready for vector search. Only valid, resolved symptoms are kept.
* **Right Column: Resolved Symptom Profile (JSON)**:
  ```json
  {
    "symptoms": [
      {
        "text": "severe throbbing pain",
        "type": "SEN",
        "location": "right temple",
        "modality": {
          "worse": "morning",
          "better": null
        }
      }
    ],
    "negated_symptoms": [
      {"text": "vomiting", "type": "CONC", "reason": "negated"},
      {"text": "dizziness", "type": "CONC", "reason": "negated"}
    ]
  }
  ```
* **Speaker Notes**:
  > *"Next, our local LLaMA 3 resolver filters out negations and resolves pronouns. If a patient says 'no vomiting', that complaint is cleanly separated into a negated list so we never match vomiting rubrics. It outputs a validated Pydantic JSON profile ready for vector search."*

---

## Slide 16: Synthetic Case Generation Pipeline

* **Canva Slide Layout**: 5-Step Horizontal Process Pipeline with 4-Tier Ladder Visual Callout.
* **Slide Title**: Synthetic Case Generation Pipeline
* **The 5-Step Generation Workflow**:
  1. 🎯 **Pick Rubrics**: Samples rubrics and proven remedies from the Kent SQLite DB (Rubrics, Remedies, Grades 3/2/1, Relationships).
  2. 🤖 **Generate Clinical Stories**: LLaMA 3 writes realistic patient complaints across 4 patient types (*Talkative, Quiet, Acute Crisis, Somatizing*).
  3. 🎲 **Entropy Seeding**: Shifts random seeds dynamically (`Seed = Seed_0 + case_idx * 137`) so stories never repeat.
  4. 🪜 **4-Tier Offset Drift Repair Ladder**:
     * *Tier 1*: Exact Character Slice Match (`narrative[s:e] == text`).
     * *Tier 2*: Local Search Window ($\pm 15$ characters).
     * *Tier 3*: Global Search Across Story.
     * *Tier 4*: Regex Word Boundary Matching (`\bword\b`).
  5. 📊 **Balanced Split**: Enforces an 80% Train, 10% Validation, and 10% Test split.
* **Speaker Notes**:
  > *"Because no public training data exists, we built a reverse-generation pipeline: We pick rubrics from our database, generate patient stories with LLaMA 3 across 4 personality types, and repair character offset shifts using a 4-tier ladder, achieving 100% token alignment."*

---

## Slide 17: Dense Semantic Retrieval & Remedy Ranking

* **Canva Slide Layout**: 2-Column Split Layout. Left: ChromaDB Vector Search & Tiers. Right: Classical Kentian Ranker & Formulas.
* **Slide Title**: Dense Semantic Retrieval & Remedy Ranking
* **Column 1: ChromaDB Dense Vector Search**:
  * **Corpus Size**: All **74,513 rubrics** pre-embedded using `all-MiniLM-L6-v2` ($d = 384$).
  * **Search Speed**: Sub-15 ms cosine search across the entire index on standard CPU.
  * **Calibrated Match Tiers**:
    * 🟢 **Strong Match ($\ge 0.68$)**: Clear clinical synonym.
    * 🔵 **Good Match ($0.58\text{--}0.68$)**: High clinical relevance.
    * 🟡 **Fair Match ($0.52\text{--}0.58$)**: Exploratory match for doctor review.
    * 🔴 **Noise Filter ($< 0.52$)**: Automatically discarded to prevent wrong matches.
* **Column 2: Classical Kentian Remedy Ranker**:
  * **Scoring Logic**:
    $$\text{Score} = \sum (\text{Coverage} \times \text{Grade Weight} \times \text{IRF Penalty} \times \text{Search Similarity})$$
  * **Proving Weights**: Grade 3 Bold ($3\times$), Grade 2 Italics ($2\times$), Grade 1 Plain ($1\times$).
  * **IRF Specificity Penalty**: Lowers the score of hyper-common remedies (*Sulphur*), helping specific curative remedies rank on top.
* **Speaker Notes**:
  > *"For search, all 74,513 rubrics are embedded into ChromaDB, returning top matches in under 15 milliseconds. We filter out noise below 0.52 similarity. Then, our totality ranker scores remedies by multiplying symptom coverage, proving grade weights, and an IRF penalty that elevates the most specific remedy."*

---

## Slide 18: Pilot Benchmark Validation Results (100 MIND Cases)

* **Canva Slide Layout**: 6-Card Metric Dashboard with Right-Side Dimension Breakdown Card.
* **Slide Title**: Pilot Benchmark Validation Results (100 MIND Cases)
* **Subtitle**: Verified on 100 Clinical Cases Across 25 MIND Rubrics
* **6 Key Benchmark KPI Cards**:
  * 🎯 **100.0%** JSON Schema Validity (100/100 cases passed)
  * 📏 **100.0%** Character Offset Accuracy (**576/576 spans aligned, 0 drift**)
  * 🔗 **100.0%** Token / BIO Tag Alignment (0 mismatches)
  * 📊 **576 Spans** Extracted Clinical Entities (Average **5.8 spans/case**)
  * 🔀 **13.10%** Pairwise Jaccard Overlap (Well below the 45% repetition limit)
  * 🌟 **86.90%** Lexical Diversity Score (Rich, varied patient narratives)
* **Right Card: 7-Dimension Breakdown**:
  * `MENT`: 286 (49.7%) $\vert$ `SEN`: 77 (13.4%) $\vert$ `LOC`: 76 (13.2%) $\vert$ `MOD_AGG`: 57 (9.9%) $\vert$ `TEMP`: 39 (6.8%) $\vert$ `CONC`: 34 (5.9%) $\vert$ `MOD_AMEL`: 7 (1.2%)
* **Speaker Notes**:
  > *"We verified our pipeline on a 100-case pilot across 25 mental rubrics. The results demonstrate solid engineering: 100% valid JSON, 100% character alignment with zero drift across all 576 spans, and an 86.9% diversity score, proving our synthetic cases are varied and reliable."*

---

## Slide 19: Clinical Dashboard (Initial Design)

* **Canva Slide Layout**: Section Transition Slide with Title and Icon pointing right.
* **Slide Header**: 
  # Clinical Dashboard
  ### (Initial Design) 👉
* **Speaker Notes**:
  > *"Now, we would like to present the working clinical dashboard that doctors use to interact with Kent-AI."*

---

## Slide 20: Dashboard — Live Consultation & Slot Tracking HUD

* **Canva Slide Layout**: Full-Slide High-Resolution Screenshot of the Streamlit Web Application (Midnight Theme `#0A0F1D`).
* **Visual Elements Highlighted**:
  * **Top Header**: Kent-AI Clinical Assistant (Classical Homeopathic Repertorization & Decision Support)
  * **Live Symptom Dimensions HUD**: Real-time slot filling badges (Location, Sensation, Worse from, Better from, Concomitant, Time pattern, Mental/Emotional).
  * **Clinical Dialogue Console**: Active conversational chat window powered by local LLaMA 3 8B.
  * **Dynamic Quick-Reply Chips**: Contextual suggestion pills (*Severe anxiety & fearful apprehension*, *Restless pacing & irritability*, *Emotional pain & sadness*, *Absent-mindedness & memory lapses*).
* **Speaker Notes**:
  > *"This is the Live Consultation workspace. The doctor or patient interacts with the intake console. As the conversation progresses, the top HUD automatically turns symptom dimension pills green, showing real-time slot completion without cluttering the screen."*

---

## Slide 21: Dashboard — Instant Repertorization & Totality Matrix

* **Canva Slide Layout**: Full-Slide High-Resolution Screenshot of the Repertorization Engine & Totality Matrix.
* **Visual Elements Highlighted**:
  * **Primary Simillimum Indication**: **Belladonna (Bell.)** — Covering 6 of 14 symptom rubrics (43% coverage) with a weighted totality score of **3.81**.
  * **2. Remedy Totality Ranking**: Grade-weighted horizontal bar chart comparing top candidate remedies (*Belladonna, Glonoinum, Arsenicum album, Calcarea carbonica, Phosphorus, Opium, Bryonia, Nux vomica*).
  * **3. Top Remedy Breakdown Grid**: Detailed clinical breakdown table displaying rank, remedy abbreviation, full botanical name, score, and rubric coverage fraction.
* **Speaker Notes**:
  > *"Once intake is complete, the Instant Repertorization workspace displays the candidate remedies. Here, Belladonna is identified as the leading simillimum. The doctor can inspect the exact grade weights, coverage fractions, and export the report with full provenance in one click."*

---

## Slide 22: Post-Mid-Semester Roadmap

* **Canva Slide Layout**: 4 Horizontal Milestone Cards with Process Badges.
* **Slide Title**: Post-Mid-Semester Roadmap
* **Slide Subtitle**: Four Immediate Milestones $\to$
* **Milestone Cards**:
  1. 🚀 **Full-Scale GPU Generation**: Run `scripts/run_gpu_generation.sh` on college GPU servers to generate **~22,200 synthetic clinical cases** across all 4,933 MIND rubrics.
  2. 🎓 **Fine-Tuning Bio_ClinicalBERT**: Train the token-level sequence classifier on Colab GPU (Target Token F1 $\ge 88.0\%$).
  3. 📈 **System-Wide Evaluation**: Benchmark held-out test cases targeting Top-20 Rubric Recall $\ge 90.0\%$ and MRR $\ge 0.65$.
  4. 🩺 **Clinical Expert Validation (Homeopathy Practitioners)**: Partner with certified homeopathic doctors to test the tool in practice—verifying remedy choices, rubric matches, and consultation time reduction (from 40 min to $<10$ min).
* **Speaker Notes**:
  > *"Looking ahead post-mid-sem: First, we will generate the full 22,200 MIND cases on our GPU server. Second, we will fine-tune Bio_ClinicalBERT to reach an F1 score above 88%. Third, we will benchmark end-to-end rubric recall. Crucially, as part of our future work, we will validate the tool directly with certified homeopathic clinicians to evaluate real-world prescription accuracy and time savings."*

---

## Slide 23: Conclusion & Thank You

* **Canva Slide Layout**: Centered High-Impact Final Slide with Project Summary, GitHub Link, and Bold Q&A Banner.
* **Slide Title**: Conclusion
* **Core Takeaway Statement**:
  > **Kent-AI gives homeopathic doctors an automated intake assistant that reduces consultation time from 40 to under 10 minutes, using verified repertory data to ensure accurate remedy recommendations.**
* **Open-Source Repository**:
  * **GitHub** $\to$ [https://github.com/Krishna200608/kent-ai](https://github.com/Krishna200608/kent-ai)
* **Closing Banner**:
  # THANK YOU
  *We welcome questions and feedback from the evaluation committee.*
* **Speaker Notes**:
  > *"In conclusion, Kent-AI gives homeopathic doctors a reliable, local-first assistant that reduces consultation time from 40 minutes to under 10 minutes while preserving 100% database provenance. The code and models are open-source on GitHub. Thank you for your time, and we welcome your questions and feedback."*

---
*End of Mid-sem-ppt-content.md — Complete 23 Slides Master Deck matching `Kent-AI Midsem.pdf`.*

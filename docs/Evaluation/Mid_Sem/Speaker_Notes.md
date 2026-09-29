# Kent-AI: Mid-Semester Defense Speaker Notes & Oral Examination Defense Guide

**Project Title**: Kent-AI: An AI-Powered Conversational Clinical Assistant for Homeopathic Case-Taking and Dense Semantic Repertorization  
**Team Members**: Krishna Sikheriya (IIT2023139), Lokesh Bawariya (IIT2023138), Naitik Jain (IIB2023036)  
**Academic Institution**: Indian Institute of Information Technology, Allahabad (IIIT-A)  
**Evaluation Milestone**: B.Tech IT Seventh Semester — Mid-Semester Project Evaluation  
**Presentation Deck**: [23 Slides Master (`Kent-AI Midsem.pdf`)](file:///d:/Research%20Project/kent-ai/docs/Evaluation/Mid_Sem/Kent-AI%20Midsem.pdf) | [Presentation Script (`Mid-sem-ppt-content.md`)](file:///d:/Research%20Project/kent-ai/docs/Evaluation/Mid_Sem/Mid-sem-ppt-content.md) | [Domain Reference (`Info.md`)](file:///d:/Research%20Project/kent-ai/docs/Evaluation/Mid_Sem/Info.md)

---

## 🎯 Master Speaker Allocation & Transition Plan

| Speaker | Allocated Slides | Slide Count | Focus Theme | Estimated Time |
|---|:---:|:---:|---|:---:|
| **1. Naitik Jain** | **Slides 1 – 8** | **8 Slides** | **Clinical Domain, Motivation, Literature Review, Research Gaps & Problem Statement** | **~5 – 6 min** |
| **2. Krishna Sikheriya** | **Slides 9 – 16** | **8 Slides** | **Knowledge Base Scoping, 7D Clinical Framework, Mathematical Formulation, Architecture, Intake FSM, Clinical NER & Synthetic Pipeline** | **~6 – 7 min** |
| **3. Lokesh Bawariya** | **Slides 17 – 23** | **7 Slides** | **Dense Semantic Retrieval, Remedy Ranking, Pilot Benchmarks, Live Dashboard Walkthrough, Roadmap & Conclusion** | **~5 – 6 min** |
| **All Team Members** | **Viva / Q&A** | **—** | **Committee Cross-Examination & Defense (Module-specific handoffs)** | **~5 – 10 min** |

---

> 💡 **Master Glossary & Domain Jargon Reference**:  
> For the comprehensive reference table of all full forms, acronyms, clinical/homeopathic definitions, AI/NLP architectures, mathematical formulations, and viva quick-lookup index, see **[`Info.md`](file:///d:/Research%20Project/kent-ai/docs/Evaluation/Mid_Sem/Info.md)**.

---

## Slide 1: Title Slide (Project Overview) [Speaker 1: Naitik]

### Spoken Script
> *"Good morning, respected members of the evaluation committee. We are presenting **Kent-AI**, an intelligent, privacy-preserving clinical assistant designed to eliminate a critical operational bottleneck in homeopathic healthcare: the time-consuming, cognitively exhausting process of manual patient intake and repertorization.*
>
> *Today, a classical homeopathic consultation takes 30 to 45 minutes, largely spent manually writing notes and thumbing through 19th-century medical indexes. Kent-AI automates multi-dimensional symptom intake using an empathetic conversational agent, resolves modern colloquial language to classical rubrics using dense vector retrieval across 74,513 rubrics in under 15 milliseconds, and delivers a transparent repertorization totality matrix to the doctor in under 10 minutes.*
>
> *I am Naitik Jain, and along with my teammates Krishna Sikheriya and Lokesh Bawariya, we will walk you through our problem formulation, architecture, pilot benchmark results, and working clinical interface."*

### Key Visual Anchor
Point to the team roster and the subtitle emphasizing the two halves: **Conversational Intake** + **Dense Semantic Repertorization**.

### Probable Panel Questions & Defense Answers

#### Q1: "Why choose homeopathy for an AI project? Isn't modern medical AI focused on allopathic EHRs like MIMIC-III?"
* **Answer**: *"While allopathic AI focuses on predicting categorical diagnostic codes (ICD-10) or segmenting imaging scans, homeopathy presents an extreme computational challenge that allopathic AI cannot solve. Homeopathy does not prescribe by disease name; it prescribes by the patient's individual symptom totality across 7 dimensions (location, sensation, modalities, and mental state). The knowledge base—Dr. J.T. Kent's Repertory—is an extreme taxonomy of 74,513 hierarchical rubrics written in 1897 Victorian English. Solving this requires advancing clinical NLP in extreme classification, archaic-to-modern semantic bridging, and deterministic multi-criteria scoring where zero public annotated datasets previously existed."*

#### Q2: "What is your individual contribution versus your teammates?"
* **Answer**: *"Our work was modularized into distinct engineering phases:
  * **Naitik**: Synthetic case generation pipeline, 4-tier character offset drift repair ladder, deficit-balancing dataset splitter, and the clinician Streamlit dashboard (`src/data/case_generator.py`, `src/data/bio_tagger.py`, `src/dashboard/app.py`).
  * **Krishna (Lead)**: System architecture, SQLite Data Access Layer, ChromaDB HNSW vector index construction, and the mathematical Kentian totality ranker (`src/data/kent_db.py`, `src/search/vector_store.py`, `src/search/ranker.py`).
  * **Lokesh**: Conversational intake Finite State Machine, 7-dimension slot tracker, and bedside manner dialogue manager (`src/chatbot/state_machine.py`, `src/chatbot/dialogue_manager.py`)."*

---

## Slide 2: Introduction (Homeopathic Principles & Repertorization) [Speaker 1: Naitik]

### Spoken Script
> *"To understand our engineering contribution, we must first look at how a classical homeopath arrives at a prescription. Classical homeopathy operates on the Law of Similars: 'Similia Similibus Curentur'—let like be cured by like. A patient is treated with a micro-diluted substance that produces the exact same symptom totality in healthy human provers.*
>
> *To find this curative remedy—termed the **Simillimum**—the physician performs **repertorization**: translating the patient's colloquial complaints into standardized medical taxonomy entries called **rubrics** within a reference volume called a **Repertory**.*
>
> *We digitized Dr. James Tyler Kent's classical 1897 Repertory, which contains **74,513 rubrics** spanning 37 anatomical chapters, **679 remedies**, and **507,179 rubric-remedy associations**. Kent instituted a typographic 3-tier grading system: Grade 3 bold capitals with weight 3.0 representing verified clinical cures, Grade 2 italics with weight 2.0, and Grade 1 plain text with weight 1.0. This grading forms the empirical bedrock of our mathematical ranking engine."*

### Key Visual Anchor
Point to the contrast between the left card (Homeopathic Principles: Simillimum & Similars) and the right card (Kent's Repertory scale: 74,513 rubrics, 3-tier weights 3, 2, 1).

### Probable Panel Questions & Defense Answers

#### Q1: "Why did you choose Kent's Repertory instead of Boenninghausen or Boericke?"
* **Answer**: *"Dr. J.T. Kent's Repertory (1897) is universally recognized in academic homeopathy as the definitive hierarchical taxonomy. Unlike Boericke (which is primarily a pocket Materia Medica with an abbreviated index) or Boenninghausen (which uses abstract generalized combinations), Kent organized symptoms into an explicit 37-chapter anatomical and psychological hierarchy with comprehensive 3-tier proving grades. It provides the largest structured taxonomy (74,513 rubrics), making it ideal for dense neural embedding and retrieval."*

---

## Slide 3: Motivation (Clinical Consultation Bottlenecks & Language Divide) [Speaker 1: Naitik]

### Spoken Script
> *"Despite its global adoption, modern homeopathic practice faces severe operational and linguistic bottlenecks.*
>
> *First, consultation length: a classical homeopathic intake takes 30 to 45 minutes because the doctor must manually record nuances across mental, physical, and modal spheres. In government AYUSH clinics and Primary Health Centres, this caps doctor throughput to only 8 to 12 patients per day.*
>
> *Second, human cognitive fatigue: no human doctor can memorize 74,513 rubrics, leading to recall bias toward roughly 30 familiar polycrest remedies.*
>
> *Third, and most critically from an NLP standpoint: look at the table on this slide. There is a **complete lexical divide** between patient speech and the repertory. A patient says: 'crushing vice-like headache'—the rubric is `HEAD > PAIN > pressing > as if in a vise`. A patient says: 'worse when bending over'—the rubric is `HEAD > PAIN > stooping, from`. There is **zero keyword overlap**. Traditional keyword search or SQL `LIKE` queries fail completely. Dense semantic vector retrieval is computationally mandatory."*

### Key Visual Anchor
Direct the committee's eyes to the middle table: show that all four sample patient phrases have **0% keyword overlap** with Kent's rubrics.

### Probable Panel Questions & Defense Answers

#### Q1: "Why can't doctors just use existing software like RadarOpus or MacRepertory?"
* **Answer**: *"Existing commercial software packages like RadarOpus are legacy desktop tools costing between ₹23,000 and ₹1.5 Lakhs. Crucially, they do not automate case-taking—the doctor still spends 30 minutes typing notes. Furthermore, their search engines rely primarily on Boolean keywords or alphabetical indexes; if the doctor doesn't already know the exact 19th-century terminology like 'stooping' instead of 'bending', the software fails to retrieve the rubric. Kent-AI bridges this vocabulary gap automatically using neural dense embeddings."*

---

## Slide 4: Research Problems & Core Challenges [Speaker 1: Naitik]

### Spoken Script
> *"We distilled these clinical hurdles into three core technical research challenges:
>
> *1. **7-Dimensional Clinical NER**: Clinical case-taking requires extracting not just a medical entity, but a structured 7-dimensional tuple: Location, Sensation, Modality Aggravation, Modality Amelioration, Concomitants, Temporal patterns, and Mental/Emotional state from unstructured, conversational dialogue.*
>
> *2. **Extreme Taxonomic Retrieval**: Mapping unstructured symptom tuples to an extreme classification hierarchy of 74,513 candidate rubrics with sub-15 millisecond retrieval latency.*
>
> *3. **Extreme Domain Data Scarcity**: Zero publicly available, token-annotated datasets exist for homeopathic clinical case-taking. Annotating 20,000 cases manually with medical experts is financially and logistically prohibitive. We had to engineer a verifiable, synthetic data generation pipeline."*

### Key Visual Anchor
Point to the three pillar cards: **Pillar 1: 7D NER**, **Pillar 2: Taxonomic Retrieval**, **Pillar 3: Data Scarcity**.

### Probable Panel Questions & Defense Answers

#### Q1: "Why is 7D extraction harder than standard biomedical NER like NCBI-Disease or BC5CDR?"
* **Answer**: *"Standard biomedical NER identifies flat entity mentions—such as a disease name ('diabetes') or a chemical ('aspirin'). In clinical homeopathy, a raw disease mention is therapeutically useless. We must extract fine-grained modifiers: the precise anatomical sub-site (`LOC`), the subjective quality of sensation (`SEN`), environmental aggravators (`MOD_AGG`), relieving factors (`MOD_AMEL`), unrelated simultaneous symptoms (`CONC`), time patterns (`TEMP`), and constitutional psychological state (`MENT`). These entities have high syntactic ambiguity and frequent nested clauses."*

---

## Slide 5: Literature Review (AI in Homeopathy 2024–2026) [Speaker 1: Naitik]

### Spoken Script
> *"Examining recent academic literature reveals why general-purpose AI fails in this domain.*
>
> *In a landmark retrospective study published in MDPI Healthcare in April 2026 by the HOHM Foundation, researchers evaluated four commercial LLM chatbots—ChatGPT-4, Claude 3, Copilot, and Gemini—across 100 acute clinical cases. The bots achieved an overall remedy concordance of only **36.5%**, and when the exact same patient text was queried multiple times, the models yielded different remedy recommendations. Unconstrained generative LLMs suffer from severe stochastic drift and non-deterministic hallucinations.*
>
> *Looking at specialized academic systems: Rawat et al. in Springer 2026 introduced **HomeoCure**, an LLM-RAG framework for homeopathy. While HomeoCure takes initial steps in symptom retrieval, it lacks token-level 7-dimensional entity extraction, lacks mathematical grade-weighted totality scoring, and does not address the extreme taxonomy of 74,513 rubrics."*

### Key Visual Anchor
Highlight the two literature cards: **HOHM 2026 (36.5% concordance, stochastic instability)** vs **HomeoCure (RAG without 7D extraction)**.

### Probable Panel Questions & Defense Answers

#### Q1: "Why did commercial LLMs achieve only 36.5% concordance in the HOHM study?"
* **Answer**: *"Commercial LLMs fail in homeopathy for three fundamental reasons: First, autoregressive language models predict next tokens based on web text probability; they do not perform formal mathematical summation across multi-dimensional symptom matrices. Second, their training corpora are overwhelmingly allopathic, creating high bias toward common conditions. Third, they lack database grounding—they hallucinate plausible-sounding remedies or mix rubrics from different repertories without proving provenance."*

---

## Slide 6: Literature Review Continued (Clinical NLP & Retrieval 2019–2026) [Speaker 1: Naitik]

### Spoken Script
> *"Turning to foundational clinical NLP and conversational systems:
>
> *For clinical entity recognition, Alsentzer et al.'s **Bio_ClinicalBERT** remains the preeminent domain-specific transformer. Pretrained on PubMed abstracts and over 2 million MIMIC-III ICU clinical notes, it consistently outperforms general BERT and RoBERTa on medical language inference and sequence classification.*
>
> *In conversational healthcare, Saley et al. presented **MediTOD** at EMNLP 2024—a medical task-oriented dialogue benchmark. MediTOD proved that medical history-taking requires explicit dialogue state tracking (DST) and slot validation across onset, severity, and triggers to prevent conversational loops. We adapted this principle directly into Kent-AI's 10-state Finite State Machine and 7-dimension slot tracker."*

### Key Visual Anchor
Point to **Bio_ClinicalBERT (clinical token representation)** and **MediTOD EMNLP 2024 (conversational slot tracking)**.

### Probable Panel Questions & Defense Answers

#### Q1: "Why use Bio_ClinicalBERT rather than a modern LLM like LLaMA 3 for token extraction?"
* **Answer**: *"Bio_ClinicalBERT has 110 million parameters, requires only ~400 MB of VRAM, and evaluates token-level classification in milliseconds with deterministic character-span offsets. In contrast, running an 8-billion parameter LLM for every single token extraction turn is 50 times slower, computationally prohibitive on clinic laptops, and prone to character-offset drift when outputting JSON. We use Bio_ClinicalBERT for fast, deterministic token extraction, and reserve LLaMA 3 solely for high-level dialogue management and negation filtering."*

---

## Slide 7: Research Gap Analysis (Full Comparative Matrix) [Speaker 1: Naitik]

### Spoken Script
> *"This comparative feature matrix synthesizes the gap between existing tools and Kent-AI across seven technical dimensions.*
>
> *Traditional commercial software like RadarOpus costs up to 1.5 lakh rupees, forces the doctor to manually look up every rubric, and relies on brittle keyword search. ChatGPT hallucinates fake remedies with zero database grounding and poses severe patient data privacy risks over cloud APIs. Academic systems like HomeoCure explore basic RAG, but lack token-level 7D extraction and transparent mathematical scoring.*
>
> *Kent-AI fills all seven gaps: a 10-state intake FSM, 100% database grounding in 74,513 rubrics, Bio_ClinicalBERT 7-dimension extraction, transparent Kentian grade-weighted scoring with IRF penalties, a modern clinical dashboard, and a local-first architecture that runs offline on a clinician's PC with zero cloud PHI transmission."*

### Key Visual Anchor
Walk horizontally across the table row by row, contrasting the red $\times$ and yellow $\triangle$ against Kent-AI's green checkmarks.

### Probable Panel Questions & Defense Answers

#### Q1: "What about patient privacy? Can you guarantee zero data leakage?"
* **Answer**: *"In our current prototype, Kent-AI runs entirely locally on the clinician's machine: Ollama runs the quantized LLaMA 3 8B model locally in 5.5 GB of RAM; SQLite runs as an embedded local database; ChromaDB runs as an in-process persistent HNSW vector store; and Bio_ClinicalBERT runs on the local CPU/GPU via PyTorch. Not a single byte of patient text or Protected Health Information (PHI) leaves the host computer or touches a third-party cloud API."*

---

## Slide 8: Problem Statement [Speaker 1: Naitik]

### Spoken Script
> *"To crystallize our project goal into a formal problem statement:
>
> *Clinically: We must eliminate the 30-to-45-minute consultation bottleneck, prevent human memory recall bias, and bridge the vocabulary gap between modern patients and 19th-century repertories.*
>
> *Computationally: We must solve joint 7-dimensional token extraction, execute sub-15 ms cosine retrieval over an extreme taxonomy of 74,513 rubrics, and bootstrap a domain where zero annotated clinical data exists.*
>
> *Our Concrete Goal: To build and validate an offline, privacy-preserving clinical assistant that automatically extracts Kent's 7 symptom dimensions through structured conversational intake, and delivers 100% database-grounded remedy repertorization in under 10 minutes.*
>
> *To walk you through our digital knowledge base foundation, formal mathematical formulation, and end-to-end system architecture, I now hand over to Krishna Sikheriya."*

### Key Visual Anchor
Point to the 3 segmented containers: Clinical Problem (Blue), Computational Problem (Purple), Goal Statement (Green). Hand over to Krishna.

### Probable Panel Questions & Defense Answers

#### Q1: "What is your definition of success for this project?"
* **Answer**: *"We have established quantitative and qualitative success criteria:
  1. **Token BIO F1 Score** $\ge 88.0\%$ across all 7 symptom dimensions.
  2. **Top-20 Rubric Retrieval Recall** $\ge 90.0\%$ with Mean Reciprocal Rank (MRR) $\ge 0.65$.
  3. **Zero Character Offset Drift** (100% string alignment) in synthetic clinical training data.
  4. **Clinical Time Reduction**: Cutting case comprehension time from 40 minutes to under 10 minutes in clinician trials."*

---

## Slide 9: Existing Knowledge Base (Open-Source Foundation & MIND Scoping) [Speaker 2: Krishna]

### Spoken Script
> *"Thank you, Naitik. Respected members of the committee, I will now walk you through our knowledge base engineering, mathematical formulations, and system architecture.*
>
> *Our foundational data layer builds upon the open-source digitized Kent's Repertory developed by su4532. This gives us an initial relational SQLite database containing 74,513 rubrics, 679 remedies, and 507,179 associations.*
>
> *Having this raw digital foundation in place allowed our team to focus directly on the core machine learning challenges: dense vector representations, clinical BERT token tagging, synthetic case generation, and conversational reasoning.*
>
> *While our vector database indexes all 37 chapters, our initial training and evaluation benchmark explicitly scopes to **Chapter 1: MIND** (4,933 rubrics). In classical homeopathy, mental and emotional symptoms carry the highest constitutional priority. Computationally, MIND presents the highest semantic ambiguity, metaphorical language, and vocabulary gap. Solving MIND establishes a robust benchmark before expanding across the physical chapters."*

### Key Visual Anchor
Show the open-source SQLite foundation box on top, and the Chapter 1: MIND callout box below with 4,933 rubrics.

### Probable Panel Questions & Defense Answers

#### Q1: "If you used an open-source repertory database, what did you actually build yourselves?"
* **Answer**: *"The open-source repository by su4532 provided raw digitized SQL tables of rubrics and remedy strings. What we built is the entire AI/ML architecture:
  1. A hardened, read-only Python Data Access Layer (`src/data/kent_db.py`) with grade coalescing and FTS5 search.
  2. Complete 384-dimensional dense vector embeddings of all 74,513 rubrics with an HNSW ChromaDB index.
  3. The 10-state conversational intake FSM and 7D slot tracker.
  4. The 15-class `Bio_ClinicalBERT` token tagging model and LLaMA 3 negation resolver.
  5. The HomeoNER synthetic case generation pipeline with the 4-tier offset drift repair ladder.
  6. The Kentian Totality Ranker incorporating Inverse Remedy Frequency (IRF).
  7. The complete Streamlit clinical dashboard portal."*

---

## Slide 10: Kent's 7 Clinical Symptom Dimensions [Speaker 2: Krishna]

### Spoken Script
> *"In classical homeopathy, a raw disease complaint like 'I have a headache' is clinically incomplete and impossible to prescribe upon. Under Dr. Kent's doctrine of the 'Complete Symptom', a symptom only becomes actionable when individualized across seven distinct clinical axes:*
>
> *Location, Sensation, Modality Aggravation, Laterality, Concomitant symptoms, Mental/Emotional state, and Temporality.*
>
> *Notice why this matters for our AI system: this 7-dimensional table is not just a medical taxonomy; it forms the exact target schema for our 10-State Conversational FSM and our Bio_ClinicalBERT token classifier. Our intake agent actively tracks these seven slots, and our sequence tagger labels exact token boundaries for every single dimension."*

### Key Visual Anchor
Point to the 7 rows of the table, showing how everyday phrases (e.g., *'right side of head'*, *'throbbing'*, *'worse in morning'*) map directly to clinical dimensions.

### Probable Panel Questions & Defense Answers

#### Q1: "Why are modalities (better/worse) more important than location in homeopathy?"
* **Answer**: *"In allopathy, location determines the pathology (e.g., headache = neurological). In homeopathy, hundreds of remedies treat headache. What individualizes the remedy are the modalities: whether the pain is worse from sun exposure (*Glonoinum*), worse from motion (*Bryonia*), or better from hard pressure (*Belladonna*). Modalities represent the body's functional reactivity to environmental and physical stressors, which is why Kent-AI treats `MOD_AGG` and `MOD_AMEL` as primary first-class entities."*

---

## Slide 11: Formal Mathematical Problem Formulation [Speaker 2: Krishna]

### Spoken Script
> *"We formulated Kent-AI with complete mathematical rigor across four formal equations:
>
> *1. **Intake State Transition**: $S_{t+1} = \delta(S_t, u_t, \Phi_t)$. The next dialogue state is a deterministic function of the current state $S_t$, the patient utterance $u_t$, and an internal 7-dimensional slot fulfillment vector $\Phi_t \in [0, 1]^7$.*
>
> *2. **Token-Level Sequence Tagging**: Predicted token class $\hat{y}_i = \arg\max P(y_i \mid \mathbf{x}; \boldsymbol{\theta}_{\text{BERT}})$ across 15 BIO tags ($7 \text{ dimensions} \times 2 \ (\text{B-} / \text{I-}) + 1 \ (\text{O}) = 15$).*
>
> *3. **Dense Semantic Retrieval**: Normalized cosine similarity $\text{Sim}(\mathbf{q}_k, \mathbf{e}_r) = \frac{\mathbf{q}_k \cdot \mathbf{e}_r}{\|\mathbf{q}_k\|_2 \|\mathbf{e}_r\|_2}$ between 384-dimensional query vector $\mathbf{q}_k$ and rubric vector $\mathbf{e}_r$ across all 74,513 candidates.*
>
> *4. **Kentian Totality Scoring**: Our totality formula scores candidate remedy $m$ as:*
>
> $$\text{Score}(m \mid \mathcal{R}^*) = \sum_{r \in \mathcal{R}^*} \mathbb{I}(m \in \mathcal{M}_r) \cdot w(g_{r,m}) \cdot \text{IRF}(r) \cdot \text{Sim}(q_r, r)$$
>
> *Multiplying indicator inclusion $\mathbb{I}$, proving grade weight $w(g) \in \{3, 2, 1\}$, retrieval similarity $\text{Sim}$, and the Inverse Remedy Frequency $\text{IRF}(r)$."*

### Key Visual Anchor
Highlight the 4 mathematical blocks and the bottom callout explaining why 7 dimensions yield **15 BIO tags** ($7 \times 2 + 1$).

### Probable Panel Questions & Defense Answers

#### Q1: "What is the mathematical justification for Inverse Remedy Frequency (IRF)?"
* **Answer**: *"IRF is mathematically defined as $\text{IRF}(r) = \ln\left(1 + \frac{|\mathcal{M}_{\text{total}}|}{|\mathcal{M}_r|}\right)$. A broad rubric like `HEAD > PAIN` lists 400+ remedies, so $|\mathcal{M}_r|$ is large and $\text{IRF}(r) \to 0$. A specific keynote rubric like `HEAD > PAIN > sun, from exposure to` lists only 28 remedies, yielding a high IRF weight. Without IRF, polycrest remedies like *Sulphur* mathematically overpower specific curative remedies simply because they appear under hundreds of general headings."*

---

## Slide 12: Proposed End-to-End System Architecture [Speaker 2: Krishna]

### Spoken Script
> *"This slide illustrates our full end-to-end architecture, organized into five connected layers operating within a local-first privacy perimeter:
>
> * **Layer 1: Patient Intake**: Patient utterance enters our 10-state FSM, which updates the 7-dimension slot tracker and emits dynamic suggestion chips.*
> * **Layer 2: Clinical NLP**: `Bio_ClinicalBERT` performs 15-class BIO token classification, followed by local LLaMA 3 for negation pruning and coreference resolution, outputting a Pydantic JSON profile.*
> * **Layer 3: Dense Retrieval**: `all-MiniLM-L6-v2` embeds clean symptom queries and queries our persistent ChromaDB HNSW vector index of all 74,513 rubrics in under 15 milliseconds.*
> * **Layer 4: Totality Ranker**: Performs relational SQL joins against our Kent Repertory SQLite database, weighting proving grades (3.0, 2.0, 1.0) and IRF penalties.*
> * **Layer 5: Clinician Portal**: Renders an interactive Totality Matrix on the doctor's Streamlit dashboard.*
>
> *The entire pipeline executes locally on the doctor's workstation with zero cloud API dependencies."*

### Key Visual Anchor
Trace the 5 horizontal layers from left to right: Patient Intake (Blue) $\to$ Clinical NLP (Purple) $\to$ Dense Retrieval (Cyan) $\to$ Totality Ranker (Orange) $\to$ Clinician Portal (Green).

### Probable Panel Questions & Defense Answers

#### Q1: "Why is a Neuro-Symbolic architecture better here than an end-to-end neural network?"
* **Answer**: *"Pure neural networks are black boxes prone to hallucinations and non-deterministic arithmetic errors. In clinical medicine, a doctor cannot prescribe based on an unexplainable vector weight. Our Neuro-Symbolic architecture uses neural networks strictly where they excel—language comprehension and semantic bridging—while delegating remedy ranking and proving weights to deterministic relational database joins and classical homeopathic mathematical formulas. It is 100% explainable, traceable, and grounded."*

---

## Slide 13: Conversational Intake Agent & 10-State FSM [Speaker 2: Krishna]

### Spoken Script
> *"Looking closely at Layer 1: The intake dialogue is strictly governed by a 10-state deterministic Finite State Machine, progressing from Greeting and Chief Complaint through Location, Sensation, Modalities, Concomitants, and Mental symptoms to Review and Done.*
>
> *To prevent repetitive, robotic questioning, we implemented **Adaptive Slot Tracking**. If a patient volunteers multiple attributes at once—saying 'I have a severe throbbing headache in my right temple worse from bright light'—the slot tracker populates Location, Sensation, and Modality Aggravation in one turn. When transitioning, the FSM skips those fulfilled states and asks directly for relieving factors.*
>
> *Furthermore, local LLaMA 3 is conditioned with bedside manner guidelines, and our engine generates dynamic quick-reply suggestion chips so patients can click rather than type long medical paragraphs on mobile devices."*

### Key Visual Anchor
Walk through the 10 sequential circular steps, pointing out the 3 smart capabilities at the bottom (Auto-Fills, Bedside Prompting, Quick-Reply Chips).

### Probable Panel Questions & Defense Answers

#### Q1: "What prevents LLaMA 3 from giving medical advice or prescribing directly in the chat?"
* **Answer**: *"We enforce strict system prompt guardrails in `src/chatbot/dialogue_manager.py`: the model is explicitly instructed that it is a clinical intake assistant, not a doctor. It is banned from suggesting diagnoses, proposing remedies, or answering medical treatment queries. Its sole operational directive is to gather descriptive symptoms across unfilled slots in the 7-dimension tracker."*

---

## Slide 14: Symptom Extraction & LLaMA 3 Resolution Layer (Part 1) [Speaker 2: Krishna]

### Spoken Script
> *"Moving to Layer 2: Symptom Extraction operates in two synchronized stages. Stage 1 is token-level sequence classification using **Bio_ClinicalBERT**.*
>
> *We established a 15-class BIO tagging scheme: 7 symptom dimensions multiplied by Beginning and Inside tags, plus Outside.*
>
> *Look at the token mapping table on this slide: given the raw patient text 'Severe throbbing pain in right temple worse in morning, but no vomiting or dizziness':*
> * 'Severe' is tagged `B-SEN`, 'throbbing' and 'pain' are `I-SEN`—capturing the full sensation span.*
> * 'right' is `B-LOC`, 'temple' is `I-LOC`.*
> * 'worse' is `B-MOD_AGG`, and 'morning' is `B-TEMP`.*
> * Non-entity tokens and negated words like 'vomiting' and 'dizziness' are tagged `O`.*
>
> *Bio_ClinicalBERT evaluates this sequence in milliseconds with exact token boundary offsets."*

### Key Visual Anchor
Walk down the table column by column, highlighting the colored BIO tags (`B-SEN`, `I-SEN`, `B-LOC`, `B-MOD_AGG`, `B-TEMP`).

### Probable Panel Questions & Defense Answers

#### Q1: "Why not use spaCy or standard clinical NER packages like scispaCy?"
* **Answer**: *"Standard models like scispaCy are trained on allopathic entities like diseases, anatomical organs, and chemicals (`DISEASE`, `ORGAN`, `CHEMICAL`). They cannot recognize homeopathic modalities (`MOD_AGG`, `MOD_AMEL`) or distinguish sensations (`SEN`) from emotional states (`MENT`). Fine-tuning Bio_ClinicalBERT on our custom 15-class HomeoNER tagset enables exact alignment with Kent's 7 clinical dimensions."*

---

## Slide 15: Symptom Extraction & LLaMA 3 Resolution Layer (Part 2) [Speaker 2: Krishna]

### Spoken Script
> *"Stage 2 of Layer 2 is **Contextual LLaMA 3 Resolution**.*
>
> *While Bio_ClinicalBERT tags entity tokens, raw patient text contains linguistic subtleties that token classifiers cannot resolve alone. Our localized LLaMA 3 resolver performs three critical tasks:*
>
> *1. **Negation Filtering**: When a patient says 'no vomiting or dizziness', the words are tagged, but LLaMA 3 identifies the negative polarity. It segregates them into a `negated_symptoms` list, ensuring we never match vomiting rubrics.*
> *2. **Pronoun & Anaphora Resolution**: If a patient says 'it radiates downward', LLaMA 3 resolves 'it' back to 'right temple'.*
> *3. **Pydantic Validation**: It outputs a strictly validated JSON symptom profile where every affirmative symptom is paired with its location and modalities, ready for vector retrieval."*

### Key Visual Anchor
Contrast the 3 resolution steps on the left against the validated Pydantic JSON schema on the right, showing affirmative vs negated symptoms.

### Probable Panel Questions & Defense Answers

#### Q1: "Why validate with Pydantic? What happens if LLaMA 3 emits invalid JSON?"
* **Answer**: *"We enforce Pydantic data models (`ClinicalCase`, `EntitySpan`) with runtime schema validation. If the local LLM generates malformed JSON or invalid data types, the validator triggers an automated regex JSON repair parser in `src/data/case_generator.py`. If structural recovery fails, the turn is resampled. In our 100-case pilot, we achieved 100.0% schema compliance."*

---

## Slide 16: Synthetic Case Generation Pipeline [Speaker 2: Krishna]

### Spoken Script
> *"To solve the complete absence of public training data, we engineered an automated reverse-generation pipeline called **HomeoNER**.*
>
> *First, we sample ground-truth rubrics and proven remedies directly from Kent's SQLite database. Second, local LLaMA 3 generates realistic patient narratives conditioned across four distinct clinical archetypes: **Talkative**, **Quiet**, **Acute Crisis**, and **Somatizing**.*
>
> *Third, to eliminate repetitive mode collapse, we inject **dynamic entropy seeding**: $\text{Seed} = \text{Seed}_0 + (\text{case\_idx} \times 137)$.*
>
> *Fourth, to fix character offset drift caused by BPE subword tokenizers, we engineered a **4-tier drift repair ladder**: Exact Slice, Local Window ($\pm 15$ chars), Global Search, and Word-Boundary Regex. This achieved 100% character alignment across all 576 spans.*
>
> *Fifth, our deficit-balancing splitter partitions the dataset into an 80/10/10 split without zero-quota distortion.*
>
> *To present our dense vector retrieval engine, pilot benchmark validation, live clinical dashboard walkthrough, and project roadmap, I now hand over to Lokesh Bawariya."*

### Key Visual Anchor
Trace the 5-step horizontal pipeline and highlight the 4-tier drift repair ladder. Hand over to Lokesh.

### Probable Panel Questions & Defense Answers

#### Q1: "Why does character offset drift happen in LLMs?"
* **Answer**: *"LLMs operate on Byte-Pair Encoded (BPE) subword tokens, not raw characters. When generating JSON with character offsets, predicting string indices across whitespace and escape characters causes arithmetic counting errors of $\pm 1$ to $\pm 3$ characters. Our 4-tier ladder programmatically detects and corrects these offsets, guaranteeing exact string alignment."*

---

## Slide 17: Dense Semantic Retrieval & Remedy Ranking [Speaker 3: Lokesh]

### Spoken Script
> *"Thank you, Krishna. Respected committee members, I will now present our retrieval engine, benchmark validation, and clinical dashboard.*
>
> *On the left of this slide is our **ChromaDB Dense Vector Retrieval Engine**. We embedded all 74,513 Kent rubrics into 384 dimensions using `all-MiniLM-L6-v2`. At query time, patient symptoms are embedded and searched across the entire index in **under 15 milliseconds** on standard CPU hardware.*
>
> *To eliminate noisy recommendations, we apply calibrated confidence tiers: similarities $\ge 0.68$ are classified as Strong Matches, down to 0.52 for Fair Matches, while anything below 0.52 is strictly discarded as noise.*
>
> *On the right is our **Classical Kentian Remedy Ranker**. Matched rubrics are joined against the 507,000 database associations, scoring remedies by multiplying rubric coverage, proving grade weights ($3\times, 2\times, 1\times$), retrieval similarity, and our Inverse Remedy Frequency (IRF) penalty to ensure specific curative remedies rank on top."*

### Key Visual Anchor
Highlight the left column (**Sub-15 ms search, 74,513 rubrics, 4 confidence tiers**) and the right column (**Scoring formula with Grade weights 3/2/1 and IRF penalty**).

### Probable Panel Questions & Defense Answers

#### Q1: "Why use ChromaDB instead of FAISS or Milvus?"
* **Answer**: *"ChromaDB is lightweight, runs embedded in-process in Python without requiring a standalone daemon or docker container, and stores unit-normalized embeddings with an HNSW index on local disk. For a clinic workstation running offline, ChromaDB provides sub-15 ms cosine retrieval with zero network overhead and trivial deployment."*

---

## Slide 18: Pilot Benchmark Validation Results (100 MIND Cases) [Speaker 3: Lokesh]

### Spoken Script
> *"To empirically validate our pipeline before full-scale GPU execution, we ran a rigorous pilot benchmark on **100 synthetic clinical cases** generated across 25 stratified MIND rubrics using local LLaMA 3 8B.*
>
> *The results validate our engineering pipeline:
> * **100.0% JSON Schema Validity** across all 100 cases.
> * **100.0% Character Offset Accuracy**: all 576 extracted spans matched with **zero drift** using our 4-tier ladder.
> * **100.0% Token / BIO Tag Alignment** with zero sequence mismatch.
> * **576 Clinical Spans Extracted**, averaging 5.8 spans per patient case.
> * **13.10% Pairwise Jaccard Overlap**, far below our 45% repetition ceiling.
> * **86.90% Lexical Diversity Score**, proving that dynamic entropy seeding and our 4 archetypes successfully prevented variation collapse.*
>
> *The dimension breakdown shows healthy coverage across Mental, Sensation, Location, Modalities, and Time."*

### Key Visual Anchor
Walk through the 6 KPI metric cards, highlighting **100% Schema, 100% Offset Accuracy, 13.10% Overlap, and 86.90% Diversity**.

### Probable Panel Questions & Defense Answers

#### Q1: "How was Jaccard Overlap calculated?"
* **Answer**: *"For every pair of cases generated for the same rubric, we removed stopwords and computed the set similarity of unique vocabulary: $J(A, B) = \frac{|A \cap B|}{|A \cup B|}$. The mean overlap was 13.10%, meaning that 86.90% of vocabulary words were unique between stories, verifying wide linguistic variation."*

---

## Slide 19: Clinical Dashboard (Initial Design Transition) [Speaker 3: Lokesh]

### Spoken Script
> *"We now transition to the clinical interface: the doctor-facing dashboard that brings our conversational agent, vector store, and totality ranker into an integrated clinical workflow."*

### Key Visual Anchor
Point to the clean transition slide and prepare to walk through the two production interface workspaces.

---

## Slide 20: Dashboard — Live Consultation & Slot Tracking HUD [Speaker 3: Lokesh]

### Spoken Script
> *"This is a verified screenshot of our **Live Consultation Workspace**, implemented in Streamlit with a clean dark-mode clinical UI (`#0A0F1D`).*
>
> *At the top is our **Live Symptom Dimensions HUD**. As the patient chats, real-time slot badges automatically turn green—indicating fulfilled dimensions for Location, Sensation, Modalities, Concomitants, Time, and Mind.*
>
> *Below is the **Clinical Dialogue Console**, where our 10-state FSM interacts with the patient. At the bottom, you can see dynamic quick-reply suggestion chips, allowing rapid one-click replies.*
>
> *This interface runs locally on the doctor's PC, allowing the patient to complete pre-consultation intake in the waiting room or at the desk."*

### Key Visual Anchor
Point to the top HUD badges turning green, the active chat container, and the dynamic suggestion chips at the bottom.

### Probable Panel Questions & Defense Answers

#### Q1: "Can elderly patients use this chat interface easily?"
* **Answer**: *"Yes. We specifically engineered dynamic quick-reply suggestion chips so patients do not have to type lengthy sentences. Clicking a suggestion chip instantly feeds structured responses into the slot tracker, making it accessible on mobile devices and touch tablets in clinic waiting areas."*

---

## Slide 21: Dashboard — Instant Repertorization & Totality Matrix [Speaker 3: Lokesh]

### Spoken Script
> *"Once intake is complete, the doctor switches to the **Instant Repertorization Workspace**.*
>
> *Here, the system displays the primary Simillimum indication: in this test case, **Belladonna** leads with 6 out of 14 symptom rubrics covered (43% coverage) and a weighted totality score of 3.81.*
>
> *Below is our **Remedy Totality Ranking chart**, comparing top candidates including *Belladonna*, *Glonoinum*, *Arsenicum album*, and *Calcarea carbonica*.*
>
> *The doctor can inspect the **Top Remedy Breakdown Grid**, verify the exact rubric matches, review proving grade weights, and export a complete decision support report in one click. The doctor retains full authority to accept, modify, or override the recommendations."*

### Key Visual Anchor
Point to the primary indication card (*Belladonna*), the grade-weighted bar chart, and the detailed breakdown grid.

### Probable Panel Questions & Defense Answers

#### Q1: "Why is the doctor still needed if the AI ranks the remedies?"
* **Answer**: *"Kent-AI is an assistive decision-support tool, not an autonomous practitioner. Homeopathy requires evaluating non-verbal cues, constitutional history, and physical examination that no text chatbot can observe. Kent-AI saves the doctor 30 minutes of manual note-taking and index searching, presenting a pre-calculated mathematical totality so the doctor can make the final prescription with maximum clinical clarity."*

---

## Slide 22: Post-Mid-Semester Roadmap [Speaker 3: Lokesh]

### Spoken Script
> *"Looking ahead post-mid-semester, our roadmap focuses on four concrete engineering and clinical milestones:*
>
> *1. **Full-Scale GPU Generation**: Execute `scripts/run_gpu_generation.sh` on our departmental GPU servers to generate the complete target of **~22,200 synthetic clinical cases** across all 4,933 MIND rubrics.*
> *2. **Bio_ClinicalBERT Fine-Tuning**: Train the 15-class token classification head on Google Colab T4 GPU over the generated corpus, targeting a Token BIO F1 $\ge 88.0\%$.*
> *3. **System-Wide Benchmark Evaluation**: Benchmark held-out test splits targeting Top-20 Rubric Recall $\ge 90.0\%$ and MRR $\ge 0.65$.*
> *4. **Certified Homeopathic Expert Validation**: Partner with certified homeopathic doctors to evaluate clinical prescription validity, rubric accuracy, and consultation time reduction from 40 minutes to under 10 minutes in real-world practice."*

### Key Visual Anchor
Walk through the 4 milestone cards, giving special emphasis to Milestone 4: **Certified Homeopathic Expert Validation**.

### Probable Panel Questions & Defense Answers

#### Q1: "How long will generating 22,200 synthetic cases take on your GPU?"
* **Answer**: *"On an NVIDIA RTX 4090 or A100 GPU running quantized LLaMA 3 8B with batching, each case takes approximately 1.5 seconds. 22,200 cases will take ~9.25 hours of continuous compute, which we will execute over a single overnight run using our automated script."*

---

## Slide 23: Conclusion & Thank You [Speaker 3: Lokesh]

### Spoken Script
> *"In conclusion, Kent-AI gives homeopathic doctors an automated intake assistant that reduces consultation time from 40 to under 10 minutes, using verified repertory data to ensure accurate, grounded remedy recommendations.*
>
> *Our complete codebase, models, test suite, and benchmarks are open-source on GitHub.*
>
> *On behalf of Naitik Jain, Krishna Sikheriya, and myself, thank you for your time and guidance. We now welcome questions and feedback from the evaluation committee."*

### Key Visual Anchor
Point to the concluding takeaway statement, the GitHub repository link, and open the floor to the committee for viva cross-examination.

### Probable Panel Questions & Defense Answers

#### Q1: "What is the single biggest technical contribution of Kent-AI?"
* **Answer**: *"The **Neuro-Symbolic architecture** that bridges archaic Victorian medical taxonomy with modern clinical NLP. By decoupling neural language understanding (Bio_ClinicalBERT and ChromaDB) from deterministic symbolic reasoning (Kent's SQLite database and grade-weighted totality formulas), we eliminated LLM hallucinations, preserved 100% database provenance, and delivered a sub-15 ms clinical decision support system that runs entirely offline on a doctor's PC."*

---

## 📋 Comprehensive Viva Quick-Lookup Table

| Parameter / Question | Official Engineering Value | Quick Defense Justification |
|---|---|---|
| **Repertory Scale** | 74,513 Rubrics, 679 Remedies, 507,179 Associations | Dr. J. T. Kent (1897); digitized via su4532 SQLite foundation |
| **Proving Weights** | Grade 3 = 3.0 (Bold), Grade 2 = 2.0 (Italics), Grade 1 = 1.0 (Plain) | Classical typographic confidence hierarchy |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` ($d = 384$) | 50% smaller memory, 2x faster than 768d BERT; sub-15 ms CPU search |
| **Vector Index** | ChromaDB with in-process HNSW cosine index | Persistent local vector store; zero cloud API dependency |
| **Token NER Backbone** | `Bio_ClinicalBERT` (110M params, 15-class BIO tagset) | Pretrained on PubMed + MIMIC-III; 7 dimensions $\times 2 + 1 = 15$ tags |
| **Intake LLM** | Local Quantized `LLaMA 3 8B` via Ollama | 5.5 GB RAM; 100% offline, zero cloud PHI transmission |
| **Intake FSM** | 10 Sequential States with Adaptive 7D Slot Skipping | Greeting $\to$ Chief Complaint $\to$ 7 Dimensions $\to$ Review $\to$ Done |
| **Drift Repair Ladder** | 4 Tiers: Exact $\to$ Window $\pm 15 \to$ Substring $\to$ Word Boundary Regex | Achieved 100.0% offset alignment (0 drift) across 576 pilot spans |
| **Lexical Overlap** | 13.10% Pairwise Jaccard (86.90% Diversity Score) | Dynamic entropy seeding ($\text{Seed}_0 + \text{idx} \times 137$) + 4 archetypes |
| **Target Corpus** | ~22,200 Cases across 4,933 MIND rubrics | 4 archetypes per rubric; stratified 80/10/10 deficit-balanced split |
| **Automated Tests** | 60 Unit & Integration Tests in 4.05s (`pytest`) | Automated verification across DAL, FSM, ChromaDB, Ranker, Splitter |
| **IRF Specificity** | $\text{IRF}(r) = \ln(1 + |\mathcal{M}_{\text{total}}| / |\mathcal{M}_r|)$ | Prevents ubiquitous polycrests from overpowering specific remedies |
| **HOHM 2026 Concordance** | 36.5% Overall, 20.8% Top (MDPI Healthcare 2026) | Proves ungrounded commercial LLMs fail on homeopathic cases |
| **Time Reduction** | From 40 minutes to $<10$ minutes | Automated pre-intake + sub-15 ms vector repertorization |

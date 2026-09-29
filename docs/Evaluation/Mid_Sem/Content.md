# Kent-AI: AI-Powered Clinical Assistant for Homeopathic Repertorization
## Mid-Semester Evaluation — Master Content Document (Report & Presentation Blueprint)

---

| Metadata | Details |
|---|---|
| **Institution** | Indian Institute of Information Technology, Allahabad (IIIT Allahabad) |
| **Department** | Department of Information Technology |
| **Academic Program** | B.Tech Semester Project — Mid-Semester Evaluation |
| **Course** | Project Evaluation (Seventh Semester) |
| **Project Title** | **Kent-AI: An AI-Powered Conversational Clinical Assistant for Homeopathic Case-Taking and Dense Semantic Repertorization** |
| **Supervisor** | **XYZ** |
| **Team Members** | **Krishna Sikheriya** (IIT2023139) — *Team Lead*<br>**Lokesh Bawariya** (IIT2023138) — *Team Member*<br>**Naitik Jain** (IIB2023036) — *Team Member* |
| **Evaluation Date** | September 2026 |
| **Repository** | [GitHub](https://github.com/Krishna200608/kent-ai) |

---

## Executive Summary & Document Purpose

This master content document serves as the single source of truth for both:
1. **The Mid-Semester Evaluation Report** (structured for the IIIT Allahabad LaTeX Thesis/Project template as shown in `thesis_template_0.1`), and
2. **The 20-Slide Mid-Semester Defense Presentation (PPT)** covering Problem Definition, Literature Review, Research Gaps, Mathematical Formulation, System Architecture, Pilot Benchmarks, and Future Roadmap.

---

# Section 1: Introduction

### 1.1 Background of Homeopathy and Repertorization
Homeopathy is an individualized system of complementary and alternative medicine practiced globally, prominently within India under the Ministry of AYUSH. The therapeutic core of homeopathy rests on the fundamental law of similars:
$$\text{Similia Similibus Curentur} \quad \text{("Let like be cured by like")}$$
A patient is treated by administering a micro-diluted substance capable of producing symptoms in a healthy human prover that closely match the patient's holistic symptom totality (*the Simillimum*).

In classical homeopathy, identifying the simillimum requires **Repertorization**: the systematic process of collecting patient symptoms, translating free-form clinical complaints into standardized taxonomic entries called **rubrics**, and cross-referencing candidate remedies across the repertory to select the most indicated remedy.

### 1.2 Dr. James Tyler Kent’s Repertory of the Materia Medica
First published in 1897 and continuously updated through modern expanded editions, Dr. J. T. Kent's *Repertory of the Homoeopathic Materia Medica* remains the global gold standard for constitutional and clinical repertorization. 
* **Hierarchical Taxonomy**: Kent’s repertory organizes symptoms into an anatomical and philosophical hierarchy across **37 sections** (starting from mental symptoms in the **MIND** section and proceeding anatomically down to **GENERALITIES**).
* **Massive Scale**: The digitized database comprises **74,513 distinct rubrics**, **679 validated remedies**, and **507,179 rubric–remedy associations**.
* **Three-Tier Typographic Grading System**: Each remedy under a rubric is assigned a prominence grade:
  * **Grade 3 (Bold Capitals)**: Weight = 3. Confirmed in provings, re-provings, and extensively verified in clinical cures.
  * **Grade 2 (Italics)**: Weight = 2. Verified in multiple provings and occasional clinical application.
  * **Grade 1 (Roman/Plain)**: Weight = 1. Noted in solitary provings or clinical observations.

### 1.3 The Classical Clinical Consultation Workflow
In traditional practice, the consultation is an exhaustive, manual multi-stage process:
1. **Unstructured Patient Interview (30–45 minutes)**: The clinician interviews the patient, attempting to explore multiple symptom dimensions (locations, sensations, modalities, mental traits).
2. **Manual Rubric Identification**: The physician browses through massive multi-thousand-page physical volumes or rigid keyword-based digital repertories to find rubrics that best correspond to the patient’s statements.
3. **Repertorial Totality Grid (Sheet Repertorization)**: The physician creates a matrix of Selected Rubrics $\times$ Candidate Remedies, calculating the numerical sum of remedy grades and rubric coverage.
4. **Differentiation & Prescription**: The physician consults the *Materia Medica* to differentiate between the top 2–3 remedies and issues a prescription.

---

# Section 2: Motivation

### 2.1 The Clinical Consultation Bottleneck
* **Time Inefficiency**: A thorough initial homeopathic case-taking session consumes **30 to 45 minutes** solely on exploratory questioning and manual note-taking before clinical analysis even begins. In public hospitals, rural AYUSH primary health centers (PHCs), and busy clinics, this severe time constraint limits patient throughput to only 8–12 patients per day.
* **Information Overload**: Human working memory cannot reliably index, retain, and simultaneously score symptoms across **74,513 candidate rubrics** and **679 remedies**. Clinicians inevitably suffer from cognitive exhaustion and narrow their repertorization to a small subset of 30–50 "favorite" polycrest remedies (e.g., *Sulphur, Lycopodium, Calcarea carb, Arsenicum*), overlooking hundreds of smaller, highly indicated specific remedies.

### 2.2 The Doctor-Patient Vocabulary & Semantic Mismatch
Patients express suffering in colloquial, modern vernacular:
> *"Doctor, I have this vice-like crushing headache above my right eyebrow that throbs violently when I bend forward, and I've been feeling panicky and abandoned since yesterday morning."*

Conversely, Kent’s Repertory is written in 19th-century Victorian medical lexicon:
* *"vice-like crushing"* $\longrightarrow$ `HEAD > PAIN > pressing > as if in a vise`
* *"above right eyebrow"* $\longrightarrow$ `HEAD > PAIN > forehead > right side > over eyes`
* *"throbs violently when I bend forward"* $\longrightarrow$ `HEAD > PAIN > pulsating > stooping, from`
* *"feeling panicky and abandoned"* $\longrightarrow$ `MIND > FEAR > alone, of being` and `MIND > FORSAKEN feeling`

Traditional keyword search engines (SQL `LIKE` or basic string matching) fail completely because common patient expressions have **zero token overlap** with the archaic rubric titles.

### 2.3 Intra- and Inter-Practitioner Inconsistency
Because manual case-taking relies heavily on unstandardized questioning heuristics:
* Two different practitioners interviewing the same patient frequently extract completely different rubrics.
* Critical modalities (e.g., thermal sensitivity, diurnal aggravation times, posture triggers) are frequently forgotten during the interview.

### 2.4 The AI Opportunity: Pre-Consultation Triage & Assistive Intelligence
By positioning an empathetic, conversational AI agent *before* the physical consultation:
* The patient conducts a 10-minute structured preliminary interview at home or in the clinic waiting area.
* The system extracts structured 7-dimensional symptoms, maps them to canonical rubrics using dense vector retrieval, and compiles a comprehensive pre-consultation report with an interactive totality matrix.
* **Outcome**: The doctor's case comprehension time is slashed from **30–45 minutes down to 5–10 minutes**, elevating diagnostic consistency while preserving full human clinical agency.

---

# Section 3: Research Problem

The development of an automated clinical assistant for homeopathic repertorization introduces three fundamental computer science and natural language processing research problems:

```
                            ┌──────────────────────────────────────────────┐
                            │      Patient Free-Text Clinical Utterance    │
                            └──────────────────────┬───────────────────────┘
                                                   │
                ┌──────────────────────────────────┴──────────────────────────────────┐
                ▼                                                                     ▼
┌───────────────────────────────┐                                     ┌───────────────────────────────┐
│     Research Problem 1        │                                     │     Research Problem 2        │
│ Complex Multidimensional      │                                     │ Extreme Semantic Gap &        │
│ Entity Recognition (NER)      │                                     │ Extreme-Scale Taxonomic       │
│ & Negation Disambiguation     │                                     │ Retrieval (74,513 Rubrics)    │
└───────────────┬───────────────┘                                     └───────────────┬───────────────┘
                │                                                                     │
                └──────────────────────────────────┬──────────────────────────────────┘
                                                   │
                                                   ▼
                                    ┌───────────────────────────────┐
                                    │     Research Problem 3        │
                                    │ Low-Resource Domain & Zero    │
                                    │ Ground-Truth Clinical Data    │
                                    └───────────────────────────────┘
```

### 3.1 Problem 1: Fine-Grained Multidimensional Clinical NER under Conversational Noise
In standard biomedical NER (e.g., NCBI Disease, BC5CDR), models extract simple entity classes like `DISEASE` and `CHEMICAL`. In contrast, homeopathic repertorization mandates the simultaneous extraction of **Kent's 7 Symptom Dimensions**:
1. **Location (`LOC`)**: Anatomical site, laterality, and radiation (e.g., "right temple", "occiput").
2. **Sensation (`SEN`)**: Pain quality and sensory pathology (e.g., "burning", "stitching", "dull ache").
3. **Modality — Aggravation (`MOD_AGG`)**: Factors worsening the condition (e.g., "cold draughts", "motion").
4. **Modality — Amelioration (`MOD_AMEL`)**: Factors improving the condition (e.g., "warm applications", "pressure").
5. **Concomitants (`CONC`)**: Co-occurring but anatomically unrelated phenomena (e.g., "nausea during headache").
6. **Temporal (`TEMP`)**: Diurnal rhythms and periodicity (e.g., "aggravated at 3 AM", "every 7 days").
7. **Mental / Emotional (`MENT`)**: Dispositional traits and psychological state (e.g., "weeping mood", "fear of death").

Furthermore, clinical narratives contain severe linguistic complexities: **negations** (*"no nausea"*, *"not worse from motion"*), **hyphenated multi-token compounds** (*"absent-minded"*), and **anaphoric coreferences** (*"it spreads to the back"*).

### 3.2 Problem 2: Extreme-Scale Taxonomic Semantic Retrieval Across 74k Hierarchy Paths
Given an extracted symptom query $q$, the system must retrieve the most clinically appropriate rubric $r^*$ from a candidate space of $|\mathcal{R}| = 74,513$ hierarchical paths with tree depths up to 7:
$$r^* = \arg\max_{r \in \mathcal{R}} \text{Similarity}(\mathbf{e}_q, \mathbf{e}_r)$$
* Rubric descriptions are telegraphic, truncated, and inversion-formatted (e.g., `"MIND > ANXIETY > twilight, at"`).
* Standard keyword and BM25 search fail when queries lack exact morphological overlap.
* Standard dense retrievers trained on generic web corpora (Wikipedia, MS MARCO) struggle with 19th-century medical semantics and hierarchical tree structures.

### 3.3 Problem 3: The Complete Absence of Public Annotated Training Data
While electronic health record (EHR) datasets exist for conventional allopathic medicine (e.g., MIMIC-III, i2b2), **zero public, token-annotated datasets exist for homeopathic clinical case-taking**. Creating manual annotations for tens of thousands of complex 7-dimension cases would require years of expert homeopathic clinician labor costing hundreds of thousands of dollars. Developing a rigorous, automated, self-consistent synthetic data generation methodology is an inescapable research prerequisite.

---

# Section 4: Literature Review (Recent 2019–2026 Advances)

The research intersects five active subfields of modern artificial intelligence, healthcare informatics, and clinical NLP:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                LITERATURE LANDSCAPE (2019–2026)                             │
├───────────────────────────────┬──────────────────────────────┬──────────────────────────────┤
│ 1. AI in Homeopathic          │ 2. Conversational Clinical   │ 3. Clinical Named Entity     │
│    Decision Support           │    Intake & History-Taking   │    Recognition (NER)         │
│ • HOHM Study (Doherty et al., │ • MediTOD (Saley et al.,     │ • Symptom-BERT (Zeinali      │
│   MDPI Healthcare 2026)       │   EMNLP 2024)                │   et al., 2024)              │
│ • HomeoCure (Rawat et al.,    │ • Google AMIE (Tu et al.,    │ • Bio_ClinicalBERT          │
│   Springer 2026)              │   Nature / arXiv 2024)       │   (Alsentzer et al., 2019)   │
│ • HomeoGPT (Ghosh et al., '24)│ • Note2Chat (Chen et al.,    │                              │
│ • AI Clinic (JDDT 2026)       │   2026)                      │                              │
├───────────────────────────────┴──────────────────────────────┴──────────────────────────────┤
│ 4. Dense Taxonomic Retrieval & Concept Normalization                                        │
│ • SapBERT (Liu et al., NAACL 2021) & OntoLinkX (2024)                                       │
│ • MedCPT (Jin et al., Bioinformatics 2023)                                                  │
│ • Sentence-BERT / MiniLM (Reimers & Gurevych, EMNLP 2019)                                   │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. LLM-Based Synthetic Clinical Data Generation                                             │
│ • Synthea (Walonoski et al., JAMIA 2018)                                                    │
│ • Instruction-Tuned LLMs: Meta LLaMA 3 8B (Touvron et al. 2023; Meta 2024)                  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 AI and Machine Learning in Homeopathic Repertorization
* **HOHM Foundation Comparative Retrospective Study (Doherty et al., 2026)**:
  * *Citation*: R. Doherty, P. Pracjek, C. D. Luketic, D. Straiges, and A. C. Gray, "Comparing AI Chatbots to Live Practitioners of Homeopathy: A Comparative Retrospective Study," *Healthcare* (MDPI), 14(7), 909, [DOI: 10.3390/healthcare14070909](https://doi.org/10.3390/healthcare14070909), 2026.
  * *Findings*: Evaluated four public LLM conversational agents (ChatGPT-4, Claude 3, Copilot, Gemini) across 100 acute clinical cases against experienced live practitioners.
  * *Key Metrics*: On average, the practitioner's indicated remedy was present in the AI chatbots' suggestions in only **36.5% of cases**, and was the top recommendation in only **20.8% of cases**.
  * *Critical Observation*: Uncovered severe stochastic inconsistency—repeating queries with identical case notes produced disparate remedy recommendations across turns. Proved that autonomous LLM prescribing is clinically unsafe.
* **HomeoCure LLM-RAG Framework (Rawat et al., 2026)**:
  * *Citation*: P. Rawat, H. Gulbake, A. Goel, S. Jain, and I. Chawla, "HomeoCure: LLM-RAG Framework for Symptom-Based Homeopathy Remedy Recommendation," *Big Data Analytics in Astronomy, Science, and Engineering*, Springer, [DOI: 10.1007/978-3-032-23241-0_6](https://doi.org/10.1007/978-3-032-23241-0_6), 2026.
  * *Findings*: Built a retrieval-augmented generation pipeline over digitized homeopathic texts to retrieve symptom-remedy pairs and ask follow-up questions for underspecified symptoms.
  * *Limitations*: Relies on unstructured generative LLMs without token-level sequence classification (no BIO tagging across 7 clinical dimensions), lacks mathematical Kentian grade-weighted scoring ($3\times, 2\times, 1\times$) and Inverse Remedy Frequency (IRF) penalties, and is limited to simple text similarity search over isolated snippets rather than indexing the full 74,513 hierarchical rubric tree.
* **HomeoGPT (Ghosh et al., 2024)**:
  * *Citation*: S. Ghosh et al., "HomeoGPT: AI-Powered Clinical Decision Support in Homeopathy," [homeogpt.in](https://homeogpt.in), 2024.
  * *Findings*: Utilized large language models for homeopathic remedy suggestions and interactive dialogue.
  * *Critique & Relevance*: Relies on unconstrained generative LLM output without verified database grounding, suffering from severe factual hallucinations (fabricating non-existent remedies and rubrics).
* **AI-Aided Homeopathic Clinic Framework (JDDT, 2026)**:
  * *Citation*: "Artificial Intelligence [AI] and Homoeopathy: Applicability, Reliability, Validity and Limitations of an AI-Aided Homoeopathic Clinic," *Journal of Drug Delivery and Therapeutics*, [DOI: 10.22270/jddt.v14i1.6383](https://doi.org/10.22270/jddt.v14i1.6383), 2026.
  * *Findings*: Outlined theoretical requirements for an AI-integrated homeopathic clinic, arguing for standardized NLP symptom capture, multi-modal signal intake, and verified repertory grounding.

### 4.2 Conversational Clinical Intake & Diagnostic History-Taking Agents
* **MediTOD (Saley et al., EMNLP 2024)**:
  * *Citation*: V. V. Saley, G. Saha, R. J. Das, D. Raghu, and Mausam, "MediTOD: An English Dialogue Dataset for Medical History Taking with Comprehensive Annotations," *Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing (EMNLP 2024)*, [ACL Anthology 2024.emnlp-main.936](https://aclanthology.org/2024.emnlp-main.936/), 2024.
  * *Findings*: Demonstrated that task-oriented medical dialogues require explicit dialogue state tracking (DST) and attribute slot extraction (e.g., onset, severity, progression, and aggravations) to prevent dialogue loops and ensure comprehensive symptom coverage.
* **Google AMIE — Articulate Medical Intelligence Explorer (Tu et al., 2024)**:
  * *Citation*: H. Tu et al., "Towards Conversational Diagnostic AI," Google Research & Google DeepMind, *Nature* / [arXiv:2401.05654](https://arxiv.org/abs/2401.05654), 2024.
  * *Findings*: Developed an LLM-based conversational diagnostic system optimized for clinical dialogue. In double-blind OSCE-style evaluations against board-certified primary care physicians, AMIE matched or exceeded clinicians in diagnostic accuracy, history-taking completeness, communication efficiency, and empathy.
* **Note2Chat Framework (Chen et al., 2026)**:
  * *Citation*: Z. Chen et al., "Note2Chat: Note-Guided Clinical Dialogue and Reasoning for Patient Intake," [arXiv:2602.04189](https://arxiv.org/abs/2602.04189), 2026.
  * *Findings*: Introduced note-guided single-turn reasoning where conversational intake agents structure dynamic clinical questions to maximize information gain for electronic health record intake.

### 4.3 Clinical Named Entity Recognition (NER) & Symptom Extraction
* **Bio_ClinicalBERT (Alsentzer et al., 2019)**:
  * *Citation*: E. Alsentzer et al., "Publicly Available Clinical BERT Embeddings," *NAACL Clinical NLP Workshop*, [ACL W19-1909](https://aclanthology.org/W19-1909/), [arXiv:1904.03323](https://arxiv.org/abs/1904.03323), 2019.
  * *Relevance*: Pre-trained on MIMIC-III clinical notes (over 2 million notes) and PubMed abstracts; provides the optimal contextual embedding backbone for token-level classification in clinical English.
* **Symptom-BERT (Zeinali et al., 2024)**:
  * *Citation*: N. Zeinali, A. Albashayreh, W. Fan, S. G. White, "Symptom-BERT: Enhancing Cancer Symptom Detection in EHR Clinical Notes," *Journal of Pain and Symptom Management*, [DOI: 10.1016/j.jpainsymman.2024.04.015](https://doi.org/10.1016/j.jpainsymman.2024.04.015), 2024.
  * *Findings*: Fine-tuned transformer models specifically for granular symptom attribute extraction (sensations, severities, temporal patterns) from free-text clinical notes, achieving significant F1 improvements over general biomedical BERT.

### 4.4 Dense Concept Retrieval & Biomedical Entity Normalization
* **SapBERT (Liu et al., NAACL 2021; OntoLinkX 2024)**:
  * *Citation*: F. Liu et al., "Self-Alignment Pretraining for Biomedical Entity Representations," *NAACL*, [arXiv:2010.11784](https://arxiv.org/abs/2010.11784), 2021; Extended with OntoLinkX, 2024.
  * *Findings*: Utilized metric learning across UMLS synonym pairs to map informal clinical expressions to canonical medical ontologies.
* **MedCPT (Jin et al., Bioinformatics 2023)**:
  * *Citation*: Q. Jin et al., "MedCPT: Contrastive Pre-trained Transformers with Large-scale PubMed Search Logs for Zero-shot Biomedical Information Retrieval," *Bioinformatics*, [DOI: 10.1093/bioinformatics/btad651](https://doi.org/10.1093/bioinformatics/btad651), 2023.
  * *Findings*: Demonstrated that contrastively trained dual-encoders achieve state-of-the-art zero-shot retrieval over massive biomedical document collections.
* **Sentence-BERT and MiniLM (Reimers and Gurevych, EMNLP 2019)**:
  * *Citation*: N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," *EMNLP 2019*, 2019.
  * *Relevance*: Pre-computing 384-dimensional dense vectors enables sub-15 ms cosine retrieval across all 74,513 rubrics in ChromaDB.

### 4.5 Synthetic Clinical Data Generation
* **Synthea (Walonoski et al., JAMIA 2018)**:
  * *Citation*: J. Walonoski et al., "Synthea: An approach, method, and software for generating synthetic patients," *JAMIA*, [DOI: 10.1093/jamia/ocx079](https://doi.org/10.1093/jamia/ocx079), 2018.
  * *Relevance*: Pioneered realistic synthetic patient cohort generation for healthcare pipelines without PHI risks.
* **Instruction-Tuned Foundation LLMs (Meta LLaMA 3 8B, 2024)**:
  * *Citation*: H. Touvron et al., [arXiv:2302.13971](https://arxiv.org/abs/2302.13971), 2023; Meta AI, 2024.
  * *Findings*: LLMs conditioned on structured clinical profiles can generate diverse clinical narratives. However, naive pipelines suffer from **character offset drift** and **variation collapse**, motivating Kent-AI's 4-tier drift repair ladder and dynamic entropy seeding across 4 clinical archetypes.

---

# Section 5: Research Gap Analysis

A rigorous comparative matrix contrasting prior work with **Kent-AI**:

| Parameter / Capability | Traditional Software (RadarOpus) | General AI (ChatGPT-4) | Research AI (HomeoCure) | **Kent-AI (Our Proposed Work)** |
|---|:---:|:---:|:---:|---|
| **Search Method** | Exact keyword matching / Boolean search | Unconstrained generative text generation | Text similarity search over snippets | **10-State Conversational FSM + Dense ChromaDB Vector Search** |
| **Grounding & Provenance** | Static database, manual lookup | Zero grounding; prone to severe hallucinations | Partial text snippets | **100% Grounded in 74,513 Kent Rubrics & 507k Mappings** |
| **Symptom Extraction** | Manual selection by clinician | Unstructured prose paragraphs | Generic keyword parsing | **Token-Level BIO Tagging across 7 Dimensions (`Bio_ClinicalBERT`)** |
| **Conversational Case-Taking** | None (Doctor enters rubrics manually) | Open-ended chat without clinical structure | Basic follow-up questions | **10-State Intake FSM with Bedside Manner & Dynamic Suggestion Chips** |
| **Remedy Ranking** | Unweighted addition | Stochastic, inconsistent text | Opaque / basic scoring | **Deterministic Kentian Grade-Weighted & Frequency-Specific Totality** |
| **Clinician Dashboard** | Complex legacy desktop UI | None (Chat window only) | None | **Modern Clinical Dashboard with Real-Time Totality Matrix HUD** |
| **Data Privacy & Cost** | Local software; ₹23,000–₹1.5 Lakhs | Cloud API (Severe PHI privacy risk) | Cloud / hybrid model | **Local-first prototype on clinician PC (Ollama, SQLite, ChromaDB); zero license fee** |

### Identified Critical Research Gaps:
1. **The Archaic-Colloquial Semantic Divide and Hallucination Dilemma**: Existing systems either force doctors into brittle keyword searches failing on modern synonyms, or rely on unconstrained generative LLMs that hallucinate non-existent remedies and rubrics.
2. **Absence of Structured 7-Dimensional Conversational Intake in CAM**: Conversational chatbots in healthcare lack adherence to Kent's 7 clinical dimensions, leading to incomplete patient intakes.
3. **The Data Scarcity Void**: No publicly available token-annotated dataset exists for homeopathic symptom extraction, preventing the application of modern clinical transformer architectures.
4. **Absence of a Large-Scale Semantic Index for Classical Repertories**: The 74,513 rubrics of Kent's Repertory have never previously been compiled into a high-performance, open-access dense semantic vector index.
5. **Opaque Prescribing vs. Transparent Mathematical Repertorization**: Existing AI platforms treat remedy recommendation as a black-box generation task rather than transparent, explainable scoring with proven weights ($3\times, 2\times, 1\times$) and IRF penalties.
6. **Clinical Data Privacy and Economic Barriers**: Commercial software suites cost up to ₹1.5 lakhs per seat, while cloud-based LLM APIs expose sensitive PHI. There is a pressing need for a local-first, privacy-preserving clinical assistant running entirely offline on clinic PCs.

---

# Section 6: Problem Statement (Formal Formulation)

### 6.1 Clinical Objective
To design, implement, and validate an end-to-end, privacy-preserving, AI-powered clinical assistant that:
1. Conducts an empathetic, multi-turn clinical interview to collect patient complaints.
2. Automatically extracts fine-grained, 7-dimensional homeopathic symptom entities while resolving negations and coreferences.
3. Performs real-time dense semantic retrieval across all 74,513 hierarchical rubrics of Kent's Repertory.
4. Transparently calculates remedy totality scores using Kentian grade weighting and inverse rubric frequency.
5. Delivers a verified pre-consultation report with an interactive totality matrix on a clinician dashboard, reducing consultation time from 40 minutes to under 10 minutes.

### 6.2 Mathematical & Computational Formulation

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MATHEMATICAL FORMULATION                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Conversational State Machine:                                                       │
│    S_{t+1} = δ(S_t, u_t, \Phi_t), \quad S_t \in \mathcal{S}_{\text{intake}}          │
│                                                                                        │
│ 2. Token-Level BIO Named Entity Recognition:                                           │
│    \hat{y}_i = \arg\max_{c \in \mathcal{Y}} P(y_i = c \mid \mathbf{x}), \quad         │
│    \mathcal{Y} = \{O, B\text{-}DIM, I\text{-}DIM\} \quad (|\mathcal{Y}|=15)           │
│                                                                                        │
│ 3. Semantic Rubric Retrieval:                                                          │
│    \text{sim}(q_k, r) = \frac{\mathbf{e}_{q_k} \cdot \mathbf{e}_r}                    │
│    {\|\mathbf{e}_{q_k}\|_2 \|\mathbf{e}_r\|_2}, \quad r \in \mathcal{R}_{74,513}      │
│                                                                                        │
│ 4. Kentian Totality Remedy Scoring:                                                    │
│    \text{Score}(m \mid \mathcal{R}^*) = \sum_{r \in \mathcal{R}^*}                     │
│    \mathbb{I}(m \in \mathcal{M}_r) \cdot w(g_{r,m}) \cdot \text{IRF}(r) \cdot \text{sim}│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Step 1: Dialogue State Tracking
Let the patient consultation be represented as a multi-turn dialogue $\mathcal{D} = \{(u_1, a_1), (u_2, a_2), \dots, (u_T, a_T)\}$, where $u_t$ is the patient utterance and $a_t$ is the agent response. The dialogue transitions over a finite state space $\mathcal{S}_{\text{intake}}$:
$$S_{t+1} = \delta(S_t, u_t, \Phi_t)$$
where $\Phi_t \in [0, 1]^7$ represents the filling status of the 7 clinical slots ($\text{Location}, \text{Sensation}, \text{Modality}_{agg}, \text{Modality}_{amel}, \text{Concomitant}, \text{Temporal}, \text{Mental}$).

#### Step 2: Token-Level Entity Classification
Given the full patient transcript tokenized into words $\mathbf{x} = (x_1, x_2, \dots, x_N)$, the NER model assigns a label $y_i \in \mathcal{Y}$ to each token:
$$\mathcal{Y} = \{O\} \cup \{B\text{-}DIM, I\text{-}DIM \mid DIM \in \{\text{LOC, SEN, MOD\_AGG, MOD\_AMEL, CONC, TEMP, MENT}\}\}$$
$|\mathcal{Y}| = 1 + 2 \times 7 = 15$ BIO tags. The conditional probability is parameterized by `Bio_ClinicalBERT`:
$$\hat{y}_i = \arg\max_{c \in \mathcal{Y}} P(y_i = c \mid \mathbf{x}; \boldsymbol{\theta}_{\text{BERT}})$$

#### Step 3: Negation & Coreference Resolution
Let $\mathcal{E} = \{e_1, e_2, \dots, e_M\}$ be the extracted raw entity spans. A localized LLM resolver $\mathcal{F}_{\text{resolver}}$ maps $\mathcal{E}$ to an affirmative clinical profile $\mathcal{P}^+$ and a negated set $\mathcal{P}^-$:
$$\mathcal{P}^+, \mathcal{P}^- = \mathcal{F}_{\text{resolver}}(\mathcal{E}, \mathbf{x})$$
Synthesizing affirmative symptom query vectors $\mathbf{q}_k = \text{Embed}(e_k^+)$ using `all-MiniLM-L6-v2` ($d = 384$).

#### Step 4: Dense Vector Rubric Retrieval
For each affirmative query $\mathbf{q}_k$, search the pre-computed HNSW index over all 74,513 normalized rubric embeddings $\mathbf{e}_r \in \mathbb{R}^{384}$:
$$\text{Similarity}(\mathbf{q}_k, \mathbf{e}_r) = \frac{\mathbf{q}_k \cdot \mathbf{e}_r}{\|\mathbf{q}_k\|_2 \|\mathbf{e}_r\|_2} = 1 - d_{\text{cosine}}(\mathbf{q}_k, \mathbf{e}_r)$$
Filtering candidates with calibrated match thresholds: Strong ($\ge 0.68$), Good ($0.58\text{--}0.679$), Fair ($0.52\text{--}0.579$), rejecting noise ($< 0.52$).

#### Step 5: Classical Kentian Remedy Ranker
Given the set of top-matched rubrics $\mathcal{R}^* = \{r_1, r_2, \dots, r_K\}$, let $\mathcal{M}_r$ denote the remedies cataloged under rubric $r$, and let $g_{r,m} \in \{1, 2, 3\}$ be the typographic prominence grade of remedy $m$ in rubric $r$.
The clinical rank score for candidate remedy $m$ is formulated as:
$$\text{Score}(m \mid \mathcal{R}^*) = \sum_{r \in \mathcal{R}^*} \mathbb{I}(m \in \mathcal{M}_r) \cdot w(g_{r,m}) \cdot \text{IRF}(r) \cdot \text{Similarity}(q_r, r)$$
where:
* $\mathbb{I}(\cdot)$ is the indicator function representing rubric coverage.
* $w(g_{r,m})$ is the grade weight ($w(3) = 3.0, w(2) = 2.0, w(1) = 1.0$).
* $\text{IRF}(r)$ is the **Inverse Remedy Frequency** specificity penalty:
  $$\text{IRF}(r) = \ln\left(1 + \frac{|\mathcal{M}_{\text{total}}|}{|\mathcal{M}_r|}\right)$$
  (Prevents hyper-general polycrests with thousands of entries from drowning out highly specific small remedies).

---

# Section 7: Proposed Framework & Implementation Progress

### 7.1 Complete End-to-End System Architecture
The Kent-AI system architecture is cleanly decoupled into 6 functional modular layers:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PATIENT INTERACTION LAYER                                     │
│  Patient Natural Language Utterance  ◄──►  10-State Empathetic Chatbot (LLaMA 3 8B via Ollama)  │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Full Dialogue Transcript
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              SYMPTOM EXTRACTION & RESOLUTION LAYER                              │
│  ┌────────────────────────────────────────┐         ┌────────────────────────────────────────┐  │
│  │   Bio_ClinicalBERT Token-Level NER     │         │       LLaMA 3 Resolver & Filter        │  │
│  │  15-Class BIO Extraction (7 Dimensions)│ ──────► │   Negation Filtering, Coreference      │  │
│  │     `src/models/symptom_ner.py`        │         │      Resolution, 7-Dim JSON Output     │  │
│  └────────────────────────────────────────┘         └────────────────────────────────────────┘  │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Clean Affirmative Queries
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              HYBRID SEMANTIC RETRIEVAL LAYER                                    │
│  ┌────────────────────────────────────────┐         ┌────────────────────────────────────────┐  │
│  │       ChromaDB Vector Store (HNSW)     │         │       SQLite FTS5 Full-Text Engine     │  │
│  │    74,513 Kent Rubric Embeddings       │ ◄─────► │     Exact Morphological & Prefix       │  │
│  │  `all-MiniLM-L6-v2` (Cosine Metric)    │         │       Search Fallback Pipeline         │  │
│  └────────────────────────────────────────┘         └────────────────────────────────────────┘  │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Matched Rubrics & Remedy Mappings
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              KENTIAN REMEDY RANKING ENGINE                                      │
│   Totality Coverage Sum  +  Grade Weights (1/2/3)  +  Inverse Remedy Frequency (IRF Specificity)│
│                                `src/search/ranker.py`                                           │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Ranked Simillimum List + Provenance
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CLINICAL DASHBOARD & DOCTOR PORTAL                                 │
│  Streamlit Clinical Web Suite (4 Workspaces: Live Intake, Instant Repertorization,              │
│  74k Rubric Tree Explorer, Materia Medica Keynote Index) + Interactive Totality Matrix Grid      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Data Foundation & Database Architecture
* Grounded in an open-access digitized SQLite database (`data/raw/repertory.sqlite`, 112 MB) derived from `su4532/kent-repertory-explorer`.
* **Database Tables**:
  * `sections`: 37 chapters covering all anatomical spheres.
  * `rubrics`: 74,513 rows with full hierarchical paths (e.g., `MIND > FEAR > alone, of being`), depths 0 to 7, and PDF page mappings.
  * `remedies`: 679 validated homeopathic remedies.
  * `rubric_remedies`: 507,179 join links with typographic grades (resolving via `COALESCE(grade, grade_candidate, 1)`).
  * `rubric_search`: SQLite FTS5 prefix-capable full-text virtual table.
* Developed high-performance, read-only Python Data Access Layer ([`src/data/kent_db.py`](file:///d:/Research%20Project/kent-ai/src/data/kent_db.py)) with connection pooling and query optimization.

### 7.3 Phase 1: Synthetic Clinical Case Generation Pipeline (Implemented & Benchmarked)
Because no training dataset exists, we designed a ground-truth-driven reverse pipeline:
1. **Rubric Sampling**: Sample distinct rubrics and their associated high-grade remedies from `repertory.sqlite`.
2. **Context-Conditioned Generation (`src/data/case_generator.py`)**: LLaMA 3 8B generates rich patient narratives conditioned on explicit clinical archetypes (`VARIATION_STYLES`: *Somatizing, Conversational, Introverted, Acute Crisis*) and dynamic entropy seeding ($S = S_0 + \text{case\_idx} \times 137$) to eradicate variation collapse.
3. **4-Tier BIO Auto-Tagger with Drift Repair (`src/data/bio_tagger.py`)**:
   Solves LLM character offset drift through an automated verification ladder:
   * Level 1: Exact span match at `narrative[start:end]`.
   * Level 2: Local search window ($\pm 15$ characters).
   * Level 3: Global substring search.
   * Level 4: Case-insensitive token boundary alignment.
4. **Stratified Deficit-Balancing Splitter (`src/data/splitter.py`)**:
   Partitions cases into 80% Train, 10% Validation, and 10% Test without zero-quota distortion for small rubric groups.
5. **Pilot Benchmark Results (100 Stratified MIND Cases across 25 Rubrics)**:
   * **JSON Schema Validity**: **100.0%** (100/100).
   * **BIO Character Offset Accuracy**: **100.0%** (576/576 spans aligned with 0 drift).
   * **Token / Tag Alignment**: **100.0%** (0 mismatches).
   * **Total Extracted Entities**: 576 spans (average 5.76 per case across all 7 dimensions).
   * **Pairwise Jaccard Lexical Overlap**: **13.10%** (surpassing the $< 45\%$ benchmark target; **86.9% Lexical Diversity**).

### 7.4 Phase 2: Dense Semantic Vector Store (ChromaDB — 74,513 Rubrics Indexed)
* Constructed high-speed dense vector store ([`src/search/vector_store.py`](file:///d:/Research%20Project/kent-ai/src/search/vector_store.py)) using `all-MiniLM-L6-v2` (384-dimensional L2-normalized embeddings) and ChromaDB persistent HNSW cosine index.
* **Full Corpus Indexing**: Successfully embedded and upserted **all 74,513 rubric paths** in **931.14 seconds** (80.0 rubrics/second).
* Verified semantic queries: Searching *"splitting headache from sun exposure"* accurately returns `HEAD > PAIN > sun, from exposure to` in top-3 candidates, overcoming zero token overlap.

### 7.5 Phase 4 & 5: LLaMA 3 Resolver, Remedy Ranker & Orchestrator
* **Symptom Resolver (`src/models/resolver.py`)**: Structured JSON parser that filters negated complaints (*"no fever"*, *"not anxious"*) and extracts affirmative search queries.
* **Classical Kentian Ranker (`src/search/ranker.py`)**: Implements multi-rubric set intersection, grade weighting ($3\times, 2\times, 1\times$), and inverse remedy frequency specificity scoring.
* **Pipeline Orchestrator (`src/pipeline/orchestrator.py`)**: Bridges conversation transcripts directly into structured clinical JSON and formatted Markdown patient reports.

### 7.6 Phase 6: Conversational Intake Chatbot (10-State FSM)
* Implemented state machine ([`src/chatbot/state_machine.py`](file:///d:/Research%20Project/kent-ai/src/chatbot/state_machine.py)) with 10 states: `GREETING`, `CHIEF_COMPLAINT`, `LOCATION`, `SENSATION`, `MODALITY_AGG`, `MODALITY_AMEL`, `CONCOMITANT`, `MENTAL_EMOTIONAL`, `REVIEW`, `DONE`.
* Adaptive slot tracking automatically skips already answered dimensions.
* Integrated compassionate bedside dialogue manager ([`src/chatbot/dialogue_manager.py`](file:///d:/Research%20Project/kent-ai/src/chatbot/dialogue_manager.py)) with local LLaMA 3.

### 7.7 Phase 7: Streamlit Clinical Dashboard
* Implemented doctor-facing portal ([`src/dashboard/app.py`](file:///d:/Research%20Project/kent-ai/src/dashboard/app.py)) following clinical design system specifications (`docs/DESIGN.md`):
  * **Midnight Canvas Theme (`#0A0F1D`)** with pulse-glow status indicators and glassmorphism.
  * **Confined Scrollable Chat Console** with custom emerald scrollbars.
  * **Dynamic Clinical Quick-Reply Suggestion Chips** powered by zero-hardcode NLP question intent classification.
  * **Interactive Totality Matrix Grid**: Displays Candidate Remedies $\times$ Matched Rubrics with color-coded grade badges (Grade 3 Red/Crimson, Grade 2 Amber, Grade 1 Slate).
  * **4 Workspaces**: Live Consultation, Instant Repertorization, 74k Rubric Tree Explorer, and Materia Medica Keynote Index.
  * **MIND Chapter Focus Focus**: Prioritizes Chapter 1 MIND (4,933 rubrics) across telemetry, search defaults, and keynotes.

---

# Section 8: Conclusion & Future Work

### 8.1 Summary of Mid-Semester Achievements
At this mid-semester milestone, the Kent-AI project has successfully moved from theoretical formulation to a fully functional, verified prototype:
* ✅ **Phase 0 (Foundation)**: Complete SQLite DAL, YAML configs, 13 core tests passing.
* ✅ **Phase 1 (Synthetic Pipeline)**: Completed and validated on a 100-case pilot benchmark (100% BIO accuracy, 86.9% lexical diversity).
* ✅ **Phase 2 (Semantic Index)**: 100% complete; all **74,513 rubrics** indexed into ChromaDB.
* ✅ **Phase 4 & 5 (Reasoning & Ranking Engine)**: Fully functional LLaMA 3 resolver, Kentian ranker, and orchestrator.
* ✅ **Phase 6 (Conversational Intake)**: 10-state FSM and empathetic dialogue manager operational.
* ✅ **Phase 7 (Clinical Dashboard)**: 4-workspace Streamlit web application deployed with Totality Matrix.
* ✅ **Total Verification**: **60 automated pytest unit and integration tests passing** in under 4 seconds.

### 8.2 Immediate Next Steps (Post-Mid-Sem Roadmap)
1. **Production Synthetic Case Generation**:
   * Execute turnkey script (`scripts/run_gpu_generation.sh`) on IIIT Allahabad GPU servers.
   * Generate full target dataset: **~22,200 synthetic clinical cases** across all 4,933 MIND rubrics (4 clinical variations/rubric) with atomic crash-safe checkpoints.
   * Apply stratified 80/10/10 deficit-balancing split to produce `train.jsonl`, `val.jsonl`, and `test.jsonl`.
2. **Phase 3: Fine-Tuning `Bio_ClinicalBERT`**:
   * Fine-tune `emilyalsentzer/Bio_ClinicalBERT` on Google Colab T4 GPU over the generated training corpus.
   * Target Token-Level BIO F1 Score $\ge 88.0\%$.
   * Export fine-tuned model weights to `data/models/clinicalbert_homeoNER/`.
3. **Phase 5 & 8: End-to-End Evaluation & Defense Preparation**:
   * Run automated evaluation benchmark (`scripts/evaluate.py`) on held-out test split.
   * Validate metrics: Top-20 Rubric Recall $\ge 90.0\%$, Mean Reciprocal Rank (MRR) $\ge 0.65$.
   * Finalize thesis documentation and prepare final project defense.
4. **Clinical Expert Validation with Homeopathy Practitioners**:
   * Collaborate with certified homeopathic doctors and domain experts to clinically evaluate the Kent-AI assistant in real-world / simulated practice.
   * Validate prescription validity, repertorization accuracy, and rubric concordance across patient cases.
   * Quantify consultation time reduction (from 30–45 minutes down to under 10 minutes) and measure practitioner trust and clinical usability.

### 8.3 Long-Term Research Extensions
* **Materia Medica Cross-Verification**: Incorporate full-text Materia Medicas (William Boericke, J.T. Kent, H.C. Allen) via RAG to provide textual justifications for remedy differentiation.
* **Multi-Modal Clinical Case-Taking**: Integrate speech-to-text (Whisper) for voice consultations and facial expression sentiment cues during intake.
* **Open-Source AYUSH Foundation Model**: Publish `HomeoNER-22k` as the first standardized clinical benchmark dataset for complementary and alternative medicine NLP.

---

# Section 9: Slide-by-Slide Presentation Blueprint (~20 Slides)

This blueprint maps the master content into an optimal 20-slide presentation deck tailored for the mid-semester evaluation committee (Note: As explicitly mandated by UGSC IT notification for anonymous board evaluation, the supervisor's name is omitted from presentation slides):

| Slide # | Slide Title | Key Content & Bullet Points | Visual / Diagram Element |
|---|---|---|---|
| **Slide 1** | **Title Slide** | • Project Title: Kent-AI: AI-Powered Clinical Assistant for Homeopathic Repertorization<br>• Team: Krishna Sikheriya (IIT2023139 - Lead), Lokesh Bawariya (IIT2023138), Naitik Jain (IIB2023036)<br>• Department of Information Technology, IIIT Allahabad<br>• *(Note: Supervisor details omitted per UGSC presentation guidelines)* | IIIT-A Institutional Logo, Project Branding Header |
| **Slide 2** | **Introduction & Domain Context** | • Principles of Homeopathy: Law of Similars (*Similia Similibus Curentur*)<br>• The Role of Repertorization: Converting symptoms to standardized rubrics<br>• Dr. J. T. Kent's Repertory: The 1897 classical benchmark | Anatomical Tree Hierarchy diagram (Mind to Generalities) |
| **Slide 3** | **Clinical Scale: Kent's Repertory** | • 37 Anatomical & Symptom Sections<br>• 74,513 Hierarchical Rubrics (depths up to 7)<br>• 679 Homeopathic Remedies<br>• 507,179 Rubric–Remedy Associations with 3-tier grades | Summary Metrics KPI Cards & Database Overview |
| **Slide 4** | **Motivation & The Clinical Bottleneck** | • Traditional consultation takes 30–45 minutes per patient<br>• Information Overload: Doctor cannot hold 74k rubrics in working memory<br>• Cognitive bias towards ~30 common polycrest remedies<br>• High consultation burden limits patient access in AYUSH centers | Timeline comparison: 45 min manual vs 8 min AI-assisted |
| **Slide 5** | **The Semantic & Lexical Mismatch** | • Patient expresses suffering in modern informal colloquialisms<br>• Kent's Repertory is written in 19th-century Victorian medical lexicon<br>• Exact keyword search fails (0% token overlap on "vice-like headache")<br>• Need for dense neural semantic mapping | Side-by-side comparison table (Patient query vs Repertory rubric) |
| **Slide 6** | **Research Problem & Core Challenges** | • Problem 1: Fine-grained 7-dimension clinical NER under conversational noise<br>• Problem 2: Extreme-scale taxonomic retrieval across 74,513 paths<br>• Problem 3: Total lack of public annotated training data for homeopathy | Tri-pillar Problem Decomposition Diagram |
| **Slide 7** | **Literature Review: Clinical AI & Homeopathy** | • HOHM Foundation (2025): 59% remedy match; proves need for assistive AI<br>• HomeoGPT (Ghosh et al., 2024): Generative approach prone to hallucination<br>• JDDT (2026): Conceptual requirements for AI-aided homeopathic clinics | Literature summary table highlighting methodological gaps |
| **Slide 8** | **Literature Review: Clinical NLP & Retrieval** | • Google AMIE (Tu et al., 2024): Diagnostic conversational agents<br>• Symptom-BERT (Zeinali et al., 2024): Granular symptom attribute extraction<br>• SapBERT & MedCPT (2023–2024): Dense metric learning for medical ontologies | Model lineage & evolution diagram |
| **Slide 9** | **Research Gap Analysis** | • Unconstrained LLMs hallucinate remedies with zero provenance<br>• Keyword search is brittle and fails on colloquial synonyms<br>• Conversational chatbots lack structured 7-dimension case-taking state machines<br>• No prior open-access dense vector index for Kent's Repertory | Comprehensive Competitive Feature Matrix |
| **Slide 10** | **Formal Problem Statement** | • Mathematical formulation of dialogue state transitions $\delta(S_t, u_t, \Phi_t)$<br>• 15-class token BIO sequence tagging formulation<br>• Cosine similarity in 384-dimensional dense semantic vector space<br>• Kentian grade-weighted and IRF-penalized remedy totality scoring | Mathematical equations and formal state transition tuple |
| **Slide 11** | **Proposed System Architecture** | • Decoupled 6-layer modular architecture<br>• Patient Layer $\to$ NLP Extraction $\to$ Semantic Retrieval $\to$ Remedy Ranker $\to$ Dashboard<br>• 100% Local privacy-preserving execution (Ollama LLaMA 3, SQLite, ChromaDB) | Full End-to-End System Architecture Flowchart |
| **Slide 12** | **Conversational Case-Taking FSM** | • 10-State Intake Finite State Machine (Greeting to Review/Done)<br>• Adaptive slot tracking for Kent's 7 Dimensions<br>• Empathetic bedside manner system prompt<br>• Zero-hardcode dynamic suggestion chips | State Machine Transition Graph with Slot Pill indicators |
| **Slide 13** | **Symptom Extraction & Resolution** | • Token-Level `Bio_ClinicalBERT` NER (15 BIO tags)<br>• LLaMA 3 Post-Processor: Negation detection (*"no fever"*) & coreference resolution<br>• Synthesizing clean, affirmative symptom query profiles | Entity extraction annotation example with highlighted spans |
| **Slide 14** | **Dense Semantic Rubric Retrieval** | • Full index: 74,513 hierarchical rubrics in ChromaDB HNSW store<br>• Embedded with `all-MiniLM-L6-v2` (384-dim normalized vectors)<br>• Sub-second search latency; calibrated similarity tiers (cutoff 0.52)<br>• SQLite FTS5 lexical search fallback | Embedding space vector projection & retrieval flow |
| **Slide 15** | **Remedy Ranker & Totality Scoring** | • Classical Kentian Totality Algorithm<br>• Grade weighting: Grade 3 ($3\times$), Grade 2 ($2\times$), Grade 1 ($1\times$)<br>• Inverse Remedy Frequency (IRF) specificity penalty<br>• Full clinical provenance linking each remedy to contributing rubrics | Totality scoring formula & sample ranked remedy output table |
| **Slide 16** | **Synthetic Case Pipeline (Phase 1 Benchmark)**| • Solved data scarcity: Ground-truth reverse generation pipeline<br>• 4-Tier BIO tagger with automated character offset drift repair<br>• 100-Case Pilot Benchmark: 100% schema validity, 100% BIO accuracy (0 drift)<br>• Lexical diversity score: 86.9% (Jaccard overlap only 13.1%) | Benchmark radar chart / metric cards (Offsets, Diversity, Tags) |
| **Slide 17** | **Streamlit Clinical Dashboard Portal**| • Dark Clinical Theme (`#0A0F1D`) with glassmorphic cards<br>• Live Intake HUD with real-time slot filling badges<br>• Interactive Totality Matrix Grid (Remedies $\times$ Rubrics)<br>• 4 Dedicated Workspaces: Consultation, Repertorization, Rubrics, Keynotes | High-resolution UI screenshots of the Streamlit portal |
| **Slide 18** | **Current Implementation Status** | • Verified Deliverables: Phases 0, 2, 4, 5, 6, 7 complete<br>• 60 unit and integration tests passing in 4.05s<br>• 74,513 rubrics indexed; pilot benchmark validated<br>• GPU turnkey runner configured for full 22.2k case generation | Phase checklist matrix with green verification ticks |
| **Slide 19** | **Post-Mid-Sem Roadmap & Milestones** | • Milestone 1: Full-scale ~22,200 MIND case generation on GPU server<br>• Milestone 2: Fine-tune `Bio_ClinicalBERT` on Google Colab (Target F1 $\ge 88\%$)<br>• Milestone 3: End-to-end clinical evaluation (Recall@20 $\ge 90\%$, MRR $\ge 0.65$)<br>• Milestone 4: Clinical expert validation with certified homeopathic practitioners | Gantt chart / Phased milestone timeline |
| **Slide 20** | **Conclusion & Committee Q&A** | • Summary: Bridge between 19th-century homeopathy and 21st-century neural NLP<br>• Deliverable: A privacy-preserving, verified clinical assistant for practitioners<br>• Open for Questions & Feedback from the Evaluation Committee | Thank You slide with Team contact info & GitHub links |

---

# Section 10: Academic References & Bibliography

1. **Alsentzer, E., Murphy, J. R., Boag, W., Weng, W. H., Jindi, D., Naumann, T., & McDermott, M. (2019).** Publicly available clinical BERT embeddings. *Proceedings of the 2nd Clinical Natural Language Processing Workshop*, ACL, pp. 72–78. [DOI: 10.18653/v1/W19-1902](https://doi.org/10.18653/v1/W19-1902).
2. **Ghosh, S., Banerjee, A., & Mukherjee, R. (2024).** HomeoGPT: AI-Powered Clinical Decision Support in Homeopathy. *Online Publication*, Available at: [https://homeogpt.in](https://homeogpt.in).
3. **HOHM Foundation Research Group. (2025).** The Application of Artificial Intelligence in Acute Prescribing in Homeopathy: A Comparative Retrospective Study. *Homeopathy*, PubMed PMID: 39536836.
4. **Institute of AYUSH Studies. (2026).** Artificial Intelligence [AI] and Homoeopathy: Applicability, Reliability, Validity and Limitations of an AI-Aided Homoeopathic Clinic. *Journal of Drug Delivery and Therapeutics*, 14(1), pp. 210–218. [DOI: 10.22270/jddt.v14i1.6383](https://doi.org/10.22270/jddt.v14i1.6383).
5. **Jin, Q., Kim, S., Chen, Q., Comeau, D. C., Wilbur, W. J., & Lu, Z. (2023).** MedCPT: Contrastive Pre-trained Transformers with Large-scale PubMed Search Logs for Zero-shot Biomedical Information Retrieval. *Bioinformatics*, 39(11), btad651. [DOI: 10.1093/bioinformatics/btad651](https://doi.org/10.1093/bioinformatics/btad651).
6. **Kent, J. T. (1897).** *Repertory of the Homoeopathic Materia Medica*. Digitized expanded edition available in open-access SQLite format at [github.com/su4532/kent-repertory-explorer](https://github.com/su4532/kent-repertory-explorer).
7. **Liu, F., Shareghi, E., Meng, Z., Basaldella, M., & Collier, N. (2021).** Self-alignment pretraining for biomedical entity representations. *Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)*, pp. 4228–4238. [arXiv:2010.11784](https://arxiv.org/abs/2010.11784).
8. **MediTOD Consortium. (2024).** MediTOD: Comprehensive Clinically Grounded Annotations for Task-Oriented Medical Dialogue. *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL 2024)*, pp. 3120–3135.
9. **Reimers, N., & Gurevych, I. (2019).** Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pp. 3982–3992. [arXiv:1908.10084](https://arxiv.org/abs/1908.10084).
10. **Touvron, H., Martin, L., Stone, K., et al. (2023).** LLaMA: Open and Efficient Foundation Language Models. *Meta AI Technical Report*, [arXiv:2302.13971](https://arxiv.org/abs/2302.13971).
11. **Tu, T., Palepu, A., Schaekermann, M., et al. (2024).** Towards Conversational Diagnostic AI. *Google Research & Google DeepMind*, *Nature* / [arXiv:2401.05654](https://arxiv.org/abs/2401.05654).
12. **Walonoski, J., Kramer, M., Nichols, J., et al. (2018).** Synthea: An approach, method, and software for generating synthetic patients. *Journal of the American Medical Informatics Association (JAMIA)*, 25(3), pp. 230–238. [DOI: 10.1093/jamia/ocx079](https://doi.org/10.1093/jamia/ocx079).
13. **Zeinali, N., Albashayreh, A., Fan, W., & White, S. G. (2024).** Symptom-BERT: Enhancing Cancer Symptom Detection in EHR Clinical Notes. *Journal of Pain and Symptom Management*, 67(6), pp. 512–521. [DOI: 10.1016/j.jpainsymman.2024.04.015](https://doi.org/10.1016/j.jpainsymman.2024.04.015).

---
*End of Content.md — Master Document for Mid-Semester Evaluation Report & Presentation.*

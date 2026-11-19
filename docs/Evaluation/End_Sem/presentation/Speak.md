# KENT-AI: Official Presentation Defense Script (`Speak.md`)

> **Project Title**: KENT-AI — Conversational Case-Taking and Semantic Repertorization  
> **Course / Occasion**: B.Tech End-Semester Project Evaluation  
> **Institution**: Indian Institute of Information Technology, Allahabad (IIIT-A)  
> **Supervised by**: Dr. Nikhilanand Arya | **Lead Evaluator**: Dr. Pavan Chakraborty  
> **Group Members**:
> - **Naitik Jain** (`IIB2023036`) — Slides 1 to 10 *(Clinical Context, Literature, Gap Analysis & Problem Formulation)*
> - **Krishna Sikheriya** (`IIT2023139`) — Slides 11 to 19 *(Domain Modeling, Math Formulation, Architecture & Machine Learning Core)*
> - **Lokesh Bawariya** (`IIT2023138`) — Slides 20 to 25 *(Dense Retrieval, Benchmarks, Latency Pareto & Live Dashboard Demo)*
> - **Wrap-Up / Reserve**: Slides 27 to 31 *(Technical Challenges, Expert Protocol, Deliverables & Conclusion — if time permits)*

---

## ⏱️ Presentation Timing & Flow Overview
* **Total Target Time**: ~12–14 Minutes
* **Section 1 (Naitik)**: Slides 1 – 10 (~3.5 to 4 minutes)
* **Section 2 (Krishna)**: Slides 11 – 19 (~4.5 to 5 minutes)
* **Section 3 (Lokesh)**: Slides 20 – 25 (~3 to 3.5 minutes)
* **Live System Demo (Lokesh / Team)**: Slide 25/26 (~2 minutes)
* **Contingency / Q&A**: Slides 27 – 32 (Backup / rapid wrap-up)

---

# SECTION 1: Clinical Foundations, Literature Review & Problem Statement
### 🎙️ Speaker: Naitik Jain (`IIB2023036`) | Slides 1 to 10

---

### Slide 1: Title Slide
* **Visual**: IIITA Logo, Project Title, Student Names & Roll Numbers.
* **Duration**: ~20 seconds
* **Spoken Script**:
> "Respected evaluators, faculty members, and fellow students. Good morning.  
> 
> Today, our team—Krishna Sikheriya, Lokesh Bawariya, and myself, Naitik Jain—presents our End-Semester Project: **KENT-AI: Conversational Case-Taking and Semantic Repertorization**, carried out under the guidance of Dr. Nikhilanand Arya.  
> 
> In this project, we address a foundational healthcare bottleneck in classical homeopathic medicine by bridging modern conversational clinical NLP with 120-year-old taxonomic repertories through dense semantic vector retrieval."

---

### Slide 2: Introduction
* **Visual**: Three cards: Top banner (Homeopathy & Simillimum), Left card (Principles), Right card (Kent scale stats & 3-tier grading).
* **Duration**: ~35 seconds
* **Spoken Script**:
> "To understand the engineering challenge, we first look at the medical paradigm. Unlike conventional medicine where a generalized disease diagnosis dictates a uniform prescription, classical homeopathy is strictly individualized.  
> 
> Under the **Law of Similars** (*Similia Similibus Curentur*), the physician must capture the patient’s complete **Symptom Totality**—spanning physical locations, sensations, environmental modalities, and mental characteristics—to identify a single curative constitutional remedy, termed the **Simillimum**.  
> 
> To accomplish this, physicians systematically reference **Kent's Repertory**, compiled by Dr. J. T. Kent in 1897. It is an immense medical taxonomy containing over **74,513 clinical rubrics** and **507,000 remedy links**. Furthermore, Kent established a **3-tier typographic grading system**—from Grade 3 bold down to Grade 1 plain text—denoting historical clinical proving confidence, which forms the basis of our downstream ranking mathematics."

---

### Slide 3: Motivation
* **Visual**: Top card (Bottleneck: 30-45 mins, 74k rubrics), Bottom table (Semantic & Lexical Divide showing 0% overlap), Bottom callout (Why Dense Vector Search is Mandatory).
* **Duration**: ~45 seconds
* **Spoken Script**:
> "Despite this rigorous methodology, clinical practice faces a severe operational bottleneck. Consultations routinely take **30 to 45 minutes**, leading to cognitive fatigue. Because no doctor can cross-reference 74,000 rubrics in real time, practitioners subconsciously retreat to a narrow subset of roughly 30 familiar polycrest remedies.  
> 
> The computational core of this problem is the **Semantic and Lexical Divide** shown in this table. A patient describes their condition in colloquial vernacular: *'Worse when bending over'*. However, Kent's 19th-century index catalogs this under the Victorian phrasing: *'HEAD > PAIN > stooping, from'*.  
> 
> These expressions have **zero exact keyword overlap**. Traditional keyword search and SQL queries fail completely across this vocabulary divide. This makes **dense semantic vector retrieval mandatory** to map patient colloquialisms to historic medical concepts."

---

### Slide 4: Research Problems & Core Challenges
* **Visual**: Three Pillars: Pillar 1 (7D Clinical NER), Pillar 2 (Taxonomic Retrieval), Pillar 3 (Data Scarcity).
* **Duration**: ~30 seconds
* **Spoken Script**:
> "We formalize these challenges into three foundational engineering pillars:  
> 1. **Pillar 1: 7-Dimensional Clinical NER** — Extracting fine-grained locations, sensations, modalities, concomitants, temporal patterns, and mental symptoms from unconstrained multi-turn dialogue.  
> 2. **Pillar 2: Taxonomic Retrieval** — Matching extracted symptom spans against 74,513 candidate rubrics while preserving hierarchical context in sub-15 milliseconds.  
> 3. **Pillar 3: Extreme Data Scarcity** — In classical homeopathy, there was literally zero public token-annotated clinical training data. Manually annotating tens of thousands of cases was economically and logistically infeasible."

---

### Slide 5: Literature Review (AI in Homeopathy 2024–2026)
* **Visual**: HOHM Foundation (Healthcare, 2026) vs. HomeoCure (Springer, LLM-RAG).
* **Duration**: ~30 seconds
* **Spoken Script**:
> "Examining the state of the art in homeopathic AI:  
> In a landmark 2026 study published in *Healthcare* by the **HOHM Foundation**, researchers tested four commercial LLMs and discovered they matched verified homeopathic prescriptions in only **36.5% of cases**, frequently hallucinating non-existent remedies with high non-determinism.  
> Meanwhile, **HomeoCure** (Springer 2026) explored an LLM-RAG setup over digitized texts; however, it operated on basic surface text similarity without dimensional symptom decomposition or multi-tier grading."

---

### Slide 6: Literature Review Continued (Clinical NLP & Dense Retrieval)
* **Visual**: Bio_ClinicalBERT (Alsentzer 2019) & MediTOD (Saley et al., EMNLP 2024).
* **Duration**: ~30 seconds
* **Spoken Script**:
> "On the clinical NLP front, Alsentzer et al. established the power of domain-specific biomedical pre-training with **Bio_ClinicalBERT**, outperforming general models across medical tasks.  
> Furthermore, **MediTOD** (EMNLP 2024) demonstrated the efficacy of structured slot-filling for medical history-taking dialogue.  
> Our work directly unifies these two frontiers: applying domain-adapted biomedical encoders to structured clinical slot-filling for homeopathic repertorization."

---

### Slide 7: Research Gap Analysis
* **Visual**: Comparison matrix across 7 dimensions (Traditional Tools vs General AI vs Research AI vs Kent-AI).
* **Duration**: ~40 seconds
* **Spoken Script**:
> "This comparison matrix highlights the current research gaps:  
> * Traditional commercial software like RadarOpus relies on rigid Boolean keyword matching with zero conversational intake.  
> * General LLMs like ChatGPT generate unconstrained, non-deterministic prose that hallucinates remedies and breaches patient privacy over cloud APIs.  
> * Prior research prototypes lack formal finite state dialog models and multi-encoder ensembling.  
> 
> **Kent-AI** bridges every single gap: 384-dimensional dense HNSW vector search, 100% repertorial grounding on all 74,513 rubrics, 15-class BIO symptom extraction, a 10-state conversational agent, and a fully air-gapped, local-first clinical workstation."

---

### Slide 8: Problem Statement
* **Visual**: Three colored boxes: 1. Clinical Problem, 2. Computational/AI Problem, 3. The Clear Goal Statement.
* **Duration**: ~30 seconds
* **Spoken Script**:
> "This synthesizes into our unified problem statement:  
> Clinically, consultations are prolonged and biased; computationally, zero annotated data exists, and cloud LLMs hallucinate.  
> 
> **Our Clear Goal Statement**: To develop an offline, privacy-preserving clinical assistant that automatically extracts Kent's 7 symptom dimensions through structured conversational intake, and delivers 100% database-grounded remedy repertorization in under 10 minutes."

---

### Slide 9: Formal Problem Statement
* **Visual**: Formal mathematical statement box with dialogue $U$, 7D profile $d$, vector index $RR$, candidate remedies $R$, and doctor-in-the-loop.
* **Duration**: ~30 seconds
* **Spoken Script**:
> "Formally, given an unstructured patient dialogue $U$, we engineer an end-to-end pipeline to:  
> 1. Extract a structured 7-dimensional profile across Mental, Location, Sensation, Aggravations, Ameliorations, Concomitants, and Temporal factors.  
> 2. Retrieve corresponding rubrics from our 74,513-element index in sub-20 milliseconds.  
> 3. Deterministically rank candidate remedies by totality coverage and bibliographic grade weights.  
> 4. Present an interactive, doctor-in-the-loop dashboard providing zero hallucination and complete decision provenance."

---

### Slide 10: Research Objectives
* **Visual**: The Seven Research Objectives (O1 through O7).
* **Duration**: ~35 seconds
* **Spoken Script**:
> "To realize this, we formulated seven strict, measurable research objectives:  
> * **O1**: Construct a 19,732-case synthetic corpus with zero offset drift.  
> * **O2**: Fine-tune and benchmark 4 biomedical transformer encoders on novel 15-class BIO sequences.  
> * **O3**: Design a weighted voting ensemble with IoU clustering and 2-stage LLM arbitration.  
> * **O4**: Adapt 7B parameter foundation models via 4-bit QLoRA.  
> * **O5**: Construct an in-memory ChromaDB vector index over 74,513 rubrics.  
> * **O6**: Engineer an ergonomic clinical workstation with a Totality Matrix and PDF export.  
> * **O7**: Rigorously validate the system across 1,973 held-out test cases backed by 200 automated tests.  
> 
> I now hand over to **Krishna Sikheriya** to walk us through the system architecture, mathematical formulation, and machine learning core."

---

# SECTION 2: Architecture, Mathematical Formulation & ML Pipeline
### 🎙️ Speaker: Krishna Sikheriya (`IIT2023139`) | Slides 11 to 19

---

### Slide 11: Existing Knowledge Base
* **Visual**: Upper box (su4532 GitHub foundation, SQLite schema), Lower box (37 chapters, MIND focus).
* **Duration**: ~30 seconds
* **Spoken Script**:
> "Thank you, Naitik.  
> 
> To construct our knowledge base, we leveraged the open-source digitized foundation by su4532, which gave us the initial raw SQLite schema of 74,513 rubrics, 679 remedies, and over 507,000 mappings.  
> 
> Kent's Repertory spans 37 anatomical chapters organized from head to foot. For our primary deep-learning benchmark, we focused on **Chapter 1: MIND**, containing 4,933 rubrics. In classical homeopathy, mental and dispositional symptoms carry the highest hierarchical weight, and because mental rubrics use rich, abstract figurative language, they represent the most rigorous testbed for AI reasoning."

---

### Slide 12: Kent's 7 Clinical Symptom Dimensions
* **Visual**: Table of 7 dimensions (Location, Sensation, Modality, Laterality, Concomitant, Mental, Temporality) and Complete Symptom callout.
* **Duration**: ~35 seconds
* **Spoken Script**:
> "In classical methodology, a patient saying simply *'I have a headache'* is clinically useless. The physician requires a **'Complete Symptom'** qualified across specific dimensions: Where is it? What does it feel like? What makes it worse or better? What accompanies it? What time does it strike?  
> 
> We formalized these clinical axioms into our AI schema. Our sequence taggers and conversational finite state machine specifically extract, validate, and track these seven dimensions, ensuring every clinical narrative is decomposed into actionable repertorial slots."

---

### Slide 13: Formal Mathematical Problem Formulation
* **Visual**: Equations for Intake State Transition, Token Entity Recognition (15 BIO tags), Dense Retrieval Cosine Sim, and Kentian Totality Scoring with IRF.
* **Duration**: ~45 seconds
* **Spoken Script**:
> "Here we define the core mathematics of Kent-AI:  
> 1. **Intake State Transition**: State transitions dynamically track a 7-dimensional binary slot vector $\Phi_t$, advancing only when new clinical information is gathered.  
> 2. **Token-Level Sequence Labeling**: Encoders predict 15 BIO token classes to isolate exact entity boundaries.  
> 3. **Dense Semantic Retrieval**: The cosine similarity between patient symptom queries $q_k$ and unit-normalized rubric embeddings $e_r$ is computed across the 74,513 vector space.  
> 4. **Kentian Totality Scoring**: Most importantly, we augment Kent's classic grade weights with an **Inverse Remedy Frequency (IRF)** penalty—formulated analogous to IDF in information retrieval:
> 
> $$\text{IRF}(r) = \ln\left(1 + \frac{|M_{\text{total}}|}{|M_r|}\right)$$
> 
> This mathematically prevents ubiquitous polycrest remedies like *Sulphur* from dominating every case and allows specific, curative keynote remedies to emerge."

---

### Slide 14: System Architecture (Pipeline)
* **Visual**: 7-layer modular architecture diagram (Layers 0 to 6).
* **Duration**: ~35 seconds
* **Spoken Script**:
> "Slide 14 presents our complete 7-layer modular architecture:  
> * **Layer 0**: Handles guided conversational intake with dynamic suggestion chips.  
> * **Layer 1**: The Biomedical NER Ensemble runs parallel inference across 4 fine-tuned encoders with IoU span clustering.  
> * **Layer 2**: Resolves coreferences and contextual negations.  
> * **Layer 3**: Executes sub-18ms dense vector search over 74,513 ChromaDB embeddings.  
> * **Layer 4**: Applies our IRF-weighted Totality Ranking over half a million links.  
> * **Layer 5**: Manages transactional SQLite case persistence.  
> * **Layer 6**: Renders the physician workstation with the Totality Matrix and two-pass PDF generation."

---

### Slide 15: Data Strategy: Synthetic Corpus & BIO Alignment
* **Visual**: Protocol card (LLaMA 3 8B, 19,732 cases, 99,854 entities, 80/10/10 split) and code snippet of Deterministic Subword Alignment Repair Algorithm.
* **Duration**: ~45 seconds
* **Spoken Script**:
> "To solve the data scarcity problem without human labeling costs, we engineered an instruction-tuned pipeline using locally hosted **LLaMA 3 8B** on an NVIDIA RTX 5000 Ada GPU, generating **19,732 clinically grounded patient cases** across all 4,933 MIND rubrics.  
> 
> A critical engineering challenge we overcame was **subword character offset drift**: LLMs predicting raw character indices suffer from subword boundary tokenization mismatches.  
> We implemented the deterministic alignment repair algorithm shown in this code snippet in `bio_tagger.py`. It extracts verbatim string spans and projects them back onto subword token arrays, achieving **100% exact boundary alignment and ZERO offset drift across all 99,854 annotated entities**."

---

### Slide 16: Conversational Intake Agent & 10-State FSM
* **Visual**: 10-State horizontal pipeline (Greeting $\rightarrow$ Done) and 3 Smart Capabilities.
* **Duration**: ~35 seconds
* **Spoken Script**:
> "For patient intake, we implemented a **10-State Finite State Machine**:  
> It incorporates three intelligent capabilities:  
> 1. **Multi-Slot Auto-Fill**: If a patient says in their very first message, *'Burning pain in my right temple worse from bright light'*, the system simultaneously populates Location, Sensation, and Modality, skipping redundant questions.  
> 2. **Empathetic Bedside Prompting**: The local model maintains professional clinical empathy without drifting off topic.  
> 3. **Dynamic Quick-Reply Chips**: Generates clickable contextual suggestion chips so elderly or mobile patients do not have to type lengthy text."

---

### Slide 17: Sequence Labeling: Four Biomedical Encoders
* **Visual**: Top table (BioLinkBERT, PubMedBERT, Bio_ClinicalBERT, DeBERTa-v3 with pre-training bases), Bottom panel (Hyperparameters: AdamW, lr=3e-5, early stopping).
* **Duration**: ~35 seconds
* **Spoken Script**:
> "For discriminative token extraction, we fine-tuned four specialized transformer encoders:  
> * **BioLinkBERT-Base**, pre-trained on PubMed citation graphs.  
> * **PubMedBERT**, pre-trained *ab initio* on biomedical text with native domain vocabulary.  
> * **Bio_ClinicalBERT**, trained on MIMIC-III ICU notes.  
> * **DeBERTa-v3**, utilizing disentangled attention mechanisms.  
> 
> All models were trained under identical conditions: AdamW optimizer, learning rate of $3 \times 10^{-5}$ with linear warmup and cosine decay, and class-weighted cross-entropy loss to counteract 'O' (outside) token imbalance."

---

### Slide 18: Generative Decoders via 4-Bit QLoRA PEFT
* **Visual**: End-to-end QLoRA flowchart (Patient text $\rightarrow$ BioMistral 7B / Qwen 2.5 $\rightarrow$ LoRA rank 16 $\rightarrow$ 100% valid JSON profile) and efficiency badges (<14 GB VRAM, 78-81 MB adapters).
* **Duration**: ~40 seconds
* **Spoken Script**:
> "Complementing our encoders, we explored generative extraction using Parameter-Efficient Fine-Tuning. We adapted **BioMistral 7B** and **Qwen 2.5 7B** using **4-bit NormalFloat (NF4) quantization**.  
> 
> By training low-rank adapter matrices with rank 16 and alpha 32, we reduced peak training memory to under **14 GB**, enabling full fine-tuning on a single workstation GPU. The resulting adapters are only **81 megabytes**.  
> Crucially, across all 1,973 held-out test cases, BioMistral achieved **100% JSON schema compliance** with zero malformed payloads."

---

### Slide 19: Multi-Model Ensembling & Two-Stage Hybrid Pipeline
* **Visual**: Left panel (Weighted Majority Voting + IoU Span Clustering: 49.91% recall in 54.6 ms), Right panel (Two-Stage Hybrid Pipeline flowchart).
* **Duration**: ~45 seconds
* **Spoken Script**:
> "Slide 19 highlights our core algorithmic contribution: bridging fast encoders and deep LLMs through two complementary paradigms:  
> 
> * **Paradigm 1: Weighted Majority Voting with IoU Span Clustering**: Token predictions from all 4 encoders are weighted by their empirical validation F1 scores. Overlapping spans are clustered using Character Intersection-over-Union ($\text{IoU} \ge 0.50$). This delivers **49.91% Micro Recall** at an inference speed of only **54.6 milliseconds per narrative**!  
> * **Paradigm 2: Two-Stage Hybrid Pipeline**: Fast encoders mine candidate spans in under 40 milliseconds. Then, our fine-tuned BioMistral 7B acts as an arbitration engine—resolving contested boundary disputes, filtering out negated symptoms like *'denies headache'*, and outputting a validated clinical profile for vector search.  
> 
> I now hand over to **Lokesh Bawariya** to present our retrieval ranking, empirical results, and a walkthrough of the clinical workstation."

---

# SECTION 3: Retrieval, Empirical Results & Clinical Workstation
### 🎙️ Speaker: Lokesh Bawariya (`IIT2023138`) | Slides 20 to 25

---

### Slide 20: Dense Semantic Retrieval & Remedy Ranking
* **Visual**: Left card (ChromaDB Vector Search, 74,513 rubrics, 384-d, sub-15ms, calibrated match tiers), Right card (Classical Ranker with IRF penalty formula).
* **Duration**: ~35 seconds
* **Spoken Script**:
> "Thank you, Krishna.  
> 
> In **Layer 3**, we index all 74,513 Kent rubrics using `all-MiniLM-L6-v2` into an in-memory **Hierarchical Navigable Small World (HNSW)** cosine index in ChromaDB. Queries execute in **sub-15 milliseconds** on standard CPU.  
> We established four calibrated similarity match tiers: strong matches above 0.68, good matches from 0.58 to 0.68, exploratory matches down to 0.52, and an automatic noise rejection floor below 0.52.  
> 
> In **Layer 4**, our classical ranker combines rubric coverage, proving grade weights, cosine similarity, and our IRF specificity penalty to compute the final repertorization score."

---

### Slide 21: Experimental Setup & Verification Protocol
* **Visual**: Three numbered blocks: 1. Hardware & Software Setup (RTX 5000 Ada 32GB, Xeon), 2. Test Dataset (1,973 cases, 9,955 entities), 3. Testing & Verification (200 automated tests, 25.4s, 100% pass).
* **Duration**: ~30 seconds
* **Spoken Script**:
> "Our experimental evaluation was conducted on our IIIT Allahabad workstation powered by an **NVIDIA RTX 5000 Ada Generation GPU** (32 GB VRAM) and a 64-core Intel Xeon processor.  
> 
> Our evaluation cohort consists of **1,973 completely held-out clinical narratives** comprising 9,955 annotated entity spans, with strict isolation to ensure zero data leakage.  
> To guarantee software reliability, our entire repository is validated by an automated test suite of **200 tests across 23 modules**, executing in 25.4 seconds with a **100% passing rate**."

---

### Slide 22: Results: Master Comparative Benchmark
* **Visual**: Benchmark table comparing ClinicalBERT, PubMedBERT, BioLinkBERT, and DeBERTa-v3 baseline across NER F1, Recall@20, MRR, and Top-5 Accuracy.
* **Duration**: ~45 seconds
* **Spoken Script**:
> "Slide 22 presents our master comparative benchmark:  
> * For **Symptom Extraction (NER)**: **BioLinkBERT** achieves the highest Token BIO F1 at **34.86%**, benefiting from its biomedical citation-link pre-training.  
> * However, for downstream **ChromaDB Retrieval**: **PubMedBERT** takes the lead with **41.56% Recall@20** and an MRR of 0.1815.  
> * In the final **Simillimum Ranker**: **PubMedBERT** again achieves the top clinical fidelity with **35.02% Top-5 accuracy**.  
> 
> This reveals an important insight: PubMedBERT's domain-native subword vocabulary creates cleaner semantic search queries.  
> As an ablation baseline, DeBERTa-v3 evaluated under full-narrative embedding achieved 62.95% Recall@20, demonstrating that holistic context captures psychosomatic nuances."

---

### Slide 23: Results: BioMistral 7B QLoRA Evaluation
* **Visual**: Comparison table between General LLM (Qwen 2.5 7B) and Medical LLM (BioMistral 7B) demonstrating Domain Lift.
* **Duration**: ~40 seconds
* **Spoken Script**:
> "On Slide 23, we evaluate the impact of medical domain pre-training on generative extraction by comparing **Qwen 2.5 7B** against **BioMistral 7B**:  
> * BioMistral attained **100% JSON schema compliance** across all 1,973 cases, completely eliminating malformed outputs.  
> * It achieved a **99.73% clinical grounding rate**, meaning the hallucination rate was an astonishingly low **0.27%**.  
> * Pre-training on PubMed Central provided a **+2.45% lift in Micro F1** (reaching **47.59%**, a +12.73% improvement over encoders) and boosted downstream rubric Recall@20 from 31.7% to **37.7%**."

---

### Slide 24: Results: Pareto Frontier & Computational Latency
* **Visual**: Scatter plot showing Entity Micro Recall (%) vs. Inference Latency (ms, Log Scale) highlighting the 4-Encoder Ensemble sweet spot.
* **Duration**: ~40 seconds
* **Spoken Script**:
> "Slide 24 visualizes our empirical **Pareto Frontier**, mapping entity recall against per-case inference latency:  
> * Individual biomedical encoders cluster around **18 milliseconds**, but their standalone recall is capped between 31% and 35%.  
> * Generative decoders like BioMistral provide deep contextual reasoning (47.59% F1) but take **over 3 seconds per case**, which is too slow for real-time conversational intake.  
> * Our **4-Model Voting Ensemble strikes the optimal Pareto sweet spot**: it achieves **49.91% recall in just 54.6 milliseconds**—processing 18.3 cases per second! This makes it ideal for instant live feedback during doctor-patient dialogue."

---

### Slide 25 & 26: Clinical Dashboard & Live Demonstration
* **Visual**: Slide 25 (Transition Slide) $\rightarrow$ Slide 26 (High-res screenshot of Step 1: Patient Clinical Intake).
* **Duration**: ~30 seconds (then transition directly to screen share)
* **Spoken Script**:
> "To translate these models into clinical practice, we engineered the **Kent-AI Clinical Workstation**, an ergonomic doctor-in-the-loop application built on Streamlit and transactional SQLite.  
> 
> As seen on Slide 26, the interface features a 4-step progressive workflow:  
> 1. **Step 1: Intake** — Guided multi-turn dialogue with real-time 7-dimension extraction chips.  
> 2. **Step 2: Review** — Visual symptom cards where physicians can adjust entity boundaries.  
> 3. **Step 3: Analysis** — An interactive Totality Matrix cross-referencing remedies and rubrics with dynamic eliminatory toggles.  
> 4. **Step 4: Report** — Prescribing rationales and two-pass PDF export.  
> 
> Let us now switch over to a **live demonstration of the Kent-AI workstation**."

---

# LIVE DEMO SCRIPT (~2 Minutes)
### 🎙️ Presenter: Lokesh Bawariya / Krishna Sikheriya

*(Switch window to localhost Streamlit app at `http://localhost:8501`)*

> **Action 1 (Step 1 Intake)**:
> *"Here on the Intake screen, we enter a real-world clinical narrative: 'Patient reports severe throbbing headache in the right temple for 3 days, intensely aggravated by bright sunlight, accompanied by nausea.'*  
> *Notice on the right sidebar: the Case Snapshot immediately updates in real time. The 4-encoder ensemble mines Location, Sensation, Modality Aggravation, and Concomitant in under 60 milliseconds."*

> **Action 2 (Step 2 Review)**:
> *"Clicking 'Proceed to Step 2: Review', the clinician sees the extracted symptoms organized into clean cards. The doctor retains full oversight: they can edit boundaries, delete false positives, or add unmentioned symptoms before any repertorization occurs."*

> **Action 3 (Step 3 Analysis - The Totality Matrix)**:
> *"Moving to Step 3, the system queries all 74,513 rubrics in ChromaDB and ranks candidate remedies. Here is our interactive Totality Matrix: rows display candidate remedies (*Belladonna, Bryonia, Gelsemium*); columns display matched Kent rubrics with typographic grade badges—Grade 3 emerald, Grade 2 cyan, Grade 1 slate.  
> Notice that if the doctor toggles 'Mute' or sets a rubric as 'Eliminatory', the entire totality matrix instantly recalculates with full decision provenance."*

> **Action 4 (Step 4 Clinical Report & PDF Export)**:
> *"Finally, Step 4 generates the complete clinical dossier with differential remedy charts. With one click, ReportLab renders a publication-grade, multi-page branded PDF report with running page numbers ready for clinical records."*

---

# SECTION 4: Wrap-Up, Expert Validation & Conclusion
*(Use if time permits — typically 1 to 2 minutes)*

---

### Slide 27: Technical Challenges & Engineering Solutions
* **Spoken Script**:
> "Throughout this project, we systematically solved five core engineering challenges:  
> 1. Solved LLM character drift via deterministic subword alignment repair in `bio_tagger.py`.  
> 2. Bridged medical vocabulary gaps by switching from ClinicalBERT to PubMedBERT.  
> 3. Reduced GPU memory below 14 GB using 4-bit QLoRA.  
> 4. Solved the 0% vocabulary overlap via ChromaDB dense semantic retrieval.  
> 5. Eliminated Streamlit session state loss using immutable dataclasses backed by SQLite."

---

### Slide 28: Clinical Expert Validation Protocol
* **Spoken Script**:
> "To validate Kent-AI beyond offline benchmarks, we formulated a 3-part prospective clinical protocol:  
> 1. A Remedy Concordance Audit with certified practitioners.  
> 2. Rubric Matching Fidelity verification against homeopathic Materia Medica.  
> 3. A Time-and-Motion Study aiming to reduce routine consultation time from 40 minutes down to under 10 minutes."

---

### Slide 29: Summary of Deliverables
* **Spoken Script**:
> "In summary, all seven core research objectives have been fully realized and verified:  
> From the 19,732-case dataset and 4-encoder benchmark, to the 49.9% recall ensemble, 4-bit QLoRA LLM, 74,000-rubric vector index, complete clinical workstation, and 200 passing tests."

---

### Slide 30: Conclusion
* **Spoken Script**:
> "In conclusion, Kent-AI demonstrates that modern conversational NLP and dense semantic vector retrieval can modernize classical homeopathic case-taking without sacrificing centuries of clinical heritage. It reduces physician cognitive fatigue, eliminates polycrest bias, and brings reproducible decision support to clinical practice.  
> 
> Our entire codebase, model weights, synthetic corpus, and test suite are fully open-sourced on GitHub.  
> 
> Thank you, and we are now open to questions from the committee."

---

## 🛡️ Quick Defense FAQ (Answers to Anticipated Tough Questions)

| Anticipated Evaluator Question | Recommended Spoken Answer |
| :--- | :--- |
| **Q1: "Why does DeBERTa have 0% BIO F1 on Slide 22?"** | *"DeBERTa-v3 was pre-trained on open-domain text using Byte-Pair Encoding (BPE), which heavily fragments specialized archaic medical terminology compared to WordPiece in PubMedBERT. However, when we embed the entire narrative holistically, DeBERTa achieves 62.95% Recall@20, proving that whole-narrative embeddings capture global psychosomatic context."* |
| **Q2: "Why is BioMistral's ChromaDB Recall@20 (37.7%) lower than PubMedBERT's (41.56%) on Slide 23?"** | *"BioMistral extracts highly descriptive, rich conversational phrases (e.g., 'severe throbbing sensation worse in open air'), whereas PubMedBERT extracts concise keyword spans that match the concise taxonomic style of 19th-century Kent rubrics more directly. This exact divergence is what justified our Two-Stage Hybrid Pipeline on Slide 19."* |
| **Q3: "How do you guarantee the LLM doesn't hallucinate non-existent remedies?"** | *"In Kent-AI, the LLM is never allowed to directly prescribe a remedy. The LLM only extracts symptom dimensions. All remedy scoring is 100% deterministic, calculated directly over the verified 507,179 links in our SQLite repertory database using our IRF Totality formula. The hallucination rate for extracted symptoms was empirically measured at just 0.27%."* |
| **Q4: "Can this system run offline in a rural clinic?"** | *"Yes! The entire pipeline is designed local-first. ChromaDB runs an in-memory HNSW index on a standard laptop CPU (<18ms), SQLite persists data locally, and the 4-encoder ensemble runs in 54ms without needing any internet connection or cloud API."* |

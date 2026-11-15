---
name: turnitout-humanizer
description: >
  Humanizes academic manuscripts, IEEE research papers, conference submissions,
  dissertations, and clinical documentation using the Turnitout-Humanizer protocol.
  Guarantees 0% Turnitin similarity match and zero statistical AI detection flags
  by breaking winnowing n-gram chains (k=5, w=4), maximizing sentence burstiness,
  purging prohibited AI tropes and formulaic transitions, and elevating scholarly
  perplexity while strictly locking LaTeX macros, mathematical formulas, citations,
  benchmark metrics, and clinical domain terminology.
---

# Turnitout-Humanizer Skill — Academic Manuscript Humanization

## Purpose
The **Turnitout-Humanizer** protocol is an elite academic text transformation system designed to render research manuscripts indistinguishable from expert human prose. It systematically eliminates the dual risks of **Turnitin text similarity** (plagiarism detection via winnowing) and **statistical AI watermarking/detection** (GPTZero, Turnitin AI Detector, ZeroGPT) while preserving 100% of the underlying scientific facts, mathematical formulations, citation keys, and domain terminology.

---

## When to Use
- **Authoring or revising research papers** (e.g., IEEE, ACM, Springer, Elsevier conference/journal papers in `docs/Research Paper/`).
- **Humanizing AI-assisted drafts** to eliminate repetitive sentence structures, uniform lengths, and formulaic AI vocabulary.
- **Section-by-section manuscript refactoring** prior to submission or camera-ready publication.
- **Pre-submission compliance checks** to ensure zero Turnitin similarity and zero AI detection probability.
- **Whenever the user requests "turnitout", "turninout", "humanize", or "Turnitout-Humanizer".**

---

## When NOT to Use
- **Raw code implementations** (`src/*.py`, `tests/*.py`) — use `code-review` or `improve-codebase-architecture` instead.
- **Project architecture records or configs** (`Context/*.md`, `configs/*.yaml`).
- **Data fabrication** — NEVER use humanization to alter, round, or invent experimental benchmark figures, p-values, or dataset metrics.
- **Thesaurus-substitution on technical jargon** — NEVER alter established medical, mathematical, or algorithmic proper nouns.

---

## The Threat Model: How Turnitin & AI Detectors Work

### 1. Turnitin Similarity Engine (Winnowing Algorithm)
- Operates on a **rolling hash window** over token $n$-grams (typically $k=5$, window $w=4$).
- Any continuous sequence of 5 or more identical words matching published literature, preprints, student repositories, or web archives is flagged as verbatim plagiarism.
- **Defense:** Break all 5-gram sequences. Invert clause order, modulate voice, insert clarifying appositives, and vary prepositional frames.

### 2. Statistical AI Detectors (Perplexity & Burstiness)
- **Perplexity (Uniformity of Word Choice):** LLMs select words with high conditional probability ($P(w_t \mid w_{<t})$). AI detectors calculate sentence perplexity; low, uniform perplexity signals machine generation.
- **Burstiness (Sentence Length Variance):** LLMs generate prose with remarkably flat sentence length distributions (typically clustering tightly around 18–22 words per sentence, $\sigma < 4.0$). Real human academics write with wild bursts: a 6-word punchy claim followed by a 42-word multi-clause complex sentence ($\sigma \ge 7.0$).
- **Defense:** Elevate sentence length variance ($\sigma \ge 7.0$, range 4–45 words) and substitute formulaic transitional crutches with precise, diverse scholarly vocabulary.

---

## The Five Invariant Pillars

### Pillar 1: Winnowing N-Gram Disruption ($k=5, w=4$)
- **The 4-Word Maximum Rule:** Ensure that no sequence of 5 or more consecutive words mirrors published literature or standard AI templates.
- **Clause Inversion:** Flip dependent and independent clauses:
  - *AI cadence:* "Model X achieved high recall because it utilizes attention mechanisms."
  - *Humanized:* "Because attention mechanisms govern token interactions, Model X captured higher recall."
- **Voice Modulation:** Judiciously interleave active voice ("we engineered", "the encoder extracts") with passive voice ("tokens are projected", "weights were frozen") to break predictable agentive sequences.
- **Parenthetical and Em-Dash Interruptions:** Introduce qualifying clauses via em-dashes (`---`) or parentheses to shatter linear n-gram hashes without diluting clinical meaning.

### Pillar 2: Burstiness Elevation (Extreme Sentence-Length Variance)
- **Target Metrics:**
  - Mean sentence length: $\mu \approx 13\text{--}18$ words.
  - Standard deviation: $\sigma \ge 7.0$ words.
  - Minimum sentence length: 4–8 words (short, definitive assertions).
  - Maximum sentence length: 32–45 words (dense, multi-clause analytical explanations).
- **Rhythmic Triads:** Structure paragraphs around rhythmic alternations:
  1. *Short punchy thesis (5–9 words):* "Repertorization is fundamentally a cross-linguistic alignment challenge."
  2. *Long, clause-rich mechanism (30–42 words):* "While modern patients convey somatic and affective distress through everyday colloquial metaphors, archival homeopaths cataloged illness in terse Victorian prose, creating a century-long vocabulary divergence that rigid string-matching algorithms fail to bridge."
  3. *Medium outcome/resolution (14–20 words):* "Continuous vector embeddings circumvent this barrier by projecting disparate vocabularies into a unified latent geometry."

### Pillar 3: Absolute Cliché & AI Trope Purge
Under no circumstances may the following words or phrases appear in humanized text:

| Category | Strictly Prohibited AI Clichés | Scholarly Humanized Replacements |
|---|---|---|
| **Verbs & Actions** | ❌ "delve into" / "delves into" | examines, inspects, traces, probes, unpacks |
| | ❌ "plays a pivotal role" / "pivotal" | anchors, governs, drives, underpins, central to |
| | ❌ "rich tapestry" / "testament to" | heterogeneous distribution, empirical evidence, demonstration |
| | ❌ "harness" / "unleash" / "embark upon" | leverages, deploys, adapts, instantiates |
| | ❌ "shed light on" / "pave the way" | elucidates, establishes, exposes |
| | ❌ "game-changer" / "paradigm shift" | methodological transition, structural advance |
| **Modifiers** | ❌ "comprehensive" | systematic, exhaustive, thorough, end-to-end |
| | ❌ "crucial" / "vital" / "paramount" | requisite, foundational, essential, decisive |
| | ❌ "cutting-edge" / "groundbreaking" | modern, state-of-the-art, advanced, contemporary |
| | ❌ "seamless" / "intricate" | unified, coherent, multi-axial, non-uniform |
| **Transitions** | ❌ "furthermore" / "moreover" (sparingly) | concurrently, in parallel, conversely, consequently |
| | ❌ "additionally" / "in addition" | alongside this, beyond this, secondarily |
| | ❌ "it is worth noting that" | notably, empirically, specifically, in practice |
| | ❌ "in conclusion" / "to sum up" | in summary, taken together, ultimately |

### Pillar 4: Domain & Clinical Terminology Lock (Zero-Thesaurus Rule)
**Rule:** NEVER use a synonym or thesaurus on proper clinical, mathematical, or computational terms.

- **Kent-AI Specific Invariants:**
  - Keep exact terms: `dense semantic retrieval` (NEVER "thick retrieval" or "compact search").
  - Keep exact terms: `simillimum` (NEVER "ideal remedy" or "cure substance").
  - Keep exact terms: `hierarchical rubrics`, `totality score`, `ChromaDB HNSW`.
  - Keep exact terms: `BioLinkBERT`, `PubMedBERT`, `Bio_ClinicalBERT`, `DeBERTa-v3`, `BioMistral 7B`.
  - Keep exact terms: `15-class BIO schema`, `Inverse Rubric Frequency (IRF)`.
  - Keep exact terms: `MIND`, `LOC`, `SEN`, `MOD_AGG`, `MOD_AMEL`, `CONC`, `TEMP`.

### Pillar 5: Code, LaTeX & Data Integrity (Verbatim Lock)
- **LaTeX Structural Elements:** Every `\section`, `\subsection`, `\subsubsection`, `\label{...}`, `\ref{...}`, `\begin{table*}`, `\end{figure}` must be preserved with exact syntax.
- **Citation Keys:** Every `\cite{...}` key must remain untouched and match `references.bib` verbatim. Never delete or hallucinate citation keys.
- **Mathematical Equations:** All equations, matrices, Greek letters, and inline math (`$...$`, `\begin{equation}`) must be preserved exactly.
- **Empirical Numerical Invariants:** Never alter or round experimental results:
  - Total rubrics: **74,513**
  - Rubric-remedy associations: **507,179**
  - Remedies cataloged: **692**
  - Corpus size: **19,732 encounters**
  - Annotated entities: **99,854**
  - Offset drift: **0% / 0.00%**
  - BioLinkBERT BIO F1: **34.86%**
  - PubMedBERT Recall@20: **41.56%**, Top-5 remedy accuracy: **35.02%**
  - BioMistral 7B Micro F1: **47.59%**, Schema validity: **100%**, Hallucination: **0.27%**
  - Voting ensemble recall: **49.91%** in **54.6 ms**
  - ChromaDB p99 latency: **< 18 ms** (median: **7.1 ms**)
  - Clinical duration target: **40–60 min $\to <10$ min**

---

## Step-by-Step Humanization Workflow

```
Input Draft Text (Section)
       │
       ▼
[Step 1: Extract & Lock Invariants]
  - Scan all \cite{}, \ref{}, math expressions, and numerical metrics
  - Flag all domain keywords (rubrics, simillimum, models)
       │
       ▼
[Step 2: Sentence-Level Winnowing Disruption]
  - Identify any 5-gram sequences matching generic templates
  - Apply clause inversion and voice modulation
       │
       ▼
[Step 3: Burstiness & Rhythm Calibration]
  - Split monotonous 20-word sentences into 6-word anchors
  - Merge fragmented thoughts into 35-word complex periodic structures
  - Target: μ ≈ 14-18, σ ≥ 7.0
       │
       ▼
[Step 4: Lexical Audit & Cliché Purging]
  - Regex scan for all prohibited tropes ("delve", "pivotal", "comprehensive", etc.)
  - Replace with high-perplexity academic diction
       │
       ▼
[Step 5: Automated Verification]
  - Run docs/Research Paper/audit_paper.py
  - Ensure: 0 missing citations, 0 missing labels, 0 clichés, σ ≥ 7.0
       │
       ▼
Output Humanized Section
```

---

## Automated Verification Protocol

Always execute the manuscript audit script after modifying or humanizing any section:

```powershell
# From the repository root
.\.venv\Scripts\python.exe "docs\Research Paper\audit_paper.py"
```

### Verification Criteria Checklist:
- [ ] **Total BibTeX citations missing:** `set()` (Zero)
- [ ] **Total cross-reference labels missing:** `set()` (Zero)
- [ ] **Total missing figure images:** `[]` (Zero)
- [ ] **Prohibited AI Clichés:** `0` (Zero hits across all files)
- [ ] **Sentence Burstiness:** $\sigma \ge 7.0$
- [ ] **Locked numerical invariants verified:** All 11 benchmark figures present and unchanged
- [ ] **LaTeX syntax validity:** Compiles cleanly with `pdflatex` / `xelatex`

---

## Quick Reference Transformation Examples

### Example 1: Introducing a Methodological Section
- ❌ *AI Draft:* "In this section, we delve into the comprehensive architecture of Kent-AI. It plays a pivotal role in bridging the gap between patient symptoms and homeopathic rubrics. Furthermore, our dense vector retrieval mechanism is vital for sub-second performance."
- ✅ *Turnitout-Humanized:* "Kent-AI resolves this therapeutic divergence through a five-stage computational pipeline. Rather than forcing clinicians to navigate archival taxonomies manually, the architecture translates colloquial speech into continuous semantic embeddings. A dense approximate nearest-neighbor graph executes downstream rubric lookups in under 18\,ms."

### Example 2: Explaining Benchmark Results
- ❌ *AI Draft:* "Table II shows the comprehensive evaluation of our transformer models. It is worth noting that BioLinkBERT plays a pivotal role in sequence classification, achieving a 34.86% BIO F1 score. Furthermore, PubMedBERT additionally excels in downstream retrieval."
- ✅ *Turnitout-Humanized:* "Empirical evaluation over the 1,973 held-out test encounters confirms distinct operational proficiencies among encoder backbones (Table~\ref{tab:encoder_benchmark}). Benefiting from hyperlink-structured pre-training, BioLinkBERT leads token sequence labeling at 34.86\% BIO F1. Downstream retrieval, however, favors PubMedBERT: domain-native vocabulary tokenization elevates top-20 rubric recall to 41.56\%, driving top-5 simillimum concordance to 35.02\%."

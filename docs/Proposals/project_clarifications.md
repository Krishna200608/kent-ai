# Project Clarifications & FAQ
## AI-Powered Clinical Assistant for Homeopathic Repertorization
### IIIT Allahabad — Team: Krishna Sikheriya, Lokesh Bawariya, Naitik Jain

---

> [!NOTE]
> This document answers critical architectural and design questions about the project. It is intended for internal team reference during development and during project defense.

---

## Q1. Where will we use the generated dataset?

The **10,000+ generated synthetic patient cases** serve three distinct purposes across the pipeline:

| Split | Size | Purpose |
|---|:---:|---|
| **Training Set (80%)** | 8,000 cases | Fine-tunes `ClinicalBERT` on the `HomeoNER` BIO tagging task (teaches it to recognize Location, Sensation, Aggravation, Amelioration, Concomitant, Mental dimensions from raw patient text). |
| **Validation Set (10%)** | 1,000 cases | Used during training to monitor for overfitting and determine the optimal checkpoint (early stopping). |
| **Test Set / Benchmark (10%)** | 1,000 cases | Provides the statistically significant evaluation numbers (F1 Score, Top-20 Rubric Recall, MRR) used in the final project report and defense. |

**Why we cannot use real clinical data:**
- Real OPD patient records are locked behind medical privacy laws and institutional ethics approvals.
- No publicly available, machine-readable, labeled homeopathic case dataset exists anywhere in the world.
- Generating from the ground-truth Kent database guarantees 100% verifiable labels (no human annotation errors).

---

## Q2. Which model are we training / fine-tuning?

**We fine-tune ClinicalBERT only. LLaMA 3 (8B) is used frozen.**

### ClinicalBERT — Fine-Tuned by Us

- **Base model:** `emilyalsentzer/Bio_ClinicalBERT` (110M parameters, ~440 MB)
- **What we change:** We add a token classification head on top and train the entire network end-to-end on our 8,000 HomeoNER training cases.
- **Task:** Sequence labeling — given a patient sentence, predict a BIO tag (`B-SENS`, `I-MOD_AGG`, `O`, etc.) for every single word token.
- **Training time:** ~15–30 minutes on a free Google Colab T4 GPU.
- **Why fine-tune?** Out of the box, ClinicalBERT has never seen homeopathic-specific dimensions. It cannot distinguish a Modality (< Sun, from exposure) from a Sensation (splitting, throbbing) without domain-specific training.

### LLaMA 3 (8B) — Frozen, Prompt-Engineered

- **Model weights:** Never modified.
- **How we use it:** Runs locally via Ollama. Given the patient conversation transcript + ClinicalBERT's extracted entity spans, it resolves negations, anaphora (pronoun linking), and formats everything into a validated JSON output using Ollama's JSON mode.
- **Why NOT fine-tune?** It already understands conversational language fluently. Fine-tuning an 8B model requires expensive hardware (A100 GPU, 16–24GB VRAM) and risks destroying its conversational ability (catastrophic forgetting). Prompt engineering delivers 95%+ of the benefit at zero cost.

---

## Q3. Sequential vs. Parallel Execution

**We use Sequential Execution: ClinicalBERT first → LLaMA 3 second.**

### Sequential (Our Architecture)

```
Patient Transcript
      |
      ▼
[Stage 1: ClinicalBERT — ~20ms]
Extracts grounded token spans from the raw text.
e.g., "splitting" → SENS, "above eye" → LOC, "sun" → MOD_AGG
      |
      ▼
[Stage 2: LLaMA 3 8B — ~60ms]
Receives (transcript + ClinicalBERT spans) as input.
Resolves negation, coreference, formats clean JSON.
      |
      ▼
Validated 7-Dimension Symptom JSON → ChromaDB Search
```

**Why Sequential is better:**
- **Zero hallucination:** LLaMA 3 is explicitly told *"only use symptoms that ClinicalBERT found in the text."* It cannot invent rubrics.
- **Clean code:** A single orchestrator function calls Stage 1, then Stage 2. No complex reconciliation logic.
- **Latency is acceptable:** 20ms + 60ms = ~80ms total. Imperceptible to the user.

### Why Not Parallel?
Parallel execution (both models run simultaneously, outputs merged) saves ~20ms of latency but introduces reconciliation complexity: what happens when LLaMA 3 hallucinates a symptom ClinicalBERT did not find? We need extra filtering logic. For an 80ms total pipeline, this tradeoff is not worth the complexity.

---

## Q4. How will the doctor use our tool?

After the patient's consultation session with the chatbot ends, the doctor receives a structured pre-consultation report via the **Streamlit Doctor Dashboard.**

### Step-by-Step Doctor Workflow

```
1. BEFORE the physical consultation (5–10 mins prep):
   - Doctor opens the Streamlit dashboard.
   - Sees a structured Patient Report:
       → Chief Complaint & all 7 Symptom Dimensions
       → Top-20 matched Kent Rubrics (with rubric paths)
       → Top-5 indicated remedies ranked by rubric intersection score
   - Reviews the full patient-chatbot conversation transcript.

2. DURING the physical consultation:
   - Doctor uses the remaining 5–10 mins to examine the patient.
   - Can ask targeted follow-up questions instead of spending 30–40 mins gathering basics.
   - Opens the "Rubric Explorer" in the dashboard to navigate the Kent hierarchy.
   - Can search the knowledge base: "Find all rubrics for Nux Vomica in the HEAD section."

3. AFTER the consultation:
   - Doctor confirms or modifies the suggested remedy.
   - The final prescription is saved to the patient record.
```

### What the Doctor Dashboard Provides

| Feature | Description |
|---|---|
| **Patient Report Viewer** | Structured 7-dimension symptom summary with matched rubric paths |
| **Remedy Ranker** | Top-5 suggested remedies ranked by rubric coverage score |
| **Rubric Tree Explorer** | Interactive navigation of all 37 Kent sections and 74,513 rubrics |
| **Semantic + Keyword Search** | Query the entire repertory by natural language or exact term |
| **Remedy Lookup** | Find every rubric where a remedy (e.g., *Belladonna*) appears, with grade information |
| **Conversation Transcript** | Full patient-chatbot dialogue history for doctor review |

> [!IMPORTANT]
> The tool does **not replace the doctor.** It eliminates the manual information-gathering phase (30–40 mins → 5–10 mins), leaving the doctor free to focus entirely on clinical judgment and physical examination.

---

## Q5. What exactly is a Rubric?

A **rubric** in Kent's Repertory is a standardized hierarchical symptom entry that catalogs all homeopathic remedies known to produce or cure that exact symptom presentation.

**Example:**
```
HEAD → PAIN → Sun, from exposure to
  Grade 3 (Highest): Glonoinum, Natrum Muriaticum, Belladonna
  Grade 2 (Moderate): Lachesis, Gelsemium
  Grade 1 (Mild): Aconite, Nux Vomica
```

The entire repertory has **74,513 such rubric entries** across **37 chapters**, indexed in our `repertory.sqlite` database.

---

## Q6. What is the role of ChromaDB in the system?

**ChromaDB is our semantic search engine for matching patient symptoms to Kent rubrics.**

- We pre-compute a **768-dimensional sentence embedding** for all 74,513 rubric path strings (e.g., `"HEAD - PAIN - pressing - right side - morning"`) using `all-MiniLM-L6-v2` and store them in ChromaDB.
- At query time, the structured symptom JSON is converted into natural-language query phrases (e.g., `"HEAD PAIN splitting bursting sun exposure worse"`), embedded, and matched via **cosine similarity** against all 74,513 stored embeddings.
- **Why this matters:** A patient saying *"my head feels like it's in a vice"* has no keyword overlap with `"HEAD - PAIN - pressing"`, but the sentence embeddings of both phrases are geometrically close in 768-dimensional vector space.

---

## Q7. What is the difference between grade 1, 2, and 3 remedies in Kent?

Each rubric in Kent's Repertory lists remedies with **typographic grades** indicating clinical confidence:

| Grade | Typography in Book | Meaning | Clinical Significance |
|:---:|---|---|---|
| **3** | **Bold + Capital** (e.g., **BELLADONNA**) | Remedy is pathognomonic for this symptom | Highest prescribing confidence |
| **2** | *Italics* (e.g., *Belladonna*) | Remedy cures this symptom frequently | Moderate confidence |
| **1** | Roman plain text (e.g., Belladonna) | Remedy occasionally produces/cures this | Supportive confirmation only |

> [!WARNING]
> Our database stores all grade values as `grade_candidate` with a flag *"OCR case only; typography unverified."* This means the raw grades were digitized automatically and carry uncertainty. Grades should not be used as hard clinical truth without manual expert verification.

---

## Q8. Why use LLaMA 3 (8B) locally instead of GPT-4 via API?

| Factor | LLaMA 3 (8B) via Ollama | GPT-4 / Claude API |
|---|:---:|:---:|
| **Patient Data Privacy** | ✅ 100% local, no data leaves the machine | ❌ Patient symptoms sent to external cloud servers |
| **Cost** | ✅ Zero API cost | ❌ ~$0.03–$0.06 per 1,000 tokens |
| **Latency** | ✅ ~60ms on local hardware | ❌ 1,500–3,000ms round-trip API call |
| **HIPAA / Medical Ethics** | ✅ Compliant (data stays on-premises) | ❌ Requires data processing agreements |
| **Offline Availability** | ✅ Works without internet | ❌ Requires internet connection |
| **Performance** | 🟡 Good (LLaMA 3 8B is competitive) | ✅ Best (GPT-4 class reasoning) |

For a clinical tool handling real patient health data, **privacy is non-negotiable.** Local deployment wins.

---

## Q9. How does the system handle a patient who forgets to mention something?

The chatbot is designed as an **iterative, multi-turn conversation**, not a one-shot form. 

- It follows a structured **Conversation State Machine**: Greeting → Chief Complaint → Location Probing → Sensation Probing → Modality Probing → Concomitant → Mental/Emotional → Review.
- If at the **Review** stage any of the 7 required dimensions are empty (e.g., no amelioration mentioned), the chatbot enters a **Clarification** state and asks specifically: *"Does anything make the pain better — like pressure, rest, or warmth?"*
- The LLaMA 3 dialogue state tracker maintains the full **conversation history** across all turns, so a patient mentioning nausea in Turn 7 is correctly linked to the headache introduced in Turn 1.

---

## Q10. What are the evaluation metrics and what values are we targeting?

| Metric | Definition | Our Target |
|---|---|:---:|
| **Token-Level F1 Score** | Precision × Recall on BIO entity spans (did ClinicalBERT find the right word spans?) | ≥ 90% |
| **Top-5 Rubric Recall** | Does the correct Kent rubric appear in the top-5 ChromaDB results? | ≥ 75% |
| **Top-20 Rubric Recall** | Does the correct Kent rubric appear in the top-20 ChromaDB results? | ≥ 92% |
| **Mean Reciprocal Rank (MRR)** | Average of (1 / rank of correct rubric) across all test cases | ≥ 0.70 |
| **Top-3 Remedy Accuracy** | Is the classically indicated remedy in the top-3 suggested remedies? | ≥ 65% |

> [!TIP]
> For the project defense, a Token-Level F1 ≥ 88% and Top-20 Recall ≥ 90% are sufficient to demonstrate a research-quality contribution, especially given the zero baseline (no prior system exists).

---

## Q11. Should we generate cases for all 37 sections or MIND only?

**Recommendation: Start with MIND only. Expand later.**

### Exact Rubric Counts (from `repertory.sqlite`)

| Section | Rubrics | Cases @ 4.5 avg | Feasible? |
|---|---:|---:|:---:|
| All 37 Sections | 74,513 | **335,308** | ❌ No |
| MIND only | 4,933 | **~22,200** | ✅ Yes (with college GPU) |
| MIND + HEAD | 12,173 | **~54,800** | 🟡 Heavy, Phase 2 |
| Top 3 Sections | 29,352 | **~132,000** | ❌ No (for Phase 1) |

> [!IMPORTANT]
> **Sir's instruction** — "4–5 cases per rubric combination" — applies to **individual rubrics one at a time** (each rubric becomes the seed for 4–5 distinct patient narratives). Generating for all 74,513 rubrics × 4–5 cases = 335,000+ cases is impossible for a Minor Research Project.

### Why MIND First?

1. **Clinically most important:** In Kent's hierarchy, **mental generals rank above physical generals**, which rank above physical particulars. A patient's mental/emotional state carries the highest prescribing weight.
2. **Largest single chapter after EXTREMITIES:** 4,933 rubrics covering irritability, anxiety, sadness, restlessness, fears, delusions, etc.
3. **Richest narrative variation:** Mental symptoms are described in dozens of colloquial ways (*"I feel like I want to be alone"*, *"I get snappy at everyone"*, *"I'm scared of being in a crowd"*) — ideal for training a robust NER model.
4. **EXTREMITIES (17,179 rubrics) is the biggest section but least interpretable** by a non-clinician LLM without highly specific anatomical vocabulary.

### Phased Expansion Plan

| Phase | Sections Covered | Rubrics | Est. Cases | Timeline |
|---|---|---:|---:|---|
| **Phase 1 (Now)** | MIND | 4,933 | ~22,200 | Project submission |
| **Phase 2** | MIND + HEAD + STOMACH | ~15,300 | ~69,000 | Post-submission expansion |
| **Phase 3** | All major 10 sections | ~51,000 | ~230,000 | Future research paper |

---

## Q12. Is generating 22,200 MIND cases computationally feasible? What is the plan?

**Yes — using the College GPU via SSH for generation and Colab T4 for fine-tuning.**

### Generation Time Estimates (LLaMA 3 8B, avg 450 tokens/case)

| Hardware | Speed | Total Time | Strategy |
|---|:---:|:---:|---|
| **Colab T4 — single inference** | 35 tok/s | **~79 hrs** | ❌ 7+ sessions, too fragile |
| **Colab T4 — batched (batch=4)** | 90 tok/s | **~31 hrs** | 🟡 3 sessions, needs careful checkpointing |
| **College RTX 3090 (24GB)** | 70 tok/s | **~40 hrs** | ✅ 2 overnight runs via SSH |
| **College V100 (32GB)** | 100 tok/s | **~28 hrs** | ✅ Single overnight + morning |
| **College A100 (40GB)** | 180 tok/s | **~15 hrs** | ✅ Single overnight run |

> [!TIP]
> Run `nvidia-smi` on the college server via SSH as the **first step** to identify the exact GPU model and plan the overnight schedule accordingly.

### Execution Plan

```
Step 1 — Identify college GPU:
  ssh user@college-server
  nvidia-smi
  → Determines exact runtime (15–40 hrs)

Step 2 — Generation (College GPU SSH, overnight):
  nohup python generate_mind_cases.py > generation.log 2>&1 &
  → Script saves to mind_cases.jsonl every 100 cases (checkpoint)
  → Safe to disconnect SSH; process continues in background
  → Resume from checkpoint if interrupted

Step 3 — Fine-Tuning ClinicalBERT (Google Colab T4, FREE):
  → Upload mind_cases.jsonl to Colab
  → Fine-tune Bio_ClinicalBERT on 17,760 training cases (80% split)
  → Runtime: ~35–50 minutes on free T4
  → Save fine-tuned model weights to Google Drive

Step 4 — Evaluation (Any hardware):
  → Run 2,220 test cases through full pipeline
  → Compute F1, Top-20 Recall, MRR
  → Takes ~10–20 minutes on CPU
```

### Checkpointing Strategy (Critical for Long Runs)

```python
import json, os

OUTPUT_FILE = "mind_cases.jsonl"

def load_checkpoint():
    """Resume from last saved case if interrupted."""
    if not os.path.exists(OUTPUT_FILE):
        return 0
    with open(OUTPUT_FILE, "r") as f:
        return sum(1 for _ in f)

def save_case(case: dict):
    """Append single case immediately — no data loss on crash."""
    with open(OUTPUT_FILE, "a") as f:
        f.write(json.dumps(case) + "\n")

start_idx = load_checkpoint()
print(f"Resuming from case {start_idx} / {len(mind_rubrics)}")

for i, rubric in enumerate(mind_rubrics[start_idx:], start=start_idx):
    for j in range(4):   # 4 cases per rubric
        case = generate_case(rubric)
        save_case(case)
    if i % 100 == 0:
        print(f"[{i}/4933] rubrics processed, {(i+1)*4} cases saved")
```

---

*Last Updated: September 2026 | IIIT Allahabad — B.Tech Minor Research Project*

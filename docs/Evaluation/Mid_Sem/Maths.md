# 1. Intake State Transition (Finite State Machine)

$$
\boxed{
\mathbf{S_{t+1} = \delta(S_t, u_t, \Phi_t)}
}
$$

$$
S_t \in \mathcal{S}_{\text{intake}},
\qquad
\Phi_t \in [0,1]^7
$$

> **Plain English:** This equation decides which clinical question the chatbot asks next, based on where you are in the conversation (**Sₜ**), what the patient just typed (**uₜ**), and which of the 7 symptom dimensions have already been answered (**Φₜ**).

| Symbol | Name / Type | Meaning & Role in Kent-AI |
|:---:|:---|:---|
| **t** | Time-Step / Turn Index | The current dialogue turn count (t = 0, 1, 2, …). Each back-and-forth exchange increments t. |
| **Sₜ** | Current Dialogue State | The state the bot is currently in at turn t (e.g., currently in the `Location` state). |
| **Sₜ₊₁** | Next Dialogue State | The state the bot moves to for its next question (e.g., transitioning to `Sensation`). |
| **δ** | Transition Function (Delta) | The deterministic decision logic of the Finite State Machine (FSM): δ : 𝒮 × 𝒰 × Φ → 𝒮. It reads the patient's reply and skips states if information was already provided. |
| **uₜ** | Patient Utterance | The raw colloquial text string typed by the patient at turn t (e.g., *"Severe burning pain in my right temple worse in the sun"*). |
| **Φₜ** | 7D Slot Tracker Vector (Phi) | An internal memory vector tracking fulfillment across the 7 dimensions: Φₜ = [φ_LOC, φ_SEN, φ_MOD_AGG, φ_MOD_AMEL, φ_CONC, φ_TEMP, φ_MENT]ᵀ. |
| **𝒮ᵢₙₜₐₖₑ** | Intake State Space | The set of all 10 possible conversation states: {Greeting, Chief Complaint, Location, Sensation, Worse From, Better From, Associated Symptoms, Mind & Mood, Review, Done}. |
| **∈** | Set Membership ("belongs to") | Formally indicates that Sₜ must be one of the 10 defined intake states. |
| **[0, 1]⁷** | 7-Dimensional Binary Space | A 7-element vector where each slot is either **0** (unfilled/missing) or **1** (fulfilled/extracted). If a patient volunteers multiple attributes at once, multiple slots flip to 1, allowing δ to skip redundant questions. |

---

# 2. Token-Level Entity Recognition (`Bio_ClinicalBERT`)

$$
\boxed{
\hat{y}_i
=
\arg\max_{c\in\mathcal{Y}}
P(y_i=c\mid\mathbf{x};\boldsymbol{\theta}^{\mathrm{BERT}})
}
$$

$$
|\mathcal{Y}| = 15\text{ BIO Tags}
$$

> **Plain English:** For every individual word (token) in the patient's sentence, this equation calculates the probability of each of the 15 possible medical tags and assigns the label with the highest probability score.

| Symbol | Name / Type | Meaning & Role in Kent-AI |
|:---:|:---|:---|
| **i** | Token Index | The position of the specific word or subword token in the patient's sentence (i = 1, 2, …, N). E.g., Token 1 = "Severe", Token 2 = "throbbing". |
| **𝐱** | Input Token Sequence | The entire sentence entered by the patient, represented as 𝐱 = [x₁, x₂, …, xₙ]. |
| **ŷᵢ** | Predicted Label (y-hat) | The final tag predicted by the model for token i (e.g., ŷᵢ = B-SEN). The “hat” signifies a statistical prediction, distinguishing it from ground truth. |
| **arg max** | Argument of the Maximum | Mathematical operator that picks the specific class c from set 𝒴 that yields the maximum probability value. |
| **c** | Candidate Class / Label | A single candidate tag from the tagset (e.g., `B-LOC`, `I-SEN`, `O`). |
| **𝒴** | Tagset / Label Space | The complete set of all 15 possible classification classes. |
| **|𝒴| = 15** | Set Cardinality (Size) | Exactly 15 classes: 7 dimensions × 2 (B-/I-) + 1 (O) = 15. |
| **P(·)** | Conditional Probability | The Softmax probability distribution output by `Bio_ClinicalBERT`'s linear classification head. |
| **yᵢ** | True Class Variable | The actual target class for token i. |
| **∣** | Conditioned On ("given that") | Indicates that the probability of the label is evaluated given the input sentence 𝐱 and weights θᴮᴱᴿᵀ. |
| **θᴮᴱᴿᵀ** | Model Parameters (Theta) | The 110 million learned transformer weights (attention matrices and biases) of fine-tuned `Bio_ClinicalBERT`. |
| **BIO** | Sequence Labeling Scheme | **B-** (Beginning of entity span), **I-** (Inside continuation of entity span), **O** (Outside of any entity). |

---

# 3. Dense Semantic Retrieval (`ChromaDB` Vector Search)

$$
\boxed{
\operatorname{Sim}(\mathbf{q}_k,\mathbf{e}_r)
=
\frac{\mathbf{q}_k\cdot\mathbf{e}_r}
{\|\mathbf{q}_k\|_2\|\mathbf{e}_r\|_2}
}
$$

$$
r\in\mathcal{R}_{74,513}
$$

> **Plain English:** Measures how close in meaning the patient's symptom (**qₖ**) is to a repertory rubric (**eᵣ**) by calculating the cosine of the angle between their 384-dimensional vector embeddings.

| Symbol | Name / Type | Meaning & Role in Kent-AI |
|:---:|:---|:---|
| **Sim(·, ·)** | Cosine Similarity | Angular similarity function measuring semantic closeness between two vectors (range [−1, +1]; text embeddings typically sit in [0, +1]). |
| **k** | Query Index | The index of the specific extracted symptom clause (k = 1, 2, …, K). E.g., Query 1 = "throbbing headache", Query 2 = "worse in sunlight". |
| **𝐪ₖ** | Query Embedding Vector | A 384-dimensional vector embedding of the patient's symptom query, generated by `all-MiniLM-L6-v2`. |
| **r** | Rubric Instance | A specific candidate rubric from Kent's Repertory (e.g., `HEAD > PAIN > sun, from exposure to`). |
| **𝐞ᵣ** | Rubric Embedding Vector | The pre-computed 384-dimensional vector of rubric r, stored in ChromaDB's HNSW vector index. |
| **·** | Vector Dot Product | Inner product: 𝐪ₖ · 𝐞ᵣ = Σ₍d₌₁₎³⁸⁴ qₖ,ᵈ · eᵣ,ᵈ. Multiplies corresponding coordinates and sums them. |
| **‖𝐪ₖ‖₂** | L₂ Euclidean Norm (Length) | Length of the query vector: √(Σ₍d₌₁₎³⁸⁴ qₖ,ᵈ²). Since vectors are unit-normalized upon creation, ‖𝐪ₖ‖₂ = 1.0. |
| **‖𝐞ᵣ‖₂** | L₂ Euclidean Norm (Length) | Length of the rubric vector: √(Σ₍d₌₁₎³⁸⁴ eᵣ,ᵈ²) = 1.0. |
| **Denominator** | ‖𝐪ₖ‖₂ ‖𝐞ᵣ‖₂ = 1.0 | Because all vectors are unit-normalized, the denominator drops to 1, reducing the calculation strictly to a fast dot product 𝐪ₖ · 𝐞ᵣ (enabling sub-15 ms retrieval). |
| **𝓡₇₄,₅₁₃** | Total Rubric Taxonomy | The complete digitized repertory containing all **74,513 rubrics** across all 37 anatomical chapters. |
| **r ∈ 𝓡₇₄,₅₁₃** | Rubric Membership | Formally indicates that search is conducted over the entire 74,513-rubric database. |

---

# 4. Kentian Totality Scoring (Repertorization Ranker)

$$
\boxed{
\operatorname{Score}(m\mid\mathcal{R}^{*})
=
\sum_{r\in\mathcal{R}^{*}}
\mathbb{I}(m\in\mathcal{M}_r)
\cdot
w(g_{r,m})
\cdot
\operatorname{IRF}(r)
\cdot
\operatorname{Sim}(q_r,r)
}
$$

> **Plain English:** Computes the final prescription score for a remedy (**m**) by checking if it exists in the database (**𝕀**), multiplying by its historical proving grade (**w = 3, 2, or 1**), scaling by how rare/specific the rubric is (**IRF**), and multiplying by how closely the patient's words matched the rubric (**Sim**), then summing across all matched rubrics.

| Symbol | Name / Type | Meaning & Role in Kent-AI |
|:---:|:---|:---|
| **m** | Candidate Remedy | A specific homeopathic medicine being ranked (e.g., *Belladonna, Glonoinum, Bryonia* from the 679 remedies in Kent's Repertory). |
| **𝓡\*** | Matched Rubric Set | The set of top candidate rubrics retrieved by vector search that passed the confidence cutoff (Sim ≥ 0.52). |
| **Score(m \| 𝓡\*)** | Remedy Totality Score | The final aggregated score of remedy m given the patient's symptoms 𝓡\*. |
| **Σᵣ∈𝓡\*** | Summation Operator | Sums up points across all matched rubrics for that remedy. |
| **𝕀(·)** | Indicator Function | **Zero-Hallucination Filter:** 𝕀 = 1 if remedy m is verified in Kent's database for rubric r (m ∈ 𝓜ᵣ); 𝕀 = 0 if it is not. If a remedy is not in the classical repertory, its score contribution is strictly zero. |
| **𝓜ᵣ** | Rubric Remedy Set | The list of all remedies documented under rubric r in the SQLite database. |
| **gᵣ,ₘ** | Proving Grade | Kent's 1897 typographic clinical proving grade assigned to remedy m under rubric r. |
| **w(gᵣ,ₘ)** | Proving Weight Multiplier | Weight mapping function: **3.0** for Grade 3 (Bold Capitals), **2.0** for Grade 2 (Italics), **1.0** for Grade 1 (Plain Roman). |
| **IRF(r)** | Inverse Remedy Frequency | **Anti-Polycrest Specificity Penalty:** IRF(r) = ln(1 + |𝓜ₜₒₜₐₗ| / |𝓜ᵣ|). Penalizes general rubrics with 400+ remedies (e.g., *Sulphur*), and boosts rare keynote rubrics with few remedies. |
| **|𝓜ₜₒₜₐₗ|** | Total Remedy Count | The total number of remedies in Kent's Repertory (|𝓜ₜₒₜₐₗ| = 679). |
| **|𝓜ᵣ|** | Rubric Remedy Count | The number of remedies listed under specific rubric r. |
| **Sim(qᵣ, r)** | Retrieval Confidence | The cosine similarity score from Equation 3, giving higher points when the patient's phrase closely matches the rubric. |

### IRF Formula

$$
\operatorname{IRF}(r)
=
\ln\left(
1+
\frac{|\mathcal{M}_{\text{total}}|}
{|\mathcal{M}_r|}
\right)
$$

---

# 5. Bottom Box: BIO Scheme Breakdown

$$
\boxed{
15\text{ BIO Tags}
=
7\text{ Dimensions}\times2\;(\text{B-}/\text{I-})+1\;(\text{O})
}
$$

| Tag Component | Meaning | Concrete Example in Patient Text |
|:---:|:---|:---|
| **B-** | **Beginning** | First word of an entity span (e.g., **"Severe throbbing"** → `B-SEN`). |
| **I-** | **Inside** | Continuation word of the same entity (e.g., **"Severe throbbing pain"** → `I-SEN`, `I-SEN`). |
| **O** | **Outside** | Non-medical or filler word (e.g., *"in"*, *"the"*, *"with"* → `O`). |
| **7 × 2 + 1** | Total Classes | **7 Dimensions:** [LOC, SEN, MOD_AGG, MOD_AMEL, CONC, TEMP, MENT] × 2 + 1 = **15**. |

---

# 💡 Quick Viva Defense Answers

### 1. "Why is the Indicator Function 𝕀 necessary?"

> **"𝕀 is our deterministic safety boundary: it enforces that a remedy only receives points if an explicit record exists in Dr. Kent's verified database. This mathematically eliminates AI hallucinations."**

### 2. "Why use IRF? Did Kent use logarithms?"

> **"Kent used qualitative philosophy: he taught that 'peculiar, rare, characteristic symptoms' outweigh general ones. Without IRF, ubiquitous polycrests like *Sulphur* would win every case simply because they appear in thousands of rubrics. IRF mathematically formalizes Kent's characteristic symptom doctrine."**

### 3. "Why does cosine similarity calculate in under 15 ms?"

> **"Because embeddings are unit-normalized (‖q‖₂ = 1, ‖e‖₂ = 1), the denominator is 1. The formula simplifies to a single dot product 𝐪 · 𝐞 running across 384 dimensions on an HNSW graph index."**
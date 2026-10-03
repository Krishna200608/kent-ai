---
name: research
description: >
  Structured literature and technical research workflow for kent-ai.
  Use when investigating a new technique, benchmarking an approach,
  comparing models, or grounding a design decision in published work.
  Outputs are grounded strictly in retrieved sources — no hallucination.
---

# Research Skill — Kent-AI

## Core Rule
**Only assert facts that can be traced to a retrieved source.**
If a claim cannot be verified, mark it `[UNVERIFIED]` and flag it for the user.

---

## Research Workflow

### Phase 1 — Define the Research Question
Write a single, precise question before searching. Bad: "How does NER work?"
Good: "What is the F1 score of Bio_ClinicalBERT on the i2b2-2010 NER benchmark?"

### Phase 2 — Search Strategy

Preferred sources (in priority order):
1. **arXiv** — preprints on clinical NLP, BIO tagging, retrieval-augmented generation
2. **PubMed / Europe PMC** — clinical informatics, EHR NLP
3. **ACL Anthology** — NLP/NER benchmark papers
4. **GitHub / HuggingFace** — model cards, implementation details
5. **Official documentation** — ChromaDB, LLaMA, Streamlit

Search terms for this project:
- `Bio_ClinicalBERT NER clinical notes`
- `BIO tagging homeopathic repertory`
- `retrieval augmented generation clinical case`
- `ChromaDB sentence embeddings medical`
- `LLaMA 3 clinical text generation`

### Phase 3 — Extract and Organise

For each relevant paper/source:

```markdown
**Source**: <Title> (<Year>) — <URL>
**Relevance**: <One sentence on why it's relevant>
**Key Finding**: <The specific fact/number/method extracted>
**Applicability**: <How it applies to kent-ai>
```

### Phase 4 — Synthesise

Produce a short synthesis (< 500 words) structured as:
1. **TL;DR** — 2-3 sentence summary of what was found.
2. **Core Findings** — bulleted list of specific facts with citations.
3. **Recommended Action** — concrete next step for the kent-ai codebase.
4. **Open Questions** — what still needs investigation.

---

## Kent-AI Research Priorities (from Context/PROGRESS.md)

| Priority | Topic |
|---|---|
| HIGH | BIO F1 benchmarks for clinical NER (target ≥ 88%) |
| HIGH | Top-k recall benchmarks for dense retrieval on medical text |
| MEDIUM | LLaMA 3 prompt engineering for structured clinical case generation |
| MEDIUM | Evaluation metrics for synthetic clinical case quality |
| LOW | Alternative embedding models to Bio_ClinicalBERT |

---

## Output Format

Deliver research findings as a structured markdown document saved to:
`Context/research_<topic>_<YYYY-MM-DD>.md`

Do NOT modify any existing `Context/` file — create a new research note file.

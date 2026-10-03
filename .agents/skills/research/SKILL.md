---
name: research
description: >
  Structured literature and technical research workflow for kent-ai.
  Use when investigating a new technique, benchmarking an approach,
  comparing models, or grounding a design decision in published work.
  Selects the authoritative source for each question type. Outputs
  are strictly grounded in retrieved sources — no hallucination.
---

# Research Skill — Kent-AI

## Core Rule
**Only assert facts that can be traced to a retrieved source.**
If a claim cannot be verified, mark it `[UNVERIFIED]` and flag it for the user.

---

## Research Workflow

### Phase 1 — Define the Research Question
Write a single, precise question before selecting a source. Examples:
- Bad: "How does NER work?"
- Good: "What is the token-level F1 of Bio_ClinicalBERT on the i2b2-2010 NER benchmark compared to the base BERT model?"

### Phase 2 — Choose the Right Source

Pick the **most authoritative source** for the question type. Do not default to arXiv for everything.

| Question Type | Primary Source |
|---|---|
| Model performance benchmarks | Original paper (arXiv / ACL Anthology) + model card |
| Bio_ClinicalBERT architecture | [HuggingFace model card](https://huggingface.co/emilyalsentzer/Bio_ClinicalBERT) |
| ChromaDB API / behaviour | [ChromaDB official docs](https://docs.trychroma.com/) |
| LLaMA 3 capabilities | [Meta AI blog](https://ai.meta.com/blog/meta-llama-3/) + model card |
| sentence-transformers embedding dim | [HuggingFace model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) |
| Ollama REST API | [Ollama GitHub API docs](https://github.com/ollama/ollama/blob/main/docs/api.md) |
| Streamlit behaviour | [Streamlit official docs](https://docs.streamlit.io/) |
| Clinical NLP papers | PubMed / Europe PMC / ACL Anthology |
| General NLP/ML preprints | arXiv (cs.CL, cs.LG) |
| Homeopathic repertory structure | Kent's Repertory source materials + `Context/DATA.md` |

### Phase 3 — Extract and Organise

For each relevant source:

```markdown
**Source**: <Title> (<Year>) — <URL or DOI>
**Relevance**: <One sentence on why it's relevant>
**Key Finding**: <The specific fact/number/method extracted>
**Applicability**: <How it applies to kent-ai>
**Verified**: Yes | [UNVERIFIED]
```

### Phase 4 — Synthesise

Produce a short synthesis structured as:
1. **TL;DR** — 2-3 sentence summary of what was found.
2. **Core Findings** — bulleted list of specific facts with source citations.
3. **Recommended Action** — concrete next step for the kent-ai codebase.
4. **Open Questions** — what still needs investigation.

---

## Kent-AI Research Priorities (from Context/PROGRESS.md)

| Priority | Topic | Current Target |
|---|---|---|
| HIGH | Bio_ClinicalBERT NER F1 on clinical text | ≥ 88% token-level F1 (Phase 3) |
| HIGH | ChromaDB cosine retrieval Top-20 recall | top_k=20 (configs/chromadb.yaml) |
| MEDIUM | LLaMA 3 prompt engineering for 7-dim case generation | 4 variations/rubric, < 45% Jaccard overlap |
| MEDIUM | Synthetic case quality metrics | BIO offset accuracy ≥ 98%, diversity > 55% |
| LOW | Alternative sentence embedding models | Current: all-MiniLM-L6-v2 (384-dim, cosine) |

---

## Output

Save research findings as a new markdown document (do NOT edit existing Context files):

```
Context/research_<topic>_<YYYY-MM-DD>.md
```

Follow the file format from `Context/CONTEXT_RULES.md`:
- Title H1 + blockquote (Last updated, Phase).
- Tables for structured comparisons.
- Mark unverified claims with `[UNVERIFIED]`.
- Use code blocks for model names, API calls, numbers.

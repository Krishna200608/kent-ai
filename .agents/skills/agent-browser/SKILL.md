---
name: agent-browser
description: >
  Browser automation and web research skill for kent-ai agent tasks.
  Use when you need to navigate to a URL, extract content from a webpage,
  verify a live endpoint, or interact with a web-based tool (e.g., HuggingFace
  model pages, arXiv, ClinicalTrials.gov). Covers safe browsing, content
  extraction, and session hygiene.
---

# Agent Browser Skill — Kent-AI

## When to Use
- Fetching a paper abstract or PDF from arXiv / PubMed / ACL Anthology.
- Verifying a HuggingFace model card (e.g., Bio_ClinicalBERT, LLaMA 3).
- Checking a live API endpoint or documentation page.
- Downloading a dataset or supplementary file from a research URL.

## When NOT to Use
- For database lookups — use the dedicated science skills (pubmed-database,
  literature-search-arxiv, etc.) instead.
- For tasks that can be done with `read_url_content` — prefer that for
  simple static page fetches (no JavaScript required).

---

## Workflow

### Step 1 — Choose the Right Tool
| Need | Tool |
|---|---|
| Static HTML page | `read_url_content` (faster, no browser overhead) |
| JavaScript-rendered page | `browser_subagent` |
| Interaction required (click, type) | `browser_subagent` |
| Bulk URL batch | `read_url_content` in sequence |

### Step 2 — Launch the Browser Subagent
When using `browser_subagent`, always specify:
- `TaskName`: Human-readable, e.g., "Fetching Bio_ClinicalBERT Model Card"
- `Task`: Include the exact URL, what to extract, and when to stop.
- `RecordingName`: Snake_case, ≤ 3 words, e.g., `model_card_fetch`
- `ReturnsCondition`: "Return when the page content is fully loaded and the
  target information has been extracted."

### Step 3 — Extract Structured Data
Ask the subagent to return information in a structured format:
```
Return a JSON object with keys:
  - title: page title
  - summary: 2-3 sentence summary
  - key_facts: list of relevant facts
  - url: the final URL visited
```

### Step 4 — Close the Browser
Always instruct the subagent: "Close all browser tabs when done."
This is a hard rule per project conventions (Context/CONVENTIONS.md).

---

## Safety Rules

- Do NOT submit forms or POST data unless explicitly instructed by the user.
- Do NOT download executable files.
- Do NOT authenticate to services without user-provided credentials.
- Do NOT follow more than 3 redirect hops.
- If a page requires login, report the URL and stop — escalate to the user.

---

## Useful URLs for Kent-AI Research

| Resource | URL |
|---|---|
| Bio_ClinicalBERT (HuggingFace) | https://huggingface.co/emilyalsentzer/Bio_ClinicalBERT |
| LLaMA 3 (Meta) | https://ai.meta.com/blog/meta-llama-3/ |
| ChromaDB Docs | https://docs.trychroma.com/ |
| i2b2 NLP Challenges | https://www.i2b2.org/NLP/DataSets/ |
| Streamlit Docs | https://docs.streamlit.io/ |
| Kent's Repertory (reference) | https://www.homeobook.com/kents-repertory/ |

---

## Output
Save any extracted content as a markdown file in:
`Context/browser_research_<topic>_<YYYY-MM-DD>.md`

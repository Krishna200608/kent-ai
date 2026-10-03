---
name: agent-browser
description: >
  Browser automation and web research skill for kent-ai agent tasks.
  Use when you need to navigate to a URL that requires JavaScript rendering
  or user interaction (clicking, typing, scrolling). For static HTML pages,
  prefer read_url_content directly. Covers safe browsing, content extraction,
  and mandatory session hygiene.
---

# Agent Browser Skill — Kent-AI

## When to Use
- A documentation page or model card requires JavaScript to render.
- You need to interact with a web page (click a tab, submit a search form).
- You need to verify a live web endpoint or download a file not accessible via direct URL.

## When NOT to Use
- The page is static HTML (no JavaScript required) → use `read_url_content` instead (faster, no overhead).
- You only need to query a database API → use the appropriate science skill (e.g., `pubmed-database`, `literature-search-arxiv`).
- You need to search for research papers → use `research` skill first, which selects the right tool.

---

## Tool Selection

| Need | Tool |
|---|---|
| Static HTML page (docs, GitHub, arXiv abstract) | `read_url_content` |
| JavaScript-rendered page | `browser_subagent` |
| Clicking, typing, or interacting | `browser_subagent` |
| Batch URL reading | `read_url_content` in sequence |

---

## Browser Subagent Workflow

### Step 1 — Launch with a Complete Task Description
When using `browser_subagent`, always specify:
- **`TaskName`**: Human-readable, e.g., "Fetching Bio_ClinicalBERT Model Card"
- **`Task`**: Include the exact URL, what content to extract, and the stop condition.
- **`RecordingName`**: Snake_case, ≤ 3 words, e.g., `model_card_fetch`

### Step 2 — Specify Exact Extraction Requirements
Tell the subagent explicitly what to return:
```
Navigate to <URL>.
Extract the following: <model name>, <description>, <license>, <usage example>.
Return a structured summary with those fields.
Stop when the content is fully visible.
```

### Step 3 — Mandatory: Close the Browser
Always end the task instruction with: **"Close all browser tabs when done."**
This is a hard requirement per project conventions (Context/CONVENTIONS.md — resource hygiene).

---

## Safety Rules

- Do NOT submit forms or POST data unless explicitly instructed.
- Do NOT download executable files.
- Do NOT authenticate to any service without user-provided credentials.
- If a page requires login, report the URL and stop — escalate to the user.
- Do not follow redirect chains longer than 3 hops.

---

## Useful URLs for Kent-AI Research

| Resource | URL |
|---|---|
| Bio_ClinicalBERT (HuggingFace) | https://huggingface.co/emilyalsentzer/Bio_ClinicalBERT |
| LLaMA 3 (Meta AI blog) | https://ai.meta.com/blog/meta-llama-3/ |
| ChromaDB Docs | https://docs.trychroma.com/ |
| sentence-transformers all-MiniLM-L6-v2 | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 |
| Streamlit Docs | https://docs.streamlit.io/ |
| Ollama API | https://github.com/ollama/ollama/blob/main/docs/api.md |

---

## Output

Save extracted content to:
`Context/browser_research_<topic>_<YYYY-MM-DD>.md`

Follow the Context file authoring rules from `Context/CONTEXT_RULES.md`:
- Start with title H1 and blockquote (Last updated, Phase).
- Mark unverified claims with `[UNVERIFIED]`.
- Do NOT overwrite or modify existing Context files.

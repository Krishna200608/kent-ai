# Context File Authoring Rules

> **Audience**: Any AI agent (or human contributor) that modifies this repository.
> **Purpose**: Ensure every agent can bootstrap project understanding from `Context/` alone, and keep the files accurate over time.

---

## 1. Why Context Files Exist

Context files are **the single source of truth** for an AI agent arriving cold to this repository. They answer:
- *What is this project?* → `PROJECT.md`
- *How is the code structured?* → `ARCHITECTURE.md`
- *What does the data look like?* → `DATA.md`
- *What coding patterns should I follow?* → `CONVENTIONS.md`
- *What has been done and what remains?* → `PROGRESS.md`
- *What gotchas will burn me?* → `GOTCHAS.md`

An agent that reads these 6 files should be able to make a correct, style-consistent code contribution without reading every source file first.

---

## 2. File Format Rules

### 2.1 Structure

Every context file MUST follow this skeleton:

```markdown
# <TITLE>

> Last updated: YYYY-MM-DD by <agent-name or human-name>
> Phase: <current phase number>

---

## Section 1
...
## Section 2
...

---
_End of file._
```

### 2.2 Header Metadata

Every file MUST begin with:
- **Title** as H1
- **Blockquote** containing:
  - `Last updated:` — ISO date of the last meaningful edit
  - `Phase:` — The project phase number at time of writing (e.g., `Phase 0`)

This metadata lets agents quickly gauge staleness.

### 2.3 Formatting Constraints

| Rule | Rationale |
|---|---|
| Use **Markdown tables** for structured data (schemas, stats, comparisons) | Agents parse tables more reliably than prose |
| Use **fenced code blocks** with language tags for all code, SQL, YAML | Prevents misinterpretation of special characters |
| Keep bullet points to **one line each** — no line-wrapping | Agents tokenize wrapped bullets poorly |
| Use `>` blockquotes for **warnings and gotchas** only | Reserves visual weight for critical info |
| Never embed images — use text descriptions or ASCII art | Images are invisible to text-only agents |
| Use H2 (`##`) for major sections, H3 (`###`) for subsections | Deeper heading levels signal "you can skip this" |

### 2.4 Content Rules

| Rule | Bad Example | Good Example |
|---|---|---|
| State **exact numbers**, never "many" or "several" | "There are many rubrics" | "There are 74,513 rubrics" |
| Include **verified** facts only; cite file paths | "The DB is somewhere in data/" | "`data/raw/repertory.sqlite` (112 MB, hardlink)" |
| Use **absolute import paths** when referencing code | "the kent module" | "`src.data.kent_db.get_mind_rubrics()`" |
| Mark uncertain info with `[UNVERIFIED]` | *(omitting uncertainty)* | "FTS5 index may be stale after bulk inserts [UNVERIFIED]" |
| If a number or path could change, add the **query/command** to re-derive it | "4,933 MIND rubrics" | "4,933 MIND rubrics (`SELECT COUNT(*) FROM rubrics WHERE section_id=1`)" |

---

## 3. When to Update

### 3.1 Mandatory Triggers

You MUST update the relevant context file(s) when you:

| Action | Files to Update |
|---|---|
| Complete a roadmap phase or milestone | `PROGRESS.md` |
| Add/rename/delete a source module | `ARCHITECTURE.md` |
| Change database schema or add new tables | `DATA.md` |
| Introduce a new coding pattern or deviate from an existing one | `CONVENTIONS.md` |
| Discover a bug, limitation, or non-obvious behavior | `GOTCHAS.md` |
| Change project scope, goals, or team | `PROJECT.md` |

### 3.2 Update Procedure

1. **Read the existing file first.** Do not rewrite from scratch unless the file is fundamentally wrong.
2. **Edit surgically.** Change only the sections affected by your work. Preserve unrelated sections verbatim.
3. **Bump the `Last updated` date and `Phase` number** in the header blockquote.
4. **Add a changelog entry** at the bottom of the file if it has a `## Changelog` section.
5. **Run the verification command** listed at the bottom of each file (if any) to confirm accuracy.

### 3.3 Prohibition

- **Never delete information** unless it is factually wrong. If something becomes obsolete, move it under a `### Deprecated` subsection — do not erase it.
- **Never change the filename** of an existing context file. Other agents and rules may reference it by name.

---

## 4. Adding a New Context File

If you need a context file for a topic not covered by the existing six:

1. Name it with a clear, uppercase noun: `DEPLOYMENT.md`, `SECURITY.md`, etc.
2. Follow the skeleton from §2.1.
3. Add a one-line entry to the table in `PROJECT.md` § "Context File Index."
4. Consider whether the information truly cannot live in an existing file before creating a new one.

---

## 5. Quality Checklist

Before committing any context file update, verify:

- [ ] `Last updated` date is today's date
- [ ] `Phase` matches the current project phase
- [ ] All file paths referenced actually exist on disk
- [ ] All numeric stats have a re-derivation query or command
- [ ] No line exceeds ~120 characters (for terminal readability)
- [ ] Tables render correctly in standard Markdown viewers
- [ ] No TODO/FIXME markers left without a tracking phase

---

_End of file._

---
name: skill-creator
description: >
  Creates new agent skills for the kent-ai .agents/skills/ directory.
  Use when the user asks to package a workflow, interaction, or process
  as a reusable skill, or when a new recurring task pattern is identified
  that would benefit from standardised agent instructions. Always inspects
  the repository and all existing skills before creating anything new.
---

# Skill Creator Skill — Kent-AI

## What is a Skill?
A skill is a directory under `.agents/skills/<skill-name>/` containing
a `SKILL.md` file with YAML frontmatter and markdown instructions.
The agent reads `SKILL.md` before executing the skill's workflow.

---

## Mandatory First Step: Inspect Before Creating

Before drafting a new skill, you MUST:

1. **List all existing skills**:
   ```
   .agents/skills/
   ```
   Check for any skill that already covers the proposed task, even partially.

2. **Read relevant existing SKILL.md files** if names overlap.

3. **Read the repository context**:
   - `Context/ARCHITECTURE.md` — to ground any path or module references.
   - `Context/CONVENTIONS.md` — to ensure the skill enforces project style.
   - `Context/PROGRESS.md` — to understand current phase and active work.

4. **Only proceed if no existing skill covers the need** and no existing skill would be made contradictory by the new one.

---

## Existing Skills (Do Not Duplicate or Contradict)

**Kent-AI domain skills:**
- `case-generation-watcher` — Monitors/audits the LLaMA 3 generation pipeline
- `chromadb-rubric-tester` — Validates ChromaDB index over 74,513 rubrics
- `context-protocol-sync` — Enforces updates across all Context/ files
- `eval-metric-parser` — Executes and parses evaluation metrics
- `kent-repertory-inspector` — Queries and debugs the Kent SQLite database

**Engineering skills:**
- `tdd` — Red-Green-Refactor TDD workflow with pytest
- `diagnosing-bugs` — 4-step bug diagnosis ladder
- `code-review` — Full review checklist
- `codebase-design` — Architecture enforcement and DDR template
- `research` — Source-grounded literature and technical research
- `improve-codebase-architecture` — Safe refactoring workflow
- `frontend-design` — Streamlit UI conventions and design system
- `agent-browser` — Browser automation for JS-rendered pages
- `skill-creator` — This skill (meta: creates new skills)
- `domain-modeling` — Rubric/entity schema and BIO label conventions

---

## Skill Creation Workflow

### Step 1 — Identify the Skill Boundary
A good skill:
- Solves one recurring, well-defined task.
- Has a clear trigger condition ("Use when...").
- Has a clear stop condition ("Stop when...").
- Does NOT duplicate an existing skill (verified above).
- Does NOT contradict guidance in an existing skill.

### Step 2 — Draft the SKILL.md

```markdown
---
name: <skill-name>                  # kebab-case, matches directory name exactly
description: >
  <One paragraph. Start with the primary use case.
  Include trigger conditions. Include what NOT to use it for.>
---

# <Skill Title> — Kent-AI

## Purpose
<Why this skill exists. What problem it solves.>

## When to Use
- <Trigger condition 1>
- <Trigger condition 2>

## When NOT to Use
- <Anti-pattern or overlapping skill>

## Workflow
### Step 1 — ...
### Step 2 — ...

## Definition of Done
- [ ] <Verifiable completion criterion 1>
- [ ] <Verifiable completion criterion 2>
```

### Step 3 — Validate Before Writing

- [ ] `name` in frontmatter matches the directory name exactly.
- [ ] `description` starts with a use-case statement ("Use when...", "Guides...", "Monitors...").
- [ ] Every path referenced (`src/`, `configs/`, `Context/`, `tests/`) actually exists in the repo.
- [ ] BIO labels used only from the 15-class system (`O`, `B-LOC`, `I-LOC`, ..., `B-MENT`, `I-MENT`).
- [ ] Config directory referenced as `configs/`, not `config/`.
- [ ] No invented module names — verify against `Context/ARCHITECTURE.md`.
- [ ] No duplicate of an existing skill.
- [ ] No contradiction with an existing skill's guidance.

### Step 4 — Create the File

```
.agents/skills/<skill-name>/SKILL.md
```

Only create additional files if the skill genuinely requires supporting resources
(e.g., a `scripts/` helper). Keep skills self-contained.

### Step 5 — Report

After creation, report:
```
Created skill: .agents/skills/<skill-name>/SKILL.md
Trigger      : "<first line of description>"
Checked for duplicates: None found
Checked for contradictions: None found
```

---

## Naming Convention

All skill names must be **kebab-case** and **all-lowercase**.

| Pattern | Example |
|---|---|
| `<domain>-<action>` | `kent-repertory-inspector` |
| `<process>-<noun>` | `case-generation-watcher` |
| `<verb>-<noun>` (generic) | `diagnosing-bugs`, `code-review` |

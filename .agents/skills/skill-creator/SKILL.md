---
name: skill-creator
description: >
  Creates new agent skills for the kent-ai .agents/skills/ directory.
  Use when the user asks to package a workflow, interaction, or process
  as a reusable skill, or when a new recurring task pattern is identified
  that would benefit from standardised agent instructions.
---

# Skill Creator Skill — Kent-AI

## What is a Skill?
A skill is a directory under `.agents/skills/<skill-name>/` containing
a `SKILL.md` file with YAML frontmatter and markdown instructions.
The agent reads `SKILL.md` before executing the skill's workflow.

---

## Skill Creation Workflow

### Step 1 — Identify the Skill Boundary
A good skill:
- Solves one recurring, well-defined task.
- Has a clear trigger condition ("Use when...").
- Has a clear termination condition ("Stop when...").
- Does NOT overlap with an existing skill (check `.agents/skills/`).

### Step 2 — Draft the SKILL.md

```markdown
---
name: <skill-name>                  # kebab-case, matches directory name
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
### Step N — ...

## Output / Definition of Done
- [ ] <Verifiable completion criterion 1>
- [ ] <Verifiable completion criterion 2>
```

### Step 3 — Validate

Before writing the file, verify:
- [ ] `name` in frontmatter matches the directory name exactly.
- [ ] `description` starts with a use-case verb ("Use when", "Guides", "Monitors").
- [ ] No duplicate of an existing skill in `.agents/skills/`.
- [ ] The skill does NOT instruct the agent to modify source code directly
      (skills are instructions, not code generators, unless specifically required).
- [ ] References to `Context/` files use correct relative paths.

### Step 4 — Create the File

```
.agents/skills/<skill-name>/SKILL.md
```

Do NOT create any other files unless the skill requires supporting resources
(e.g., a `scripts/` or `examples/` subdirectory with a clear purpose).

### Step 5 — Register / Announce

After creation, report:
```
Created skill: .agents/skills/<skill-name>/SKILL.md
Trigger: "<first line of description>"
Conflicts with existing skills: None / <list>
```

---

## Kent-AI Skill Naming Convention

| Pattern | Example |
|---|---|
| `<domain>-<action>` | `kent-repertory-inspector` |
| `<process>-<noun>` | `case-generation-watcher` |
| `<verb>-<noun>` (generic) | `diagnosing-bugs`, `code-review` |

All skill names must be **kebab-case** and **all-lowercase**.

---

## Existing Skills (Do Not Duplicate)

**Kent-AI domain skills:**
- `case-generation-watcher`
- `chromadb-rubric-tester`
- `context-protocol-sync`
- `eval-metric-parser`
- `kent-repertory-inspector`

**Engineering skills:**
- `tdd`, `diagnosing-bugs`, `code-review`, `codebase-design`
- `research`, `improve-codebase-architecture`, `frontend-design`
- `agent-browser`, `skill-creator`, `domain-modeling`

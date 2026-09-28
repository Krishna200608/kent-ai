# Kent-AI — Design System & UX Specification (Google Stitch Standard)

> **Standard**: Google Stitch UI/UX Design System Specification
> **Theme**: Modern Clinical Emerald & Deep Midnight Slate
> **Target**: Streamlit Clinical Dashboard (`src/dashboard/app.py`)

---

## 1. Visual Identity & Brand Philosophy

Kent-AI bridges classical 19th-century homeopathic medical repertorization with 21st-century artificial intelligence.
- **Tone**: Calm, trustworthy, clinical, empathetic, and technologically sophisticated.
- **Aesthetic**: Sleek dark mode, frosted glass surfaces (`backdrop-filter: blur`), subtle emerald glowing accents, crisp typography, and clean data density.

---

## 2. Design Tokens

### 2.1 Color Palette

| Token | Hex Value | Purpose / Meaning |
|---|---|---|
| `--bg-canvas` | `#0A0F1D` | Deep midnight canvas background |
| `--bg-surface` | `#111827` | Primary card & container surface |
| `--bg-surface-elevated` | `#1F2937` | Hover states, dropdowns, elevated panels |
| `--border-subtle` | `rgba(255, 255, 255, 0.08)` | Minimal glass border separation |
| `--border-accent` | `rgba(16, 185, 129, 0.3)` | Emerald active focus border |
| `--primary-emerald` | `#10B981` | Core brand, vitality, confirmed remedies (Grade 3) |
| `--accent-teal` | `#06B6D4` | AI intelligence, dense similarity match, Grade 2 remedies |
| `--accent-purple` | `#8B5CF6` | Mental & emotional symptoms (`MENT`) |
| `--warning-amber` | `#F59E0B` | Modalities - Aggravations (`MOD_AGG`) |
| `--success-mint` | `#34D399` | Modalities - Ameliorations (`MOD_AMEL`) |
| `--danger-rose` | `#F43F5E` | Negated symptoms, active exclusions |
| `--text-primary` | `#F9FAFB` | High-contrast headers, values, emphasis |
| `--text-secondary` | `#9CA3AF` | Supporting descriptions, metadata labels |
| `--text-muted` | `#8492A6` | Subtle hints, footnotes (WCAG AA 5.61:1 compliant, replacing legacy `#6B7280`) |
| `--badge-why-hint-bg` | `rgba(255, 255, 255, 0.12)` | Inline explainability why? affordance pill |
| `--session-popover-bg` | `#111827` | Consolidated session telemetry popover background |
| `--disclaimer-bg` | `rgba(17, 24, 39, 0.5)` | Persistent low-emphasis clinical disclaimer background |

### 2.2 Typography Hierarchy

- **Font Family**: `'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Headings**:
  - `H1 (Page Title)`: 28px / 700 bold / `letter-spacing: -0.02em`
  - `H2 (Section Header)`: 20px / 600 semi-bold / `letter-spacing: -0.01em`
  - `H3 (Card Title)`: 16px / 600 semi-bold
- **Body & Data**:
  - `Body Regular`: 14px / 400 normal / line-height 1.5
  - `Clinical Monospace (Rubric IDs, Tokens)`: `'Fira Code', 'JetBrains Mono', monospace` / 12px

---

## 3. Component Anatomy

### 3.1 Glassmorphic Cards (`.stGlassCard`)
```css
background: rgba(17, 24, 39, 0.75);
backdrop-filter: blur(16px);
-webkit-backdrop-filter: blur(16px);
border: 1px solid rgba(255, 255, 255, 0.08);
border-radius: 12px;
padding: 20px;
box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
```

### 3.2 Canonical 7-Dimension Clinical Badges & Reference

| Dimension Code | Key | Canonical Label | What it Captures | Example | Badge Class | Text Color |
|---|---|---|---|---|---|---|
| `LOC` | `location` | Location | Body part/region | "Right side of head" | `.badge-loc` | `#22D3EE` (Cyan) |
| `SEN` | `sensation` | Sensation | Type of feeling | "Pressing, throbbing, burning" | `.badge-sen` | `#34D399` (Emerald) |
| `MOD_AGG` | `modality_agg` | Worse from (aggravation) | Aggravating factors or triggers | "Worse in morning, worse cold" | `.badge-agg` | `#FBBF24` (Amber) |
| `MOD_AMEL` | `modality_amel` | Better from (amelioration) | Relieving or soothing factors | "Better by pressure, fresh air" | `.badge-amel` | `#6EE7B7` (Mint) |
| `CONC` | `concomitant` | Concomitant | Accompanying symptoms | "With nausea and anxiety" | `.badge-conc` | `#F472B6` (Pink) |
| `TEMP` | `temporal` | Time pattern | Time patterns and periodicity | "Worse at midnight, periodic" | `.badge-temp` | `#60A5FA` (Blue) |
| `MENT` | `mental` | Mental/Emotional | Psychological state | "Irritable, restless at night" | `.badge-ment` | `#A78BFA` (Purple) |
| `NEG` | `negated` | Negated / Denied | Ruled out symptoms | "No fever, denied nausea" | `.badge-neg` | `#F87171` (Rose) |

### 3.3 Semantic Match Tiers & Calibrated Cutoffs

| Match Tier | Similarity Range | Badge Class | Color | Default Visibility |
|---|---|---|---|---|
| **Strong match** | $\ge 0.68$ | `.match-strong` | `#34D399` (Emerald) | Visible |
| **Good match** | $0.58\text{--}0.679$ | `.match-good` | `#38BDF8` (Sky) | Visible |
| **Fair match** | $0.52\text{--}0.579$ | `.match-fair` | `#FBBF24` (Amber) | Visible |
| **Weak match** | $< 0.52$ | `.match-weak` | `#9CA3AF` (Muted) | Hidden by default (toggle: `< 0.52`) |

### 3.4 Remedy Grade Indicators (Classical Kentian)
- **Grade 3 (Bold / Verified)**: `#10B981` (Vibrant Emerald with bold weight)
- **Grade 2 (Italics / Qualified)**: `#06B6D4` (Teal italic badge)
- **Grade 1 (Plain / Clinical)**: `#8492A6` (Muted silver badge, WCAG AA compliant 5.61:1, upgraded from `#6B7280`)

---

## 4. Layout Architecture

1. **Header Bar**:
   - Logo: Glowing emerald leaf (`🌿 Kent-AI`).
   - Consolidated Session Telemetry: Compact pill with expandable hover popover for active scope, Ollama LLM (`llama3:8b`), and database metrics (`74,513 rubrics indexed`).
2. **Main Navigation**:
   - 💬 **Live Patient Intake**: Interactive consultation with live slot extraction and 1-click repertorization.
   - 📊 **Clinical Repertorization**: Multi-rubric totality matrix, Plotly remedy ranking chart, and primary simillimum spotlight.
   - 🔍 **Rubric Explorer**: Search all 74,513 rubrics with hybrid dense + FTS5 search, chapter filters, and remedy inspector.
   - 💊 **Materia Medica**: Remedy dictionary browser with abbreviations, synonyms, and characteristic rubrics.

---

## 5. Accessibility & WCAG AA Contrast Audit (Task 6)

All 7 dimension badges evaluated against `--bg-surface` (`#111827`) blended with 15% alpha background:
- **WCAG AA Threshold**: Minimum 4.5:1 for standard body text.
- **Results**:
  - `LOC`: 7.74:1 (PASS)
  - `SEN`: 7.31:1 (PASS)
  - `MOD_AGG`: 8.25:1 (PASS)
  - `MOD_AMEL`: 8.71:1 (PASS)
  - `CONC`: 5.73:1 (PASS)
  - `TEMP`: 5.84:1 (PASS)
  - `MENT`: 5.56:1 (PASS)
  - `NEG`: 5.60:1 (PASS)
- **Contrast Remediation**:
  - Legacy `--text-muted` (`#6B7280`) measured **3.67:1** against `#111827` (FAIL).
  - Remediated to `#8492A6` (**5.61:1**, PASS) and `#9CA3AF` (**7.31:1**, PASS) across dashboard footers, timestamps, and Grade 1 badges.

---

_End of file._


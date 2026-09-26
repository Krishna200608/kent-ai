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
| `--text-muted` | `#6B7280` | Subtle hints, timestamps, footnotes |

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

### 3.2 7-Dimension Clinical Pill Badges

| Dimension | Class | Background | Text Color |
|---|---|---|---|
| `LOC` (Location) | `.badge-loc` | `rgba(6, 182, 212, 0.15)` | `#22D3EE` (Cyan) |
| `SEN` (Sensation) | `.badge-sen` | `rgba(16, 185, 129, 0.15)` | `#34D399` (Emerald) |
| `MOD_AGG` (Aggravation) | `.badge-agg` | `rgba(245, 158, 11, 0.15)` | `#FBBF24` (Amber) |
| `MOD_AMEL` (Amelioration) | `.badge-amel`| `rgba(52, 211, 153, 0.15)` | `#6EE7B7` (Mint) |
| `CONC` (Concomitant) | `.badge-conc`| `rgba(236, 72, 153, 0.15)` | `#F472B6` (Pink) |
| `TEMP` (Temporal) | `.badge-temp`| `rgba(59, 130, 246, 0.15)` | `#60A5FA` (Blue) |
| `MENT` (Mental) | `.badge-ment`| `rgba(139, 92, 246, 0.15)` | `#A78BFA` (Purple) |
| `NEGATED` (Denied) | `.badge-neg` | `rgba(239, 68, 68, 0.15)` | `#F87171` (Rose) |

### 3.3 Remedy Grade Indicators (Classical Kentian)
- **Grade 3 (Bold / Verified)**: `#10B981` (Vibrant Emerald with bold weight)
- **Grade 2 (Italics / Qualified)**: `#06B6D4` (Teal italic badge)
- **Grade 1 (Plain / Clinical)**: `#6B7280` (Muted silver badge)

---

## 4. Layout Architecture

1. **Header Bar**:
   - Logo: Glowing emerald leaf (`🌿 Kent-AI`).
   - Status indicators: Model (`llama3:8b`), ChromaDB Vector Store (`74,513 rubrics indexed`), DB status (`Connected`).
2. **Main Navigation**:
   - 💬 **Live Patient Intake**: Interactive consultation with live slot extraction and 1-click repertorization.
   - 📊 **Clinical Repertorization**: Multi-rubric totality matrix, Plotly remedy ranking chart, and primary simillimum spotlight.
   - 🔍 **Rubric Explorer**: Search all 74,513 rubrics with hybrid dense + FTS5 search, chapter filters, and remedy inspector.
   - 💊 **Materia Medica**: Remedy dictionary browser with abbreviations, synonyms, and characteristic rubrics.

---

_End of file._

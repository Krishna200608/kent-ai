<USER_REQUEST>
# Kent-AI: UI/UX overhaul brief (for the IDE agent)

You are working on **kent-ai**, a Streamlit clinical decision-support *research* app for classical homeopathic repertorization (Kent). It uses a local Ollama LLM, SQLite case storage, and vector + exact search over 74,513 rubrics. Case flow: Intake → Review → Analysis → Report. Top-level areas: Case Workspace, Case Library, Rubric Explorer, Materia Medica, Settings & Methodology, plus a sidebar.

This brief comes from a UI/UX audit of screenshots. Implement it in the phases below.

---

## Ground rules

1. **Explore before editing.** Do not assume file names or structure. Locate the code for each screen, the CSS, the `st.session_state` keys, and the DB schema first (Phase 0).
2. **UI, state and presentation only.** Do NOT change scoring, NLP extraction, retrieval/ranking defaults, or DB semantics. If a change needs backend work (lazy case creation, tray persistence), make the smallest backward-compatible change (additive, idempotent migrations; the existing ~81 cases must still open) and list it in the final report.
3. **Check the pinned Streamlit version first.** Use newer APIs (`st.navigation`, `st.fragment`, `st.dialog`, `st.popover`, `st.toast`, `st.status`, `st.segmented_control`, `st.container(key=...)`) only if available. Otherwise use the closest fallback and note it.
4. **Single source of truth.** Create one constants module holding: the 7 canonical dimensions (key, label, hint, order, recommended flag), grade weights, scope definitions (counts included), the model display name (derived from the actually configured model), and the app version. Every screen, including the Methodology page, imports from it. No hard-coded duplicates.
5. **One stylesheet.** All CSS lives in one file loaded once, built on CSS variables (tokens below). Target stable hooks (`st.container(key=...)` → `.st-key-*`, `data-testid`), never hashed Streamlit class names. No inline-style duplication.
6. **Keep the research disclaimer.** Consolidate it; never delete it.
7. **No new heavy dependencies.** The app must keep working offline. Self-host fonts (`server.enableStaticServing = true`, files under `static/`) with system-font fallbacks.
8. **Work phase by phase.** After each phase: run the app, fix errors, run existing tests, list changed files, and commit (`ui: phase N – <summary>`). No single giant diff.
9. **If something is ambiguous**, choose the safer option, record it under "Assumptions" in `docs/ui/UI_CHANGELOG.md`, and keep going.

---

## Design tokens (put in the stylesheet)

```css
:root {
  --bg: #0B1117;
  --surface: #121A23;
  --surface-2: #182330;
  --line: #243243;
  --text: #E8EDF3;
  --text-muted: #A3B0C2;     /* ≥4.5:1 on all surfaces */
  --text-faint: #8A98AE;     /* decorative/secondary only */
  --accent: #10B981;         /* primary actions + "captured/online" state ONLY */
  --accent-hover: #34D399;
  --accent-ink: #03160F;     /* text ON accent fills (≈7:1) */
  --accent-soft: rgba(16, 185, 129, 0.14);
  --info: #5BB8F0;
  --warn: #F5B94A;
  --danger: #F26D6D;
  --radius-sm: 6px; --radius-md: 10px; --radius-lg: 14px;
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-6: 24px; --space-8: 32px;
  --font-ui: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-rubric: "Source Serif 4", Georgia, "Times New Roman", serif;
}
```

**Typography:**
- UI text uses `--font-ui`.
- Rubric paths and remedy names use `--font-rubric`.
- Base size 15px, secondary 13px, **minimum 12px anywhere**.
- Line length under 80ch.
- Do not use ALL-CAPS, letter-spaced, or monospace styling for small labels (dimension cards, chips). Monospace is only for IDs such as `CASE-2026-090`.
- Keep the repertory convention for grades: **Grade 3 = bold, Grade 2 = italic, Grade 1 = roman**. Because italic already means Grade 2, never italicise remedy names for any other reason.

**Colour discipline:** green is for primary buttons, the current step, and captured/online states. Do not use it on headings, borders, tab outlines, or decorative chips. Borders use `--line`. Limit nesting to two levels of bordered containers.

**Signature element:** a **7-segment totality ring** (SVG, one segment per dimension, lit when captured). Build one reusable `totality_ring(captured_keys, size)` and use it in the case bar, the sidebar active-case card, and Library rows.

**Canonical dimension labels** (sentence case, used everywhere, including the Methodology page):

| key | label | hint |
|---|---|---|
| mental | Mental/Emotional | Mood, fears, behaviour |
| location | Location | Where in the body |
| sensation | Sensation | What it feels like |
| worse | Worse from | What aggravates it |
| better | Better from | What relieves it |
| concomitant | Concomitants | Accompanying symptoms |
| time | Time pattern | When it occurs |

Map existing internal keys onto these; do not rename DB fields. Keep existing "recommended" flags. Additionally, when scope = MIND, flag Mental/Emotional as "paramount" and order it first (this matches the Methodology page). Note the decision in the changelog.

**Microcopy rules:**
- Sentence case. Verb-first actions ("Continue to review", "Start over", "Open", "Export").
- The same action keeps the same name through its flow (Save → toast "Saved").
- No "[Locked]", "(Recommended)" in parentheses, "?", or bare "—" placeholders. Use "Not set", "Not analysed yet", or omit the field.
- Dates are relative with a full-timestamp tooltip (e.g. "2 min ago" → "1 Nov 2026, 07:55").
- Correct plurals ("81 consultations").
- Model display name format: "Llama 3 8B" (derive it from config).
- Errors state what happened and what to do next. They never apologise.

---

## Phase 0: Audit (no code edits)

Write `docs/ui/UI_AUDIT_MAP.md` (≤1 page):
- For each screen: file/function, session_state keys, CSS hooks, DB tables used.
- Streamlit version and how navigation currently works (`st.tabs` vs other).
- Every place that currently renders: repertory scope, engine status, disclaimer, branding, the "x/7" count, the 7-dimension list, export/copy controls, patient details, and totality principles.
- Which statuses exist for cases (Draft / In review / Analysed / Reported?).

Then continue to Phase 1.

---

## Phase 1: Bug fixes

- [ ] **Stuck tooltip:** the stepper/Intake tooltip overlaps and clips the case bar in Paste notes. Fix z-index and positioning, or remove the tooltip in favour of the step sub-labels (Phase 2). Ensure the case bar has a min-height and `overflow: visible`.
- [ ] **Console heading collision:** "Kent-AI Clinical Companion Active" touches the panel's top border. Add padding, remove the redundant double border (outer container + inner panel).
- [ ] **Tabs/nav:** padding `10px 16px`; the active indicator is a 2px underline in `--accent` (not a box hugging the text).
- [ ] **Primary buttons:** text `--accent-ink` on `--accent`; define hover, active, disabled and loading states. Applies to Search Rubrics, Extract & review, Resume, + New Case, and the active step.
- [ ] **Focus:** global `:focus-visible` ring (2px `--accent`, 2px offset). Remove the default blue ring on text inputs and the chat input.
- [ ] **Placeholder leaks:** hide empty age/sex/"?"/"—". Rewrite the Library meta line and "Leading Remedy" (Phase 5).
- [ ] **Model name:** derive from config and render identically in the top bar, console, sidebar and Methodology (the app currently shows both "LLaMA 3:8B" and "LLaMA 3.1 8B"). Reconcile with what is actually configured.
- [ ] **Rubric breadcrumbs:** a `format_rubric_path()` renders every path with ` › ` at render time (do not mutate data). Investigate and fix the dropped trailing dot ("4 a.m" → "4 a.m.").
- [ ] **"Try an example" chips:** `flex-wrap`, or replace with a "Load example" select. No clipped chips.
- [ ] **Results slider:** remove it; replace with a segmented control 10 / 15 / 25 / 50 (Phase 6).
- [ ] **Heading anchors:** hide the auto-anchor link icon (`[data-testid="stHeaderActionElements"]`).
- [ ] **Lazy case creation:** do not insert a DB row on page open. Keep a draft in `session_state`; persist on the first captured dimension or an explicit Save. Library hides cases with 0 dimensions and 0 messages by default (Phase 5).

---

## Phase 2: Shell, navigation, case bar, stepper

1. **Top bar (single row, ≤56px)** replaces the large header card:
   - Left: leaf icon + "Kent-AI" wordmark.
   - Nav next to it.
   - Right: engine status pill (dot + model + latency; click → popover with endpoint, Test connection, Retry), a **Tray (n)** popover (mirrors the sidebar tray; works when the sidebar is collapsed), a read-only scope chip, and a Settings icon.
   - Move the long subtitle ("Classical Homeopathic Repertorization · Dr. J. T. Kent Framework") to the About section and the browser tab title.
2. **Navigation:** use `st.navigation` (top position if available) so each page runs only its own code. Fallback: `st.segmented_control` + conditional rendering. **Do not use `st.tabs`** (it executes every tab body on every rerun).
3. **Sticky case sub-header** (case bar + stepper):
   - Case bar: `[CASE-ID, copy]  [Patient label ✎ inline-editable]  [Saved hh:mm | Unsaved]  …  [totality ring + n/7]  [Patient info]  [Save]`.
   - "Patient info" opens one `st.dialog` (age, sex, chief complaint). Remove the duplicate "Optional: Patient details" expander in Paste notes.
4. **Stepper** (4 steps):
   - Each step shows an SVG icon for its state (current / complete ✓ / available / locked 🔒), a title, and a one-line sub-label: "Capture symptoms", "Confirm and edit", "Rank remedies", "Export report".
   - Locked steps show their reason on hover/focus (`aria-disabled`). No "[Locked]" text and no standalone hint line.
   - Review unlocks only when ≥1 dimension is captured, so the stepper and the Continue button always agree.
   - Current step = `--accent-soft` fill + accent border. No glow.
5. **Sticky bottom action bar** on every step: `Back · Save draft · Continue to <next step>`. Disabled with a reason when not ready.
6. **Footer:** one-line 12–13px muted disclaimer, not a full-width card. Add a first-run acknowledgement dialog (non-blocking, stored in settings).
7. **Layout:** content max-width 1440px, centred; side padding 24px (16px below 1100px).

---

## Phase 3: Sidebar

Width ~296px (clamp 280–320). Left-aligned text only (no `text-align: justify`). Only the middle section scrolls; the footer is sticky. Nothing cut off at the bottom.

1. **Brand row:** 28px icon + "Kent-AI" wordmark + collapse button. Remove the long title and the "Classical Decision Support" subtitle.
2. **Active case card:** copyable case ID, patient label, status chip, `totality_ring`, current step name, "Go to step" button. No case → "No active case" + primary "New case".
3. **Case tray** (the primary block):
   - Heading with count badge.
   - Groups: Rubrics, Remedies.
   - Each row: rubric path (serif, single line, truncated, full path tooltip), grade badges (③ n, ② n), × remove.
   - "Clear tray" (confirm if >3 items).
   - A primary action for whatever consumes the tray. Find how the app uses tray items today and expose that here.
   - Empty state: one sentence + "Open Rubric Explorer" button.
   - **Persist the tray to the active case** (survives refresh; restored on Resume).
4. **Repertory scope:** segmented control "MIND focus" | "All chapters", with rubric counts (4,933 / 74,513) as a caption. Writes `st.session_state.scope`, the **single source of truth**. The top-bar chip reflects it. Changing scope marks existing Explorer results as stale.
5. **Engine row:** status dot + model name + latency. Expands to endpoint, model, temperature (only what already exists), "Test connection". Offline → red dot + "Start Ollama" hint + Retry.
6. **Sticky footer:** links to Methodology, Totality principles (anchor link to the Methodology page; **no duplicated text**), About/version (git short SHA), and a one-line disclaimer with "Read full notice".
7. Remember collapsed state; auto-collapse below ~1100px.

Remove from the sidebar: the duplicated "Dr. Kent's Totality Principles" expander, the long justified disclaimer, and the "Inference Engine & Settings" expander body (moves to the Settings page in Phase 7).

---

## Phase 4: Case Workspace

**4.1 Layout.** Two columns (~7:3).
- Left: mode control (Guided / Paste / Manual), step progress, transcript, suggestions, input.
- Right: a sticky **Case snapshot** rail (`position: sticky; top: <subheader height>`; use a `key`ed container and a `:has()` hook).

**4.2 Case snapshot** replaces the Totality Strip, "Active Case Summary" and the "What to Include" dimension list.
- Seven rows in canonical order, each showing label, hint, and the captured value (one line, tooltip for the full text) or "Not yet".
- Row states: empty / captured / low-confidence (amber) / edited by you.
- Clicking a captured row opens a popover with the source sentence(s), confidence (if the pipeline stores it), and an edit/lock action. Do not change the NLP pipeline. If provenance or confidence isn't stored, show what is available.
- Under the list: readiness line ("Ready: 4/7 · Missing: Time pattern (recommended)") and the Continue button. Keep the existing minimum of 1 dimension, but show a soft warning below 3 and when Mental/Emotional is missing in MIND scope ("Continue anyway" stays enabled).
- Export and Start over live in a ⋯ menu at the rail's bottom.

**4.3 Chat.**
- The transcript is a fixed-height scroll container (keyed; ≈ `clamp(420px, 60vh, 640px)` via CSS), with the input directly beneath it.
- Compact bubbles: the user is right-aligned (max ~70% width); the assistant is left-aligned with a 28px avatar. Timestamps on hover. Per-message copy. Regenerate on the last assistant message.
- The welcome blurb collapses after the first message.
- Stream tokens with `st.write_stream`. Keep partial output in `session_state` so a Stop/rerun doesn't lose it. Provide Stop and Retry. Disable the input while generating. Show a clear offline/timeout error with an action.
- Input: Enter sends, Shift+Enter inserts a newline, send button ≥40px, accent focus ring.

**4.4 Controls row.**
- Merge the "Patient Self-Intake" chip and the Patient/Practitioner toggle into a single segmented control labelled "Speaking as".
- "Step 1 of 10: Greeting" becomes a thin progress bar + label, with step names on hover.
- Merge "Copy Chat" and "Export Consultation Transcript" into one **Export** popover (copy, .txt, .md, .json, and PDF if it already exists).
- "Reset Consultation" → **"Start over"**: danger-outline style, separated from Export. It opens a confirm dialog stating what is lost ("12 messages, 3 dimensions") and shows an Undo toast (snapshot kept in `session_state` ~30s).

**4.5 Suggested replies.**
- Make them step-aware and neutral, driven by a config map keyed by intake step. Greeting examples: "I'd like to describe how I feel", "I have a physical complaint", "It's mostly emotional".
- Remove the static symptom-specific chips (headache, reflux, joints).
- Hide them when "Speaking as" = Practitioner.
- Add a Settings toggle: "Show suggested replies".

**4.6 Paste notes.**
- Drop the duplicate dimension list. Use the same Case snapshot rail, and collapse the "what to include" tips by default.
- Style the textarea placeholder unmistakably as placeholder text.
- Show a word count.
- Wrap the extraction in `st.status` with stages (encoding → extracting → arbitration → done), then show a "found n of 7" preview before moving to Review.
- Show the privacy line ("Stored on this device; nothing leaves this machine.") next to the textarea. Verify this is actually true before shipping it.

**4.7 Enter manually.** Apply the same labels, hints, components and snapshot rail.

---

## Phase 5: Case Library

- **Header:** "Case library" with the caption "{n} cases · stored on this device". Remove "Persistent SQLite Consultation Storage".
- **Toolbar:**
  - Search (name, ID, chief complaint, and symptoms if feasible).
  - Status filter (segmented, matching the real statuses).
  - Sort (Updated, Created, Totality).
  - Cards / compact-table toggle.
  - "+ New case".
- **Defaults:** hide empty drafts (0 dimensions and 0 messages) behind a "Show empty drafts (n)" toggle. Add "Clean up empty cases" (confirm dialog; **default action = archive, not delete**).
- **Pagination:** 12 per page for cards, 25 for the table, with "1–12 of 81".
- **Row/card:**
  - Title fallback chain: user title → chief complaint → first captured symptom → "Untitled case".
  - Structured meta fields: patient label; age/sex only if known; case ID in mono; relative updated time with a full-timestamp tooltip.
  - `totality_ring`-style mini indicator + "4/7".
  - Leading remedy chip, or "Not analysed yet".
  - Status chips coloured per status.
- **Actions:**
  - The whole row opens the case.
  - A smaller secondary "Open" button.
  - A ⋯ menu: Rename, Duplicate, Export, Archive, Delete (confirm dialog + undo toast).
  - Checkbox multi-select for bulk Archive / Export / Delete.

---

## Phase 6: Rubric Explorer

**Search card:**
- A single row: query input (clear × button, placeholder "e.g. fear of dark, anxiety in the evening").
- Mode segmented control: Meaning | Exact | Hybrid (show Hybrid only if the backend supports it; see the optional item below), each with a one-line explanation tooltip.
- Result count segmented control: 10 / 15 / 25 / 50.
- A Search button (normal size, not full-width).
- Wrap it all in `st.form` so Enter submits.
- Under the form, a caption "Searching MIND · 4,933 rubrics [Change]". The chapter select appears only when scope = All chapters.
- An "Advanced filters" expander: minimum similarity, remedy-count range, sort (Relevance, Remedy count, A–Z).

**Result row (collapsed):**
- Checkbox.
- Breadcrumb in `--font-rubric` (ancestors muted, leaf strong, query terms highlighted, ` › ` separators).
- Remedy-count badge with a specificity tag ("Specific" / "Broad"; thresholds in constants).
- Thin similarity bar + % with the tooltip "Semantic similarity to your query, not clinical relevance".
- "+ Add" icon button that toggles to "✓ Added" and fires `st.toast`.

**Expanded row:**
- Show only the remedies. Do not repeat the path, match % or count.
- One wrapped group per non-empty grade (hide empty grades entirely), with ③/②/① badges plus the bold/italic/roman encoding.
- Chip text is the abbreviation; the full name is in the tooltip. Clicking a chip opens the remedy in a Materia Medica `st.dialog`.

**Other:**
- Sticky "Add selected (n)" bar when ≥1 row is checked.
- Loading skeleton rows and a no-results state with query suggestions.
- **Optional, behind a feature flag, off by default:** hybrid ranking that blends lexical and semantic scores so literal hits (e.g. "FEAR › dark" for "anxiety dark") are not outranked by loosely related rubrics. Do not change default ranking without approval.

---

## Phase 7: Methodology and Settings (split into two pages)

**Methodology** (docs):
- Rename the tab/page.
- Render grade weights, model names and metrics from the constants/config.
- Add a plain-language one-liner under each metric (e.g. Recall@20 = how often the right rubric appears in the top 20).
- Accordions or equal-height cards, and no anchor icons.
- Wording: prefer "7 totality dimensions" over "7 Kentian dimensions".
- Disclaimer §3 stays here in full.

**Settings** (new):
- Engine: endpoint, model, Test connection.
- Default scope.
- Theme (dark default) and density (comfortable/compact).
- Autosave on/off.
- Show suggested replies.
- Data: export all cases, import, delete all (typed confirmation).
- About: version, git SHA.

---

## Phase 8: Review, Analysis, Report, Materia Medica (not yet audited)

Audit these against the same rules: no duplicate chrome, tokens, sticky action bar, canonical labels, no placeholders. Then:
- **Review:** an editable dimension table with confidence/provenance where available.
- **Analysis:**
  - A remedy ranking table with a score breakdown (grade weights, specificity, dimension coverage) and an expandable "why this remedy" list of matched rubrics.
  - Show the top N with alternatives and never present a single "answer".
- **Report:**
  - A paper-style printable layout (light surface regardless of theme, serif, print CSS).
  - Includes case metadata, dimensions, rubrics used, the ranking, model and version, and the full disclaimer.
  - Export PDF/MD.
- **Materia Medica:** use the same row/chip patterns and the remedy dialog from Phase 6.

---

## Phase 9: States, feedback, performance

- **Engine health:** checked on load and before each generation (cached ~10s). Offline shows a banner with an actionable message. First run shows a model warm-up `st.status`.
- **Caching:** use `st.cache_resource` for encoders, the vector index and the DB connection, and cache query embeddings by (query, mode, scope). Verify what is already cached first.
- **Fragments:** wrap the chat panel and the rubric results in `st.fragment` so a message or search doesn't rerun the whole page.
- **Autosave:** debounced, with a "Saved hh:mm" indicator and an "Unsaved changes" state on failure.
- **Toasts** for save, add, export and error. Confirm dialogs plus undo for destructive actions.
- **Demo mode:** a "Load demo case" button in the empty workspace and the empty Library, loading a static realistic MIND case with ~6/7 dimensions so Review/Analysis/Report can be shown without waiting on the LLM. Label it clearly as demo data.
- **Optional:** a light theme, plus print CSS for the Report.

---

## Phase 10: QA and acceptance criteria

- **Viewports** 1920×1080, 1366×768 and 1024×768: at 1366×768 the chat input is visible without page scroll on first load of Guided mode; no horizontal scroll anywhere. Capture before/after Playwright screenshots into `docs/screens/`.
- **Accessibility:** run axe-core via Playwright on every page and fix critical/serious issues. Text ≥4.5:1, UI components ≥3:1. No text under 12px. `prefers-reduced-motion` disables glow, shimmer and transitions. Complete a keyboard-only walkthrough (top bar → stepper → chat → send); dialogs trap focus and Esc closes them; focus ring always visible.
- **No duplication left:**
  - Scope: one control (sidebar) + one read-only chip.
  - Engine status: one pill.
  - Disclaimer: slim footer + first-run dialog + full text on Methodology.
  - "n/7": ring only.
  - Dimension list: one component.
- **Tests** (add alongside existing ones; use `streamlit.testing.v1.AppTest` where practical):
  - Lazy case creation.
  - Scope sync across sidebar / chip / Explorer.
  - Tray add / remove / persist / restore.
  - Stepper gating (Review unlocks at ≥1 dimension).
  - `format_rubric_path`.
  - The Methodology page renders from constants (changing a weight changes the page).
- **Regression:** the existing ~81 cases open; the migration is idempotent; start-up time is not noticeably worse.

## Deliverables

- Commits per phase.
- `docs/ui/UI_CHANGELOG.md` with Assumptions, backend changes, and deferred items.
- `docs/ui/UI_AUDIT_MAP.md`.
- Before/after screenshots in `docs/screens/`.
- A final summary listing every changed file by phase and any open questions.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-11-01T14:09:10+05:30.

The user's current state is as follows:
Active Document: d:\Research Project\kent-ai\src\dashboard\components\case_bulk_actions.py (LANGUAGE_UNSPECIFIED)
Cursor is on line: 1
Other open documents:
- d:\Research Project\kent-ai\tests\test_app_smoke.py (LANGUAGE_UNSPECIFIED)
- d:\Research Project\kent-ai\tests\test_case.py (LANGUAGE_UNSPECIFIED)
- d:\Research Project\kent-ai\docs\Proposals\generate_proposal_pdf.py (LANGUAGE_UNSPECIFIED)
</ADDITIONAL_METADATA>
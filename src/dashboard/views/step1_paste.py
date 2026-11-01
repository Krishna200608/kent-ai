"""Step 1 Paste Clinical Narrative view (structured extraction from clinical notes) (Phase 4 & UI Overhaul)."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Dict, List
import streamlit as st

from src.dashboard.components.extraction_preview import render_extraction_preview
from src.dashboard.components.icons import get_icon
from src.dashboard.examples import CLINICAL_VIGNETTES, get_vignette_by_title
from src.dashboard.utils import esc, safe_rerun_fragment
from src.data.case_store import save_case
from src.models.case import CANONICAL_DIMENSIONS, ClinicalCase
from src.pipeline.narrative import derive_chief_complaint
from src.pipeline.safety import screen_red_flags

if TYPE_CHECKING:
    from src.chatbot.dialogue_manager import DialogueManager


def _on_example_pill_change() -> None:
    """Callback when user selects an example clinical vignette pill."""
    selected = st.session_state.get("example_pill_select")
    if selected:
        v = get_vignette_by_title(selected)
        if v:
            st.session_state.paste_text = v.narrative
            st.session_state.paste_preview = None


@st.fragment
def render_step1_paste_view(current_case: ClinicalCase, dm: DialogueManager, pipeline: Any) -> None:
    """Render the Paste Clinical Narrative view with word count, local privacy badge, and extraction stages."""
    # Example pills above the form
    example_titles = [v.title for v in CLINICAL_VIGNETTES]
    st.html(
        f"""
        <div style="font-size: 12px; font-weight: 600; color: var(--accent, #10B981); margin-bottom: 4px; display: flex; align-items: center; gap: 5px;">
            {get_icon('sparkles', size=14, color='var(--accent, #10B981)')}
            <span>Try an example vignette:</span>
        </div>
        """
    )
    st.pills(
        "Try an example",
        example_titles,
        key="example_pill_select",
        label_visibility="collapsed",
        on_change=_on_example_pill_change,
    )

    with st.form("paste_intake", border=True):
        st.html(
            f"""
            <div style="font-size: 13px; font-weight: 700; color: var(--text, #E8EDF3); margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                {get_icon('clinical_notes', size=16, color='var(--accent, #10B981)')}
                <span>Clinical Narrative Notes</span>
            </div>
            """
        )
        narrative_text = st.text_area(
            "Clinical Narrative Notes",
            key="paste_text",
            height=220,
            placeholder="Doctor, I feel terribly anxious and depressed every morning, worse when alone. Thoughts race with fear. I have no fever and no nausea...",
            label_visibility="collapsed",
        )

        current_val = narrative_text.strip()
        word_count = len(current_val.split()) if current_val else 0

        st.html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 4px 0 10px 0; font-size: 11.5px;">
                <span class="paste-word-count">Word count: <b>{word_count}</b> words</span>
                <span class="paste-privacy-line">
                    {get_icon('lock', size=13, color='var(--accent, #10B981)')} Stored on this device; nothing leaves this machine.
                </span>
            </div>
            """
        )

        submit_extract = st.form_submit_button(
            "Extract & review",
            type="primary",
            width="stretch",
        )

    # Collapsible clinical documentation tips
    with st.expander("Clinical documentation tips (what to include)", expanded=False):
        st.markdown(
            "- **Mental/Emotional:** Mood changes, fears, anxiety, cognitive pace, irritability.\n"
            "- **Location & Sensation:** Exact body parts, depth, character of pain (throbbing, burning, stitching).\n"
            "- **Modalities:** Triggers that aggravate (heat, cold, motion, noise) or ameliorate (rest, warmth, open air).\n"
            "- **Time Pattern:** Specific clock hours, morning upon waking, afternoon, or night aggravation.\n"
            "- **Concomitants:** Associated reactions (perspiration, chills, vertigo, digestive reflex)."
        )

    if submit_extract:
        clean_text = narrative_text.strip()
        if len(clean_text) < 20:
            st.warning(
                "Add a little more detail: where it is, what it feels like, and what changes it."
            )
        else:
            profile = None
            is_cold = not st.session_state.get("_models_warmed", False)
            with st.status("Analyzing clinical narrative with local NLP pipeline...", expanded=True) as status_box:
                try:
                    if is_cold:
                        status_box.write("Loading models (first run only)...")
                    section_id = 1 if (current_case.scope_chapter and "MIND" in current_case.scope_chapter) else None
                    profile = pipeline.extract_profile(clean_text, section_id=section_id)
                    st.session_state["_models_warmed"] = True

                    raw_spans = getattr(profile, "raw_entities", []) or []
                    status_box.write(f"Encoded clinical text with BioLinkBERT · Extracted {len(raw_spans)} symptom entities")
                    if getattr(profile, "negated", None):
                        status_box.write(f"Filtered {len(profile.negated)} negated findings")
                    found_count = sum(1 for k in CANONICAL_DIMENSIONS if getattr(profile, k, []))
                    status_box.write(f"Arbitrated totality dimensions · {found_count} of 7 dimensions mapped")
                    status_box.update(
                        label=f"Extraction complete! Found {found_count} of 7 dimensions.",
                        state="complete",
                        expanded=False,
                    )
                except Exception as err:
                    status_box.update(label="Extraction error", state="error", expanded=True)
                    st.error(
                        f"Unable to complete extraction: {esc(str(err))}. "
                        "Your text has been preserved above. Please review and try again."
                    )

            if profile is not None:
                has_extracted = any(
                    bool(getattr(profile, k, [])) for k in CANONICAL_DIMENSIONS
                )

                if not has_extracted:
                    st.info(
                        "No symptoms found. Try mentioning where it is, what it feels like, "
                        "and what makes it better or worse."
                    )
                else:
                    new_text_items: Dict[str, List[Dict[str, Any]]] = {k: [] for k in CANONICAL_DIMENSIONS}
                    raw_spans = getattr(profile, "raw_entities", []) or []

                    for dim_key in CANONICAL_DIMENSIONS:
                        dim_vals = getattr(profile, dim_key, []) or []
                        for v in dim_vals:
                            v_clean = str(v).strip()
                            sp = next(
                                (
                                    s for s in raw_spans
                                    if s.get("text", "").strip().lower() == v_clean.lower()
                                ),
                                {},
                            )
                            new_text_items[dim_key].append({
                                "text": v_clean,
                                "confidence": sp.get("score") or sp.get("confidence") or 0.95,
                                "start": sp.get("start"),
                                "end": sp.get("end"),
                                "origin": "text",
                            })

                    # Screen safety red flags
                    red_flags = screen_red_flags(clean_text)

                    # Update case using replace_text_extracted_items (keeps manual/chat intact)
                    current_case.transcript = clean_text
                    current_case.replace_text_extracted_items(
                        new_text_items=new_text_items,
                        source="paste",
                        negated=profile.negated,
                        red_flags=[rf.to_dict() for rf in red_flags],
                    )

                    # Set chief complaint if not already specified
                    if not current_case.chief_complaint:
                        current_case.chief_complaint = derive_chief_complaint(clean_text, profile.chief_complaint)

                    save_case(current_case)
                    saved_time = datetime.datetime.now().strftime("%H:%M")
                    st.caption(f"✓ Saved {saved_time}")
                    st.session_state.paste_preview = True
                    safe_rerun_fragment()

    # If extraction preview is active, render below
    if st.session_state.get("paste_preview", False):
        st.markdown("---")
        # Display red flags notice if present (non-blocking)
        meta = getattr(current_case, "extraction_meta", {}) or {}
        rf_list = meta.get("red_flags", [])
        if rf_list:
            categories_str = ", ".join(set(rf.get("category", "") for rf in rf_list if rf.get("category")))
            st.warning(
                f"Safety notice: this narrative mentions **{categories_str}**. "
                "Kent-AI is not an emergency or diagnostic tool; consider whether urgent clinical evaluation is needed. "
                "You can continue with the case."
            )
        render_extraction_preview(current_case, dm)

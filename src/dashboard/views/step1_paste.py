"""Step 1 Paste Clinical Narrative view (structured extraction from clinical notes)."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Dict, List
import streamlit as st

from src.dashboard.components.extraction_preview import render_extraction_preview
from src.dashboard.components.icons import get_icon
from src.dashboard.components.intake_guide import render_intake_guide_rail
from src.dashboard.components.symptom_strip import render_slot_badges
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
    """Render the Paste Clinical Narrative view with guidance rail and extraction preview."""
    # Hide heading anchors globally
    st.html("<style>[data-testid='stHeaderActionElements']{display:none !important;}</style>")

    # Top instructions & totality strip
    st.markdown(
        "<div style='font-size: 13.5px; color: #9CA3AF; margin-bottom: 12px;'>"
        "Describe the patient in their own words. Kent-AI extracts the 7 Kentian dimensions."
        "</div>",
        unsafe_allow_html=True,
    )
    render_slot_badges(current_case.dimensions)
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    col_main, col_rail = st.columns([3, 2], gap="large")

    with col_rail:
        render_intake_guide_rail(current_case)

    with col_main:
        # Example pills above the form
        example_titles = [v.title for v in CLINICAL_VIGNETTES]
        st.markdown(
            f"<div style='font-size: 12px; font-weight: 600; color: #10B981; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;'>"
            f"{get_icon('sparkles', size=14, color='#10B981')} Try an example:"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.pills(
            "Try an example",
            example_titles,
            key="example_pill_select",
            label_visibility="collapsed",
            on_change=_on_example_pill_change,
        )

        with st.form("paste_intake", border=True):
            st.markdown(
                f"<div style='font-size: 13px; font-weight: 700; color: #F3F4F6; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;'>"
                f"{get_icon('clinical_notes', size=16, color='#10B981')} Clinical Narrative Notes"
                f"</div>",
                unsafe_allow_html=True,
            )
            narrative_text = st.text_area(
                "Clinical Narrative Notes",
                key="paste_text",
                height=220,
                placeholder="Doctor, I feel terribly anxious and depressed every morning, worse when alone. Thoughts race with fear. I have no fever and no nausea...",
                label_visibility="collapsed",
            )

            # Optional Patient Demographics & Chief Complaint Expander
            with st.expander("Optional: Patient details & chief complaint", expanded=False):
                c_p1, c_p2, c_p3 = st.columns([2, 1, 1])
                with c_p1:
                    p_name = st.text_input(
                        "Patient Name / Initials",
                        value=current_case.patient_name if current_case.patient_name != "Anonymous Patient" else "",
                        placeholder="e.g. Jane Doe or J.D.",
                        key="paste_p_name",
                    )
                with c_p2:
                    p_age = st.number_input(
                        "Age",
                        min_value=0,
                        max_value=120,
                        value=current_case.patient_age or 0,
                        step=1,
                        key="paste_p_age",
                    )
                with c_p3:
                    sex_options = ["Unspecified", "Female", "Male", "Other"]
                    default_sex_idx = 0
                    if current_case.patient_sex in sex_options:
                        default_sex_idx = sex_options.index(current_case.patient_sex)
                    p_sex = st.selectbox(
                        "Sex",
                        sex_options,
                        index=default_sex_idx,
                        key="paste_p_sex",
                    )

                p_cc = st.text_input(
                    "Chief Complaint",
                    value=current_case.chief_complaint,
                    placeholder="Auto-derived or enter manually...",
                    key="paste_p_cc",
                )

            submit_extract = st.form_submit_button(
                "Extract & review",
                type="primary",
                width="stretch",
            )

        if submit_extract:
            clean_text = narrative_text.strip()
            if len(clean_text) < 20:
                st.warning(
                    "Add a little more detail: where it is, what it feels like, and what changes it.",
                    icon="⚠️",
                )
            else:
                profile = None
                with st.status("Analyzing clinical narrative...", expanded=True) as status_box:
                    try:
                        status_box.write("Reading narrative...")
                        status_box.write("Extracting dimensions...")
                        section_id = 1 if (current_case.scope_chapter and "MIND" in current_case.scope_chapter) else None
                        profile = pipeline.extract_profile(clean_text, section_id=section_id)
                        status_box.write("Checking negations...")
                        status_box.update(label="Extraction complete!", state="complete", expanded=False)
                    except Exception as err:
                        status_box.update(label="Extraction error", state="error", expanded=True)
                        st.error(
                            f"Unable to complete extraction: {esc(str(err))}. "
                            "Your text has been preserved above. Please review and try again."
                        )

                if profile is not None:
                    # Check if anything was extracted
                    has_extracted = any(
                        bool(getattr(profile, k, [])) for k in CANONICAL_DIMENSIONS
                    )

                    if not has_extracted:
                        st.info(
                            "No symptoms found. Try mentioning where it is, what it feels like, "
                            "and what makes it better or worse.",
                            icon="ℹ️",
                        )
                    else:
                        # Build extraction_meta items
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

                        # Set chief complaint and demographics
                        if p_cc and p_cc.strip():
                            current_case.chief_complaint = p_cc.strip()
                        else:
                            current_case.chief_complaint = derive_chief_complaint(clean_text, profile.chief_complaint)

                        if p_name and p_name.strip():
                            current_case.patient_name = p_name.strip()
                        if p_age > 0:
                            current_case.patient_age = int(p_age)
                        if p_sex and p_sex != "Unspecified":
                            current_case.patient_sex = p_sex

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
                "You can continue with the case.",
                icon="⚠️",
            )
        render_extraction_preview(current_case, dm)


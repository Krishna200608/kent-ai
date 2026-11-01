"""Modal dialogs for Kent-AI clinical consultation (Phase 2 & UI Overhaul).

Provides:
- Patient Information dialog (demographics, chief complaint)
- First-run Clinical Research Disclaimer acknowledgement dialog
"""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.busy import busy_slot
from src.dashboard.components.icons import get_icon
from src.dashboard.utils import esc
from src.data.case_store import save_case, set_app_setting
from src.models.case import ClinicalCase


@st.dialog("Patient Information")
def show_patient_info_dialog(case: ClinicalCase) -> None:
    """Modal dialog for editing patient demographics and chief complaint."""
    st.markdown(
        f"""
        <div style="font-size: 13px; color: var(--text-muted, #A3B0C2); margin-bottom: 12px;">
            Update consultation demographics for <b>{esc(case.case_id)}</b>. Data is stored locally on this machine.
        </div>
        """,
        unsafe_allow_html=True,
    )

    new_name = st.text_input(
        "Patient Name / Clinical ID:",
        value=case.patient_name,
        key="dlg_pt_name",
        help="Patient identifier or pseudonym for consultation records",
    )

    c_age, c_sex = st.columns(2)
    with c_age:
        new_age = st.number_input(
            "Age (years):",
            min_value=0,
            max_value=120,
            value=case.patient_age or 35,
            key="dlg_pt_age",
        )
    with c_sex:
        sex_opts = ["Unspecified", "Female", "Male", "Other"]
        curr_idx = sex_opts.index(case.patient_sex) if case.patient_sex in sex_opts else 0
        new_sex = st.selectbox("Biological Sex:", sex_opts, index=curr_idx, key="dlg_pt_sex")

    new_chief = st.text_area(
        "Chief Complaint / Reason for Encounter:",
        value=case.chief_complaint,
        placeholder="Primary presenting symptom, onset, and chief suffering...",
        key="dlg_pt_chief",
        height=100,
    )

    c_save, c_cancel = st.columns([1.2, 1])
    with c_save:
        slot_save = st.empty()
        if slot_save.button("Save Demographics", type="primary", width="stretch", key="dlg_btn_save"):
            with busy_slot(slot_save, "Saving...", key="dlg_btn_save", type="primary"):
                case.patient_name = new_name.strip() or "Anonymous Patient"
                case.patient_age = int(new_age) if new_age else None
                case.patient_sex = new_sex if new_sex != "Unspecified" else None
                case.chief_complaint = new_chief.strip()
                save_case(case)
                st.toast("Patient demographics updated.")
                st.rerun()
    with c_cancel:
        if st.button("Cancel", width="stretch", key="dlg_btn_cancel"):
            st.rerun()


@st.dialog("Clinical Decision Support Notice")
def show_first_run_disclaimer_dialog() -> None:
    """Non-blocking first-run acknowledgement dialog for clinical research tool."""
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            {get_icon('verified', size=24, color='#10B981')}
            <span style="font-size: 16px; font-weight: 700; color: var(--text, #E8EDF3);">
                Investigational Clinical Decision Support
            </span>
        </div>
        <div style="font-size: 13.5px; color: var(--text, #E8EDF3); line-height: 1.6; margin-bottom: 16px;">
            Kent-AI is an investigational software platform for classical homeopathic repertorization
            synthesizing Dr. J. T. Kent's 74,513 rubrics with biomedical language models.
            <ul style="margin: 8px 0 12px 18px; padding: 0; color: var(--text-muted, #A3B0C2);">
                <li>It does <b>not</b> provide autonomous diagnoses or prescriptions.</li>
                <li>All repertory indications must be validated by a certified practitioner.</li>
                <li>All case data remains encrypted/stored locally on this machine.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    dont_show = st.checkbox("Remember my acknowledgement on this machine", value=True, key="chk_persist_disclaimer")
    c_ack, c_dismiss = st.columns([1.5, 1])
    with c_ack:
        if st.button("I Acknowledge & Understand", type="primary", width="stretch", key="dlg_ack_disclaimer"):
            st.session_state["has_acknowledged_disclaimer"] = True
            if dont_show:
                set_app_setting("has_acknowledged_disclaimer", True)
            st.toast("Acknowledgement recorded.")
            st.rerun()
    with c_dismiss:
        if st.button("Dismiss", width="stretch", key="dlg_dismiss_disclaimer"):
            st.session_state["has_acknowledged_disclaimer"] = True
            if dont_show:
                set_app_setting("has_acknowledged_disclaimer", True)
            st.rerun()


@st.dialog("Materia Medica — Remedy Keynotes", width="large")
def show_remedy_dialog(remedy_id_or_abbr: int | str, db: Any) -> None:
    """Modal dialog displaying Materia Medica details and characteristic keynotes for a remedy."""
    if not remedy_id_or_abbr:
        st.error("Invalid remedy specified.")
        return

    from src.dashboard.constants import format_rubric_path
    from src.data.kent_db import get_remedy_rubrics

    rem = None
    with db.connect() as conn:
        cur = conn.cursor()
        is_num = isinstance(remedy_id_or_abbr, int) or (isinstance(remedy_id_or_abbr, str) and remedy_id_or_abbr.isdigit())
        if is_num:
            cur.execute("SELECT id, abbreviation, full_name, normalized FROM remedies WHERE id = ?", (int(remedy_id_or_abbr),))
        else:
            s_val = str(remedy_id_or_abbr).strip()
            cur.execute(
                "SELECT id, abbreviation, full_name, normalized FROM remedies WHERE abbreviation = ? OR abbreviation = ? OR normalized = ? LIMIT 1",
                (s_val, s_val + ".", s_val.lower().rstrip(".")),
            )
        row = cur.fetchone()
        if row:
            rem = dict(row)

    if not rem:
        st.error(f"Remedy '{esc(str(remedy_id_or_abbr))}' was not found in Kent's Repertory.")
        return

    rem_id = rem["id"]
    abbr = rem["abbreviation"]
    name = rem["full_name"] or abbr

    with db.connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM rubric_remedies WHERE remedy_id = ?", (rem_id,))
        total_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM rubric_remedies rr JOIN rubrics r ON rr.rubric_id = r.id WHERE rr.remedy_id = ? AND r.section_id = 1", (rem_id,))
        mind_count = cur.fetchone()[0]

    st.html(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; border-bottom: 1px solid var(--line, #243243); padding-bottom: 10px;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    {get_icon('medication', size=22, color='var(--accent, #10B981)')}
                    <span style="font-size: 18px; font-weight: 800; color: var(--text, #E8EDF3);">{esc(name)}</span>
                    <span style="font-family: var(--font-mono, monospace); font-size: 13px; font-weight: 700; background: var(--surface-2, #182330); border: 1px solid var(--line, #243243); border-radius: 4px; padding: 2px 6px; color: var(--accent, #10B981);">{esc(abbr)}</span>
                </div>
            </div>
            <div style="text-align: right; font-size: 12.5px; color: var(--text-muted, #A3B0C2);">
                <b>{total_count:,}</b> rubrics cataloged &middot; <span style="color: var(--accent, #10B981); font-weight: 700;">{mind_count:,} in MIND</span>
            </div>
        </div>
        """
    )

    st.markdown("##### Characteristic Keynotes (Grade 3 Confirmed Symptoms)")
    try:
        keynotes = get_remedy_rubrics(rem_id, min_grade=3, prioritize_mind=True, rank_by_specificity=True, limit=8, db_path=db.db_path)
    except Exception:
        keynotes = []

    if not keynotes:
        st.info(f"No Grade 3 keynotes cataloged for {name}.")
    else:
        for kn in keynotes:
            r_path = kn.get("path", "")
            disp_path = format_rubric_path(r_path)
            r_count = kn.get("remedy_count", 0)
            kn_id = kn.get("rubric_id")

            c_text, c_btn = st.columns([5, 1.2], vertical_alignment="center")
            with c_text:
                st.html(
                    f"""
                    <div style="font-family: var(--font-rubric, Georgia, serif); font-size: 13.5px; color: var(--text, #E8EDF3); margin-bottom: 2px;">
                        {esc(disp_path)}
                        <span style="font-family: var(--font-ui, sans-serif); font-size: 11px; color: var(--text-muted, #A3B0C2); margin-left: 6px;">({r_count} remedies)</span>
                    </div>
                    """
                )
            with c_btn:
                tray = st.session_state.get("case_tray", {"rubrics": [], "remedies": []})
                in_tray = any(item.get("id") == kn_id for item in tray.get("rubrics", []))
                if in_tray:
                    st.caption("Added")
                else:
                    if st.button("+ Add", key=f"dlg_add_kn_{rem_id}_{kn_id}", width="stretch"):
                        if "case_tray" not in st.session_state:
                            st.session_state.case_tray = {"rubrics": [], "remedies": []}
                        leaf = disp_path.split(" › ")[-1] if " › " in disp_path else disp_path
                        st.session_state.case_tray["rubrics"].append({
                            "id": kn_id,
                            "rubric_id": kn_id,
                            "path": r_path,
                            "name": leaf,
                            "similarity": 1.0,
                            "remedy_count": r_count,
                        })
                        cur_c = st.session_state.get("current_case")
                        if cur_c is not None:
                            if kn_id not in cur_c.selected_rubric_ids:
                                cur_c.selected_rubric_ids.append(kn_id)
                            try:
                                save_case(cur_c)
                            except Exception:
                                pass
                        st.toast(f"Added '{leaf}' to tray.")
                        st.rerun()

    st.markdown("---")
    if st.button("Close", width="stretch", key="dlg_btn_close_rem"):
        st.rerun()



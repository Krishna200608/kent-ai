"""Unit tests for Streamlit Clinical Dashboard (Phase 7)."""

from __future__ import annotations

import pytest
from src.data.kent_db import KentDB
from src.pipeline.orchestrator import PatientReport
from src.dashboard.components.chat_viewer import render_slot_badges
from src.dashboard.components.rubric_tree import render_rubric_card


def test_kent_db_get_remedy_rubrics():
    """Verify KentDB.get_remedy_rubrics returns keynotes with correct schema."""
    db = KentDB()
    # Remedy 1 (Aconitum napellus / Acon.)
    keynotes = db.get_remedy_rubrics(remedy_id=1, min_grade=3, limit=5)
    assert isinstance(keynotes, list)
    assert len(keynotes) > 0
    first = keynotes[0]
    assert "rubric_id" in first
    assert "path" in first
    assert "grade" in first
    assert first["grade"] == 3


def test_render_slot_badges_empty_and_filled(monkeypatch):
    """Test slot badges rendering safely under empty and filled dictionary states."""
    rendered_markdown = []

    # Mock st.markdown and st.html
    import streamlit as st
    monkeypatch.setattr(st, "markdown", lambda text, **kw: rendered_markdown.append(text))
    if hasattr(st, "html"):
        monkeypatch.setattr(st, "html", lambda text, **kw: rendered_markdown.append(text))

    # Empty slots - 7-segment HUD renders unfilled segments
    render_slot_badges({})
    assert len(rendered_markdown) == 1
    assert "hud-segments-grid" in rendered_markdown[0]
    assert "hud-segment-unfilled" in rendered_markdown[0]
    assert "LOC" in rendered_markdown[0]
    assert "MENT" in rendered_markdown[0]

    # Filled slots
    rendered_markdown.clear()
    sample_slots = {
        "location": ["head"],
        "sensation": ["throbbing"],
        "modality_agg": ["sun"],
        "modality_amel": ["cold"],
        "temporal": ["morning"],
        "mental": ["anxious"],
    }
    render_slot_badges(sample_slots)
    assert len(rendered_markdown) == 1
    assert "badge-loc" in rendered_markdown[0]
    assert "badge-sen" in rendered_markdown[0]
    assert "badge-agg" in rendered_markdown[0]


def test_patient_report_markdown_and_json_exports():
    """Ensure PatientReport exports clean markdown and JSON for dashboard download."""
    report = PatientReport(
        patient_id="TEST_CLINICAL_01",
        transcript="Severe throbbing headache worse from sun",
        dimensions={"location": ["head"], "sensation": ["throbbing"]},
        matched_rubrics=[
            {"rubric_id": 2797, "path": "HEAD > PAIN > sun, from", "similarity": 0.91}
        ],
        ranked_remedies=[
            {
                "remedy_id": 1,
                "abbreviation": "Bell.",
                "full_name": "Belladonna",
                "score": 3.0,
                "rubric_count": 1,
                "coverage_ratio": 1.0,
            }
        ],
    )

    md = report.to_markdown()
    assert "TEST_CLINICAL_01" in md
    assert "Belladonna" in md

    js = report.to_json()
    assert "TEST_CLINICAL_01" in js
    assert "Bell." in js


def test_render_rubric_card_mind_badge(monkeypatch):
    """Verify that render_rubric_card displays an explicit MIND chapter badge for MIND rubrics."""
    import streamlit as st
    html_rendered = []
    monkeypatch.setattr(st, "html", lambda text, **kw: html_rendered.append(text))
    # Mock expander
    class DummyExpander:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(st, "expander", lambda *args, **kw: DummyExpander())

    db = KentDB()
    # MIND rubric
    mind_rubric = {
        "rubric_id": 1,
        "path": "MIND > ABANDONED > feels he is",
        "similarity": 0.95,
        "remedy_count": 14,
        "section_id": 1,
    }
    render_rubric_card(mind_rubric, db)
    assert len(html_rendered) >= 1
    assert "MIND CHAPTER" in html_rendered[0]

    # Non-MIND rubric
    html_rendered.clear()
    head_rubric = {
        "rubric_id": 2797,
        "path": "HEAD > PAIN > sun, from",
        "similarity": 0.88,
        "remedy_count": 25,
        "section_id": 3,
    }
    render_rubric_card(head_rubric, db)
    assert len(html_rendered) >= 1
    assert "MIND CHAPTER" not in html_rendered[0]


def test_render_rubric_card_safe_id_handling(monkeypatch):
    """Verify render_rubric_card handles None, string prefix, and invalid IDs without crashing."""
    import streamlit as st
    html_rendered = []
    writes = []
    monkeypatch.setattr(st, "html", lambda text, **kw: html_rendered.append(text))
    monkeypatch.setattr(st, "write", lambda text, **kw: writes.append(text))
    monkeypatch.setattr(st, "markdown", lambda text, **kw: None)

    class DummyColumns:
        def __enter__(self): return self
        def __exit__(self, *args): pass

    monkeypatch.setattr(st, "columns", lambda n: [DummyColumns() for _ in range(n)])

    class DummyExpander:
        def __enter__(self): return self
        def __exit__(self, *args): pass

    monkeypatch.setattr(st, "expander", lambda *args, **kw: DummyExpander())

    db = KentDB()

    # Case 1: Missing ID / None
    render_rubric_card({"path": "MIND > ANXIETY"}, db)
    assert any("No remedies cataloged" in w for w in writes)

    # Case 2: String formatted ID with prefix
    writes.clear()
    render_rubric_card({"id": "rubric_4", "path": "MIND > ANXIETY"}, db)
    # Rubric #4 has remedies in Kent DB
    assert len(html_rendered) > 0

    # Case 3: Completely invalid ID
    writes.clear()
    render_rubric_card({"id": "corrupted_id", "path": "MIND > UNKNOWN"}, db)
    assert any("No remedies cataloged" in w for w in writes)

def test_format_chat_transcript():
    """Verify format_chat_transcript compiles clean, structured debug output."""
    from src.chatbot.dialogue_manager import DialogueManager
    from src.dashboard.components.chat_viewer import format_chat_transcript

    dm = DialogueManager()
    dm.get_greeting()
    dm.extracted_slots["location"].append("head")
    dm.extracted_slots["mental"].extend(["anxiety", "fear"])
    dm.history.append({"role": "user", "content": "Severe anxiety & fearful apprehension"})
    dm.history.append({"role": "assistant", "content": "I am here to support you."})

    transcript = format_chat_transcript(dm)
    assert "# Kent-AI Clinical Consultation Transcript" in transcript
    assert "Current Stage" in transcript
    assert "**Totality Coverage**: 2/7 dimensions" in transcript
    assert "Location" in transcript
    assert "head" in transcript
    assert "Mental/Emotional" in transcript
    assert "anxiety" in transcript
    assert "Severe anxiety & fearful apprehension" in transcript
    assert "I am here to support you." in transcript


def test_dashboard_engine_options_and_pipeline():
    """Verify that dashboard ENGINE_OPTIONS are correctly defined and get_pipeline supports them."""
    from src.dashboard.app import ENGINE_OPTIONS, get_pipeline
    from src.pipeline.orchestrator import PipelineOrchestrator
    from src.models.hybrid_pipeline import HybridPipelineOrchestrator

    assert len(ENGINE_OPTIONS) == 4
    assert any("BioLinkBERT" in opt for opt in ENGINE_OPTIONS)
    assert any("PubMedBERT" in opt for opt in ENGINE_OPTIONS)
    assert any("Ensemble" in opt for opt in ENGINE_OPTIONS)
    assert any("Hybrid" in opt for opt in ENGINE_OPTIONS)

    # Test BioLinkBERT pipeline instantiation
    p1 = get_pipeline(ENGINE_OPTIONS[0])
    assert isinstance(p1, PipelineOrchestrator)

    # Test Hybrid pipeline instantiation
    p_hybrid = get_pipeline(ENGINE_OPTIONS[3])
    assert isinstance(p_hybrid, HybridPipelineOrchestrator)


def test_check_ollama_online_and_caching(monkeypatch):
    """Verify check_ollama_online returns False in mock mode and True when server returns 200."""
    from src.dashboard.components.ollama_status import check_ollama_online

    # 1. In mock pipeline mode, always returns False
    monkeypatch.setenv("KENT_MOCK_PIPELINE", "1")
    assert check_ollama_online() is False

    # 2. When mock mode disabled and HTTP 200 returned
    monkeypatch.setenv("KENT_MOCK_PIPELINE", "0")

    class DummyResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass

    class DummyOpener:
        def open(self, req, timeout=None):
            return DummyResponse()

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: DummyOpener())
    # Clear cache to verify fresh call
    import streamlit as st
    st.cache_data.clear()
    assert check_ollama_online("http://127.0.0.1:11434") is True


def test_render_chat_llm_badge_dynamic(monkeypatch):
    """Verify render_chat_llm_badge auto-resets last_call_failed and renders online vs offline fallback HTML."""
    import streamlit as st
    from src.chatbot.dialogue_manager import DialogueManager
    from src.dashboard.components.chat_header import render_chat_llm_badge

    dm = DialogueManager()
    dm.last_call_failed = True

    html_captured = []
    monkeypatch.setattr(st, "html", lambda h, **kw: html_captured.append(h))

    # Case 1: Ollama is online -> clears last_call_failed and displays LLaMA 3:8B Online
    monkeypatch.setattr("src.dashboard.components.chat_header.check_ollama_online", lambda *args, **kw: True)
    fn = getattr(render_chat_llm_badge, "__wrapped__", render_chat_llm_badge)
    fn(dm)

    assert dm.last_call_failed is False
    assert len(html_captured) == 1
    assert "LLaMA 3:8B Online" in html_captured[0]
    assert "status-dot" in html_captured[0]

    # Case 2: Ollama is offline -> displays Offline Fallback
    html_captured.clear()
    monkeypatch.setattr("src.dashboard.components.chat_header.check_ollama_online", lambda *args, **kw: False)
    fn(dm)

    assert len(html_captured) == 1
    assert "Offline Fallback (ollama serve)" in html_captured[0]
    assert "status-dot-amber" in html_captured[0]


def test_render_header_dynamic(monkeypatch):
    """Verify top brand header renders dynamic online and offline status pills with auto-reset."""
    import streamlit as st
    from src.chatbot.dialogue_manager import DialogueManager
    from src.dashboard.views.header import render_header

    dm = DialogueManager()
    dm.last_call_failed = True
    st.session_state["dialogue_manager"] = dm

    html_captured = []
    monkeypatch.setattr(st, "html", lambda h, **kw: html_captured.append(h))
    fn = getattr(render_header, "__wrapped__", render_header)

    # Case 1: Online
    monkeypatch.setattr("src.dashboard.views.header.check_ollama_online", lambda *args, **kw: True)
    fn()

    assert dm.last_call_failed is False
    assert len(html_captured) == 1
    assert "LLaMA 3:8B Online" in html_captured[0]

    # Case 2: Offline
    html_captured.clear()
    monkeypatch.setattr("src.dashboard.views.header.check_ollama_online", lambda *args, **kw: False)
    fn()

    assert len(html_captured) == 1
    assert "Offline Fallback (ollama serve)" in html_captured[0]



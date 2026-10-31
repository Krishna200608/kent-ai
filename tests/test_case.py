"""Unit tests for ClinicalCase model, CaseStore persistence, and PDF export (Phase 0-3)."""

from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import pytest

from src.models.case import ClinicalCase
from src.data.case_store import (
    delete_case,
    generate_case_id,
    get_case,
    init_case_db,
    list_cases,
    purge_blank_cases,
    save_case,
)
from src.dashboard.pdf_exporter import generate_case_pdf
from src.pipeline.orchestrator import PipelineOrchestrator, PatientReport, rescore_report
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore
from src.search.embedder import RubricEmbedder


def test_clinical_case_lifecycle():
    """Verify ClinicalCase model creation, symptom mutation, and query derivation."""
    case = ClinicalCase(case_id="TEST-2026-001", patient_name="Jane Doe", patient_age=32, patient_sex="Female")
    assert case.case_id == "TEST-2026-001"
    assert "32 yrs" in case.demographics_string
    assert "Female" in case.demographics_string
    assert case.filled_dimensions_count == 0
    assert not case.is_ready_for_repertorization

    # Add symptoms across multiple dimensions
    case.add_symptom("location", "forehead")
    case.add_symptom("location", "temples")
    case.add_symptom("sensation", "throbbing")
    case.add_symptom("modality_agg", "warmth")
    case.add_symptom("mental", "anxiety about health")

    assert case.filled_dimensions_count == 4
    assert case.is_ready_for_repertorization
    assert len(case.dimensions["location"]) == 2
    assert "forehead" in case.dimensions["location"]

    # Deduplication check
    case.add_symptom("location", "forehead")
    assert len(case.dimensions["location"]) == 2

    # Remove symptom
    case.remove_symptom("location", "temples")
    assert len(case.dimensions["location"]) == 1

    # Search queries derivation
    queries = case.get_search_queries()
    assert len(queries) == 3
    assert any("throbbing" in q for q in queries)
    assert any("warmth" in q for q in queries)
    assert any("anxiety" in q for q in queries)


def test_clinical_case_serialization():
    """Verify dictionary and JSON round-trip serialization."""
    case = ClinicalCase(
        case_id="TEST-2026-002",
        patient_name="John Smith",
        patient_age=45,
        patient_sex="Male",
        chief_complaint="Severe migraine with photophobia",
        scope_chapter="MIND",
        selected_rubric_ids=[2797, 2800],
        muted_rubric_ids=[2800],
        eliminatory_rubric_ids=[2797],
    )
    case.add_symptom("location", "head")
    case.add_symptom("sensation", "pulsating")

    data = case.to_dict()
    assert data["case_id"] == "TEST-2026-002"
    assert data["patient_name"] == "John Smith"
    assert data["selected_rubric_ids"] == [2797, 2800]
    assert data["muted_rubric_ids"] == [2800]
    assert data["eliminatory_rubric_ids"] == [2797]

    # JSON round trip
    json_str = case.to_json()
    loaded_case = ClinicalCase.from_json(json_str)
    assert loaded_case.case_id == case.case_id
    assert loaded_case.patient_name == case.patient_name
    assert loaded_case.dimensions == case.dimensions
    assert loaded_case.selected_rubric_ids == case.selected_rubric_ids
    assert loaded_case.muted_rubric_ids == case.muted_rubric_ids
    assert loaded_case.eliminatory_rubric_ids == case.eliminatory_rubric_ids


def test_case_store_crud(tmp_path):
    """Test SQLite persistence layer for ClinicalCase."""
    db_path = tmp_path / "test_cases.sqlite"
    init_case_db(db_path)

    cid = generate_case_id()
    assert cid.startswith("CASE-")

    case = ClinicalCase(case_id=cid, patient_name="Alice Brown", patient_age=28)
    case.add_symptom("mental", "fear of darkness")
    case.add_symptom("sensation", "burning")

    # Save
    save_case(case, db_path=db_path)

    # Retrieve
    retrieved = get_case(cid, db_path=db_path)
    assert retrieved is not None
    assert retrieved.case_id == cid
    assert retrieved.patient_name == "Alice Brown"
    assert "fear of darkness" in retrieved.dimensions["mental"]

    # List
    cases = list_cases(db_path=db_path)
    assert len(cases) == 1
    assert cases[0]["case_id"] == cid
    assert cases[0]["patient_name"] == "Alice Brown"

    # Delete
    deleted = delete_case(cid, db_path=db_path)
    assert deleted is True
    assert get_case(cid, db_path=db_path) is None
    assert len(list_cases(db_path=db_path)) == 0


def test_pdf_exporter():
    """Verify PDF export produces valid non-empty PDF binary."""
    case = ClinicalCase(
        case_id="CASE-PDF-TEST",
        patient_name="Robert Green",
        patient_age=50,
        patient_sex="Male",
        chief_complaint="Anxiety with heart palpitations",
    )
    case.add_symptom("location", "chest, heart")
    case.add_symptom("sensation", "palpitation, fluttering")
    case.add_symptom("modality_agg", "lying on left side")
    case.add_symptom("mental", "anxious restlessness, fear of death")

    case.report_data = {
        "patient_id": case.case_id,
        "transcript": "Anxiety with heart palpitations, worse lying on left side",
        "dimensions": case.dimensions,
        "ranked_remedies": [
            {
                "remedy_id": 1,
                "abbreviation": "Acon.",
                "full_name": "Aconitum Napellus",
                "score": 9.2,
                "rubric_count": 4,
                "coverage_ratio": 1.0,
                "rank": 1,
                "margin_to_next": 1.4,
            },
            {
                "remedy_id": 2,
                "abbreviation": "Ars.",
                "full_name": "Arsenicum Album",
                "score": 7.8,
                "rubric_count": 3,
                "coverage_ratio": 0.75,
                "rank": 2,
                "margin_to_next": 0.6,
            },
        ],
        "matched_rubrics": [
            {"rubric_id": 1, "path": "MIND > ANXIETY > fear with", "similarity": 0.88, "remedy_count": 42},
            {"rubric_id": 2, "path": "CHEST > PALPITATION > heart", "similarity": 0.82, "remedy_count": 55},
        ],
    }

    pdf_bytes = generate_case_pdf(case)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_repertorize_case_mock():
    """Verify PipelineOrchestrator.repertorize_case executes without re-parsing chat transcript."""
    embedder = RubricEmbedder(mock_mode=True)
    vector_store = RubricVectorStore(embedder=embedder)
    ranker = RemedyRanker()
    orchestrator = PipelineOrchestrator(
        ner=None,
        vector_store=vector_store,
        ranker=ranker,
        mock_mode=True,
    )

    case = ClinicalCase(case_id="CASE-REP-TEST", patient_name="Test Patient")
    case.add_symptom("location", "head")
    case.add_symptom("sensation", "sharp pain")
    case.add_symptom("mental", "grief and sadness")

    report = orchestrator.repertorize_case(case)
    assert isinstance(report, PatientReport)
    assert report.patient_id == case.case_id
    assert "location" in report.dimensions
    assert len(report.matched_rubrics) > 0
    assert len(report.ranked_remedies) > 0


def test_case_is_blank_and_save_case_skips_blank(tmp_path):
    """Verify is_blank accurately detects empty cases and save_case returns without writing."""
    db_path = tmp_path / "blank_test.sqlite"
    init_case_db(db_path)

    blank_case = ClinicalCase(case_id="CASE-BLANK-001")
    assert blank_case.is_blank is True

    # save_case should not write blank case
    save_case(blank_case, db_path=db_path)
    assert get_case("CASE-BLANK-001", db_path=db_path) is None
    assert len(list_cases(db_path=db_path)) == 0

    # Non-blank: has symptom
    case_with_sym = ClinicalCase(case_id="CASE-SYM-001")
    case_with_sym.add_symptom("location", "head")
    assert case_with_sym.is_blank is False
    save_case(case_with_sym, db_path=db_path)
    assert get_case("CASE-SYM-001", db_path=db_path) is not None

    # Non-blank: has chief complaint
    case_with_cc = ClinicalCase(case_id="CASE-CC-001", chief_complaint="Throbbing migraine")
    assert case_with_cc.is_blank is False
    save_case(case_with_cc, db_path=db_path)
    assert get_case("CASE-CC-001", db_path=db_path) is not None

    # Non-blank: patient name changed
    case_with_name = ClinicalCase(case_id="CASE-NAME-001", patient_name="John Doe")
    assert case_with_name.is_blank is False
    save_case(case_with_name, db_path=db_path)
    assert get_case("CASE-NAME-001", db_path=db_path) is not None


def test_generate_case_id_delete_then_create_no_collision(tmp_path):
    """Verify generate_case_id uses MAX suffix so deleting an earlier case never collides."""
    db_path = tmp_path / "id_test.sqlite"
    init_case_db(db_path)

    import datetime
    year = datetime.date.today().year

    # Create cases 1, 2, 3
    c1 = ClinicalCase(case_id=f"CASE-{year}-001", chief_complaint="Case 1")
    c2 = ClinicalCase(case_id=f"CASE-{year}-002", chief_complaint="Case 2")
    c3 = ClinicalCase(case_id=f"CASE-{year}-003", chief_complaint="Case 3")
    save_case(c1, db_path=db_path)
    save_case(c2, db_path=db_path)
    save_case(c3, db_path=db_path)

    # Delete case #2
    delete_case(f"CASE-{year}-002", db_path=db_path)
    assert get_case(f"CASE-{year}-002", db_path=db_path) is None

    # Next generated ID must be 004, NOT 003 (which would collide/overwrite case 3)
    next_id = generate_case_id(db_path=db_path)
    assert next_id == f"CASE-{year}-004"


def test_purge_blank_cases(tmp_path):
    """Verify purge_blank_cases removes cases with 0 captured dimensions and empty chief complaint."""
    db_path = tmp_path / "purge_test.sqlite"
    init_case_db(db_path)

    # Force save a blank case directly by bypassing is_blank check
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO clinical_cases (
                case_id, patient_name, chief_complaint, status, created_at, updated_at,
                dimensions_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("CASE-DRAFT-001", "Anonymous Patient", "", "intake", "2026-01-01", "2026-01-01", "{}"),
        )
        conn.commit()

    # Save an active case with symptoms
    active_case = ClinicalCase(case_id="CASE-ACTIVE-001", patient_name="Jane Active")
    active_case.add_symptom("mental", "anxiety")
    save_case(active_case, db_path=db_path)

    assert len(list_cases(db_path=db_path)) == 2

    # Purge
    deleted_count = purge_blank_cases(db_path=db_path)
    assert deleted_count == 1

    remaining = list_cases(db_path=db_path)
    assert len(remaining) == 1
    assert remaining[0]["case_id"] == "CASE-ACTIVE-001"


def test_rescore_report_excludes_muted_from_ranking_but_keeps_in_matched():
    """Verify rescore_report excludes muted rubrics from ranker.rank while keeping them in matched_rubrics."""
    ranker = RemedyRanker()
    case = ClinicalCase(case_id="CASE-MUTE-001")

    # Matched rubrics with 2 entries
    r1 = {"rubric_id": 1, "path": "MIND > ANXIETY", "similarity": 0.9, "remedy_count": 10}
    r2 = {"rubric_id": 2, "path": "HEAD > PAIN", "similarity": 0.85, "remedy_count": 15}

    report = PatientReport(
        patient_id=case.case_id,
        transcript="Test transcript",
        dimensions={"mental": ["anxiety"], "location": ["head"]},
        matched_rubrics=[r1, r2],
        ranked_remedies=ranker.rank([r1, r2]),
        search_queries=["anxiety", "head"],
    )

    # Initial rescore: nothing muted
    rescored = rescore_report(ranker, report, case)
    assert len(rescored.matched_rubrics) == 2
    assert not rescored.matched_rubrics[0].get("muted")
    assert not rescored.matched_rubrics[1].get("muted")

    # Mute rubric #2
    case.muted_rubric_ids = [2]
    rescored_muted = rescore_report(ranker, report, case)

    # Both rubrics must still be present in matched_rubrics!
    assert len(rescored_muted.matched_rubrics) == 2
    assert rescored_muted.matched_rubrics[0]["muted"] is False
    assert rescored_muted.matched_rubrics[1]["muted"] is True

    # Case report_data must be synced
    assert case.report_data is not None
    assert len(case.report_data["matched_rubrics"]) == 2

    # Un-mute rubric #2
    case.muted_rubric_ids = []
    rescored_unmuted = rescore_report(ranker, report, case)
    assert len(rescored_unmuted.matched_rubrics) == 2
    assert rescored_unmuted.matched_rubrics[1]["muted"] is False


def test_html_escaping():
    """Verify esc() helper safely escapes malicious HTML/XSS payloads and handles edge cases."""
    from src.dashboard.utils import esc
    assert esc("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    assert esc('"hello" & "world"') == "&quot;hello&quot; &amp; &quot;world&quot;"
    assert esc("<b>bold</b>") == "&lt;b&gt;bold&lt;/b&gt;"
    assert esc(None) == ""
    assert esc("") == ""
    assert esc(12345) == "12345"



def test_case_summarizer(tmp_path: Path):
    """Verify CaseSummarizer generates clinical briefs with LLM sanitization and extractive fallback."""
    from src.pipeline.case_summarizer import CaseSummarizer

    summarizer = CaseSummarizer()

    # Empty case returns initial notice
    empty_case = ClinicalCase(case_id="EMPTY-CASE")
    assert "No clinical symptoms recorded yet" in summarizer.generate_summary(empty_case)

    # Active clinical case
    case = ClinicalCase(
        case_id="SUM-TEST-001",
        patient_name="Arthur Dent",
        patient_age=42,
        patient_sex="Male",
        chief_complaint="Severe migraine",
    )
    case.add_symptom("location", "temples, forehead")
    case.add_symptom("sensation", "throbbing, hammering")
    case.add_symptom("modality_agg", "bright sunlight, motion")
    case.add_symptom("modality_amel", "cold pressure")
    case.add_symptom("concomitant", "nausea")
    case.add_symptom("mental", "irritable, desires solitude")

    # Extractive fallback verification
    summary_text = summarizer.generate_summary(case, use_llm=False)
    assert "42-year-old male" in summary_text
    assert "temples, forehead" in summary_text
    assert "throbbing, hammering" in summary_text
    assert "bright sunlight, motion" in summary_text
    assert "cold pressure" in summary_text
    assert "nausea" in summary_text
    assert "irritable, desires solitude" in summary_text

    # Sanitizer verification
    raw_llm = 'Here is a concise clinical summary for the physician:\n\n"The patient presents with severe migraine..."'
    cleaned = CaseSummarizer._sanitize_llm_output(raw_llm)
    assert not cleaned.startswith("Here is")
    assert not cleaned.startswith('"')
    assert "The patient presents" in cleaned

    # Persistence verification
    db_path = tmp_path / "summary_cases.sqlite"
    case.clinical_summary = summary_text
    save_case(case, db_path=db_path)

    retrieved = get_case(case.case_id, db_path=db_path)
    assert retrieved is not None
    assert retrieved.clinical_summary == summary_text

    # PDF Exporter verification
    pdf_bytes = generate_case_pdf(case)
    assert len(pdf_bytes) > 2000
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        assert "CLINICAL CASE SUMMARY" in doc[0].get_text()
    except ImportError:
        pass

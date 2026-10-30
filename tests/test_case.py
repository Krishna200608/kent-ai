"""Unit tests for ClinicalCase model, CaseStore persistence, and PDF export (Phase 0-3)."""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from src.models.case import ClinicalCase
from src.data.case_store import (
    generate_case_id,
    init_case_db,
    save_case,
    get_case,
    list_cases,
    delete_case,
)
from src.dashboard.pdf_exporter import generate_case_pdf
from src.pipeline.orchestrator import PipelineOrchestrator, PatientReport
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore
from src.search.embedder import RubricEmbedder


def test_clinical_case_lifecycle():
    """Verify ClinicalCase model creation, symptom mutation, and query derivation."""
    case = ClinicalCase(case_id="TEST-2026-001", patient_name="Jane Doe", patient_age=32, patient_sex="Female")
    assert case.case_id == "TEST-2026-001"
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

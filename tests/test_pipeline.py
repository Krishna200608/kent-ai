"""Integration tests for end-to-end transcript to report pipeline (Phase 5)."""

import pytest

from src.models.resolver import SymptomResolver
from src.pipeline.orchestrator import PatientReport, PipelineOrchestrator
from src.pipeline.report_generator import generate_json_report, generate_markdown_report
from src.search.embedder import RubricEmbedder
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore


import uuid


@pytest.fixture
def mock_pipeline():
    embedder = RubricEmbedder(mock_mode=True)
    vector_store = RubricVectorStore(
        collection_name=f"test_rubrics_{uuid.uuid4().hex[:8]}",
        embedder=embedder,
        in_memory=True,
    )

    # Seed mock vector store with rubrics
    sample_rubrics = [
        {
            "id": 1,
            "section_id": 1,
            "section_name": "MIND",
            "depth": 0,
            "label": "ABANDONED",
            "path": "MIND > ABANDONED",
            "remedy_count": 5,
        },
        {
            "id": 4,
            "section_id": 1,
            "section_name": "MIND",
            "depth": 0,
            "label": "ABSENT-MINDED",
            "path": "MIND > ABSENT-MINDED",
            "remedy_count": 8,
        },
    ]
    vector_store.add_rubrics(sample_rubrics)

    resolver = SymptomResolver(mock_mode=True)
    ranker = RemedyRanker()

    return PipelineOrchestrator(
        resolver=resolver,
        vector_store=vector_store,
        ranker=ranker,
        mock_mode=True,
    )


def test_patient_report_markdown_and_json():
    report_data = {
        "patient_id": "PT-TEST-001",
        "transcript": "Doctor, I feel terribly abandoned and absent-minded every morning.",
        "dimensions": {
            "location": [],
            "sensation": [],
            "modality_agg": [],
            "modality_amel": [],
            "concomitant": [],
            "temporal": ["morning"],
            "mental": ["abandoned", "absent-minded"],
            "negated": [],
        },
        "matched_rubrics": [
            {
                "rubric_id": 1,
                "path": "MIND > ABANDONED",
                "similarity": 0.92,
                "remedy_count": 5,
            }
        ],
        "ranked_remedies": [
            {
                "remedy_id": 10,
                "abbreviation": "Lach.",
                "full_name": "Lachesis Muta",
                "score": 2.76,
                "rubric_count": 1,
                "coverage_ratio": 1.0,
            }
        ],
    }

    md = generate_markdown_report(report_data)
    assert "# Kent-AI — Clinical Repertorization Report" in md
    assert "PT-TEST-001" in md
    assert "Lachesis Muta" in md
    assert "`Lach.`" in md

    js = generate_json_report(report_data)
    assert "PT-TEST-001" in js
    assert "Lach." in js


def test_pipeline_orchestrator_mock_process(mock_pipeline):
    transcript = "I feel abandoned and alone, but I have no headache."
    report = mock_pipeline.process_transcript(
        transcript=transcript,
        patient_id="PT-TEST-MOCK",
        top_remedies=5,
    )

    assert isinstance(report, PatientReport)
    assert report.patient_id == "PT-TEST-MOCK"
    assert report.transcript == transcript
    assert len(report.search_queries) > 0

    # Markdown and JSON methods work cleanly
    md = report.to_markdown()
    assert "PT-TEST-MOCK" in md
    assert "Kent-AI" in md

    js = report.to_json()
    assert "PT-TEST-MOCK" in js

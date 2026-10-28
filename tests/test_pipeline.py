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


def test_pipeline_two_stage_ner_to_resolver(mock_pipeline):
    """Verify SymptomNER entity extraction flows into SymptomResolver and PatientReport."""
    transcript = "Doctor, I feel terribly anxious and depressed every morning, worse alone."
    report = mock_pipeline.process_transcript(transcript)

    assert isinstance(report, PatientReport)
    # Check that NER extracted entities are attached to the report
    assert len(report.entities) > 0
    entity_texts = [e["text"].lower() for e in report.entities]
    assert any("anxious" in t or "anxiety" in t or "depressed" in t for t in entity_texts)

    # Check that dimensions include mental and temporal
    assert len(report.dimensions.get("mental", [])) > 0
    assert len(report.dimensions.get("temporal", [])) > 0


def test_pipeline_negation_filtering_in_two_stage(mock_pipeline):
    """Verify that negated entities are filtered into dimensions['negated']."""
    transcript = "I have terrible anxiety every morning, but no headache and no nausea."
    report = mock_pipeline.process_transcript(transcript)

    assert isinstance(report, PatientReport)
    negated = [n.lower() for n in report.dimensions.get("negated", [])]
    assert any("headache" in n or "head" in n or "nausea" in n for n in negated)
    # Negated items must not be included in positive location or sensation
    assert not any("headache" in loc.lower() for loc in report.dimensions.get("location", []))


def test_pipeline_real_ner_inference_if_available():
    """Verify real Bio_ClinicalBERT inference through pipeline when weights exist."""
    from src.models.symptom_ner import SymptomNER
    from src.config import get_project_root

    weights_dir = get_project_root() / "data/models/clinicalbert_homeoNER"
    if not (weights_dir.exists() and any(weights_dir.glob("*.safetensors"))):
        pytest.skip("Fine-tuned weights not found on disk.")

    embedder = RubricEmbedder(mock_mode=True)
    vector_store = RubricVectorStore(
        collection_name=f"test_real_{uuid.uuid4().hex[:8]}",
        embedder=embedder,
        in_memory=True,
    )
    vector_store.add_rubrics([{
        "id": 1,
        "section_id": 1,
        "section_name": "MIND",
        "depth": 0,
        "label": "ANXIETY",
        "path": "MIND > ANXIETY",
        "remedy_count": 10,
    }])

    ner = SymptomNER(mock_mode=False)
    resolver = SymptomResolver(mock_mode=True)
    orchestrator = PipelineOrchestrator(
        ner=ner,
        resolver=resolver,
        vector_store=vector_store,
        mock_mode=False,
    )

    transcript = "Doctor, I feel severe anxiety and restlessness every morning."
    report = orchestrator.process_transcript(transcript)

    assert isinstance(report, PatientReport)
    assert len(report.entities) > 0
    assert report.patient_id.startswith("PT-")
    assert any(e.get("label") == "MENT" for e in report.entities)

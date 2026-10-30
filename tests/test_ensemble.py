"""Unit and regression tests for Week 3 Ensemble & Hybrid Pipeline (Phase 9/10)."""

from __future__ import annotations

import pytest

from src.models.ensemble import EnsembleEntity, EnsembleNER
from src.models.hybrid_pipeline import HybridArbitrationResult, HybridPipelineOrchestrator
from src.pipeline.orchestrator import PatientReport


def test_ensemble_entity_dataclass():
    ent = EnsembleEntity(
        text="throbbing headache",
        label="SEN",
        start=0,
        end=18,
        confidence=0.85,
        votes=3,
        total_models=4,
        supporting_models=["biolinkbert", "pubmedbert", "clinicalbert"],
        is_unanimous=False,
    )
    d = ent.to_dict()
    assert d["text"] == "throbbing headache"
    assert d["label"] == "SEN"
    assert d["votes"] == 3
    assert d["confidence"] == 0.85
    assert not d["is_unanimous"]


def test_ensemble_ner_mock_initialization():
    ensemble = EnsembleNER(mock_mode=True)
    assert len(ensemble.models) >= 1
    # Check normalized weights sum to ~1.0
    total_weight = sum(ensemble.weights.values())
    assert pytest.approx(total_weight, abs=1e-4) == 1.0


def test_ensemble_ner_extraction_clustering():
    ensemble = EnsembleNER(mock_mode=True)
    transcript = "Patient reports severe anxiety in morning with violent headache."
    entities = ensemble.extract_entities(transcript, min_votes=1)

    assert isinstance(entities, list)
    assert len(entities) > 0
    first = entities[0]
    assert "text" in first
    assert "label" in first
    assert "confidence" in first
    assert "votes" in first


def test_hybrid_pipeline_arbitration():
    orchestrator = HybridPipelineOrchestrator(mock_mode=True)
    narrative = "Patient suffers from severe anxiety in morning, but denies nausea or fever."
    
    mock_candidates = [
        {
            "text": "severe anxiety",
            "label": "MENT",
            "start": 21,
            "end": 35,
            "confidence": 0.95,
            "votes": 4,
            "total_models": 4,
            "is_unanimous": True,
        },
        {
            "text": "morning",
            "label": "TEMP",
            "start": 39,
            "end": 46,
            "confidence": 0.70,
            "votes": 3,
            "total_models": 4,
            "is_unanimous": False,
        },
        {
            "text": "nausea",
            "label": "SEN",
            "start": 59,
            "end": 65,
            "confidence": 0.60,
            "votes": 2,
            "total_models": 4,
            "is_unanimous": False,
        },
    ]

    result = orchestrator.arbitrate_candidates(narrative, mock_candidates)
    assert isinstance(result, HybridArbitrationResult)
    assert len(result.unanimous_entities) == 1
    assert len(result.contested_entities) == 2
    
    # Check that "nausea" was identified as negated due to "denies nausea"
    assert "nausea" in result.negated_entities
    assert "nausea" not in result.arbitrated_profile["SEN"]

    # Check that positive symptoms are in final profile
    assert "severe anxiety" in result.arbitrated_profile["MENT"]
    assert "morning" in result.arbitrated_profile["TEMP"]


def test_hybrid_pipeline_process_transcript():
    orchestrator = HybridPipelineOrchestrator(mock_mode=True)
    transcript = "Patient has severe despair of recovery and restlessness in evening."
    report = orchestrator.process_transcript(transcript, patient_id="TEST-HYBRID-01")

    assert isinstance(report, PatientReport)
    assert report.patient_id == "TEST-HYBRID-01"
    assert report.transcript == transcript
    assert "MENT" in report.dimensions
    assert len(report.search_queries) > 0

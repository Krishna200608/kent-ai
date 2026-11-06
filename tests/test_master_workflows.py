"""Master Integration Tests verifying end-to-end clinical workflows (Workflows A to E).

Strictly tests:
- Workflow A: Fresh consultation -> Greeting -> Symptom collection -> Review -> Analysis -> Report.
- Workflow B: Paste clinical narrative -> Extraction -> Preview -> Manual correction -> Analysis -> Report.
- Workflow C: Save case -> Restart/reload -> Resume case -> Continue consultation.
- Workflow D: Practitioner mode -> Manual case entry -> Repertorization -> Remedy comparison -> PDF export.
- Workflow E: Ollama unavailable -> Fallback behavior -> Recovery without data loss.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.chatbot.dialogue_manager import DialogueManager
from src.chatbot.state_machine import IntakeState
from src.dashboard.pdf_exporter import generate_case_pdf
from src.data.case_store import delete_case, get_case, init_case_db, save_case
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import (
    PipelineOrchestrator,
    rescore_report,
)
from src.search.embedder import RubricEmbedder
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Provide isolated test SQLite case store database."""
    db_file = tmp_path / "test_cases.sqlite"
    init_case_db(db_file)
    return db_file


@pytest.fixture
def mock_orchestrator() -> PipelineOrchestrator:
    """Provide deterministic mock pipeline orchestrator."""
    embedder = RubricEmbedder(mock_mode=True)
    vector_store = RubricVectorStore(embedder=embedder)
    # Seed mock collection with representative test rubrics
    sample_rubrics = [
        {
            "id": 1,
            "path": "MIND > ANXIETY > evening",
            "label": "evening",
            "section_id": 1,
            "section_name": "MIND",
            "remedy_count": 45,
        },
        {
            "id": 2,
            "path": "MIND > FEAR > alone, when",
            "label": "alone, when",
            "section_id": 1,
            "section_name": "MIND",
            "remedy_count": 32,
        },
        {
            "id": 4,
            "path": "MIND > RESTLESSNESS > night",
            "label": "night",
            "section_id": 1,
            "section_name": "MIND",
            "remedy_count": 55,
        },
        {
            "id": 10,
            "path": "MIND > SADNESS > weeping",
            "label": "weeping",
            "section_id": 1,
            "section_name": "MIND",
            "remedy_count": 28,
        },
    ]
    vector_store.add_rubrics(sample_rubrics, batch_size=10, show_progress=False)
    ranker = RemedyRanker()
    return PipelineOrchestrator(
        vector_store=vector_store, ranker=ranker, mock_mode=True
    )


def test_workflow_a_fresh_consultation_to_report(
    temp_db_path: Path, mock_orchestrator: PipelineOrchestrator
):
    """Workflow A: Fresh consultation -> Greeting -> Symptom collection -> Review -> Analysis -> Report."""
    # 1. Initialize fresh consultation case
    case = ClinicalCase()
    assert case.is_blank is True
    assert case.filled_dimensions_count == 0

    case.patient_name = "Workflow A Patient"
    case.patient_age = 32
    case.patient_sex = "Female"

    # 2. Mount dialogue manager and check deterministic greeting
    dm = DialogueManager(case=case, mock_mode=True, orchestrator=mock_orchestrator)
    greeting = dm.get_greeting()
    assert "Kent-AI" in greeting
    assert dm.state_machine.current_state == IntakeState.GREETING

    # 3. Patient provides chief complaint & location
    resp1 = dm.process_turn(
        "I have intense fear and anxiety whenever I am left alone, especially in the evening"
    )
    assert len(resp1) > 0
    assert len(dm.history) >= 3  # greeting + user turn + assistant reply
    dm.sync_to_case(case)
    save_case(case, db_path=temp_db_path)

    assert case.is_blank is False
    assert case.filled_dimensions_count >= 1
    assert dm.state_machine.current_state != IntakeState.GREETING

    # 4. Patient provides mental state & modalities
    dm.process_turn("Worse in the evening and in dark rooms, better from quiet company")
    dm.sync_to_case(case)
    save_case(case, db_path=temp_db_path)

    # 5. Move to review and confirmation
    dm.state_machine.current_state = IntakeState.REVIEW
    dm.process_turn(
        "Yes, that covers all my symptoms accurately, please proceed to analysis"
    )
    assert dm.state_machine.current_state == IntakeState.DONE

    # 6. Execute clinical repertorization analysis
    report = mock_orchestrator.repertorize_case(case, top_remedies=10)
    assert report is not None
    assert len(report.matched_rubrics) >= 1
    assert len(report.ranked_remedies) >= 1
    assert case.report_data is not None

    # 7. Generate final PDF report
    pdf_bytes = generate_case_pdf(case, report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")


def test_workflow_b_paste_narrative_to_report(
    temp_db_path: Path, mock_orchestrator: PipelineOrchestrator
):
    """Workflow B: Paste clinical narrative -> Extraction -> Preview -> Manual correction -> Analysis -> Report."""
    narrative = (
        "Patient presents with severe chronic anxiety and palpitations in evening. "
        "Intense fear of being alone and restlessness at night. Worse in warm rooms, "
        "relieved by open cool air and gentle walking."
    )
    case = ClinicalCase(
        patient_name="Workflow B Patient", patient_age=45, patient_sex="Male"
    )
    case.transcript = narrative

    # 1. Extract structured 7-dimensional profile from pasted text
    profile = mock_orchestrator.extract_profile(narrative)
    assert profile is not None

    # 2. Populate case dimensions and metadata
    for dim_key, vals in profile.to_dict().items():
        if dim_key in case.dimensions and vals:
            case.set_dimension_values(dim_key, vals)

    case.extraction_meta = {
        "source": "paste",
        "negated": profile.negated,
        "raw_entity_count": len(profile.raw_entities),
    }

    assert case.filled_dimensions_count >= 1
    save_case(case, db_path=temp_db_path)

    # 3. Simulate Clinician manual correction in Step 2 Review:
    # Add an overlooked symptom and adjust sensation
    case.add_symptom("mental", "fear of crowd")
    assert "fear of crowd" in case.get_dimension_values("mental")

    # 4. Step 3: Compute repertorization ranking
    report = mock_orchestrator.repertorize_case(case, top_remedies=15)
    assert report is not None
    assert len(report.ranked_remedies) >= 1

    # 5. Clinician mutes top rubric to inspect differential impact
    if report.matched_rubrics:
        top_rubric_id = report.matched_rubrics[0]["rubric_id"]
        case.muted_rubric_ids = [top_rubric_id]
        rescored = rescore_report(mock_orchestrator.ranker, report, case, top_n=15)
        # Verify muted rubric is retained in evidence but excluded from ranking scoring
        top_muted_elem = next(
            (r for r in rescored.matched_rubrics if r["rubric_id"] == top_rubric_id),
            None,
        )
        assert top_muted_elem is not None
        assert top_muted_elem["muted"] is True

    # 6. Step 4: Generate consolidated PDF report
    pdf_bytes = generate_case_pdf(case, report)
    assert pdf_bytes.startswith(b"%PDF-")


def test_workflow_c_save_reload_resume_consultation(temp_db_path: Path):
    """Workflow C: Save case -> Restart/reload -> Resume case -> Continue consultation."""
    case_id = "CASE-2026-TESTC"
    original_case = ClinicalCase(
        case_id=case_id,
        patient_name="Workflow C Persistent Patient",
        patient_age=28,
        patient_sex="Female",
        chief_complaint="Recurrent melancholy and weeping",
    )
    original_case.add_symptom("mental", "sadness and involuntary weeping")
    original_case.add_symptom("modality_agg", "worse in morning on waking")

    dm1 = DialogueManager(case=original_case, mock_mode=True)
    dm1.process_turn("I feel sad without cause and weep easily in morning")
    dm1.sync_to_case(original_case)
    save_case(original_case, db_path=temp_db_path)

    # Simulate application restart: load case from SQLite
    loaded_case = get_case(case_id, db_path=temp_db_path)
    assert loaded_case is not None
    assert loaded_case.patient_name == "Workflow C Persistent Patient"
    assert loaded_case.filled_dimensions_count == original_case.filled_dimensions_count
    assert len(loaded_case.dialogue_history) == len(original_case.dialogue_history)

    # Resume consultation on loaded case with fresh dialogue manager
    dm2 = DialogueManager(case=loaded_case, mock_mode=True)
    assert len(dm2.history) == len(loaded_case.dialogue_history)

    # Continue intake with additional turn
    dm2.process_turn("Consolation makes me feel much worse and irritated")
    dm2.sync_to_case(loaded_case)
    save_case(loaded_case, db_path=temp_db_path)

    # Verify updated turn count and symptoms persisted cleanly
    reloaded_case = get_case(case_id, db_path=temp_db_path)
    assert reloaded_case is not None
    assert len(reloaded_case.dialogue_history) > len(original_case.dialogue_history)

    # Clean up test database
    delete_case(case_id, db_path=temp_db_path)
    assert get_case(case_id, db_path=temp_db_path) is None


def test_workflow_d_practitioner_mode_manual_entry_repertorization_pdf(
    temp_db_path: Path, mock_orchestrator: PipelineOrchestrator
):
    """Workflow D: Practitioner mode -> Manual case entry -> Repertorization -> Remedy comparison -> PDF export."""
    case = ClinicalCase(
        patient_name="Practitioner Vignette Case",
        patient_age=50,
        patient_sex="Male",
        chief_complaint="Anticipatory anxiety before public engagement",
        scope_chapter="MIND",
    )
    dm = DialogueManager(case=case, mock_mode=True, orchestrator=mock_orchestrator)
    dm.set_intake_mode("practitioner")
    assert dm.intake_mode == "practitioner"

    # Practitioner greeting check
    greeting = dm.get_greeting()
    assert "Practitioner Mode" in greeting

    # Manual case entry directly into 7 canonical dimensions
    case.set_dimension_values(
        "mental", ["anticipatory anxiety", "fear of public speaking", "restlessness"]
    )
    case.set_dimension_values(
        "modality_agg", ["worse from mental exertion", "worse from coffee"]
    )
    case.set_dimension_values(
        "modality_amel", ["better in open fresh air", "better from motion"]
    )
    case.set_dimension_values("temporal", ["aggravation at 3 AM"])
    case.set_dimension_values("concomitant", ["diarrhea from anxiety"])

    assert case.filled_dimensions_count == 5
    save_case(case, db_path=temp_db_path)

    # Perform repertorization ranking
    report = mock_orchestrator.repertorize_case(case, top_remedies=10)
    assert report is not None
    assert len(report.ranked_remedies) >= 1

    # Verify top remedy structure
    top_remedy = report.ranked_remedies[0]
    assert "abbreviation" in top_remedy
    assert "score" in top_remedy
    assert "rubric_count" in top_remedy

    # Generate PDF export
    pdf_bytes = generate_case_pdf(case, report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")


def test_workflow_e_ollama_unavailable_fallback_recovery(
    temp_db_path: Path, mock_orchestrator: PipelineOrchestrator
):
    """Workflow E: Ollama unavailable -> Fallback behavior -> Recovery without data loss."""
    case = ClinicalCase(patient_name="Offline Fallback Patient", patient_age=24)
    dm = DialogueManager(case=case, mock_mode=False, orchestrator=mock_orchestrator)

    # 1. Simulate Ollama daemon offline with ConnectionError
    with patch.object(
        dm, "_call_ollama_chat_stream", side_effect=ConnectionError("Daemon offline")
    ):
        reply = dm.process_turn("I have severe anxiety and trembling")
        assert reply is not None
        assert len(reply.strip()) > 0
        assert dm.last_call_failed is True

        # Verify symptoms and turn were safely captured despite LLM failure
        assert len(dm.history) >= 2  # user + fallback assistant
        dm.sync_to_case(case)
        save_case(case, db_path=temp_db_path)

        saved = get_case(case.case_id, db_path=temp_db_path)
        assert saved is not None
        assert len(saved.dialogue_history) >= 2
        assert saved.filled_dimensions_count >= 1

    # 2. Simulate daemon recovery
    with patch.object(
        dm,
        "_call_ollama_chat_stream",
        return_value=["I hear your concern. Where do you feel the trembling?"],
    ):
        dm.last_call_failed = False
        reply2 = dm.process_turn("The trembling is mostly in my hands and stomach")
        assert "trembling" in reply2 or "feel" in reply2
        assert dm.last_call_failed is False
        assert len(dm.history) >= 4

        dm.sync_to_case(case)
        save_case(case, db_path=temp_db_path)

        recovered = get_case(case.case_id, db_path=temp_db_path)
        assert recovered is not None
        assert len(recovered.dialogue_history) >= 4

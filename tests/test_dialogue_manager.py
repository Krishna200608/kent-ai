"""Unit tests for DialogueManager (Phase 6)."""

import pytest

from src.chatbot.dialogue_manager import DialogueManager
from src.chatbot.state_machine import ConversationStateMachine, IntakeState
from src.models.resolver import SymptomResolver
from src.pipeline.orchestrator import PipelineOrchestrator
from src.search.embedder import RubricEmbedder
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore


@pytest.fixture
def mock_dialogue_manager():
    embedder = RubricEmbedder(mock_mode=True)
    vector_store = RubricVectorStore(
        collection_name="test_dm_collection",
        embedder=embedder,
        in_memory=True,
    )
    vector_store.add_rubrics([
        {
            "id": 1,
            "section_id": 1,
            "section_name": "MIND",
            "depth": 0,
            "label": "ABANDONED",
            "path": "MIND > ABANDONED",
            "remedy_count": 5,
        }
    ])
    resolver = SymptomResolver(mock_mode=True)
    ranker = RemedyRanker()
    orchestrator = PipelineOrchestrator(
        resolver=resolver,
        vector_store=vector_store,
        ranker=ranker,
        mock_mode=True,
    )
    return DialogueManager(
        orchestrator=orchestrator,
        mock_mode=True,
    )


def test_dialogue_manager_greeting(mock_dialogue_manager):
    greeting = mock_dialogue_manager.get_greeting()
    assert "Kent-AI" in greeting
    assert len(mock_dialogue_manager.history) == 1
    assert mock_dialogue_manager.history[0]["role"] == "assistant"


def test_dialogue_manager_slot_extraction(mock_dialogue_manager):
    utterance = "I have a throbbing headache in my forehead, worse from sun and noise."
    slots = mock_dialogue_manager._extract_slots_heuristic(utterance)

    assert "head" in slots.get("location", []) or "forehead" in slots.get("location", [])
    assert "throbbing" in slots.get("sensation", [])
    assert "sun" in slots.get("modality_agg", []) or "noise" in slots.get("modality_agg", [])


def test_dialogue_manager_multi_turn_flow(mock_dialogue_manager):
    mock_dialogue_manager.get_greeting()

    # Turn 1
    resp1 = mock_dialogue_manager.process_turn("I have terrible anxiety every morning.")
    assert len(resp1) > 0
    assert len(mock_dialogue_manager.history) == 3

    # Turn 2
    resp2 = mock_dialogue_manager.process_turn("It feels like severe restlessness and fear.")
    assert len(resp2) > 0

    transcript = mock_dialogue_manager.get_full_transcript()
    assert "anxiety" in transcript
    assert "restlessness" in transcript


def test_dialogue_manager_handover_on_done(mock_dialogue_manager):
    mock_dialogue_manager.get_greeting()

    # Fast forward state machine to REVIEW
    mock_dialogue_manager.state_machine.current_state = IntakeState.REVIEW

    # Patient confirms
    mock_dialogue_manager.process_turn("Yes, that is completely accurate.")

    assert mock_dialogue_manager.state_machine.current_state == IntakeState.DONE
    # Report should have been generated automatically
    report = mock_dialogue_manager.get_patient_report()
    assert report is not None
    assert report.patient_id.startswith("PT-")
    assert report.to_markdown() is not None


def test_dynamic_suggestions_generation(mock_dialogue_manager):
    """Verify that dynamic suggestions match the question asked by the chatbot."""
    # 1. Greeting suggestions
    greeting = mock_dialogue_manager.get_greeting()
    suggestions = mock_dialogue_manager.get_current_suggestions()
    assert len(suggestions) >= 3
    assert any("headache" in s.lower() or "pain" in s.lower() for s in suggestions)

    # 2. Location question suggestions
    loc_suggestions = mock_dialogue_manager.generate_dynamic_suggestions(
        "Whereabouts in your body or head does this feel most intense?"
    )
    assert len(loc_suggestions) >= 3
    assert any("forehead" in s.lower() or "temple" in s.lower() for s in loc_suggestions)

    # 3. Sensation question suggestions
    sen_suggestions = mock_dialogue_manager.generate_dynamic_suggestions(
        "How would you describe the feeling—is it more of a throbbing, burning, or sharp ache?"
    )
    assert len(sen_suggestions) >= 3
    assert any("throbbing" in s.lower() or "sharp" in s.lower() for s in sen_suggestions)

    # 4. Modality question suggestions
    mod_suggestions = mock_dialogue_manager.generate_dynamic_suggestions(
        "What seems to make it worse, or what triggers it?"
    )
    assert len(mod_suggestions) >= 3
    assert any("worse" in s.lower() or "heat" in s.lower() for s in mod_suggestions)

    # 5. Quick replies parsing
    model_output = (
        "I'm noting that down. Where does it hurt?\n"
        'QUICK_REPLIES: ["Left temple", "Right forehead", "Behind both eyes"]'
    )
    clean_text, parsed_opts = mock_dialogue_manager._parse_and_strip_quick_replies(model_output)
    assert "QUICK_REPLIES" not in clean_text
    assert parsed_opts == ["Left temple", "Right forehead", "Behind both eyes"]


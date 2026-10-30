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


def test_dialogue_manager_transcript_dimensions_coverage(mock_dialogue_manager):
    """Verify that clinical intake accurately captures all dimensions from real transcript expressions."""
    dm = mock_dialogue_manager
    dm.get_greeting()

    # Patient answers covering all 7 dimensions
    dm.process_turn("Severe anxiety & fearful apprehension")
    assert any("anxiet" in m or "fear" in m for m in dm.extracted_slots.get("mental", []))

    dm.process_turn("In my stomach and abdomen")
    assert "stomach" in dm.extracted_slots.get("location", [])
    assert "abdomen" in dm.extracted_slots.get("location", [])

    dm.process_turn("Heavy and tight")
    assert "heavy" in dm.extracted_slots.get("sensation", [])
    assert "tight" in dm.extracted_slots.get("sensation", [])

    dm.process_turn("Movement makes it worse")
    assert any("move" in a for a in dm.extracted_slots.get("modality_agg", []))

    dm.process_turn("Consistent feeling")
    assert "consistent" in dm.extracted_slots.get("temporal", [])

    dm.process_turn("Warmth soothes")
    assert any("warm" in a for a in dm.extracted_slots.get("modality_amel", []))

    dm.process_turn("Dizzy and nauseous")
    assert any("dizz" in c for c in dm.extracted_slots.get("concomitant", []))
    assert any("nause" in c for c in dm.extracted_slots.get("concomitant", []))

    # All 7 dimensions must have detected entries
    assert all(dm.detected_dimensions.values())


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
    assert report.patient_id.startswith(("PT-", "CASE-"))
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


def test_clean_message_text_strips_dangling_brackets_and_metadata():
    """Verify that clean_message_text completely removes lone brackets and leaked metadata."""
    # 1. Lone trailing bracket on newline (from screenshot bug)
    dirty_text_1 = "Noted — that sounds quite intense. Where in your body do you feel this?\n\n["
    assert DialogueManager.clean_message_text(dirty_text_1) == "Noted — that sounds quite intense. Where in your body do you feel this?"

    # 2. Text with bracketed QUICK_REPLIES
    dirty_text_2 = (
        "Noted — work stress can be overwhelming. Where in your body do you feel this?\n\n"
        "[\n"
        'QUICK_REPLIES: ["Head", "Chest", "Stomach", "Shoulders"]\n'
        "]"
    )
    dm = DialogueManager(mock_mode=True)
    clean_text, options = dm._parse_and_strip_quick_replies(dirty_text_2)
    assert clean_text == "Noted — work stress can be overwhelming. Where in your body do you feel this?"
    assert options == ["Head", "Chest", "Stomach", "Shoulders"]

    # 3. Text with both SLOT_UPDATE and QUICK_REPLIES
    dirty_text_3 = (
        "I understand completely. What sensation do you feel?\n\n"
        'SLOT_UPDATE: {"location": ["stomach"]}\n'
        'QUICK_REPLIES: ["Heavy and tight", "Burning ache"]'
    )
    text_after_slot, slots = dm._parse_and_strip_slot_update(dirty_text_3)
    assert slots.get("location") == ["stomach"]
    clean_text_3, options_3 = dm._parse_and_strip_quick_replies(text_after_slot)
    assert clean_text_3 == "I understand completely. What sensation do you feel?"
    assert options_3 == ["Heavy and tight", "Burning ache"]


def test_sanitize_extracted_slots():
    """Verify that sanitize_extracted_slots eliminates stopwords, resolves cross-dimension conflicts, and subsumes sub-phrases."""
    dirty_slots = {
        "location": ["stomach", "abdomen"],
        "sensation": ["sharp"],
        "modality_agg": ["alone", "worse alone", "sharp", "electric stabs"],
        "concomitant": ["sweating"],
        "mental": [
            "sadness",
            "alone",
            "emotional pain & sadness",
            "worse than",
            "hopeless",
            "utterly hopeless",
            "hopelessness",
        ],
    }
    cleaned = DialogueManager.sanitize_extracted_slots(dirty_slots)

    # 1. Location remains intact
    assert cleaned["location"] == ["stomach", "abdomen"]

    # 2. Sensation gets 'electric stabs' moved from modality_agg, sharp retained
    assert "sharp" in cleaned["sensation"]
    assert "electric stabs" in cleaned["sensation"]

    # 3. Modality Agg: 'sharp' and 'electric stabs' removed; 'alone' disambiguated in favor of 'worse alone'
    assert cleaned["modality_agg"] == ["worse alone"]

    # 4. Concomitant remains intact
    assert cleaned["concomitant"] == ["sweating"]

    # 5. Mental: 'worse than' stopword dropped; 'alone' removed; 'sadness', 'hopeless', 'hopelessness' subsumed
    assert "emotional pain & sadness" in cleaned["mental"]
    assert "utterly hopeless" in cleaned["mental"]
    assert "alone" not in cleaned["mental"]
    assert "worse than" not in cleaned["mental"]
    assert "hopeless" not in cleaned["mental"]
    assert "hopelessness" not in cleaned["mental"]
    assert "sadness" not in cleaned["mental"]


def test_parse_and_strip_quick_replies_rejects_clinician_questions():
    """Verify that suggestion chips never present doctor follow-up questions to the patient."""
    dm = DialogueManager(mock_mode=True)

    # Doctor questions generated by LLM (from screenshot bug)
    dirty_output = (
        "Noted — the intensity is increasing. Does this affect your daily life and relationships?\n\n"
        'QUICK_REPLIES: ["How long has this feeling of hopelessness been present?", '
        '"Are there any specific situations or people that trigger this feeling?", '
        '"Can you describe any recent changes or stressors that might be present?", '
        '"Is there anything that provides you with a sense of comfort or relief?"]'
    )
    clean_text, options = dm._parse_and_strip_quick_replies(dirty_output)

    # Doctor questions must be completely rejected
    assert options == []

    # Dynamic suggestions should produce valid first-person patient answers
    dynamic_replies = dm.generate_dynamic_suggestions(clean_text)
    assert len(dynamic_replies) >= 3
    for reply in dynamic_replies:
        assert not reply.endswith("?")
        assert not any(reply.lower().startswith(q) for q in ["how ", "what ", "why ", "can you ", "are there "])


def test_state_machine_confirmation_triggers():
    """Verify that state machine advances from REVIEW to DONE with conversational confirmation keywords."""
    fsm = ConversationStateMachine()
    fsm.current_state = IntakeState.REVIEW

    # Test various user confirmations
    confirmations = ["proceed", "ready to view remedies", "that covers everything", "analyze my remedies"]
    for phrase in confirmations:
        fsm.current_state = IntakeState.REVIEW
        fsm.next_state(phrase)
        assert fsm.current_state == IntakeState.DONE


def test_ollama_chat_timeout_fallback(monkeypatch):
    """Verify that TimeoutError or network exceptions in _call_ollama_chat gracefully return fallback."""
    import urllib.request

    dm = DialogueManager(mock_mode=False)

    class DummyOpener:
        def open(self, *args, **kwargs):
            raise TimeoutError("timed out")

    monkeypatch.setattr(urllib.request, "build_opener", lambda *args: DummyOpener())

    # Must NOT raise TimeoutError; must return fallback message safely
    reply = dm._call_ollama_chat("Hello")
    assert reply is not None
    assert len(reply) > 0


def test_done_transition_instant_response(mock_dialogue_manager):
    """Verify that proceeding from REVIEW to DONE generates report and immediate response without hanging."""
    dm = mock_dialogue_manager
    dm.state_machine.current_state = IntakeState.REVIEW
    dm.extracted_slots = {
        "location": ["head and temples"],
        "sensation": ["sharp", "dizziness"],
        "modality_agg": ["motion"],
        "modality_amel": [],
        "concomitant": ["lightheadedness"],
        "temporal": [],
        "mental": ["severe anxiety"],
    }

    reply = dm.process_turn("Let's proceed with the analysis")
    assert dm.state_machine.current_state == IntakeState.DONE
    assert "repertorization" in reply.lower() or "framework" in reply.lower() or "ready" in reply.lower()
    assert dm.get_patient_report() is not None
    assert any("remed" in s.lower() or "consultation" in s.lower() for s in dm.current_suggestions)




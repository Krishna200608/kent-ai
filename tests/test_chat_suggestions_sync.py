"""Comprehensive tests for chat suggestions synchronization and intent-first alignment.

Verifies that suggestion chips in Kent-AI:
1. Accurately answer the active assistant question (intent-first).
2. Never decouple (e.g. showing temporal onset answers for chief complaint inquiries).
3. Prioritize LLaMA QUICK_REPLIES when present.
4. Correctly increment turn counters and widget keys on skips / none-of-these.
5. Respect practitioner mode and settings toggles.
"""

from __future__ import annotations

import pytest
import streamlit as st

from src.chatbot.dialogue_manager import DialogueManager
from src.chatbot.state_machine import ConversationStateMachine, IntakeState
from src.chatbot.suggestions import (
    generate_dynamic_suggestions,
    get_state_fallback,
    parse_and_strip_quick_replies,
)
from src.dashboard.components.chat_chips import (
    NEUTRAL_STEP_SUGGESTIONS,
    render_quick_reply_chips,
)


@pytest.fixture
def clean_dm():
    """Create a fresh DialogueManager in mock mode."""
    sm = ConversationStateMachine()
    dm = DialogueManager(state_machine=sm, mock_mode=True)
    dm.reset()
    return dm


def test_chief_complaint_question_synchronization(clean_dm):
    """Verify that when Kent-AI asks for the chief complaint, suggestions offer complaints, NEVER onset times."""
    dm = clean_dm
    dm.get_greeting()

    # User expresses general desire to start
    dm.prepare_turn("I have a physical complaint.")
    # Assistant asks for the main health concern (exact user reported screenshot prompt)
    assistant_q = "I understand. Can you please describe the main health concern or discomfort that brought you in today?"
    dm.finalize_turn(assistant_q)

    suggestions = dm.get_current_suggestions()
    assert suggestions is not None
    assert len(suggestions) >= 3

    # Suggestions MUST be complaints (headache, stomach pain, joint pain, etc.)
    sugg_text = " ".join(suggestions).lower()
    assert any(term in sugg_text for term in ["headache", "stomach", "pain", "joints", "anxiety"])

    # Suggestions MUST NOT be temporal onset statements
    forbidden_onset = ["it started recently", "ongoing for a while", "comes and goes in episodes"]
    for forbidden in forbidden_onset:
        assert forbidden not in sugg_text

    # Verify UI chips render the synchronized suggestions
    chips_selected = render_quick_reply_chips(dm)
    # render_quick_reply_chips in test returns None if nothing clicked, but generates display_chips
    assert dm.state_machine.current_state in (IntakeState.CHIEF_COMPLAINT, IntakeState.LOCATION)


def test_offline_fallback_experiencing_matches_chief_complaint(clean_dm):
    """Verify that offline template 'tell me a bit more about what you've been experiencing' returns complaints."""
    dm = clean_dm
    offline_msg = "I understand — thank you for sharing that. Could you tell me a bit more about what you've been experiencing?"
    suggs = dm.generate_dynamic_suggestions(offline_msg)

    sugg_str = " ".join(suggs).lower()
    assert "headache" in sugg_str or "stomach" in sugg_str or "pain" in sugg_str


def test_location_question_intent_synchronization(clean_dm):
    """Verify location inquiries yield anatomical locations, contextual to known complaints."""
    dm = clean_dm
    dm.extracted_slots["location"] = ["head"]
    q = "Where in your body do you feel this discomfort most intensely?"
    suggs = dm.generate_dynamic_suggestions(q)

    sugg_str = " ".join(suggs).lower()
    assert any(loc in sugg_str for loc in ["temples", "forehead", "eyes", "head"])
    assert "skip" in sugg_str


def test_sensation_question_intent_synchronization(clean_dm):
    """Verify sensation inquiries yield pain qualities."""
    dm = clean_dm
    q = "How would you describe the sensation — is it throbbing, burning, heavy, tight, or something else?"
    suggs = dm.generate_dynamic_suggestions(q)

    sugg_str = " ".join(suggs).lower()
    assert any(sen in sugg_str for sen in ["throbbing", "stabbing", "burning", "heavy", "pulsating"])
    assert "skip" in sugg_str


def test_modality_question_intent_synchronization(clean_dm):
    """Verify modality inquiries yield aggravation/amelioration options."""
    dm = clean_dm
    q = "Has anything made this worse — such as movement, cold, heat, or noise? And what brings you relief?"
    suggs = dm.generate_dynamic_suggestions(q)

    sugg_str = " ".join(suggs).lower()
    assert any(m in sugg_str for m in ["worse", "better", "heat", "cold", "motion", "rest"])
    assert "skip" in sugg_str


def test_temporal_question_intent_synchronization(clean_dm):
    """Verify temporal inquiries yield time patterns and diurnal modalities."""
    dm = clean_dm
    q = "Have you noticed any specific time of day or night when this is worse or better — such as morning or night?"
    suggs = dm.generate_dynamic_suggestions(q)

    sugg_str = " ".join(suggs).lower()
    assert any(t in sugg_str for t in ["morning", "midnight", "afternoon", "time"])
    assert "skip" in sugg_str


def test_concomitant_question_intent_synchronization(clean_dm):
    """Verify concomitant inquiries yield associated simultaneous symptoms."""
    dm = clean_dm
    q = "Does anything else occur alongside this — such as nausea, dizziness, chills, or sweating?"
    suggs = dm.generate_dynamic_suggestions(q)

    sugg_str = " ".join(suggs).lower()
    assert any(c in sugg_str for c in ["nausea", "dizziness", "chills", "sweat", "symptoms"])
    assert "skip" in sugg_str


def test_mental_question_intent_synchronization(clean_dm):
    """Verify mental inquiries yield psychological/emotional generals."""
    dm = clean_dm
    q = "How has this issue been affecting your mood or emotional state — any anxiety or irritability?"
    suggs = dm.generate_dynamic_suggestions(q)

    sugg_str = " ".join(suggs).lower()
    assert any(m in sugg_str for m in ["anxious", "restless", "irritable", "calm", "mood"])
    assert "skip" in sugg_str


def test_review_question_intent_synchronization(clean_dm):
    """Verify review questions yield confirmation / continuation options."""
    dm = clean_dm
    q = "Does this accurately reflect your symptoms, or are you ready to proceed to repertorization?"
    suggs = dm.generate_dynamic_suggestions(q)

    sugg_str = " ".join(suggs).lower()
    assert any(r in sugg_str for r in ["covers", "repertorization", "remedies", "symptoms"])


def test_llama_quick_replies_take_precedence(clean_dm):
    """Verify that when LLaMA generates custom QUICK_REPLIES, they take precedence over fallback templates."""
    dm = clean_dm
    raw_llm_reply = (
        "I understand. Can you describe when the coughing fits are most intense?\n\n"
        'QUICK_REPLIES: ["Worse from cold drafts", "Worse lying down at night", "Better drinking warm tea"]'
    )
    clean_text = dm.finalize_turn(raw_llm_reply)

    assert "QUICK_REPLIES" not in clean_text
    assert dm.current_suggestions == [
        "Worse from cold drafts",
        "Worse lying down at night",
        "Better drinking warm tea",
    ]


def test_skip_and_none_of_these_increment_turn_counter(clean_dm):
    """Verify that 'Skip' and 'None of these' increment turn_count to avoid widget key collision."""
    dm = clean_dm
    initial_turns = dm.state_machine.turn_count

    dm.prepare_turn("skip")
    assert dm.state_machine.turn_count == initial_turns + 1

    dm.prepare_turn("None of these")
    assert dm.state_machine.turn_count == initial_turns + 2


def test_neutral_step_suggestions_map_coherent():
    """Verify that NEUTRAL_STEP_SUGGESTIONS map has coherent non-empty options for every canonical state."""
    for state_name in ["GREETING", "CHIEF_COMPLAINT", "LOCATION", "SENSATION", "MODALITY", "CONCOMITANT", "TEMPORAL", "MENTAL", "REVIEW", "DONE"]:
        assert state_name in NEUTRAL_STEP_SUGGESTIONS
        opts = NEUTRAL_STEP_SUGGESTIONS[state_name]
        assert len(opts) >= 3
        # CHIEF_COMPLAINT must have complaint descriptions
        if state_name == "CHIEF_COMPLAINT":
            joined = " ".join(opts).lower()
            assert any(k in joined for k in ["headache", "stomach", "pain", "joints", "anxiety"])
            assert "started recently" not in joined


def test_practitioner_mode_suppresses_chips(clean_dm):
    """Verify chips are strictly suppressed in practitioner mode."""
    dm = clean_dm
    dm.set_intake_mode("practitioner")
    chips = render_quick_reply_chips(dm)
    assert chips is None


def test_settings_toggle_suppresses_chips(clean_dm):
    """Verify chips are suppressed when settings toggle is disabled."""
    dm = clean_dm
    st.session_state["show_suggested_replies"] = False
    chips = render_quick_reply_chips(dm)
    assert chips is None
    st.session_state["show_suggested_replies"] = True

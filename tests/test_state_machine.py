"""Unit tests for ConversationStateMachine (Phase 6)."""

import pytest

from src.chatbot.state_machine import ConversationStateMachine, IntakeState


def test_state_machine_initial_state():
    fsm = ConversationStateMachine()
    assert fsm.current_state == IntakeState.GREETING
    assert not fsm.can_terminate()


def test_state_machine_basic_transition():
    fsm = ConversationStateMachine()
    
    # 1. Greeting -> Chief complaint
    state = fsm.next_state("Hello, I am not feeling well.")
    assert state == IntakeState.CHIEF_COMPLAINT

    # 2. Chief complaint -> Location
    state = fsm.next_state("My head has been hurting.")
    assert state == IntakeState.LOCATION


def test_state_machine_adaptive_slot_skipping():
    fsm = ConversationStateMachine()
    fsm.next_state("Hello")  # Now at CHIEF_COMPLAINT

    # User immediately provides location AND sensation AND temporal
    extracted = {
        "location": ["forehead"],
        "sensation": ["throbbing"],
        "temporal": ["morning"],
    }
    state = fsm.next_state(
        "I have a throbbing pain in my forehead every morning.",
        extracted_slots=extracted,
    )
    # Since location and sensation are already filled, it should skip directly to MODALITY!
    assert state == IntakeState.MODALITY
    assert "location" in fsm.filled_slots
    assert "sensation" in fsm.filled_slots


def test_state_machine_review_and_done():
    fsm = ConversationStateMachine()
    fsm.current_state = IntakeState.REVIEW
    
    # User confirms
    next_s = fsm.next_state("Yes, that sounds exactly right, thank you.")
    assert next_s == IntakeState.DONE
    assert fsm.can_terminate()


def test_state_machine_review_and_clarification():
    fsm = ConversationStateMachine()
    fsm.current_state = IntakeState.REVIEW

    # User adds a correction
    next_s = fsm.next_state("Actually, it also hurts when I drink cold water.")
    assert next_s == IntakeState.CLARIFICATION

    # From clarification, goes back to review
    next_s = fsm.next_state("That is all now.")
    assert next_s == IntakeState.REVIEW


def test_state_machine_max_turns_termination():
    fsm = ConversationStateMachine(max_turns=3)
    fsm.next_state("Turn 1")
    fsm.next_state("Turn 2")
    fsm.next_state("Turn 3")
    assert fsm.current_state == IntakeState.DONE

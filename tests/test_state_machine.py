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


def test_state_machine_temporal_intake_flow():
    """Verify that IntakeState.TEMPORAL is systematically visited before MENTAL and REVIEW."""
    fsm = ConversationStateMachine()
    
    # 1. Greeting -> Chief complaint
    assert fsm.next_state("Hello") == IntakeState.CHIEF_COMPLAINT

    # 2. Chief complaint -> Location
    assert fsm.next_state("Chest pain") == IntakeState.LOCATION

    # 3. Location -> Sensation
    assert fsm.next_state("In the center of my chest", extracted_slots={"location": ["chest"]}) == IntakeState.SENSATION

    # 4. Sensation -> Modalities
    assert fsm.next_state("Heavy pressing dull ache", extracted_slots={"sensation": ["heavy", "pressing"]}) == IntakeState.MODALITY

    # 5. Modalities -> Concomitants
    assert fsm.next_state("Worse walking, better resting", extracted_slots={"modality_agg": ["walking"], "modality_amel": ["resting"]}) == IntakeState.CONCOMITANT

    # 6. Concomitants -> TEMPORAL (Time pattern MUST be asked!)
    assert fsm.next_state("Bloating in stomach", extracted_slots={"concomitant": ["bloating"]}) == IntakeState.TEMPORAL

    # 7. Temporal -> Mental
    assert fsm.next_state("Worse around 3 AM", extracted_slots={"temporal": ["3 AM"]}) == IntakeState.MENTAL

    # 8. Mental -> Review
    assert fsm.next_state("Very anxious and restless", extracted_slots={"mental": ["anxious"]}) == IntakeState.REVIEW

    # 9. Review confirmation -> DONE
    assert fsm.next_state("Yes, that covers all my symptoms!") == IntakeState.DONE
    assert fsm.can_terminate()


def test_state_machine_clinical_stage_flow():
    """Verify that clinical stage flow contains 10 steps including Time Pattern."""
    flow = ConversationStateMachine.get_clinical_stage_flow()
    assert len(flow) == 10
    stage_enums = [s[0] for s in flow]
    assert IntakeState.TEMPORAL in stage_enums
    # Check proper order
    assert stage_enums == [
        IntakeState.GREETING,
        IntakeState.CHIEF_COMPLAINT,
        IntakeState.LOCATION,
        IntakeState.SENSATION,
        IntakeState.MODALITY,
        IntakeState.CONCOMITANT,
        IntakeState.TEMPORAL,
        IntakeState.MENTAL,
        IntakeState.REVIEW,
        IntakeState.DONE,
    ]


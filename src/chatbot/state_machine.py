"""Patient intake conversation state machine with finite states."""

from __future__ import annotations

from enum import Enum
from typing import Optional


class IntakeState(str, Enum):
    """Dialogue states for patient symptom intake."""
    GREETING = "GREETING"
    CHIEF_COMPLAINT = "CHIEF_COMPLAINT"
    LOCATION = "LOCATION"
    SENSATION = "SENSATION"
    MODALITY = "MODALITY"
    CONCOMITANT = "CONCOMITANT"
    MENTAL = "MENTAL"
    REVIEW = "REVIEW"
    CLARIFICATION = "CLARIFICATION"
    DONE = "DONE"


class ConversationStateMachine:
    """Manages transitions between clinical intake states."""

    def __init__(self, initial_state: IntakeState = IntakeState.GREETING) -> None:
        self.current_state = initial_state

    def next_state(self, user_response: str) -> IntakeState:
        """Evaluate response and transition to next state."""
        raise NotImplementedError("Phase 6 implementation pending.")

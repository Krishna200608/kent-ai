"""Multi-turn dialogue manager orchestrating context history and slot filling."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.chatbot.state_machine import ConversationStateMachine, IntakeState


class DialogueManager:
    """Orchestrates intake conversation turns, slot filling, and termination."""

    def __init__(self, state_machine: Optional[ConversationStateMachine] = None) -> None:
        self.state_machine = state_machine or ConversationStateMachine()
        self.history: List[Dict[str, str]] = []
        self.extracted_slots: Dict[str, Any] = {}

    def process_turn(self, user_utterance: str) -> str:
        """Process user input and return bot response."""
        raise NotImplementedError("Phase 6 implementation pending.")

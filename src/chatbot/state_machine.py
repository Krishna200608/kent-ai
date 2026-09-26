"""Patient intake conversation state machine with finite states (Phase 6).

Implements adaptive dialogue flow across Kent's 7 dimensions with automatic slot
skipping, gentle confirmation, and pipeline handover.
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.config import get_chatbot_config

logger = logging.getLogger("state_machine")


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

    SLOT_ORDER: List[IntakeState] = [
        IntakeState.LOCATION,
        IntakeState.SENSATION,
        IntakeState.MODALITY,
        IntakeState.CONCOMITANT,
        IntakeState.MENTAL,
    ]

    def __init__(
        self,
        initial_state: IntakeState = IntakeState.GREETING,
        min_dimensions_required: Optional[int] = None,
        max_turns: Optional[int] = None,
    ) -> None:
        cfg = get_chatbot_config().get("chatbot", {})
        self.current_state = initial_state
        self.min_dimensions_required = min_dimensions_required or cfg.get("min_dimensions_required", 4)
        self.max_turns = max_turns or cfg.get("max_turns", 15)
        self.turn_count = 0
        self.filled_slots: Set[str] = set()

    def update_slots(self, extracted_slots: Dict[str, Any]) -> None:
        """Register newly identified clinical dimensions."""
        for slot_name, val in extracted_slots.items():
            if val and (isinstance(val, list) and len(val) > 0 or isinstance(val, str) and val.strip()):
                self.filled_slots.add(slot_name.lower())

    def _is_slot_filled(self, state: IntakeState) -> bool:
        """Check whether a specific dimension state has adequate information."""
        if state == IntakeState.LOCATION:
            return "location" in self.filled_slots or "loc" in self.filled_slots
        elif state == IntakeState.SENSATION:
            return "sensation" in self.filled_slots or "sen" in self.filled_slots
        elif state == IntakeState.MODALITY:
            return (
                "modality_agg" in self.filled_slots
                or "modality_amel" in self.filled_slots
                or "modality" in self.filled_slots
            )
        elif state == IntakeState.CONCOMITANT:
            return "concomitant" in self.filled_slots or "conc" in self.filled_slots
        elif state == IntakeState.MENTAL:
            return "mental" in self.filled_slots or "ment" in self.filled_slots
        return False

    def _get_next_unfilled_slot(self) -> Optional[IntakeState]:
        """Find the next clinical dimension that has not yet been addressed."""
        for state in self.SLOT_ORDER:
            if not self._is_slot_filled(state):
                return state
        return None

    def _is_confirmation(self, text: str) -> bool:
        """Detect patient confirmation in review state."""
        cleaned = text.strip().lower()
        positive_patterns = [
            r"^(?:yes|yeah|yep|correct|that'?s (?:it|all|right|correct)|sounds (?:good|right|accurate)|accurate|perfect|all good|no more|nothing else|that covers it)\b",
            r"\b(?:looks good|all set|nothing to add|that is all)\b",
        ]
        return any(re.search(pat, cleaned) for pat in positive_patterns)

    def next_state(
        self,
        user_response: str,
        extracted_slots: Optional[Dict[str, Any]] = None,
    ) -> IntakeState:
        """Evaluate patient response, update slots, and transition to next state.
        
        Args:
            user_response: What the patient said in the latest turn.
            extracted_slots: Optional dictionary of newly discovered slots.
            
        Returns:
            The updated IntakeState.
        """
        self.turn_count += 1
        if extracted_slots:
            self.update_slots(extracted_slots)

        # Force termination if maximum turns exceeded
        if self.turn_count >= self.max_turns:
            self.current_state = IntakeState.DONE
            return self.current_state

        if self.current_state == IntakeState.GREETING:
            self.current_state = IntakeState.CHIEF_COMPLAINT

        elif self.current_state == IntakeState.CHIEF_COMPLAINT:
            next_slot = self._get_next_unfilled_slot()
            self.current_state = next_slot if next_slot else IntakeState.REVIEW

        elif self.current_state in self.SLOT_ORDER:
            # Check if we have met the required quota of dimensions
            if len(self.filled_slots) >= self.min_dimensions_required and self.turn_count >= 5:
                next_slot = self._get_next_unfilled_slot()
                # If only 1 slot left or patient covered essentials, move to review
                if not next_slot or len(self.filled_slots) >= 5:
                    self.current_state = IntakeState.REVIEW
                else:
                    self.current_state = next_slot
            else:
                next_slot = self._get_next_unfilled_slot()
                self.current_state = next_slot if next_slot else IntakeState.REVIEW

        elif self.current_state == IntakeState.REVIEW:
            if self._is_confirmation(user_response):
                self.current_state = IntakeState.DONE
            else:
                self.current_state = IntakeState.CLARIFICATION

        elif self.current_state == IntakeState.CLARIFICATION:
            self.current_state = IntakeState.REVIEW

        return self.current_state

    def get_current_goal_description(self) -> str:
        """Returns a natural guiding focus for the LLM based on the active state."""
        goals = {
            IntakeState.GREETING: "Warmly introduce yourself as Kent-AI and invite the patient to share how they are feeling today.",
            IntakeState.CHIEF_COMPLAINT: "Ask what main health concern or discomfort brought them in today.",
            IntakeState.LOCATION: "Gently ask where in the body the discomfort or pain is located (e.g. side, specific organ or region).",
            IntakeState.SENSATION: "Inquire about what the sensation feels like (e.g. throbbing, burning, dull ache, stitching, pressure).",
            IntakeState.MODALITY: "Ask what makes the symptom feel worse (motion, cold, heat, light, noise) or what brings comfort and relief.",
            IntakeState.CONCOMITANT: "Kindly check if any other symptoms or feelings happen at the same time (like nausea, dizziness, chills).",
            IntakeState.MENTAL: "Ask with compassion how this issue has been affecting their mood, energy, or stress levels.",
            IntakeState.REVIEW: "Warmly summarize the key symptoms they described and ask if this sounds accurate or if they'd like to add anything.",
            IntakeState.CLARIFICATION: "Thank the patient for clarifying and confirm the updated detail.",
            IntakeState.DONE: "Warmly conclude the conversation, reassure them, and let them know their repertory report is ready.",
        }
        return goals.get(self.current_state, "Listen attentively and support the patient.")

    def can_terminate(self) -> bool:
        """Check if consultation has reached completion."""
        return self.current_state == IntakeState.DONE

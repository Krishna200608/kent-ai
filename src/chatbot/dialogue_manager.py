"""Multi-turn dialogue manager orchestrating context history and slot filling (Phase 6).

Coordinates clinical intake across conversation turns, delegating extraction to
slot_extractor, HTTP calls to ollama_client, and suggestions to suggestions.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from src.chatbot.prompts import (
    CHATBOT_PRACTITIONER_SYSTEM_PROMPT,
    CHATBOT_SYSTEM_PROMPT,
    CHATBOT_TURN_PROMPT,
)
from src.chatbot.state_machine import ConversationStateMachine, IntakeState
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport, PipelineOrchestrator

from src.config import get_chatbot_config

from src.chatbot.slot_extractor import (
    _load_vocab,
    _load_llm_extraction_config,
    _load_generate_button_config,
    get_min_dimensions_to_unlock,
    extract_slots_heuristic,
    extract_slots_clinicalbert,
    extract_slots_llm,
    extract_all_slots,
    sanitize_extracted_slots,
)
from src.chatbot.ollama_client import (
    is_ollama_online,
    call_ollama_chat_stream,
    call_ollama_chat,
    visible_only,
)
from src.chatbot.suggestions import (
    clean_message_text,
    parse_and_strip_quick_replies,
    parse_and_strip_slot_update,
    generate_dynamic_suggestions,
    get_state_fallback,
)

logger = logging.getLogger("dialogue_manager")

# Re-exports for 100% backward compatibility
__all__ = [
    "DialogueManager",
    "get_min_dimensions_to_unlock",
    "_load_vocab",
    "_load_llm_extraction_config",
    "_load_generate_button_config",
    "clean_message_text",
    "sanitize_extracted_slots",
    "is_ollama_online",
    "visible_only",
]


PATIENT_GREETING = (
    "Hello, I am Kent-AI, your clinical homeopathic intake assistant. "
    "I'm here to understand what is troubling you today. "
    "Please describe what primary symptoms or discomfort brought you in."
)

PRACTITIONER_GREETING = (
    "Kent-AI Practitioner Mode active. Ready for clinical intake — "
    "enter patient chief complaint, observations, or presenting symptoms."
)


class DialogueManager:
    """Orchestrates intake conversation turns, slot filling, and termination.

    Slot extraction uses a 3-tier pipeline (see module docstring). The tiers
    are independent — failure in any tier is silently logged and the next tier
    continues, ensuring robustness regardless of model availability.
    """

    def __init__(
        self,
        state_machine: Optional[ConversationStateMachine] = None,
        orchestrator: Optional[PipelineOrchestrator] = None,
        model_name: Optional[str] = None,
        api_base: Optional[str] = None,
        mock_mode: bool = False,
        case: Optional[ClinicalCase] = None,
    ) -> None:
        cfg = get_chatbot_config().get("chatbot", {})
        self.state_machine = state_machine or ConversationStateMachine()
        self.orchestrator = orchestrator
        self.model_name = model_name or cfg.get("model", "llama3:8b")
        self.api_base = api_base or cfg.get("api_base", "http://127.0.0.1:11434")
        self.temperature = float(cfg.get("temperature", 0.5))
        self.mock_mode = mock_mode
        self.case = case

        self.history: List[Dict[str, str]] = []
        self.extracted_slots: Dict[str, List[str]] = {
            "location": [],
            "sensation": [],
            "modality_agg": [],
            "modality_amel": [],
            "concomitant": [],
            "temporal": [],
            "mental": [],
        }
        self.patient_report: Optional[PatientReport] = None
        self.current_suggestions: List[str] = []
        self.last_call_failed: bool = False
        self.intake_mode: str = "patient"

        if case is not None:
            self.load_from_case(case)

    def sync_to_case(self, target_case: Optional[ClinicalCase] = None) -> ClinicalCase:
        """Synchronize dialogue manager slots and history into the typed ClinicalCase."""
        c = target_case or self.case or ClinicalCase()
        for k in c.dimensions:
            if k in self.extracted_slots:
                c.set_dimension_values(k, self.extracted_slots[k])
        c.dialogue_history = list(self.history)
        if not c.chief_complaint and self.history:
            for turn in self.history:
                if turn.get("role") == "user":
                    c.chief_complaint = turn["content"][:120]
                    break
        c.transcript = self.get_full_transcript()
        return c

    def load_from_case(self, source_case: ClinicalCase) -> None:
        """Hydrate dialogue state and history from an existing ClinicalCase."""
        self.case = source_case
        for k, vals in source_case.dimensions.items():
            if k in self.extracted_slots:
                self.extracted_slots[k] = list(vals)
                if vals:
                    self.state_machine.filled_slots.add(k)
        if source_case.dialogue_history:
            self.history = list(source_case.dialogue_history)

    @property
    def detected_dimensions(self) -> Dict[str, bool]:
        """Expose dimension detection flags covering Kent's 7 canonical totality dimensions."""
        return {
            "location": bool(self.extracted_slots.get("location")),
            "sensation": bool(self.extracted_slots.get("sensation")),
            "modality_agg": bool(self.extracted_slots.get("modality_agg")),
            "modality_amel": bool(self.extracted_slots.get("modality_amel")),
            "concomitant": bool(self.extracted_slots.get("concomitant")),
            "temporal": bool(self.extracted_slots.get("temporal")),
            "mental": bool(self.extracted_slots.get("mental")),
        }

    def get_greeting(self) -> str:
        """Return opening message and add to history if starting fresh."""
        is_practitioner = getattr(self, "intake_mode", "patient") == "practitioner"
        greeting = PRACTITIONER_GREETING if is_practitioner else PATIENT_GREETING
        if not self.history:
            self.history.append({"role": "assistant", "content": greeting})
            self.current_suggestions = self.generate_dynamic_suggestions(greeting)
        return greeting

    def set_intake_mode(self, mode: str) -> None:
        """Update intake mode ('patient' or 'practitioner') and update opening message if fresh."""
        new_mode = (mode or "patient").lower().strip()
        old_mode = getattr(self, "intake_mode", "patient")
        self.intake_mode = new_mode

        # If fresh session (only the initial greeting is present), update the greeting text
        if len(self.history) == 1 and self.history[0]["role"] == "assistant":
            if self.history[0]["content"] in (PATIENT_GREETING, PRACTITIONER_GREETING) or old_mode != new_mode:
                new_greeting = PRACTITIONER_GREETING if new_mode == "practitioner" else PATIENT_GREETING
                self.history[0]["content"] = new_greeting
                self.current_suggestions = self.generate_dynamic_suggestions(new_greeting)

    # Delegated Slot Extraction Helpers
    def _extract_slots_heuristic(self, text: str) -> Dict[str, List[str]]:
        return extract_slots_heuristic(text, current_state=self.state_machine.current_state)

    def _extract_slots_clinicalbert(self, text: str) -> Dict[str, List[str]]:
        return extract_slots_clinicalbert(text, orchestrator=self.orchestrator)

    def _extract_slots_llm(self, user_utterance: str) -> Dict[str, List[str]]:
        return extract_slots_llm(
            user_utterance,
            api_base=self.api_base,
            model_name=self.model_name,
            current_state=self.state_machine.current_state,
        )

    def _extract_all_slots(self, user_utterance: str) -> Dict[str, List[str]]:
        return extract_all_slots(
            user_utterance,
            current_state=self.state_machine.current_state,
            orchestrator=self.orchestrator,
            api_base=self.api_base,
            model_name=self.model_name,
            mock_mode=self.mock_mode,
            is_llm_online=self.is_ollama_online(),
        )

    @staticmethod
    def sanitize_extracted_slots(slots: Dict[str, List[str]]) -> Dict[str, List[str]]:
        return sanitize_extracted_slots(slots)

    # Delegated Ollama HTTP Client Methods
    def _call_ollama_chat_stream(self, user_prompt: str):
        system_prompt = (
            CHATBOT_PRACTITIONER_SYSTEM_PROMPT
            if getattr(self, "intake_mode", "patient") == "practitioner"
            else CHATBOT_SYSTEM_PROMPT
        )
        return call_ollama_chat_stream(
            user_prompt=user_prompt,
            api_base=self.api_base,
            model_name=self.model_name,
            system_prompt=system_prompt,
            history=self.history[:-1],
            temperature=self.temperature,
        )

    def _call_ollama_chat(self, user_prompt: str, stream: bool = False):
        if stream:
            return self._call_ollama_chat_stream(user_prompt)
        try:
            full = "".join(self._call_ollama_chat_stream(user_prompt)).strip()
            return full or self._mock_response_for_state()
        except Exception as err:
            logger.warning("Ollama call failed or timed out (%s). Using fallback template.", err)
            self.last_call_failed = True
            return self._mock_response_for_state()

    def stream_reply(self, turn_prompt: str):
        """Expose a generator yielding reply pieces from Ollama or fallback template."""
        current_state = self.state_machine.current_state
        if self.mock_mode or current_state == IntakeState.DONE or not turn_prompt:
            yield self._mock_response_for_state()
            return

        had_chunks = False
        try:
            for piece in self._call_ollama_chat(turn_prompt, stream=True):
                had_chunks = True
                yield piece
        except Exception as err:
            logger.warning("Error in stream_reply (%s). Using fallback.", err)
            self.last_call_failed = True
            if not had_chunks:
                yield self._mock_response_for_state()

    @staticmethod
    def visible_only(chunks, sink: list):
        return visible_only(chunks, sink)

    def is_ollama_online(self) -> bool:
        return is_ollama_online(self.api_base)

    # Deterministic Mock Fallback per State
    def _mock_response_for_state(self) -> str:
        """Deterministic, clinically focused offline fallback responses per state."""
        state = self.state_machine.current_state
        is_practitioner = getattr(self, "intake_mode", "patient") == "practitioner"

        if is_practitioner:
            if state == IntakeState.REVIEW:
                summary_lines = []
                for k, v in self.extracted_slots.items():
                    if v:
                        dim_title = k.replace("_", " ").title()
                        summary_lines.append(f"• **{dim_title}**: {', '.join(v)}")
                summary_block = "\n".join(summary_lines) if summary_lines else "• Primary complaint noted."
                return (
                    "Clinical Totality Review:\n\n"
                    f"{summary_block}\n\n"
                    "Verify recorded totality or enter additional clinical findings."
                )
            if state == IntakeState.CLARIFICATION:
                return "Enter the specific clinical finding or modality to add."
            practitioner_templates = {
                IntakeState.GREETING: PRACTITIONER_GREETING,
                IntakeState.CHIEF_COMPLAINT: "Chief complaint noted. Specify primary anatomical location or affected organ system.",
                IntakeState.LOCATION: "Location recorded. Describe sensation quality (e.g., throbbing, stitching, burning, dull heaviness).",
                IntakeState.SENSATION: "Sensation recorded. Specify modalities: what aggravates (MOD_AGG) or ameliorates (MOD_AMEL) this condition?",
                IntakeState.MODALITY: "Modalities recorded. Are there any concomitant symptoms occurring simultaneously (e.g., nausea, vertigo, chills)?",
                IntakeState.CONCOMITANT: "Concomitants recorded. Note temporal periodicity or specific diurnal aggravation hours (e.g., 3 AM, morning, evening).",
                IntakeState.TEMPORAL: "Temporal pattern recorded. Note mental/emotional generals (e.g., anxiety, restlessness, irritability, depression).",
                IntakeState.MENTAL: "Mental generals recorded. Clinical intake totality complete.",
                IntakeState.DONE: (
                    "Clinical totality recorded. Click **Proceed to Review →** above to inspect 7-dimension cards and compute repertorization ranking."
                ),
            }
            return practitioner_templates.get(state, "Enter additional clinical observation.")

        if state == IntakeState.REVIEW:
            summary_lines = []
            for k, v in self.extracted_slots.items():
                if v:
                    dim_title = k.replace("_", " ").title()
                    summary_lines.append(f"• **{dim_title}**: {', '.join(v)}")
            summary_block = "\n".join(summary_lines) if summary_lines else "• Primary complaint noted."
            return (
                "Thank you for sharing all of this with me. Let me confirm what we've captured:\n\n"
                f"{summary_block}\n\n"
                "Does this accurately reflect your symptoms, or would you like to add or correct any detail?"
            )

        if state == IntakeState.CLARIFICATION:
            return "Please describe the additional symptom or detail you'd like to add."

        templates = {
            IntakeState.CHIEF_COMPLAINT: (
                "I understand — thank you for sharing that. "
                "Could you tell me a bit more about what you've been experiencing?"
            ),
            IntakeState.LOCATION: (
                "Noted. Where in your body do you feel this most intensely?"
            ),
            IntakeState.SENSATION: (
                "Thank you. How would you describe the sensation — "
                "is it throbbing, burning, heavy, tight, or something else?"
            ),
            IntakeState.MODALITY: (
                "That helps. Has anything made this worse — such as movement, cold, heat, or noise? "
                "And what brings you any relief?"
            ),
            IntakeState.CONCOMITANT: (
                "Noted. Does anything else occur alongside this — "
                "such as nausea, dizziness, chills, or sweating?"
            ),
            IntakeState.TEMPORAL: (
                "Thank you. Have you noticed any specific time of day or night when this is worse or better — "
                "such as in the morning on waking, afternoon, late evening, or waking up around 2-3 AM?"
            ),
            IntakeState.MENTAL: (
                "I appreciate you sharing that. How has this been affecting your mood "
                "or emotional state — any anxiety, irritability, or low energy?"
            ),
            IntakeState.DONE: (
                "Thank you — I have gathered and structured all your clinical symptoms into the Kentian totality framework. "
                "You can now click on **Proceed to Review →** above to inspect your captured dimensions, validate the doctor's case summary, and run repertorization analysis."
            ),
        }
        return templates.get(state, "Please tell me more about that.")

    # Sanitization & Parsing Methods
    @staticmethod
    def clean_message_text(text: str) -> str:
        return clean_message_text(text)

    def _parse_and_strip_quick_replies(self, text: str) -> Tuple[str, List[str]]:
        return parse_and_strip_quick_replies(text)

    def _parse_and_strip_slot_update(self, text: str) -> Tuple[str, Dict[str, List[str]]]:
        return parse_and_strip_slot_update(text)

    # Dynamic Suggestions
    def generate_dynamic_suggestions(self, bot_message: str) -> List[str]:
        return generate_dynamic_suggestions(
            bot_message,
            extracted_slots=self.extracted_slots,
            current_state=self.state_machine.current_state,
            intake_mode=getattr(self, "intake_mode", "patient"),
        )

    def get_current_suggestions(self) -> List[str]:
        """Return the current dynamic instant-reply suggestions for the patient."""
        if not self.current_suggestions and self.history:
            last_bot_msg = self.history[-1]["content"] if self.history[-1]["role"] == "assistant" else ""
            if last_bot_msg:
                self.current_suggestions = self.generate_dynamic_suggestions(last_bot_msg)
        return self.current_suggestions or self.generate_dynamic_suggestions(
            self.history[-1]["content"] if self.history else ""
        )

    # Core Turn Processing
    def prepare_turn(self, user_utterance: str) -> str:
        """Run FSM transitions, history recording, and slot extraction.

        Returns the formatted turn prompt for LLM generation (or empty string if mock/done).
        """
        self.history.append({"role": "user", "content": user_utterance})
        new_slots = self._extract_all_slots(user_utterance)

        # Merge new slots into session-accumulated slots
        for k, v in new_slots.items():
            for item in v:
                if item not in self.extracted_slots.setdefault(k, []):
                    self.extracted_slots[k].append(item)

        # Advance state machine
        self.state_machine.next_state(user_utterance, extracted_slots=new_slots)

        current_state = self.state_machine.current_state
        if self.mock_mode or current_state == IntakeState.DONE:
            return ""

        # Build turn prompt for LLaMA 3
        current_goal = self.state_machine.get_current_goal_description()
        slots_lines = []
        for k, v in self.extracted_slots.items():
            if v:
                slots_lines.append(f"  {k}: {', '.join(v)}")
        slots_summary = "\n".join(slots_lines) if slots_lines else "  None yet"

        hist_lines = []
        for turn in self.history[-4:]:
            role_label = "Kent-AI" if turn["role"] == "assistant" else "Patient"
            hist_lines.append(f"{role_label}: {turn['content']}")
        hist_text = "\n".join(hist_lines)

        turn_prompt = CHATBOT_TURN_PROMPT.format(
            current_goal=current_goal,
            slots_summary=slots_summary,
            history=hist_text,
            user_utterance=user_utterance,
        )
        return turn_prompt

    def finalize_turn(self, raw_reply: str) -> str:
        """Sanitize raw LLaMA reply, extract inline metadata, and update suggestions."""
        current_state = self.state_machine.current_state

        if current_state == IntakeState.DONE:
            clean_reply = self._mock_response_for_state()
            self.history.append({"role": "assistant", "content": clean_reply})
            self.current_suggestions = ["Proceed to Review →", "Check Captured Symptoms", "Add Another Detail", "Start New Consultation"]
            if self.orchestrator:
                self.patient_report = self.orchestrator.process_transcript(
                    self.get_full_transcript(),
                    patient_id="PT-INTAKE",
                )
            return clean_reply

        clean_text, direct_options = self._parse_and_strip_quick_replies(raw_reply)
        clean_text, bot_extracted = self._parse_and_strip_slot_update(clean_text)

        if bot_extracted:
            for k, v in bot_extracted.items():
                for item in v:
                    if item not in self.extracted_slots.setdefault(k, []):
                        self.extracted_slots[k].append(item)
            self.state_machine.update_slots(bot_extracted)

        clean_text = self.clean_message_text(clean_text)
        if not clean_text:
            clean_text = self._mock_response_for_state()

        self.history.append({"role": "assistant", "content": clean_text})

        if direct_options and len(direct_options) >= 2:
            self.current_suggestions = direct_options[:4]
        else:
            self.current_suggestions = self.generate_dynamic_suggestions(clean_text)

        return clean_text

    def process_turn(self, user_utterance: str) -> str:
        """Process a complete dialogue turn synchronously (convenience wrapper for non-streaming callers)."""
        prompt = self.prepare_turn(user_utterance)
        if not prompt or self.mock_mode or self.state_machine.current_state == IntakeState.DONE:
            raw_reply = self._mock_response_for_state()
        else:
            raw_reply = self._call_ollama_chat(prompt, stream=False)

        return self.finalize_turn(raw_reply)

    def get_full_transcript(self) -> str:
        """Return human-readable conversation transcript."""
        transcript_lines = []
        for turn in self.history:
            role = "Kent-AI" if turn["role"] == "assistant" else "Patient"
            transcript_lines.append(f"{role}: {turn['content']}")
        return "\n".join(transcript_lines)

    def get_patient_report(self) -> Optional[PatientReport]:
        return self.patient_report

    def reset(self) -> None:
        """Reset the conversation state for a new session."""
        self.state_machine = ConversationStateMachine()
        self.history = []
        for k in self.extracted_slots:
            self.extracted_slots[k] = []
        self.patient_report = None
        self.current_suggestions = []
        self.last_call_failed = False

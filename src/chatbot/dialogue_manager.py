"""Multi-turn dialogue manager orchestrating context history and slot filling (Phase 6).

Coordinates clinical intake across conversation turns, delegating extraction to
slot_extractor, HTTP calls to ollama_client, suggestions to suggestions,
and offline templates to fallbacks.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.chatbot.prompts import (
    CHATBOT_PRACTITIONER_SYSTEM_PROMPT,
    CHATBOT_PRACTITIONER_TURN_PROMPT,
    CHATBOT_SYSTEM_PROMPT,
    CHATBOT_TURN_PROMPT,
)
from src.chatbot.state_machine import ConversationStateMachine, IntakeState
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport, PipelineOrchestrator
from src.pipeline.safety import screen_red_flags

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
from src.chatbot.fallbacks import (
    PATIENT_GREETING,
    PRACTITIONER_GREETING,
    get_mock_response_for_state,
)
from src.chatbot.turn_history import (
    apply_undo_capture,
    apply_undo_last_turn,
    build_turn_prompt,
    seed_opener_for_case,
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
    "SAFETY_RESPONSE_TEXT",
]

# PENDING CLINICAL REVIEW BY SUPERVISOR
SAFETY_RESPONSE_TEXT = (
    "Thank you for telling me. Kent-AI is not an emergency or diagnostic service. "
    "If you or someone else may be in danger, please contact local emergency services "
    "or a trusted person right now. You can continue the intake afterwards."
)


class DialogueManager:
    """Orchestrates intake conversation turns, slot filling, and termination.

    Slot extraction uses a 3-tier pipeline. The tiers are independent — failure
    in any tier is silently logged and the next tier continues, ensuring robustness.
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

        self.history: List[Dict[str, Any]] = []
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
            self.resume_from_case(case)

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
                    c.chief_complaint = str(turn.get("content", ""))[:120]
                    break
        has_user_turns = any(turn.get("role") == "user" for turn in self.history)
        c.transcript = self.get_full_transcript() if has_user_turns else ""
        if not hasattr(c, "extraction_meta") or not isinstance(c.extraction_meta, dict):
            c.extraction_meta = {}
        c.extraction_meta["intake_mode"] = getattr(self, "intake_mode", "patient")
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

    def resume_from_case(self, case: ClinicalCase) -> None:
        """Resume or initialize consultation from an existing ClinicalCase.

        Hydrates slots, restores intake_mode, advances the state machine to the
        first unfilled gap (or REVIEW if complete), and seeds ONE deterministic
        assistant opener if history is empty (idempotent).
        """
        self.load_from_case(case)

        # Restore persisted intake mode
        if isinstance(case.extraction_meta, dict) and "intake_mode" in case.extraction_meta:
            self.intake_mode = str(case.extraction_meta["intake_mode"]).lower()

        # Advance state machine to first gap
        self.state_machine.advance_to_next_gap()

        # If history is empty, seed ONE deterministic assistant opener (no LLM call)
        if not self.history:
            opener, origin = seed_opener_for_case(
                case=case,
                intake_mode=self.intake_mode,
                mock_response_fn=self._mock_response_for_state,
            )
            self.history.append({"role": "assistant", "content": opener, "origin": origin})
            self.current_suggestions = self.generate_dynamic_suggestions(opener)

        # Persist mode into extraction_meta and sync
        if not hasattr(case, "extraction_meta") or not isinstance(case.extraction_meta, dict):
            case.extraction_meta = {}
        case.extraction_meta["intake_mode"] = self.intake_mode
        self.sync_to_case(case)

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
            self.history.append({"role": "assistant", "content": greeting, "origin": "scripted"})
            self.current_suggestions = self.generate_dynamic_suggestions(greeting)
        return greeting

    def set_intake_mode(self, mode: str) -> None:
        """Update intake mode ('patient' or 'practitioner') and update opening message if fresh."""
        new_mode = (mode or "patient").lower().strip()
        old_mode = getattr(self, "intake_mode", "patient")
        self.intake_mode = new_mode

        if len(self.history) == 1 and self.history[0].get("role") == "assistant":
            if self.history[0].get("content") in (PATIENT_GREETING, PRACTITIONER_GREETING) or old_mode != new_mode:
                new_greeting = PRACTITIONER_GREETING if new_mode == "practitioner" else PATIENT_GREETING
                self.history[0]["content"] = new_greeting
                self.history[0]["origin"] = "scripted"
                self.current_suggestions = self.generate_dynamic_suggestions(new_greeting)

        if self.case is not None and isinstance(self.case.extraction_meta, dict):
            self.case.extraction_meta["intake_mode"] = self.intake_mode

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

    def _mock_response_for_state(self) -> str:
        """Deterministic, clinically focused offline fallback responses per state."""
        return get_mock_response_for_state(
            state=self.state_machine.current_state,
            intake_mode=getattr(self, "intake_mode", "patient"),
            extracted_slots=self.extracted_slots,
        )

    # Sanitization & Parsing Methods
    @staticmethod
    def clean_message_text(text: str) -> str:
        return clean_message_text(text)

    def _parse_and_strip_quick_replies(self, text: str) -> Tuple[str, List[str]]:
        return parse_and_strip_quick_replies(text, intake_mode=getattr(self, "intake_mode", "patient"))

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
        """Return the current dynamic instant-reply suggestions for the active question."""
        if not self.current_suggestions and self.history:
            last_bot_msg = next((t["content"] for t in reversed(self.history) if t.get("role") == "assistant"), "")
            if last_bot_msg:
                self.current_suggestions = self.generate_dynamic_suggestions(last_bot_msg)
        return self.current_suggestions or get_state_fallback(self.state_machine.current_state)

    # Core Turn Processing
    def prepare_turn(self, user_utterance: str) -> str:
        """Run FSM transitions, history recording, and slot extraction with diff tracking.

        Returns the formatted turn prompt for LLM generation (or empty string if mock/done).
        """
        turn_id = f"turn_{len(self.history) + 1}"

        # 1. Non-blocking safety screening
        flags = screen_red_flags(user_utterance)
        if flags:
            self.history.append({
                "role": "assistant",
                "content": SAFETY_RESPONSE_TEXT,
                "origin": "safety",
            })
            if self.case is not None and isinstance(self.case.extraction_meta, dict):
                rf_list = self.case.extraction_meta.setdefault("red_flags", [])
                for fl in flags:
                    rf_list.append({"category": fl.category, "snippet": fl.snippet})

        # 2. Handle 'Skip'
        cleaned_input = user_utterance.strip().lower()
        if cleaned_input == "skip":
            self.state_machine.turn_count += 1
            self.state_machine.skip_current_slot()
            self.history.append({
                "role": "user",
                "content": "Skip",
                "turn_id": turn_id,
                "captured": {},
            })
            self.sync_to_case()
            return ""

        # 3. Handle 'None of these' / denial
        if cleaned_input in ("none of these", "none"):
            self.state_machine.turn_count += 1
            curr_state = self.state_machine.current_state
            dim_map = {
                IntakeState.LOCATION: "location",
                IntakeState.SENSATION: "sensation",
                IntakeState.MODALITY: "modality_agg",
                IntakeState.CONCOMITANT: "concomitant",
                IntakeState.TEMPORAL: "temporal",
                IntakeState.MENTAL: "mental",
            }
            dim_key = dim_map.get(curr_state)
            if dim_key:
                self.state_machine.denied_slots.add(dim_key)
                if self.case is not None and isinstance(self.case.extraction_meta, dict):
                    negated = self.case.extraction_meta.setdefault("negated", [])
                    if dim_key not in negated:
                        negated.append(dim_key)

            self.state_machine.skip_current_slot()
            self.history.append({
                "role": "user",
                "content": "None of these",
                "turn_id": turn_id,
                "captured": {},
            })
            self.sync_to_case()
            return ""

        # 4. Standard turn: extract slots and compute diff
        new_slots = self._extract_all_slots(user_utterance)
        captured_diff: Dict[str, List[str]] = {}
        for k, v in new_slots.items():
            new_items = []
            for item in v:
                if item not in self.extracted_slots.setdefault(k, []):
                    self.extracted_slots[k].append(item)
                    new_items.append(item)
            if new_items:
                captured_diff[k] = new_items

        self.history.append({
            "role": "user",
            "content": user_utterance,
            "turn_id": turn_id,
            "captured": captured_diff,
        })

        if self.case is not None and captured_diff and isinstance(self.case.extraction_meta, dict):
            meta_items = self.case.extraction_meta.setdefault("items", {})
            for dim_k, items_list in captured_diff.items():
                dim_meta = meta_items.setdefault(dim_k, [])
                for it in items_list:
                    dim_meta.append({
                        "text": it,
                        "confidence": 1.0,
                        "start": None,
                        "end": None,
                        "origin": "chat",
                    })

        # Advance state machine
        self.state_machine.next_state(user_utterance, extracted_slots=new_slots)
        self.sync_to_case()

        current_state = self.state_machine.current_state
        if self.mock_mode or current_state == IntakeState.DONE:
            return ""

        # Build turn prompt for LLaMA 3
        return build_turn_prompt(
            state_machine=self.state_machine,
            extracted_slots=self.extracted_slots,
            history=self.history,
            user_utterance=user_utterance,
            intake_mode=getattr(self, "intake_mode", "patient"),
        )

    def finalize_turn(self, raw_reply: str) -> str:
        """Sanitize reply, record provenance, update suggestions, and omit heavy processing."""
        current_state = self.state_machine.current_state

        if current_state == IntakeState.DONE:
            clean_reply = self._mock_response_for_state()
            self.history.append({"role": "assistant", "content": clean_reply, "origin": "scripted"})
            self.current_suggestions = ["Everything looks accurate", "I'd like to check my answers", "No other symptoms"]
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
        origin = "llm"
        if not clean_text or self.mock_mode or getattr(self, "last_call_failed", False):
            clean_text = self._mock_response_for_state()
            origin = "scripted"

        self.history.append({"role": "assistant", "content": clean_text, "origin": origin})

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

    def undo_capture(self, turn_id: str, dim_key: str, item: str) -> None:
        """Remove a specific extracted symptom token from turn history, slot registry, and case."""
        apply_undo_capture(
            history=self.history,
            extracted_slots=self.extracted_slots,
            filled_slots=self.state_machine.filled_slots,
            case=self.case,
            turn_id=turn_id,
            dim_key=dim_key,
            item=item,
        )
        self.sync_to_case()

    def undo_last_turn(self) -> None:
        """Pop the last assistant + user turn pair and revert all tokens captured in that turn."""
        apply_undo_last_turn(
            history=self.history,
            extracted_slots=self.extracted_slots,
            filled_slots=self.state_machine.filled_slots,
            case=self.case,
        )
        self.state_machine.advance_to_next_gap()
        self.sync_to_case()
        if self.history:
            last_bot = next((t["content"] for t in reversed(self.history) if t.get("role") == "assistant"), "")
            self.current_suggestions = self.generate_dynamic_suggestions(last_bot)

    def get_action_options(self) -> List[Dict[str, str]]:
        """Return typed terminal action options for the DONE state."""
        return [
            {"id": "continue_review", "label": "Continue to Review →", "type": "primary"},
            {"id": "add_detail", "label": "Add Another Detail", "type": "secondary"},
            {"id": "start_new", "label": "Start New Consultation", "type": "secondary"},
        ]

    def get_full_transcript(self) -> str:
        """Return human-readable conversation transcript."""
        transcript_lines = []
        for turn in self.history:
            role = "Kent-AI" if turn.get("role") == "assistant" else "Patient"
            transcript_lines.append(f"{role}: {turn.get('content', '')}")
        return "\n".join(transcript_lines)

    def get_patient_report(self) -> Optional[PatientReport]:
        """Lazily compute patient report if requested and orchestrator is present."""
        if self.patient_report is None and self.orchestrator is not None:
            self.patient_report = self.orchestrator.process_transcript(
                self.get_full_transcript(),
                patient_id="PT-INTAKE",
            )
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

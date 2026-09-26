"""Multi-turn dialogue manager orchestrating context history and slot filling (Phase 6).

Implements a warm, empathetic clinical consultation partner backed by LLaMA 3
(via local Ollama) or deterministic friendly templates in mock mode.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from src.chatbot.prompts import CHATBOT_SYSTEM_PROMPT, CHATBOT_TURN_PROMPT
from src.chatbot.state_machine import ConversationStateMachine, IntakeState
from src.config import get_chatbot_config
from src.pipeline.orchestrator import PatientReport, PipelineOrchestrator

logger = logging.getLogger("dialogue_manager")


class DialogueManager:
    """Orchestrates intake conversation turns, slot filling, and termination."""

    def __init__(
        self,
        state_machine: Optional[ConversationStateMachine] = None,
        orchestrator: Optional[PipelineOrchestrator] = None,
        model_name: Optional[str] = None,
        api_base: Optional[str] = None,
        mock_mode: bool = False,
    ) -> None:
        cfg = get_chatbot_config().get("chatbot", {})
        self.state_machine = state_machine or ConversationStateMachine()
        self.orchestrator = orchestrator
        self.model_name = model_name or cfg.get("model", "llama3:8b")
        self.api_base = api_base or cfg.get("api_base", "http://localhost:11434")
        self.temperature = float(cfg.get("temperature", 0.5))
        self.mock_mode = mock_mode

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

    def get_greeting(self) -> str:
        """Provide a warm, welcoming initial opening message."""
        greeting = (
            "Hello! I'm Kent-AI, your clinical intake companion. I'm here to listen and help "
            "gather details about how you're feeling so we can find the best homeopathic match. "
            "How are you doing today, and what's been bothering you most?"
        )
        if not self.history:
            self.history.append({"role": "assistant", "content": greeting})
        return greeting

    def _extract_slots_heuristic(self, text: str) -> Dict[str, List[str]]:
        """Fast regex heuristic slot extractor to detect patient dimensions."""
        found: Dict[str, List[str]] = {}
        t_low = text.lower()

        # Anatomical locations
        locations = [
            "head", "forehead", "temple", "temples", "vertex", "occiput", "eyes", "eye",
            "throat", "chest", "heart", "stomach", "abdomen", "back", "neck", "joints",
            "knee", "knees", "limbs", "hands", "feet", "ears", "nose"
        ]
        for loc in locations:
            if re.search(r"\b" + re.escape(loc) + r"\b", t_low):
                found.setdefault("location", []).append(loc)

        # Sensation qualities
        sensations = [
            "throbbing", "pounding", "splitting", "burning", "stitching", "dull", "sharp",
            "heavy", "pressure", "cramping", "aching", "shooting", "bursting", "sore"
        ]
        for sen in sensations:
            if re.search(r"\b" + re.escape(sen) + r"\b", t_low):
                found.setdefault("sensation", []).append(sen)

        # Modalities (Aggravations)
        aggs = [
            "sun", "sunlight", "warm room", "heat", "cold", "cold air", "motion", "moving",
            "noise", "light", "touch", "eating", "after eating", "night", "morning"
        ]
        if "worse" in t_low or "aggravat" in t_low:
            for agg in aggs:
                if agg in t_low:
                    found.setdefault("modality_agg", []).append(agg)

        # Modalities (Ameliorations)
        amels = [
            "rest", "lying down", "dark room", "sleep", "pressure", "cold compress",
            "warm compress", "fresh air", "open air", "walking"
        ]
        if "better" in t_low or "reliev" in t_low or "help" in t_low:
            for amel in amels:
                if amel in t_low:
                    found.setdefault("modality_amel", []).append(amel)

        # Temporals
        temporals = [
            "morning", "waking", "afternoon", "evening", "night", "midnight", "twilight",
            "3 am", "3 pm", "winter", "summer", "periodically"
        ]
        for temp in temporals:
            if re.search(r"\b" + re.escape(temp) + r"\b", t_low):
                found.setdefault("temporal", []).append(temp)

        # Mental / Emotional
        mentals = [
            "anxious", "anxiety", "depressed", "depression", "sad", "weeping", "crying",
            "irritable", "irritability", "angry", "restless", "fear", "alone", "worried"
        ]
        for ment in mentals:
            if re.search(r"\b" + re.escape(ment) + r"\b", t_low):
                found.setdefault("mental", []).append(ment)

        # Concomitants
        concs = [
            "nausea", "vomiting", "dizziness", "vertigo", "chills", "fever", "sweating",
            "trembling", "blur"
        ]
        for conc in concs:
            if re.search(r"\b" + re.escape(conc) + r"\b", t_low):
                found.setdefault("concomitant", []).append(conc)

        return found

    def _call_ollama_chat(self, user_prompt: str) -> str:
        """Call Ollama /api/chat with full conversational context."""
        url = f"{self.api_base}/api/chat"

        messages = [{"role": "system", "content": CHATBOT_SYSTEM_PROMPT}]
        for turn in self.history[-6:]:  # Keep recent history
            messages.append(turn)
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "num_predict": 256,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("message", {}).get("content", "").strip()
        except urllib.error.URLError as err:
            logger.warning("Ollama unreachable for chat (%s). Using fallback template.", err)
            return self._mock_response_for_state()

    def _mock_response_for_state(self) -> str:
        """Friendly deterministic response generator for offline testing."""
        state = self.state_machine.current_state

        templates = {
            IntakeState.CHIEF_COMPLAINT: "I'm really sorry you're feeling unwell. Could you tell me a little more about what's been troubling you most?",
            IntakeState.LOCATION: "I hear you, and that sounds uncomfortable. Whereabouts in your body does this feel most intense?",
            IntakeState.SENSATION: "Thank you for sharing that. How would you describe the feeling—is it more of a throbbing, burning, heavy, or sharp ache?",
            IntakeState.MODALITY: "That helps me picture it. Have you noticed anything that makes it worse, like movement or noise, or anything that brings relief?",
            IntakeState.CONCOMITANT: "I'm noting that down. Does anything else happen alongside this, such as nausea, dizziness, or chills?",
            IntakeState.MENTAL: "Dealing with this must be draining. How has this been affecting your mood, stress, or peace of mind lately?",
            IntakeState.REVIEW: "Thank you for sharing all of this with me. Let me make sure I've got it right—does this summary sound accurate to you?",
            IntakeState.CLARIFICATION: "Thank you for clarifying! I've noted that adjustment. Does everything feel complete now?",
            IntakeState.DONE: "Thank you so much. I have all the details needed, and your homeopathic repertory analysis is now complete!",
        }
        return templates.get(state, "I understand. Please tell me more about that.")

    def process_turn(self, user_utterance: str) -> str:
        """Process one conversational turn from the patient.
        
        Args:
            user_utterance: Patient's message.
            
        Returns:
            Friendly response message from Kent-AI.
        """
        # 1. Record patient utterance
        self.history.append({"role": "user", "content": user_utterance})

        # 2. Extract clinical slots
        new_slots = self._extract_slots_heuristic(user_utterance)
        for slot_k, vals in new_slots.items():
            for v in vals:
                if v not in self.extracted_slots.get(slot_k, []):
                    self.extracted_slots.setdefault(slot_k, []).append(v)

        # 3. Transition FSM
        self.state_machine.next_state(user_utterance, extracted_slots=new_slots)
        current_state = self.state_machine.current_state
        goal_desc = self.state_machine.get_current_goal_description()

        # 4. Generate bot response
        if self.mock_mode:
            bot_reply = self._mock_response_for_state()
        else:
            slots_summary = "\n".join(
                f"- {k.capitalize()}: {', '.join(v)}"
                for k, v in self.extracted_slots.items()
                if v
            ) or "- None yet."

            recent_history = "\n".join(
                f"{turn['role'].capitalize()}: {turn['content']}"
                for turn in self.history[-4:]
            )

            turn_prompt = CHATBOT_TURN_PROMPT.format(
                current_goal=goal_desc,
                slots_summary=slots_summary,
                history=recent_history,
                user_utterance=user_utterance,
            )

            bot_reply = self._call_ollama_chat(turn_prompt)
            if not bot_reply:
                bot_reply = self._mock_response_for_state()

        # 5. Record bot response
        self.history.append({"role": "assistant", "content": bot_reply})

        # 6. Handover to pipeline if consultation is DONE
        if current_state == IntakeState.DONE and self.orchestrator:
            try:
                transcript = self.get_full_transcript()
                self.patient_report = self.orchestrator.process_transcript(transcript)
            except Exception as e:
                logger.error("Error executing handover to pipeline orchestrator: %s", e)

        return bot_reply

    def get_full_transcript(self) -> str:
        """Compile complete multi-turn dialogue into a coherent clinical narrative."""
        patient_utterances = [
            turn["content"] for turn in self.history if turn["role"] == "user"
        ]
        return " ".join(patient_utterances)

    def get_patient_report(self) -> Optional[PatientReport]:
        """Retrieve the final repertorization report if intake is complete."""
        return self.patient_report

    def reset(self) -> None:
        """Reset conversation state for a new consultation."""
        self.state_machine = ConversationStateMachine()
        self.history.clear()
        self.extracted_slots = {k: [] for k in self.extracted_slots}
        self.patient_report = None

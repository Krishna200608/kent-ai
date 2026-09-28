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
        self.current_suggestions: List[str] = []

    @property
    def detected_dimensions(self) -> Dict[str, bool]:
        """Read-only mapping of which of the 7 Kent dimensions are detected."""
        sm_dims = self.state_machine.detected_dimensions
        return {
            k: sm_dims.get(k, False) or bool(self.extracted_slots.get(k))
            for k in [
                "location", "sensation", "modality_agg", "modality_amel",
                "concomitant", "temporal", "mental"
            ]
        }

    def get_greeting(self) -> str:
        """Provide a concrete, welcoming initial opening message detailing what will be asked."""
        greeting = (
            "Hello! I'm Kent-AI, your clinical intake companion. We will examine your "
            "main complaint, including location, sensations, triggers, relief factors, "
            "and emotional state to guide classical repertorization. What primary symptoms have been troubling you most?"
        )
        if not self.history:
            self.history.append({"role": "assistant", "content": greeting})
            self.current_suggestions = self.generate_dynamic_suggestions(greeting)
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

    def is_ollama_online(self) -> bool:
        """Check if local Ollama daemon is currently running and responding."""
        try:
            url = f"{self.api_base}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _mock_response_for_state(self) -> str:
        """Friendly deterministic response generator for offline fallback testing."""
        state = self.state_machine.current_state

        if state == IntakeState.REVIEW:
            summary_lines = []
            for k, v in self.extracted_slots.items():
                if v:
                    dim_title = k.replace("_", " ").title()
                    summary_lines.append(f"• **{dim_title}**: {', '.join(v)}")
            summary_block = "\n".join(summary_lines) if summary_lines else "• Primary complaint noted."
            return (
                "Thank you for sharing all of this with me. Let me make sure I've got your case right:\n\n"
                f"{summary_block}\n\n"
                "Does this summary sound accurate, or would you like to add or adjust any details?"
            )

        if state == IntakeState.CLARIFICATION:
            return "Please go ahead and describe the additional symptom, sensation, or detail you'd like to add."

        templates = {
            IntakeState.CHIEF_COMPLAINT: "I'm really sorry you're feeling unwell. Could you tell me a little more about what's been troubling you most?",
            IntakeState.LOCATION: "I hear you, and that sounds uncomfortable. Whereabouts in your body does this feel most intense?",
            IntakeState.SENSATION: "Thank you for sharing that. How would you describe the feeling—is it more of a throbbing, burning, heavy, or sharp ache?",
            IntakeState.MODALITY: "That helps me picture it. Have you noticed anything that makes it worse, like movement or noise, or anything that brings relief?",
            IntakeState.CONCOMITANT: "I'm noting that down. Does anything else happen alongside this, such as nausea, dizziness, or chills?",
            IntakeState.MENTAL: "Dealing with this must be draining. How has this been affecting your mood, stress, or peace of mind lately?",
            IntakeState.DONE: "Thank you so much. I have all the details needed, and your homeopathic repertory analysis is now complete!",
        }
        return templates.get(state, "I understand. Please tell me more about that.")

    def _parse_and_strip_quick_replies(self, text: str) -> tuple[str, List[str]]:
        """Extract QUICK_REPLIES JSON from model output and return clean response and options."""
        if not text:
            return "", []

        pattern = r"QUICK_REPLIES:\s*(\[.*?\])"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            raw_replies = match.group(1).strip()
            clean_text = text[:match.start()].strip()
            try:
                parsed = json.loads(raw_replies)
                if isinstance(parsed, list) and len(parsed) > 0:
                    clean_options = [str(opt).strip(' "\'') for opt in parsed if str(opt).strip()]
                    return clean_text, clean_options[:4]
            except Exception:
                quoted = re.findall(r'["\']([^"\']+)["\']', raw_replies)
                if quoted:
                    return clean_text, quoted[:4]
            return clean_text, []
        return text.strip(), []

    def generate_dynamic_suggestions(self, bot_message: str) -> List[str]:
        """Dynamically generate 3-4 natural first-person instant answers to the current question."""
        text = (bot_message or "").lower()
        slots = self.extracted_slots

        # 1. Opening / Chief Complaint (Highest Priority on Initial Turns - MIND Focus)
        if any(p in text for p in ["how are you", "bothering you", "troubling you", "bring you in", "bothers you most", "what brings", "primary symptoms"]):
            return [
                "Severe anxiety & fearful apprehension",
                "Emotional pain & sadness, worse alone",
                "Restless pacing & irritability",
                "Absent-mindedness & memory lapses",
            ]

        # 2. Concomitants / Other Associated Symptoms (Checked before review because of 'anything else')
        if any(w in text for w in ["alongside", "other symptom", "at the same time", "also notice", "nausea, dizziness"]):
            return [
                "Accompanied by nausea",
                "Dizziness and lightheadedness",
                "Chills and cold sweat",
                "No other physical symptoms",
            ]

        # 3. Location / Anatomy Inquiry
        if any(w in text for w in ["where", "location", "part of your", "which side", "whereabouts", "where in"]):
            known_locs = " ".join(slots.get("location", [])).lower()
            if "head" in known_locs or "head" in text or "migraine" in text or "temple" in text:
                return [
                    "Forehead and temples",
                    "Top of head (vertex)",
                    "Back of head (occiput)",
                    "Behind my eyes",
                ]
            elif "stomach" in known_locs or "abdomen" in known_locs or "stomach" in text or "nausea" in text:
                return [
                    "Pit of stomach (epigastrium)",
                    "Lower abdomen & cramping",
                    "All across my stomach",
                    "Around my navel area",
                ]
            elif "chest" in known_locs or "chest" in text or "heart" in text or "breath" in text:
                return [
                    "Center of my chest",
                    "Left side around heart",
                    "Upper chest and lungs",
                    "Tightness across my ribs",
                ]
            elif "throat" in known_locs or "throat" in text:
                return [
                    "Right side of throat",
                    "Left side and tonsils",
                    "Deep down in the throat",
                    "Larynx and voice box",
                ]
            elif "back" in known_locs or "back" in text or "spine" in text or "lumbar" in text:
                return [
                    "Lower lumbar area",
                    "Upper back between shoulders",
                    "Along the entire spine",
                    "Sacrum and tailbone",
                ]
            elif "joint" in known_locs or "knee" in known_locs or "joint" in text or "limb" in text:
                return [
                    "Knees and ankles",
                    "Hands and wrists",
                    "Shoulders and elbows",
                    "Small finger joints",
                ]
            else:
                return [
                    "In my head and temples",
                    "In my stomach and abdomen",
                    "In my chest and throat",
                    "In my lower back and joints",
                ]

        # 4. Sensation / Character of Pain Inquiry
        if any(w in text for w in ["sensation", "feel like", "kind of pain", "type of", "throbbing", "burning", "stabbing", "describe the"]):
            return [
                "Pulsating, throbbing beat",
                "Sharp, stabbing pain",
                "Dull, heavy aching pressure",
                "Burning like hot embers",
            ]

        # 5. Modality (Aggravation / Amelioration / Worse / Better)
        if any(w in text for w in ["makes it worse", "make it worse", "aggravat", "flare", "trigger", "worse from", "bring relief", "brings relief", "comfort", "soothe", "better from", "relieved by"]):
            return [
                "Worse in heat & bright sun",
                "Worse from motion or walking",
                "Better with cold compresses",
                "Better resting in a dark room",
            ]

        # 6. Temporal / Time of Day
        if any(w in text for w in ["what time", "time of day", "when does", "morning or night", "waking up", "periodicity", "hour", "clock"]):
            return [
                "Worse in morning on waking",
                "Worse in afternoon (around 3-4 PM)",
                "Worse in evening & night",
                "Worse after midnight (2-3 AM)",
            ]

        # 7. Mental / Emotional State / Mood
        if any(w in text for w in ["mood", "stress", "emotion", "feeling mentally", "anxious", "mind", "irritab", "peace of mind"]):
            return [
                "Restless, anxious, and uneasy",
                "Irritable and easily angered",
                "Depressed, tired, and quiet",
                "My mood is relatively calm",
            ]

        # 8. Review / Summary Confirmation
        if any(w in text for w in ["accurate", "summarize", "anything else", "sound right", "add anything", "confirm", "covers it", "got it right"]):
            return [
                "Yes, that covers all my symptoms!",
                "I also want to add another detail",
                "Please proceed to repertorization",
            ]

        # Adaptive state-based fallback
        state_fallback = {
            IntakeState.GREETING: ["Severe recurring headache", "Stomach pain and burning", "Severe anxiety and fatigue"],
            IntakeState.CHIEF_COMPLAINT: ["Headache in temples", "Stomach ache after food", "Anxious and sleepless"],
            IntakeState.LOCATION: ["Forehead and temples", "Stomach & abdomen", "Chest and throat", "Lower back & joints"],
            IntakeState.SENSATION: ["Throbbing and pulsating", "Sharp stabbing pain", "Dull heavy ache", "Burning sensation"],
            IntakeState.MODALITY: ["Worse in heat and sun", "Worse from motion", "Better with cold compress", "Better in quiet dark"],
            IntakeState.CONCOMITANT: ["Nausea and dizziness", "Chills and perspiration", "Extreme fatigue", "No other symptoms"],
            IntakeState.MENTAL: ["Restless and anxious", "Irritable and frustrated", "Down and tearful", "Calm and peaceful"],
            IntakeState.REVIEW: ["Yes, that covers all my symptoms!", "I want to add another symptom", "Please proceed to repertorization"],
        }
        return state_fallback.get(self.state_machine.current_state, [
            "Yes, exactly like that",
            "Not quite, let me explain",
            "Please analyze my remedies now",
        ])

    def get_current_suggestions(self) -> List[str]:
        """Return the current dynamic instant answer suggestions for the patient."""
        if not self.current_suggestions and self.history:
            last_bot_msg = self.history[-1]["content"] if self.history[-1]["role"] == "assistant" else ""
            if last_bot_msg:
                self.current_suggestions = self.generate_dynamic_suggestions(last_bot_msg)
        return self.current_suggestions or self.generate_dynamic_suggestions(
            self.history[-1]["content"] if self.history else ""
        )

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
            raw_reply = self._mock_response_for_state()
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

            raw_reply = self._call_ollama_chat(turn_prompt)
            if not raw_reply:
                raw_reply = self._mock_response_for_state()

        # 5. Extract dynamic quick replies and clean the text
        clean_reply, quick_replies = self._parse_and_strip_quick_replies(raw_reply)
        if not quick_replies:
            quick_replies = self.generate_dynamic_suggestions(clean_reply)
        self.current_suggestions = quick_replies

        # 6. Record clean bot response
        self.history.append({"role": "assistant", "content": clean_reply})

        # 7. Handover to pipeline if consultation is DONE
        if current_state == IntakeState.DONE and self.orchestrator:
            try:
                transcript = self.get_full_transcript()
                self.patient_report = self.orchestrator.process_transcript(transcript)
            except Exception as e:
                logger.error("Error executing handover to pipeline orchestrator: %s", e)

        return clean_reply

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
        self.current_suggestions = []


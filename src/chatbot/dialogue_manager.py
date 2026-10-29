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
        self.api_base = api_base or cfg.get("api_base", "http://127.0.0.1:11434")
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
        """Fast, robust clinical slot extractor covering Kent's 7 dimensions."""
        found: Dict[str, List[str]] = {}
        t_low = text.lower().strip()
        if not t_low:
            return found

        # 1. Anatomical locations
        locations = [
            "stomach", "abdomen", "belly", "gut", "tummy", "epigastrium",
            "head", "forehead", "temple", "temples", "vertex", "occiput",
            "eyes", "eye", "ears", "ear", "nose", "throat", "pharynx",
            "chest", "heart", "lungs", "back", "spine", "neck", "lumbar",
            "joints", "knee", "knees", "limbs", "hands", "hand", "feet", "foot",
            "pelvis", "bladder", "kidneys", "skin", "shoulder", "shoulders"
        ]
        for loc in locations:
            if re.search(r"\b" + re.escape(loc) + r"\b", t_low):
                found.setdefault("location", []).append(loc)

        # 2. Sensation qualities
        sensations = [
            "heavy", "heaviness", "tight", "tightness", "constriction", "constricted",
            "throbbing", "pounding", "splitting", "pulsating", "burning", "heat",
            "stitching", "sharp", "stabbing", "piercing", "dull", "aching", "ache",
            "sore", "soreness", "cramping", "cramp", "shooting", "bursting", "pressure",
            "fullness", "numb", "numbness", "tingling", "fluttering", "flutter"
        ]
        for sen in sensations:
            if re.search(r"\b" + re.escape(sen) + r"\b", t_low):
                found.setdefault("sensation", []).append(sen)

        # 3. Modalities (Aggravations)
        aggs = [
            "movement", "moving", "motion", "move", "exercise", "exercising", "exertion",
            "walking", "running", "stairs", "bending", "standing", "sitting", "lying",
            "noise", "sound", "loud", "light", "sun", "sunlight", "heat", "warm room",
            "cold", "cold air", "draft", "wind", "weather", "storm", "damp", "touch",
            "pressure", "eating", "after eating", "food", "coffee", "night", "morning",
            "stress", "crowds"
        ]
        is_agg = any(
            re.search(p, t_low) for p in [
                r"\bworse\b", r"\baggravat\w*", r"\btrigger\w*",
                r"\bamplif\w*", r"\bintensif\w*", r"\bworsen\w*",
                r"makes?\s+it\s+worse"
            ]
        )
        for agg in aggs:
            if re.search(r"\b" + re.escape(agg) + r"\b", t_low):
                if is_agg or (hasattr(self, "state_machine") and self.state_machine.current_state == IntakeState.MODALITY):
                    if not any(rel in t_low for rel in ["soothe", "better", "relief", "reliev", "ease", "calm", "help"]):
                        found.setdefault("modality_agg", []).append(agg)

        m_x_worse = re.search(r"([a-zA-Z\s]{2,25})\s+(?:makes?\s+it\s+worse|aggravates?|triggers?|worsens?|amplifies?)", t_low)
        if m_x_worse:
            phrase = re.sub(r"^(?:that|this|it|which|and|but|also)\s+", "", m_x_worse.group(1).strip())
            if phrase and phrase not in found.get("modality_agg", []):
                found.setdefault("modality_agg", []).append(phrase)

        # 4. Modalities (Ameliorations)
        amels = [
            "warmth", "warm", "warm compress", "warm drinks", "sunny spot", "sunshine", "sun",
            "rest", "resting", "lying down", "sleep", "sleeping", "dark room", "darkness",
            "quiet", "solitude", "peaceful", "peace", "pressure", "cold compress", "fresh air",
            "open air", "walking slowly", "gentle motion", "massage"
        ]
        is_amel = any(
            re.search(p, t_low) for p in [
                r"\bbetter\b", r"\brelie\w*", r"\bsooth\w*", r"\beas\w*",
                r"\bimprov\w*", r"\bhelp\w*", r"\bcalm\w*", r"\bcomfort\w*",
                r"makes?\s+it\s+better", r"brings?\s+relief"
            ]
        )
        for amel in amels:
            if re.search(r"\b" + re.escape(amel) + r"\b", t_low):
                if is_amel or (hasattr(self, "state_machine") and self.state_machine.current_state == IntakeState.MODALITY and is_amel):
                    found.setdefault("modality_amel", []).append(amel)

        m_x_better = re.search(r"([a-zA-Z\s]{2,25})\s+(?:makes?\s+it\s+better|soothes?|relieves?|helps?|eases?|calms?)", t_low)
        if m_x_better:
            phrase = re.sub(r"^(?:that|this|it|which|and|but|also)\s+", "", m_x_better.group(1).strip())
            if phrase and phrase not in found.get("modality_amel", []):
                found.setdefault("modality_amel", []).append(phrase)

        # 5. Concomitants
        concs = [
            "dizzy", "dizziness", "dizzy spells", "vertigo", "giddy", "giddiness",
            "nausea", "nauseous", "nauseated", "vomiting", "vomit", "queasy",
            "chills", "fever", "sweating", "sweat", "cold sweat", "perspiration",
            "trembling", "tremor", "palpitations", "faint", "fainting", "faintness",
            "blur", "blurred vision", "headache", "weakness", "exhaustion", "thirst",
            "dry mouth", "insomnia", "sleeplessness"
        ]
        for conc in concs:
            if re.search(r"\b" + re.escape(conc) + r"\b", t_low):
                found.setdefault("concomitant", []).append(conc)

        # 6. Temporals
        temporals = [
            "morning", "waking", "after waking", "forenoon", "noon", "midday",
            "afternoon", "evening", "night", "midnight", "twilight", "bedtime",
            "3 am", "3 pm", "winter", "summer", "periodically", "periodic",
            "consistent", "constant", "continuous", "daily", "all day", "spells", "attacks"
        ]
        for temp in temporals:
            if re.search(r"\b" + re.escape(temp) + r"\b", t_low):
                found.setdefault("temporal", []).append(temp)

        # 7. Mental / Emotional
        mentals = [
            "anxious", "anxiety", "fear", "fearful", "apprehension", "apprehensive",
            "panic", "distress", "worry", "worried", "restless", "restlessness", "pacing",
            "irritable", "irritability", "angry", "anger", "rage", "sad", "sadness",
            "depressed", "depression", "grief", "weeping", "crying", "alone", "solitude",
            "absent-minded", "confusion", "memory loss"
        ]
        for ment in mentals:
            if re.search(r"\b" + re.escape(ment) + r"\b", t_low):
                found.setdefault("mental", []).append(ment)

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

        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("message", {}).get("content", "").strip()
        except urllib.error.URLError as err:
            logger.warning("Ollama unreachable for chat (%s). Using fallback template.", err)
            return self._mock_response_for_state()

    def is_ollama_online(self) -> bool:
        """Check if local Ollama daemon is currently running and responding.
        
        Attempts connection on 127.0.0.1 (IPv4) first to bypass Windows IPv6 resolution latency.
        Uses empty proxy handler to avoid intercepting loopback requests.
        """
        candidates = ["http://127.0.0.1:11434", self.api_base, "http://localhost:11434"]
        seen = set()
        unique_candidates = [c for c in candidates if c and not (c in seen or seen.add(c))]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for base in unique_candidates:
            try:
                url = f"{base.rstrip('/')}/api/tags"
                req = urllib.request.Request(url, method="GET")
                with opener.open(req, timeout=1.5) as resp:
                    if resp.status == 200:
                        self.api_base = base
                        return True
            except Exception:
                continue
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

        # 2. Extract clinical slots via robust regex heuristic
        new_slots = self._extract_slots_heuristic(user_utterance)

        # Also extract via fine-tuned Bio_ClinicalBERT if orchestrator NER is available
        if self.orchestrator and getattr(self.orchestrator, "ner", None):
            try:
                ner_ents = self.orchestrator.ner.extract_entities(user_utterance)
                lbl_map = {
                    "LOC": "location",
                    "SEN": "sensation",
                    "MOD_AGG": "modality_agg",
                    "MOD_AMEL": "modality_amel",
                    "CONC": "concomitant",
                    "TEMP": "temporal",
                    "MENT": "mental",
                }
                for ent in ner_ents:
                    k = lbl_map.get(ent.get("label", "").upper())
                    txt = ent.get("text", "").strip()
                    if k and txt:
                        new_slots.setdefault(k, []).append(txt)
            except Exception as err:
                logger.debug("Live NER extraction skipped: %s", err)

        # Deduplicate and register into extracted_slots
        for slot_k, vals in new_slots.items():
            for v in vals:
                v_clean = v.strip().lower()
                existing = [x.lower() for x in self.extracted_slots.get(slot_k, [])]
                if v_clean and v_clean not in existing:
                    self.extracted_slots.setdefault(slot_k, []).append(v_clean)

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


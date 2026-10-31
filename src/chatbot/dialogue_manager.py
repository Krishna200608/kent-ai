"""Multi-turn dialogue manager orchestrating context history and slot filling (Phase 6).

Architecture — 3-Tier Clinical Slot Extraction Pipeline:
    Tier 1 (fast, <1ms):   YAML-backed regex heuristic (configs/extraction_vocabulary.yaml)
    Tier 2 (primary, ~0.5-1.5s): Fine-tuned Bio_ClinicalBERT NER (when weights available)
    Tier 3 (LLM, ~2-4s):  LLaMA 3 structured JSON slot extraction as verification/enrichment layer

Each tier enriches the slot set; later tiers override or supplement earlier ones.
The heuristic is a fast safety net — ClinicalBERT is the preferred primary extractor.
LLaMA structured extraction is used when the utterance is substantive enough to justify the latency.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from src.chatbot.prompts import (
    CHATBOT_PRACTITIONER_SYSTEM_PROMPT,
    CHATBOT_SYSTEM_PROMPT,
    CHATBOT_TURN_PROMPT,
)
from src.chatbot.state_machine import ConversationStateMachine, IntakeState
from src.models.case import ClinicalCase

try:
    from src.config import get_chatbot_config, get_extraction_vocabulary
except ImportError:
    import importlib
    import src.config as _config_mod
    importlib.reload(_config_mod)
    try:
        from src.config import get_chatbot_config, get_extraction_vocabulary
    except ImportError:
        from src.config import get_chatbot_config, load_config

        def get_extraction_vocabulary(filepath: Optional[str] = None) -> Dict[str, Any]:
            return load_config("extraction_vocabulary.yaml")

from src.pipeline.orchestrator import PatientReport, PipelineOrchestrator

logger = logging.getLogger("dialogue_manager")

# Minimum word count in a patient utterance to justify ClinicalBERT inference.
# Single-word or very short replies ("yes", "no", "3am") skip the model for speed.
_MIN_WORDS_FOR_BERT = 2

# Minimum word count in a patient utterance to justify LLaMA slot extraction call.
_MIN_WORDS_FOR_LLM_EXTRACTION = 4


@lru_cache(maxsize=1)
def _load_vocab() -> Dict[str, Any]:
    """Load extraction vocabulary from YAML (cached for the process lifetime).

    Falls back to an empty dict if the file is missing so the heuristic gracefully
    degrades to the ClinicalBERT and LLaMA tiers instead of crashing.
    """
    try:
        data = get_extraction_vocabulary()
        return data.get("dimensions", {})
    except FileNotFoundError:
        logger.warning(
            "extraction_vocabulary.yaml not found. Heuristic extractor will produce no results. "
            "ClinicalBERT and LLaMA tiers remain active."
        )
        return {}


@lru_cache(maxsize=1)
def _load_llm_extraction_config() -> Dict[str, Any]:
    """Load LLM slot extraction config from YAML (cached)."""
    try:
        data = get_extraction_vocabulary()
        return data.get("llm_extraction", {})
    except FileNotFoundError:
        return {}


@lru_cache(maxsize=1)
def _load_generate_button_config() -> Dict[str, Any]:
    """Load generate button unlock config from YAML (cached)."""
    try:
        data = get_extraction_vocabulary()
        return data.get("generate_button", {})
    except FileNotFoundError:
        return {}


def get_min_dimensions_to_unlock() -> int:
    """Return the minimum Kent dimensions required to unlock 'Generate Repertorization'.

    Configured in configs/extraction_vocabulary.yaml → generate_button.min_dimensions_to_unlock.
    Defaults to 1 so the button unlocks as soon as any complaint is captured.
    """
    return int(_load_generate_button_config().get("min_dimensions_to_unlock", 1))


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
        self.case = c
        c.dimensions = self.sanitize_extracted_slots(self.extracted_slots)
        c.transcript = self.get_full_transcript()
        c.dialogue_history = list(self.history)
        if self.patient_report:
            c.report_data = self.patient_report.to_dict()
        return c

    def load_from_case(self, source_case: ClinicalCase) -> None:
        """Load dialogue manager state and slots from a ClinicalCase."""
        self.case = source_case
        self.extracted_slots = self.sanitize_extracted_slots(source_case.dimensions)
        self.history = list(source_case.dialogue_history)
        for dim_k, vals in self.extracted_slots.items():
            if vals:
                self.state_machine.filled_slots.add(dim_k.lower())

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
        """Provide a welcoming initial opening message detailing what will be assessed."""
        greeting = (
            "Hello! I'm Kent-AI, your clinical intake companion. We will examine your "
            "main complaint, including location, sensations, triggers, relief factors, "
            "and emotional state to guide classical repertorization. What primary symptoms have been troubling you most?"
        )
        if not self.history:
            self.history.append({"role": "assistant", "content": greeting})
            self.current_suggestions = self.generate_dynamic_suggestions(greeting)
        return greeting

    # =========================================================================
    # TIER 1: YAML-backed Heuristic Extractor
    # =========================================================================

    def _extract_slots_heuristic(self, text: str) -> Dict[str, List[str]]:
        """Tier 1 — Fast YAML-vocabulary regex extractor covering Kent's 7 dimensions.

        Why regex + YAML instead of pure ML here:
        - Sub-millisecond latency ensures UI responsiveness on every turn.
        - YAML vocabulary is entirely configurable without touching Python code.
        - Acts as a high-recall safety net when the model tiers are unavailable.
        - Bio_ClinicalBERT (Tier 2) provides high-precision correction on top.
        """
        found: Dict[str, List[str]] = {}
        t_low = text.lower().strip()
        if not t_low:
            return found

        vocab = _load_vocab()

        # --- 1. Simple keyword matching for all 7 basic dimensions ---
        simple_dims = [
            ("location", "location"),
            ("sensation", "sensation"),
            ("concomitant", "concomitant"),
            ("temporal", "temporal"),
            ("mental", "mental"),
        ]
        for yaml_key, slot_key in simple_dims:
            for term in vocab.get(yaml_key, []):
                if re.search(r"\b" + re.escape(term) + r"\b", t_low):
                    found.setdefault(slot_key, []).append(term)

        # --- 2. Aggravation — directional (requires contextual marker) ---
        agg_trigger_patterns = vocab.get("aggravation_trigger_patterns", [
            r"\bworse\b", r"\baggravat\w*", r"\btrigger\w*",
            r"\bamplif\w*", r"\bintensif\w*", r"\bworsen\w*", r"makes?\s+it\s+worse",
        ])
        relief_phrases = vocab.get("relief_phrases", ["soothe", "better", "relief", "reliev", "ease", "calm", "help"])

        is_agg = any(re.search(p, t_low) for p in agg_trigger_patterns)
        is_in_modality_state = (
            hasattr(self, "state_machine")
            and self.state_machine.current_state == IntakeState.MODALITY
        )
        has_relief_context = any(r in t_low for r in relief_phrases)

        for agg_term in vocab.get("modality_agg", []):
            if re.search(r"\b" + re.escape(agg_term) + r"\b", t_low):
                if (is_agg or is_in_modality_state) and not has_relief_context:
                    found.setdefault("modality_agg", []).append(agg_term)

        # Free-form "X makes it worse" pattern capture
        m_x_worse = re.search(
            r"([a-zA-Z\s]{2,30})\s+(?:makes?\s+it\s+worse|aggravates?|triggers?|worsens?|amplifies?)",
            t_low,
        )
        if m_x_worse:
            phrase = re.sub(r"^(?:that|this|it|which|and|but|also)\s+", "", m_x_worse.group(1).strip())
            if phrase and phrase not in found.get("modality_agg", []):
                found.setdefault("modality_agg", []).append(phrase)

        # --- 3. Amelioration — directional ---
        amel_trigger_patterns = vocab.get("amelioration_trigger_patterns", [
            r"\bbetter\b", r"\brelie\w*", r"\bsooth\w*", r"\beas\w*",
            r"\bimprov\w*", r"\bhelp\w*", r"\bcalm\w*", r"\bcomfort\w*",
            r"makes?\s+it\s+better", r"brings?\s+relief",
        ])
        is_amel = any(re.search(p, t_low) for p in amel_trigger_patterns)

        for amel_term in vocab.get("modality_amel", []):
            if re.search(r"\b" + re.escape(amel_term) + r"\b", t_low):
                if is_amel or (is_in_modality_state and is_amel):
                    found.setdefault("modality_amel", []).append(amel_term)

        # Free-form "X soothes / relieves" pattern capture
        m_x_better = re.search(
            r"([a-zA-Z\s]{2,30})\s+(?:makes?\s+it\s+better|soothes?|relieves?|helps?|eases?|calms?)",
            t_low,
        )
        if m_x_better:
            phrase = re.sub(r"^(?:that|this|it|which|and|but|also)\s+", "", m_x_better.group(1).strip())
            if phrase and phrase not in found.get("modality_amel", []):
                found.setdefault("modality_amel", []).append(phrase)

        return found

    # =========================================================================
    # TIER 2: Bio_ClinicalBERT NER Extractor
    # =========================================================================

    def _extract_slots_clinicalbert(self, text: str) -> Dict[str, List[str]]:
        """Tier 2 — Fine-tuned Bio_ClinicalBERT NER extraction.

        Why ClinicalBERT as Tier 2 (not Tier 1):
        - The model adds ~0.5–1.5s CPU latency; the heuristic runs in <1ms.
        - ClinicalBERT understands context and sub-word morphology that regex misses
          (e.g. 'amplifying the heaviness' maps MOD_AGG + SEN correctly).
        - Only runs when utterance has enough words to justify inference cost.

        Returns empty dict if NER is unavailable or utterance is too short.
        """
        word_count = len(text.split())
        if word_count < _MIN_WORDS_FOR_BERT:
            return {}

        ner = None
        if self.orchestrator and getattr(self.orchestrator, "ner", None):
            ner = self.orchestrator.ner
        else:
            # Attempt to instantiate NER directly if orchestrator isn't wired up
            try:
                from src.models.symptom_ner import SymptomNER
                ner = SymptomNER()  # will use fine-tuned weights if available
            except Exception as err:
                logger.debug("Could not instantiate SymptomNER for Tier 2: %s", err)
                return {}

        if ner is None or getattr(ner, "mock_mode", True):
            # Mock mode means no real weights — skip to avoid polluting slots with
            # keyword-only fallback that duplicates Tier 1 output.
            return {}

        lbl_map = {
            "LOC": "location",
            "SEN": "sensation",
            "MOD_AGG": "modality_agg",
            "MOD_AMEL": "modality_amel",
            "CONC": "concomitant",
            "TEMP": "temporal",
            "MENT": "mental",
        }
        found: Dict[str, List[str]] = {}
        try:
            ner_ents = ner.extract_entities(text)
            for ent in ner_ents:
                slot_k = lbl_map.get(ent.get("label", "").upper())
                ent_text = ent.get("text", "").strip().lower()
                confidence = ent.get("confidence", 0.0)
                # Only accept high-confidence spans (≥0.7) to avoid noisy predictions
                if slot_k and ent_text and confidence >= 0.7:
                    found.setdefault(slot_k, []).append(ent_text)
        except Exception as err:
            logger.debug("ClinicalBERT NER extraction failed (Tier 2): %s", err)

        return found

    # =========================================================================
    # TIER 3: LLaMA Structured JSON Slot Extraction
    # =========================================================================

    def _extract_slots_llm(self, user_utterance: str) -> Dict[str, List[str]]:
        """Tier 3 — LLaMA 3 structured JSON slot extraction for verification/enrichment.

        Why LLaMA as Tier 3:
        - LLaMA understands nuanced phrasing ("feels like a storm inside" → anxiety/MENT)
          that neither regex nor fine-tuned ClinicalBERT reliably catches.
        - Used as an enrichment layer — only invoked when the utterance is substantive
          (>= _MIN_WORDS_FOR_LLM_EXTRACTION words) to avoid latency on short replies.
        - Parses SLOT_UPDATE JSON from the bot's own reply (zero extra network calls)
          OR makes a dedicated lightweight extraction call if needed.

        Returns empty dict on failure — non-blocking.
        """
        word_count = len(user_utterance.split())
        llm_cfg = _load_llm_extraction_config()

        if self.mock_mode or not llm_cfg.get("enabled", True):
            return {}

        min_words = int(llm_cfg.get("min_word_count", _MIN_WORDS_FOR_LLM_EXTRACTION))
        if word_count < min_words:
            return {}

        slot_extraction_prompt = (
            f"Extract ONLY the clinical symptom information from this single patient statement:\n"
            f"\"{user_utterance}\"\n\n"
            f"Return ONLY a valid JSON object with exactly these 7 keys (use lowercase strings, empty list [] if not mentioned):\n"
            f"{{\"location\": [], \"sensation\": [], \"modality_agg\": [], \"modality_amel\": [], "
            f"\"concomitant\": [], \"temporal\": [], \"mental\": []}}\n"
            f"Do NOT add any other text. Do NOT infer. Only extract what is explicitly stated."
        )

        url = f"{self.api_base}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": slot_extraction_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,   # zero temperature for deterministic JSON output
                "num_predict": 128,   # slot JSON is short
                "top_p": 1.0,
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
            with opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_text = data.get("response", "").strip()
        except Exception as err:
            logger.debug("LLaMA slot extraction call failed (Tier 3): %s", err)
            return {}

        # Try to parse the JSON — LLaMA sometimes adds backticks or extra text
        json_match = re.search(r"\{[^{}]+\}", raw_text, re.DOTALL)
        if not json_match:
            logger.debug("LLaMA Tier 3: no JSON object found in response: %r", raw_text[:200])
            return {}

        try:
            parsed = json.loads(json_match.group(0))
        except json.JSONDecodeError as err:
            logger.debug("LLaMA Tier 3: JSON parse error: %s | raw: %r", err, raw_text[:200])
            return {}

        found: Dict[str, List[str]] = {}
        valid_keys = {"location", "sensation", "modality_agg", "modality_amel", "concomitant", "temporal", "mental"}
        for key, vals in parsed.items():
            if key in valid_keys and isinstance(vals, list):
                clean_vals = [str(v).strip().lower() for v in vals if str(v).strip()]
                if clean_vals:
                    found[key] = clean_vals

        return found

    # =========================================================================
    # 3-Tier Merge Orchestrator & Sanitizer
    # =========================================================================

    @staticmethod
    def sanitize_extracted_slots(slots: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Clean, deduplicate, and resolve cross-dimension conflicts in extracted symptom slots.

        - Drops conversational stopwords & non-symptoms (e.g. 'actually', 'worse than', 'than that').
        - Resolves sensation vs aggravation conflict (e.g. 'sharp, electric stabs' belongs in sensation, not modality_agg).
        - Resolves 'worse alone' vs 'alone' conflict (removes 'alone' from mental when 'worse alone' is in modality_agg).
        - Performs subsumption deduplication (e.g. keeps 'utterly hopeless', drops redundant 'hopeless' / 'hopelessness').
        """
        if not slots:
            return {k: [] for k in ["location", "sensation", "modality_agg", "modality_amel", "concomitant", "temporal", "mental"]}

        cleaned: Dict[str, List[str]] = {
            k: [str(item).strip().lower() for item in slots.get(k, []) if str(item).strip()]
            for k in ["location", "sensation", "modality_agg", "modality_amel", "concomitant", "temporal", "mental"]
        }

        # 1. Conversational stopword removal
        STOPWORDS = {
            "worse than", "worse than that", "than that", "actually", "it's", "it is",
            "yes", "no", "yeah", "yep", "not really", "that's it", "nothing else",
            "i feel", "i have", "patient has", "doctor", "please", "help", "thank you",
            "everything", "covers it", "all of it", "that is all", "it", "that", "this",
            "more", "much", "very", "severe", "increasing", "escalating", "terrible", "bad"
        }
        for k in cleaned:
            cleaned[k] = [v for v in cleaned[k] if v not in STOPWORDS and len(v) >= 2]

        # 2. Sensation vs Aggravation conflict resolution
        SENSATION_INDICATORS = {
            "sharp", "stab", "stabbing", "stabs", "electric", "throbbing", "pounding",
            "burning", "splitting", "pulsating", "pulsing", "stitching", "heavy", "tight"
        }
        filtered_agg: List[str] = []
        for term in cleaned["modality_agg"]:
            is_sensation = any(re.search(r"\b" + re.escape(si) + r"\b", term) for si in SENSATION_INDICATORS)
            if is_sensation:
                if term not in cleaned["sensation"]:
                    cleaned["sensation"].append(term)
            else:
                filtered_agg.append(term)
        cleaned["modality_agg"] = filtered_agg

        # 3. 'worse alone' vs 'alone' resolution
        has_worse_alone = any("worse alone" in a or "alone" in a for a in cleaned["modality_agg"])
        if has_worse_alone:
            if "worse alone" in cleaned["modality_agg"] and "alone" in cleaned["modality_agg"]:
                cleaned["modality_agg"].remove("alone")
            if "alone" in cleaned["mental"]:
                cleaned["mental"].remove("alone")

        # 4. Redundant sub-phrase subsumption within each dimension
        for k in cleaned:
            unique_vals = list(dict.fromkeys(cleaned[k]))
            if len(unique_vals) <= 1:
                cleaned[k] = unique_vals
                continue

            sorted_by_len = sorted(unique_vals, key=len, reverse=True)
            pruned: List[str] = []
            for item in sorted_by_len:
                is_sub = False
                for keeper in pruned:
                    if item in keeper.split() or (item in keeper and len(item) < len(keeper)):
                        is_sub = True
                        break
                    # Root / morphological stem match (e.g. 'hopelessness' subsumed by 'utterly hopeless')
                    keeper_words = [w for w in re.findall(r"\b\w+\b", keeper) if len(w) >= 4]
                    item_words = [w for w in re.findall(r"\b\w+\b", item) if len(w) >= 4]
                    for kw in keeper_words:
                        for iw in item_words:
                            if (kw.startswith(iw) or iw.startswith(kw)) and min(len(kw), len(iw)) >= 4:
                                is_sub = True
                                break
                        if is_sub:
                            break
                if not is_sub:
                    pruned.append(item)
            cleaned[k] = pruned

        return cleaned

    def _extract_all_slots(self, user_utterance: str) -> Dict[str, List[str]]:
        """Run all 3 extraction tiers and merge results, deduplicating per dimension.

        Merge order: Tier 1 → Tier 2 → Tier 3.
        Later tiers supplement (never erase) earlier tiers.
        """
        merged: Dict[str, List[str]] = {}

        def _merge_tier(tier_result: Dict[str, List[str]]) -> None:
            for slot_k, vals in tier_result.items():
                for v in vals:
                    v_clean = v.strip().lower()
                    existing = [x.lower() for x in merged.get(slot_k, [])]
                    if v_clean and v_clean not in existing:
                        merged.setdefault(slot_k, []).append(v_clean)

        # Tier 1 — YAML heuristic (always runs, <1ms)
        _merge_tier(self._extract_slots_heuristic(user_utterance))

        # Tier 2 — Fine-tuned biomedical encoder (BioLinkBERT / PubMedBERT / Ensemble)
        _merge_tier(self._extract_slots_clinicalbert(user_utterance))

        # Tier 3 — LLaMA structured extraction (when utterance is substantive, ~2–4s)
        _merge_tier(self._extract_slots_llm(user_utterance))

        # Sanitize and resolve cross-dimension conflicts
        return self.sanitize_extracted_slots(merged)

    # =========================================================================
    # Ollama Chat Helpers
    # =========================================================================

    def _call_ollama_chat_stream(self, user_prompt: str):
        """Call Ollama /api/chat with streaming NDJSON and yield content pieces.

        Streams chunks from local Ollama daemon with 120s timeout and num_predict: 256.
        """
        url = f"{self.api_base}/api/chat"

        sys_prompt = (
            CHATBOT_PRACTITIONER_SYSTEM_PROMPT
            if getattr(self, "intake_mode", "patient") == "practitioner"
            else CHATBOT_SYSTEM_PROMPT
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
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
            with opener.open(req, timeout=120) as resp:
                self.last_call_failed = False
                for line in resp:
                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue
                    try:
                        chunk = json.loads(line_str)
                    except json.JSONDecodeError:
                        continue
                    piece = chunk.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if chunk.get("done", False):
                        break
        except (urllib.error.URLError, TimeoutError, OSError, Exception) as err:
            logger.warning("Ollama streaming call failed or timed out (%s).", err)
            self.last_call_failed = True
            raise err

    def _call_ollama_chat(self, user_prompt: str, stream: bool = False):
        """Call Ollama /api/chat.

        If stream=True, yields NDJSON chunks as a generator.
        If stream=False, returns the complete reply string, falling back safely on error.
        """
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
        """Yield visible text chunks while collecting the complete raw stream in sink.

        Stops yielding visible text as soon as control tags like QUICK_REPLIES,
        SLOT_UPDATE, or bracketed control syntax appear, keeping the user-facing
        chat completely free of raw control syntax.
        """
        stopped = False
        buffer = ""
        control_pattern = re.compile(
            r"(\[?\s*(?:QUICK_REPLIES|SLOT_UPDATE)\b|\[\s*\"|\[\s*\{|```)",
            re.IGNORECASE,
        )

        for piece in chunks:
            sink.append(piece)
            if stopped:
                continue

            buffer += piece
            match = control_pattern.search(buffer)
            if match:
                stopped = True
                visible_text = buffer[: match.start()]
                if visible_text:
                    yield visible_text
                buffer = ""
            else:
                partial_match = re.search(
                    r"(\[|\[?\s*Q(?:U(?:I(?:C(?:K(?:_(?:R(?:E(?:P(?:L(?:I(?:E(?:S)?)?)?)?)?)?)?)?)?)?)?)?$|\[?\s*S(?:L(?:O(?:T(?:_(?:U(?:P(?:D(?:A(?:T(?:E)?)?)?)?)?)?)?)?)?)?$|`{1,3}$)",
                    buffer,
                    re.IGNORECASE,
                )
                if partial_match:
                    safe_len = partial_match.start()
                    safe_chunk = buffer[:safe_len]
                    buffer = buffer[safe_len:]
                    if safe_chunk:
                        yield safe_chunk
                else:
                    yield buffer
                    buffer = ""

        if not stopped and buffer:
            yield buffer

    def is_ollama_online(self) -> bool:
        """Check if local Ollama daemon is responding.

        Tries 127.0.0.1 first to bypass Windows IPv6 resolution latency on localhost.
        """
        candidates = ["http://127.0.0.1:11434", self.api_base, "http://localhost:11434"]
        seen: set = set()
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

    # =========================================================================
    # Fallback Responses (offline / mock mode)
    # =========================================================================

    def _mock_response_for_state(self) -> str:
        """Deterministic, clinically focused offline fallback responses per state."""
        state = self.state_machine.current_state

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

    # =========================================================================
    # Quick Reply / Suggestion Chip Generation & Text Sanitization
    # =========================================================================

    @staticmethod
    def clean_message_text(text: str) -> str:
        """Strip all metadata markers, leaked JSON, code fences, and dangling brackets from bot text."""
        if not text:
            return ""

        # 1. Remove SLOT_UPDATE and QUICK_REPLIES blocks anywhere in the text (bracketed and unbracketed)
        text = re.sub(r"\[?\s*SLOT_UPDATE\s*:\s*\{[^{}]*\}\s*\]?", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"\[?\s*QUICK_REPLIES\s*:\s*\[.*?\]\s*\]?", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"(?:\[\s*)?QUICK_REPLIES\s*:.*$", "", text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        text = re.sub(r"(?:\[\s*)?SLOT_UPDATE\s*:.*$", "", text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)

        # 2. Remove any trailing JSON array or object
        text = re.sub(r"\[\s*\"[^\"]+\"\s*(?:,\s*\"[^\"]+\"\s*)*\]\s*$", "", text.strip(), flags=re.DOTALL)
        text = re.sub(r"\{[^{}]*\}\s*$", "", text.strip(), flags=re.DOTALL)

        # 3. Remove markdown fences like ```json ... ``` or hanging ```
        text = re.sub(r"```(?:json)?\s*$", "", text.strip(), flags=re.IGNORECASE)

        # 4. Remove labels if they appear on their own lines or at the end
        text = re.sub(r"(?:QUICK_REPLIES|SLOT_UPDATE)\s*:\s*$", "", text.strip(), flags=re.IGNORECASE)

        # 5. Split into lines and filter out any lines that are just lone punctuation/brackets
        cleaned_lines = []
        for line in text.split("\n"):
            stripped = line.strip()
            # Drop lines consisting only of brackets, braces, code fences, or punctuation
            if stripped in ("[", "]", "{", "}", "(", ")", "```", "```json", "QUICK_REPLIES:", "SLOT_UPDATE:"):
                continue
            if re.match(r"^\[\s*(?:QUICK_REPLIES|SLOT_UPDATE)?:?\]?$", stripped, re.IGNORECASE):
                continue
            cleaned_lines.append(line)

        text = "\n".join(cleaned_lines).strip()

        # 6. Strip any trailing dangling punctuation or unclosed opening brackets
        while text and text[-1] in "[\n\r\t `:,-({":
            text = text[:-1].rstrip()

        return text.strip()

    def _parse_and_strip_quick_replies(self, text: str) -> Tuple[str, List[str]]:
        """Extract QUICK_REPLIES from LLaMA output (bracketed JSON or unbracketed list) and return clean text + options."""
        if not text:
            return "", []

        quick_options: List[str] = []
        clean_part = text

        match = re.search(r"(?:\[\s*)?QUICK_REPLIES\s*:\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
        if match:
            clean_part = text[: match.start()].strip()
            raw = match.group(1).strip()

            # Attempt A: bracketed list or JSON
            if raw.startswith("["):
                bracket_match = re.match(r"\[(.*?)\]", raw, re.DOTALL)
                if bracket_match:
                    try:
                        parsed = json.loads("[" + bracket_match.group(1) + "]")
                        if isinstance(parsed, list):
                            quick_options = [str(x).strip(' "\'') for x in parsed if str(x).strip()]
                    except Exception:
                        quoted = re.findall(r'["\']([^"\']+)["\']', bracket_match.group(1))
                        if quoted:
                            quick_options = [q.strip() for q in quoted if q.strip()]

            # Attempt B: comma or newline separated plain items (e.g. "Worst after exercise, Better when sitting")
            if not quick_options:
                clean_raw = re.sub(r"[\]\}\)]+$", "", raw).strip()
                lines = clean_raw.splitlines()
                if len(lines) > 1:
                    for line in lines:
                        l = re.sub(r"^[\s\-\*\d\.\•]+", "", line).strip(' "\'')
                        if l:
                            quick_options.append(l)
                else:
                    parts = clean_raw.split(",")
                    for p in parts:
                        p_clean = re.sub(r"^[\s\-\*\d\.\•]+", "", p).strip(' "\'')
                        if p_clean:
                            quick_options.append(p_clean)

            quick_options = [
                opt.capitalize() if opt.islower() else opt
                for opt in quick_options
                if opt
            ]

        # Strict validation: Quick replies must be patient statements, never doctor questions
        valid_patient_replies: List[str] = []
        question_openers = (
            "how ", "what ", "why ", "when ", "where ", "can you ", "could you ",
            "is there ", "are there ", "do you ", "tell me ", "describe ", "would you ",
            "which ", "have you ", "should you ", "can we ", "could we "
        )
        for opt in quick_options:
            s_opt = opt.strip()
            if not s_opt:
                continue
            # Must NOT end with '?'
            if s_opt.endswith("?"):
                continue
            # Must NOT start with interrogatives
            if s_opt.lower().startswith(question_openers):
                continue
            # Must not be an excessively long sentence
            if len(s_opt.split()) > 8:
                continue
            valid_patient_replies.append(s_opt)

        # If LLM generated questions or failed validation, discard so dynamic suggestions take over
        if len(valid_patient_replies) < 2:
            valid_patient_replies = []

        clean_text = self.clean_message_text(clean_part)
        return clean_text, valid_patient_replies[:4]

    def _parse_and_strip_slot_update(self, text: str) -> Tuple[str, Dict[str, List[str]]]:
        """Extract SLOT_UPDATE JSON from LLaMA chatbot reply."""
        if not text:
            return text, {}

        pattern = r"(?:\[\s*)?SLOT_UPDATE:\s*(\{[^{}]+\})(?:\s*\])?"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        found: Dict[str, List[str]] = {}

        if match:
            raw_json = match.group(1)
            text_without_slot = text[: match.start()] + text[match.end() :]
            try:
                parsed = json.loads(raw_json)
                valid_keys = {"location", "sensation", "modality_agg", "modality_amel", "concomitant", "temporal", "mental"}
                for key, vals in parsed.items():
                    if key in valid_keys and isinstance(vals, list):
                        clean_vals = [str(v).strip().lower() for v in vals if str(v).strip()]
                        if clean_vals:
                            found[key] = clean_vals
            except Exception:
                pass
            return text_without_slot.strip(), found

        return text, found

    def generate_dynamic_suggestions(self, bot_message: str) -> List[str]:
        """Generate 3-4 contextual first-person instant-reply suggestions for the patient.

        Suggestions are keyed on the current bot question text (not the state directly)
        so they adapt to what the bot actually asked, not just which state we're in.
        The vocabulary used here is intentionally kept in Python (not YAML) because
        these are UI presentation strings, not clinical extraction keywords.
        """
        text = (bot_message or "").lower()
        slots = self.extracted_slots

        # Opening / Chief Complaint (Kentian anatomical location first)
        if not text or any(p in text for p in ["troubling you", "primary symptoms", "bring you in", "bothers you", "what brings", "how are you"]):
            return [
                "Headache / Forehead / Temples",
                "Chest pain / Respiration",
                "Stomach pain / Digestion",
                "Joint pain / Musculoskeletal",
            ]

        # Concomitants
        if any(w in text for w in ["alongside", "other symptom", "at the same time", "also notice", "nausea, dizziness"]):
            return [
                "Accompanied by nausea",
                "Dizziness and lightheadedness",
                "Chills and cold sweat",
                "No other physical symptoms",
            ]

        # Location
        if any(w in text for w in ["where", "location", "part of your", "which side", "whereabouts", "where in"]):
            known_locs = " ".join(slots.get("location", [])).lower()
            if "head" in known_locs or "head" in text or "migraine" in text or "temple" in text:
                return ["Forehead and temples", "Top of head (vertex)", "Back of head (occiput)", "Behind my eyes"]
            elif "stomach" in known_locs or "abdomen" in known_locs or "stomach" in text or "nausea" in text:
                return ["Pit of stomach (epigastrium)", "Lower abdomen & cramping", "All across my stomach", "Around my navel area"]
            elif "chest" in known_locs or "chest" in text or "heart" in text or "breath" in text:
                return ["Center of my chest", "Left side around heart", "Upper chest and lungs", "Tightness across my ribs"]
            elif "throat" in known_locs or "throat" in text:
                return ["Right side of throat", "Left side and tonsils", "Deep down in the throat", "Larynx and voice box"]
            elif "back" in known_locs or "back" in text or "spine" in text or "lumbar" in text:
                return ["Lower lumbar area", "Upper back between shoulders", "Along the entire spine", "Sacrum and tailbone"]
            elif "joint" in known_locs or "knee" in known_locs or "joint" in text or "limb" in text:
                return ["Knees and ankles", "Hands and wrists", "Shoulders and elbows", "Small finger joints"]
            else:
                return ["In my head and temples", "In my stomach and abdomen", "In my chest and throat", "In my lower back and joints"]

        # Sensation
        if any(w in text for w in ["sensation", "feel like", "kind of pain", "type of", "throbbing", "burning", "stabbing", "describe the", "how does it"]):
            return [
                "Sharp, electric stabs",
                "Dull, heavy pressure",
                "Vibrating, humming noise",
                "Pulsating, throbbing rhythm",
            ]

        # Modality
        if any(w in text for w in ["makes it worse", "make it worse", "aggravat", "flare", "trigger", "worse from", "bring relief", "brings relief", "comfort", "soothe", "better from", "relieved by"]):
            return [
                "Worse in heat & bright sun",
                "Worse from motion or walking",
                "Better with cold compresses",
                "Better resting in a dark room",
            ]

        # Temporal
        if any(w in text for w in ["what time", "time of day", "time pattern", "when does", "morning or night", "day or night", "waking up", "periodicity", "hour", "clock", "midnight"]):
            return [
                "Worse in morning on waking",
                "Worse after midnight (2-3 AM)",
                "Worse in afternoon (around 3-4 PM)",
                "No specific time pattern",
            ]

        # Mental/Emotional
        if any(w in text for w in ["mood", "stress", "emotion", "feeling mentally", "anxious", "mind", "irritab", "peace of mind", "emotional"]):
            return [
                "Restless, anxious, and uneasy",
                "Irritable and easily angered",
                "Depressed, tired, and quiet",
                "My mood is relatively calm",
            ]

        # Review / Confirmation / Clarification / Readiness
        if any(w in text for w in ["accurate", "summarize", "anything else", "sound right", "add anything", "confirm", "covers it", "got it right", "proceed", "repertoriz", "ready"]):
            return [
                "Yes, that covers all my symptoms!",
                "Please proceed to repertorization",
                "I also want to add another detail",
                "Ready to view my remedies",
            ]

        # Impact on daily life / relationships / coping
        if any(w in text for w in ["daily life", "relationships", "affecting", "coping", "manage", "interfere", "routine"]):
            return [
                "Yes, deeply affecting my daily life",
                "I struggle to get through each day",
                "Mostly overwhelming when alone",
                "I try to hide it from others",
            ]

        # Hopelessness / Despair / Grief
        if any(w in text for w in ["hopeless", "despair", "grief", "forsaken", "weep", "tearful"]):
            return [
                "I feel completely hopeless & forsaken",
                "Weeping easily from any emotional upset",
                "Worse in morning on waking",
                "Unable to find joy in anything",
            ]

        # Intensity / Escalation / "worse than that"
        if any(w in text for w in ["intensity", "increasing", "getting worse", "escalat"]):
            return [
                "The emotional despair is unbearable",
                "Physical pains worsen with sadness",
                "Worse when alone and thinking",
                "I feel utterly exhausted by it",
            ]

        # Adaptive state-based fallback
        state_fallback = {
            IntakeState.GREETING: ["Severe recurring headache", "Stomach pain and burning", "Severe anxiety and fatigue"],
            IntakeState.CHIEF_COMPLAINT: ["Headache in temples", "Stomach ache after food", "Anxious and sleepless"],
            IntakeState.LOCATION: ["Forehead and temples", "Stomach & abdomen", "Chest and throat", "Lower back & joints"],
            IntakeState.SENSATION: ["Throbbing and pulsating", "Sharp stabbing pain", "Dull heavy ache", "Burning sensation"],
            IntakeState.MODALITY: ["Worse in heat and sun", "Worse from motion", "Better with cold compress", "Better in quiet dark"],
            IntakeState.CONCOMITANT: ["Nausea and dizziness", "Chills and perspiration", "Extreme fatigue", "No other symptoms"],
            IntakeState.TEMPORAL: ["Worse in morning on waking", "Worse after midnight (2-3 AM)", "Worse in afternoon / evening", "No specific time pattern"],
            IntakeState.MENTAL: ["Restless and anxious", "Irritable and frustrated", "Down and tearful", "Calm and peaceful"],
            IntakeState.REVIEW: ["Yes, that covers all my symptoms!", "I want to add another symptom", "Please proceed to repertorization"],
            IntakeState.DONE: ["Proceed to Review →", "Check Captured Symptoms", "Add Another Detail", "Start New Consultation"],
        }
        return state_fallback.get(self.state_machine.current_state, [
            "Yes, exactly like that",
            "Not quite, let me explain",
            "Please analyze my remedies now",
        ])

    def get_current_suggestions(self) -> List[str]:
        """Return the current dynamic instant-reply suggestions for the patient."""
        if not self.current_suggestions and self.history:
            last_bot_msg = self.history[-1]["content"] if self.history[-1]["role"] == "assistant" else ""
            if last_bot_msg:
                self.current_suggestions = self.generate_dynamic_suggestions(last_bot_msg)
        return self.current_suggestions or self.generate_dynamic_suggestions(
            self.history[-1]["content"] if self.history else ""
        )

    # =========================================================================
    # Core Turn Processing
    # =========================================================================

    def prepare_turn(self, user_utterance: str) -> str:
        """Run FSM transitions, history recording, and slot extraction.

        Returns the formatted turn prompt for LLM generation (or empty string if mock/done).
        """
        # 1. Record patient utterance
        self.history.append({"role": "user", "content": user_utterance})

        # 2. 3-tier slot extraction
        new_slots = self._extract_all_slots(user_utterance)

        # 3. Merge into accumulated session slots
        for slot_k, vals in new_slots.items():
            for v in vals:
                v_clean = v.strip().lower()
                existing = [x.lower() for x in self.extracted_slots.get(slot_k, [])]
                if v_clean and v_clean not in existing:
                    self.extracted_slots.setdefault(slot_k, []).append(v_clean)
        self.extracted_slots = self.sanitize_extracted_slots(self.extracted_slots)

        # 4. Transition FSM
        self.state_machine.next_state(user_utterance, extracted_slots=new_slots)
        current_state = self.state_machine.current_state
        goal_desc = self.state_machine.get_current_goal_description()

        # 5. Build prompt if not mock / done
        if self.mock_mode or current_state == IntakeState.DONE:
            return ""

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
        return turn_prompt

    def finalize_turn(self, raw_reply: str) -> str:
        """Parse inline tags, update slots, record assistant message in history,
        and trigger pipeline handover if intake reached DONE.

        Returns clean reply text.
        """
        if not raw_reply:
            raw_reply = self._mock_response_for_state()

        # 6. Extract inline SLOT_UPDATE from bot reply (free Tier 3 enrichment)
        raw_reply, inline_slots = self._parse_and_strip_slot_update(raw_reply)
        if inline_slots:
            for slot_k, vals in inline_slots.items():
                for v in vals:
                    v_clean = v.strip().lower()
                    existing = [x.lower() for x in self.extracted_slots.get(slot_k, [])]
                    if v_clean and v_clean not in existing:
                        self.extracted_slots.setdefault(slot_k, []).append(v_clean)
            self.extracted_slots = self.sanitize_extracted_slots(self.extracted_slots)

        # 7. Extract QUICK_REPLIES or generate dynamic suggestions
        clean_reply, quick_replies = self._parse_and_strip_quick_replies(raw_reply)
        if not quick_replies:
            quick_replies = self.generate_dynamic_suggestions(clean_reply)
        self.current_suggestions = quick_replies

        # 8. Record clean bot response
        self.history.append({"role": "assistant", "content": clean_reply})

        # 9. Handover to pipeline orchestrator when intake is complete
        current_state = self.state_machine.current_state
        if current_state == IntakeState.DONE and self.orchestrator:
            try:
                active_case = self.sync_to_case(self.case)
                if hasattr(self.orchestrator, "repertorize_case"):
                    self.patient_report = self.orchestrator.repertorize_case(active_case)
                else:
                    transcript = self.get_full_transcript()
                    self.patient_report = self.orchestrator.process_transcript(transcript)
            except Exception as e:
                logger.error("Error executing handover to pipeline orchestrator: %s", e)

        return clean_reply

    def process_turn(self, user_utterance: str) -> str:
        """Process a single turn of clinical intake dialogue.

        Coordinates slot extraction, state transition, LLM response generation,
        and post-turn slot persistence.

        Args:
            user_utterance: Patient's message.

        Returns:
            Friendly clinical response message from Kent-AI.
        """
        turn_prompt = self.prepare_turn(user_utterance)
        full_reply = "".join(self.stream_reply(turn_prompt))
        return self.finalize_turn(full_reply)


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
        self.last_call_failed = False

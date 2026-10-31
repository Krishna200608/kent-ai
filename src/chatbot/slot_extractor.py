"""Multi-tier clinical slot extraction pipeline for Kent-AI (Phase 6).

3-Tier Architecture:
    Tier 1 (fast, <1ms):    YAML-backed regex heuristic (configs/extraction_vocabulary.yaml)
    Tier 2 (primary, ~0.5-1.5s): Fine-tuned Bio_ClinicalBERT NER (when weights available)
    Tier 3 (LLM, ~2-4s):   LLaMA 3 structured JSON slot extraction
"""

from __future__ import annotations

import json
from functools import lru_cache
import logging
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from src.chatbot.state_machine import IntakeState

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

logger = logging.getLogger("slot_extractor")

# Minimum word count in a patient utterance to justify ClinicalBERT inference.
_MIN_WORDS_FOR_BERT = 2

# Minimum word count in a patient utterance to justify LLaMA slot extraction call.
_MIN_WORDS_FOR_LLM_EXTRACTION = 4


@lru_cache(maxsize=1)
def load_vocab() -> Dict[str, Any]:
    """Load extraction vocabulary from YAML (cached for the process lifetime)."""
    try:
        data = get_extraction_vocabulary()
        return data.get("dimensions", {})
    except FileNotFoundError:
        logger.warning(
            "extraction_vocabulary.yaml not found. Heuristic extractor will produce no results. "
            "ClinicalBERT and LLaMA tiers remain active."
        )
        return {}


_load_vocab = load_vocab


@lru_cache(maxsize=1)
def load_llm_extraction_config() -> Dict[str, Any]:
    """Load LLM slot extraction config from YAML (cached)."""
    try:
        data = get_extraction_vocabulary()
        return data.get("llm_extraction", {})
    except FileNotFoundError:
        return {}


_load_llm_extraction_config = load_llm_extraction_config


@lru_cache(maxsize=1)
def load_generate_button_config() -> Dict[str, Any]:
    """Load generate button unlock config from YAML (cached)."""
    try:
        data = get_extraction_vocabulary()
        return data.get("generate_button", {})
    except FileNotFoundError:
        return {}


_load_generate_button_config = load_generate_button_config


def get_min_dimensions_to_unlock() -> int:
    """Return the minimum Kent dimensions required to unlock 'Generate Repertorization'."""
    return int(load_generate_button_config().get("min_dimensions_to_unlock", 1))


def extract_slots_heuristic(
    text: str,
    current_state: Optional[IntakeState] = None,
) -> Dict[str, List[str]]:
    """Tier 1 — Fast YAML-vocabulary regex extractor covering Kent's 7 dimensions."""
    found: Dict[str, List[str]] = {}
    t_low = text.lower().strip()
    if not t_low:
        return found

    vocab = load_vocab()

    # --- 1. Simple keyword matching for all basic dimensions ---
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
    is_in_modality_state = current_state == IntakeState.MODALITY
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


def extract_slots_clinicalbert(
    text: str,
    orchestrator: Optional[Any] = None,
) -> Dict[str, List[str]]:
    """Tier 2 — Fine-tuned Bio_ClinicalBERT NER extraction."""
    word_count = len(text.split())
    if word_count < _MIN_WORDS_FOR_BERT:
        return {}

    ner = None
    if orchestrator and getattr(orchestrator, "ner", None):
        ner = orchestrator.ner
    else:
        try:
            from src.models.symptom_ner import SymptomNER
            ner = SymptomNER()
        except Exception as err:
            logger.debug("Could not instantiate SymptomNER for Tier 2: %s", err)
            return {}

    if ner is None or getattr(ner, "mock_mode", True):
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
            if slot_k and ent_text and confidence >= 0.7:
                found.setdefault(slot_k, []).append(ent_text)
    except Exception as err:
        logger.debug("ClinicalBERT NER extraction failed (Tier 2): %s", err)

    return found


def extract_slots_llm(
    user_utterance: str,
    api_base: str,
    model_name: str,
    current_state: Optional[IntakeState] = None,
) -> Dict[str, List[str]]:
    """Tier 3 — LLaMA 3 structured JSON slot extraction via Ollama."""
    word_count = len(user_utterance.split())
    if word_count < _MIN_WORDS_FOR_LLM_EXTRACTION:
        return {}

    cfg = load_llm_extraction_config()
    timeout = float(cfg.get("timeout_seconds", 3.5))
    temperature = float(cfg.get("temperature", 0.0))
    num_predict = int(cfg.get("num_predict", 128))

    system_prompt = (
        "You are a clinical entity extractor for a homeopathic repertorization system. "
        "Extract clinical symptoms mentioned by the patient into JSON. "
        "Return ONLY a valid JSON object with any of these keys (omit empty keys):\n"
        '  "location": [anatomical body parts or organs],\n'
        '  "sensation": [types of physical feeling, e.g. throbbing, burning, heavy],\n'
        '  "modality_agg": [things making it worse, e.g. cold air, bright light, movement],\n'
        '  "modality_amel": [things bringing relief, e.g. warm drinks, rest, fresh air],\n'
        '  "concomitant": [accompanying symptoms, e.g. nausea, dizziness, chills],\n'
        '  "temporal": [time of day or periodicity, e.g. morning, 3am, periodic],\n'
        '  "mental": [emotional state, e.g. anxiety, irritability, sadness]\n'
        "CRITICAL: Return ONLY valid JSON. No conversational text, no explanation."
    )

    state_hint = f" (Focus on: {current_state.value})" if current_state else ""
    user_msg = f'Patient statement{state_hint}: "{user_utterance}"'

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }

    url = f"{api_base.rstrip('/')}/api/chat"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    try:
        with opener.open(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_content = data.get("message", {}).get("content", "").strip()
            if not raw_content:
                return {}
            parsed = json.loads(raw_content)
            valid_keys = {"location", "sensation", "modality_agg", "modality_amel", "concomitant", "temporal", "mental"}
            found: Dict[str, List[str]] = {}
            for k, vals in parsed.items():
                if k in valid_keys and isinstance(vals, list):
                    clean_vals = [str(v).strip().lower() for v in vals if str(v).strip()]
                    if clean_vals:
                        found[k] = clean_vals
            return found
    except Exception as err:
        logger.debug("LLaMA slot extraction skipped or timed out (Tier 3): %s", err)
        return {}


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


def extract_all_slots(
    user_utterance: str,
    current_state: Optional[IntakeState] = None,
    orchestrator: Optional[Any] = None,
    api_base: str = "http://127.0.0.1:11434",
    model_name: str = "llama3:8b",
    mock_mode: bool = False,
    is_llm_online: bool = False,
) -> Dict[str, List[str]]:
    """Execute the 3-tier extraction pipeline and return newly extracted slots."""
    new_slots: Dict[str, List[str]] = {}

    def _merge_tier(tier_result: Dict[str, List[str]]) -> None:
        for k, vals in tier_result.items():
            for v in vals:
                v_clean = v.strip().lower()
                if v_clean and v_clean not in new_slots.setdefault(k, []):
                    new_slots[k].append(v_clean)

    # Tier 1: Fast YAML heuristic (<1ms)
    t1 = extract_slots_heuristic(user_utterance, current_state=current_state)
    _merge_tier(t1)

    # Tier 2: Bio_ClinicalBERT NER (~0.5-1.5s)
    if not mock_mode:
        t2 = extract_slots_clinicalbert(user_utterance, orchestrator=orchestrator)
        _merge_tier(t2)

    # Tier 3: LLaMA 3 zero-shot JSON extraction (~2-4s)
    if not mock_mode and is_llm_online:
        t3 = extract_slots_llm(
            user_utterance,
            api_base=api_base,
            model_name=model_name,
            current_state=current_state,
        )
        _merge_tier(t3)

    return sanitize_extracted_slots(new_slots)

"""Instruction dataset preparation, formatting, and JSON validation for generative LLM QLoRA.

Converts 7-dimension annotated clinical cases (train.jsonl, val.jsonl, test.jsonl) into
instruction-following pairs for autoregressive causal language models (Qwen-2.5, BioMistral, LLaMA-3.1).
Includes robust JSON output extraction, markdown stripping, and verbatim substring grounding checks.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("llm_dataset")

# 7 Canonical Symptom Dimensions in Kent-AI
CANONICAL_DIMENSIONS = [
    "LOC",        # Anatomical Location
    "SEN",        # Sensation & Pain Quality
    "MOD_AGG",    # Modality: Aggravation (worse from)
    "MOD_AMEL",   # Modality: Amelioration (better from)
    "CONC",       # Concomitant Symptom
    "TEMP",       # Temporal Modality
    "MENT",       # Mental & Emotional State
]

SYSTEM_PROMPT_7DIM = (
    "You are an expert clinical NLP information extraction system specialized in classical homeopathic repertorization. "
    "Your task is to analyze the patient clinical narrative and extract all symptom dimensions into a strict, valid JSON object. "
    "The JSON keys MUST be exactly: LOC, SEN, MOD_AGG, MOD_AMEL, CONC, TEMP, MENT. "
    "Each key must map to a list of exact string phrases mentioned in the text. "
    "If a dimension is not present, provide an empty list []. Do not include explanations, conversational filler, or markdown."
)


def extract_7dim_slots_from_case(case: Dict[str, Any]) -> Dict[str, List[str]]:
    """Group entity annotations from a case dictionary into canonical 7-dimension lists."""
    slots: Dict[str, List[str]] = {dim: [] for dim in CANONICAL_DIMENSIONS}
    entities = case.get("entities", [])
    
    for ent in entities:
        label = ent.get("label", "").upper().strip()
        text = ent.get("text", "").strip()
        if not text:
            continue
        if label in slots:
            if text not in slots[label]:
                slots[label].append(text)
        else:
            # Handle possible naming variations
            normalized = normalize_dimension_key(label)
            if normalized and normalized in slots and text not in slots[normalized]:
                slots[normalized].append(text)
                
    return slots


def normalize_dimension_key(key: str) -> Optional[str]:
    """Normalize user or model dimension keys to canonical 7-dim labels."""
    k = key.upper().strip().replace(" ", "_")
    mapping = {
        "LOCATION": "LOC",
        "LOC": "LOC",
        "SENSATION": "SEN",
        "SEN": "SEN",
        "MODALITY_AGG": "MOD_AGG",
        "MOD_AGG": "MOD_AGG",
        "AGGRAVATION": "MOD_AGG",
        "WORSE": "MOD_AGG",
        "MODALITY_AMEL": "MOD_AMEL",
        "MOD_AMEL": "MOD_AMEL",
        "AMELIORATION": "MOD_AMEL",
        "BETTER": "MOD_AMEL",
        "CONCOMITANT": "CONC",
        "CONC": "CONC",
        "TEMPORAL": "TEMP",
        "TEMP": "TEMP",
        "TIME": "TEMP",
        "MENTAL": "MENT",
        "MENT": "MENT",
        "EMOTIONAL": "MENT",
    }
    return mapping.get(k)


def format_case_to_messages(case: Dict[str, Any]) -> List[Dict[str, str]]:
    """Convert a single clinical case dictionary into standard chat completion messages."""
    narrative = case.get("narrative", "").strip()
    slots = extract_7dim_slots_from_case(case)
    
    user_prompt = (
        f"Patient Clinical Narrative:\n"
        f"\"{narrative}\"\n\n"
        f"Extract all 7 symptom dimensions strictly in valid JSON format."
    )
    
    assistant_content = json.dumps(slots, ensure_ascii=False)
    
    return [
        {"role": "system", "content": SYSTEM_PROMPT_7DIM},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": assistant_content},
    ]


def format_case_for_training(case: Dict[str, Any], tokenizer: Any) -> Dict[str, Any]:
    """Format a case into input text using the tokenizer's chat template."""
    messages = format_case_to_messages(case)
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            text = tokenizer.apply_chat_template(messages, tokenize=False)
        except Exception:
            # If chat template rejects 'system' role (e.g., Mistral/BioMistral), merge system into user
            merged_messages = [
                {
                    "role": "user",
                    "content": f"{messages[0]['content']}\n\n{messages[1]['content']}",
                },
                messages[2],
            ]
            text = tokenizer.apply_chat_template(merged_messages, tokenize=False)
            messages = merged_messages
    else:
        # Fallback text formatting
        text = (
            f"<|system|>\n{messages[0]['content']}\n"
            f"<|user|>\n{messages[1]['content']}\n"
            f"<|assistant|>\n{messages[2]['content']}"
        )
    return {"text": text, "messages": messages, "case_id": case.get("case_id", "")}


def load_instruction_dataset(
    jsonl_path: str | Path,
    max_samples: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Load JSONL dataset of cases and return raw list of case dictionaries."""
    path = Path(jsonl_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    cases: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if max_samples is not None and idx >= max_samples:
                break
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                cases.append(data)
            except json.JSONDecodeError as err:
                logger.warning("Skipping malformed line %d in %s: %s", idx, path, err)

    return cases


def clean_llm_json_response(raw_text: str) -> Tuple[Optional[Dict[str, List[str]]], bool]:
    """Robustly extract and validate 7-dimension JSON from generative LLM text.
    
    Strips markdown code blocks (```json ... ```), finds outermost braces,
    validates JSON structure, and normalizes dimension keys.
    
    Returns:
        (parsed_dict, is_clean_syntax)
        where parsed_dict is normalized to {dim: [str, ...]} or None if unparseable,
        and is_clean_syntax is True if parsed without fallback repair.
    """
    if not raw_text or not raw_text.strip():
        return None, False

    text = raw_text.strip()
    
    # 1. Strip markdown fences: ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    
    # 2. Try direct JSON parse
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return _normalize_parsed_slots(data), True
    except json.JSONDecodeError:
        pass

    # 3. Fallback: find outermost curly braces
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        bracketed = cleaned[start_idx : end_idx + 1]
        try:
            data = json.loads(bracketed)
            if isinstance(data, dict):
                return _normalize_parsed_slots(data), False
        except json.JSONDecodeError:
            pass

    # 4. Regex-based key-value recovery fallback
    recovered: Dict[str, List[str]] = {dim: [] for dim in CANONICAL_DIMENSIONS}
    found_any = False
    for dim in CANONICAL_DIMENSIONS:
        pattern = rf'"{dim}"\s*:\s*\[(.*?)\]'
        match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            found_any = True
            items_str = match.group(1)
            # Find quoted items inside list
            items = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', items_str)
            recovered[dim] = [it.strip() for it in items if it.strip()]
            
    if found_any:
        return recovered, False

    return None, False


def _normalize_parsed_slots(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Normalize parsed dictionary into {CANONICAL_DIM: List[str]}."""
    normalized: Dict[str, List[str]] = {dim: [] for dim in CANONICAL_DIMENSIONS}
    for k, v in data.items():
        norm_key = normalize_dimension_key(str(k))
        if not norm_key or norm_key not in normalized:
            continue
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str) and item.strip():
                    normalized[norm_key].append(item.strip())
                elif isinstance(item, dict) and "text" in item:
                    txt = str(item["text"]).strip()
                    if txt:
                        normalized[norm_key].append(txt)
        elif isinstance(v, str) and v.strip():
            normalized[norm_key].append(v.strip())
            
    return normalized


def calculate_grounding_rate(
    extracted_slots: Dict[str, List[str]],
    narrative: str,
) -> Tuple[float, int, int]:
    """Calculate verbatim substring grounding (hallucination rate check).
    
    Checks what proportion of extracted symptom entities are exact or case-insensitive
    substrings of the input patient narrative.
    
    Returns:
        (grounding_ratio, grounded_count, total_extracted_entities)
    """
    total = 0
    grounded = 0
    narrative_lower = narrative.lower()

    for dim, items in extracted_slots.items():
        for item in items:
            total += 1
            item_clean = item.strip().lower()
            if not item_clean:
                continue
            if item_clean in narrative_lower:
                grounded += 1

    ratio = (grounded / total) if total > 0 else 1.0
    return ratio, grounded, total


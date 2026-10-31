"""Dynamic quick reply suggestion generation and chatbot text cleaning for Kent-AI."""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from src.chatbot.state_machine import IntakeState

logger = logging.getLogger("suggestions")


def clean_message_text(text: str) -> str:
    """Strip all metadata markers, leaked JSON, code fences, and dangling brackets from bot text."""
    if not text:
        return ""

    # Strip leading conversational metadata / preambles (e.g. "Here is my response:", "Response:", "Kent-AI:")
    text = re.sub(
        r"^(?:(?:here\s+(?:is|are)\s+(?:my|the|a|kent-ai's)?\s*response\s*:?)|(?:response\s*:)|(?:kent-ai\s*:)|(?:assistant\s*:))\s*",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )

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


def parse_and_strip_quick_replies(text: str, intake_mode: str = "patient") -> Tuple[str, List[str]]:
    """Extract QUICK_REPLIES from LLaMA output (bracketed JSON or unbracketed list) and return clean text + options."""
    if not text:
        return "", []

    is_practitioner = (intake_mode or "").lower() == "practitioner"
    quick_options: List[str] = []
    clean_part = text

    match = re.search(r"(?:\[\s*)?QUICK_REPLIES\s*:\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
    if match:
        clean_part = text[: match.start()].strip()
        raw_replies = match.group(1).strip()
        raw_replies = re.sub(r"\]\s*$", "", raw_replies).strip()

        try:
            parsed = json.loads(raw_replies)
            if isinstance(parsed, list):
                quick_options = [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            clean_raw = raw_replies.strip("[]")
            if "\n" in clean_raw:
                lines = clean_raw.split("\n")
                for l in lines:
                    l = re.sub(r"^[\s\-\*\d\.\•]+", "", l).strip(' "\'')
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

    # Strict validation: Quick replies must be valid statements/observations, never doctor questions
    valid_replies: List[str] = []
    question_openers = (
        "how ", "what ", "why ", "when ", "where ", "can you ", "could you ",
        "is there ", "are there ", "do you ", "tell me ", "describe ", "would you ",
        "which ", "have you ", "should you ", "can we ", "could we "
    )
    forbidden_practitioner_openers = (
        "makes me ", "i feel ", "i am ", "feel helpless", "affecting my"
    )
    for opt in quick_options:
        s_opt = opt.strip()
        if not s_opt:
            continue
        if s_opt.endswith("?"):
            continue
        if s_opt.lower().startswith(question_openers):
            continue
        if is_practitioner and any(f in s_opt.lower() for f in forbidden_practitioner_openers):
            continue
        if len(s_opt.split()) > 8:
            continue
        valid_replies.append(s_opt)

    if len(valid_replies) < 2:
        valid_replies = []

    clean_text = clean_message_text(clean_part)
    return clean_text, valid_replies[:4]


def parse_and_strip_slot_update(text: str) -> Tuple[str, Dict[str, List[str]]]:
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


def get_state_fallback(state: IntakeState) -> List[str]:
    """Adaptive state-based fallback options for instant replies."""
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
    return state_fallback.get(state, [
        "Yes, exactly like that",
        "Not quite, let me explain",
        "Please analyze my remedies now",
    ])


def generate_dynamic_suggestions(
    bot_message: str,
    extracted_slots: Optional[Dict[str, List[str]]] = None,
    current_state: Optional[IntakeState] = None,
    intake_mode: str = "patient",
) -> List[str]:
    """Generate 3-4 contextual first-person or clinical instant-reply suggestions."""
    text = (bot_message or "").lower()
    slots = extracted_slots or {}
    is_practitioner = (intake_mode or "").lower() == "practitioner" or "practitioner" in text

    # Opening / Chief Complaint (Kentian anatomical location first)
    if not text or any(p in text for p in ["troubling you", "primary symptoms", "bring you in", "bothers you", "what brings", "how are you", "practitioner mode", "chief complaint"]):
        if is_practitioner:
            return [
                "Headache / Migraine (Frontal/Temporal)",
                "Abdominal / Gastric distress",
                "Chest / Respiratory tightness",
                "Mental / Restless anxiety",
            ]
        return [
            "Severe throbbing headache",
            "Stomach pain & acid reflux",
            "Aching joints & stiffness",
            "Anxiety & trouble sleeping",
        ]

    # Concomitants
    if any(w in text for w in ["alongside", "other symptom", "at the same time", "also notice", "nausea, dizziness", "concomitant"]):
        if is_practitioner:
            return [
                "Concomitant nausea & vertigo",
                "Chills with cold perspiration",
                "Extreme prostration & trembling",
                "No physical concomitants observed",
            ]
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
        if is_practitioner:
            return [
                "Throbbing / Pulsating rhythm",
                "Sharp / Stabbing pain",
                "Burning / Acrid heat",
                "Dull ache / Heavy pressure",
            ]
        return [
            "Sharp, stabbing pain",
            "Dull, heavy pressure",
            "Burning heat and soreness",
            "Pulsating, throbbing rhythm",
        ]

    # Modality
    if any(w in text for w in ["makes it worse", "make it worse", "aggravat", "flare", "trigger", "worse from", "bring relief", "brings relief", "comfort", "soothe", "better from", "relieved by", "modality", "modalities"]):
        if is_practitioner:
            return [
                "Worse: Motion & physical exertion",
                "Worse: Cold air & draft",
                "Better: Warmth & hot applications",
                "Better: Absolute rest in dark",
            ]
        return [
            "Worse in heat & bright sun",
            "Worse from motion or walking",
            "Better with cold compresses",
            "Better resting in a dark room",
        ]

    # Temporal
    if any(w in text for w in ["what time", "time of day", "time pattern", "when does", "morning or night", "day or night", "waking up", "periodicity", "hour", "clock", "midnight", "temporal"]):
        if is_practitioner:
            return [
                "Aggravation: Morning on waking",
                "Aggravation: 2-3 AM (Night)",
                "Aggravation: 3-5 PM (Afternoon)",
                "No distinct temporal pattern",
            ]
        return [
            "Worse in morning on waking",
            "Worse after midnight (2-3 AM)",
            "Worse in afternoon (around 3-4 PM)",
            "No specific time pattern",
        ]

    # Mental/Emotional
    if any(w in text for w in ["mood", "stress", "emotion", "feeling mentally", "anxious", "mind", "irritab", "peace of mind", "emotional", "mental"]):
        if is_practitioner:
            return [
                "Restless, anxious, pacing",
                "Irritable, intolerant of noise",
                "Depressed, silent, tearful",
                "Apathetic and indifferent",
            ]
        return [
            "Restless, anxious, and uneasy",
            "Irritable and easily angered",
            "Depressed, tired, and quiet",
            "My mood is relatively calm",
        ]

    # Review / Confirmation / Clarification / Readiness
    if any(w in text for w in ["accurate", "summarize", "anything else", "sound right", "add anything", "confirm", "covers it", "got it right", "proceed", "repertoriz", "ready"]):
        if is_practitioner:
            return [
                "Proceed to Review →",
                "Add missing modality",
                "Add mental general",
                "Totality complete",
            ]
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
            "Worse when alone and thinking",
            "I feel utterly exhausted by it",
        ]

    # Adaptive state-based fallback
    if current_state:
        return get_state_fallback(current_state)

    return [
        "Yes, exactly like that",
        "Not quite, let me explain",
        "Please analyze my remedies now",
    ]

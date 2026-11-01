"""Turn history, opener generation, and undo operations for Kent-AI dialogue intake."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from src.chatbot.prompts import (
    CHATBOT_PRACTITIONER_TURN_PROMPT,
    CHATBOT_TURN_PROMPT,
)
from src.chatbot.fallbacks import PATIENT_GREETING, PRACTITIONER_GREETING
from src.chatbot.state_machine import ConversationStateMachine
from src.models.case import ClinicalCase


def seed_opener_for_case(
    case: ClinicalCase,
    intake_mode: str,
    mock_response_fn: Callable[[], str],
) -> Tuple[str, str]:
    """Generate a deterministic opener for a resumed case based on existing captured dimensions."""
    captured_parts = []
    for dim_key in ["location", "sensation", "modality_agg", "modality_amel", "concomitant", "temporal", "mental"]:
        vals = case.get_dimension_values(dim_key)
        if vals:
            label = dim_key.replace("_", " ").title()
            captured_parts.append(f"{label} - {', '.join(vals)}")

    if captured_parts:
        summary_str = "; ".join(captured_parts)
        gap_prompt = mock_response_fn()
        if intake_mode == "practitioner":
            opener = f"Welcome back. Recorded totality: {summary_str}. Next: {gap_prompt}"
        else:
            opener = f"Welcome back. So far I have: {summary_str}. Next, {gap_prompt}"
    else:
        opener = PRACTITIONER_GREETING if intake_mode == "practitioner" else PATIENT_GREETING

    return opener, "scripted"


def build_turn_prompt(
    state_machine: ConversationStateMachine,
    extracted_slots: Dict[str, List[str]],
    history: List[Dict[str, Any]],
    user_utterance: str,
    intake_mode: str,
) -> str:
    """Build the structured LLaMA 3 prompt for the current dialogue turn."""
    current_goal = state_machine.get_current_goal_description()
    slots_lines = []
    for k, v in extracted_slots.items():
        if v:
            slots_lines.append(f"  {k}: {', '.join(v)}")
    slots_summary = "\n".join(slots_lines) if slots_lines else "  None yet"

    is_practitioner = intake_mode == "practitioner"
    hist_lines = []
    for turn in history[-4:]:
        if turn.get("role") == "assistant":
            role_label = "Kent-AI"
        else:
            role_label = "Practitioner" if is_practitioner else "Patient"
        hist_lines.append(f"{role_label}: {turn.get('content', '')}")
    hist_text = "\n".join(hist_lines)

    template = CHATBOT_PRACTITIONER_TURN_PROMPT if is_practitioner else CHATBOT_TURN_PROMPT
    return template.format(
        current_goal=current_goal,
        slots_summary=slots_summary,
        history=hist_text,
        user_utterance=user_utterance,
    )


def apply_undo_capture(
    history: List[Dict[str, Any]],
    extracted_slots: Dict[str, List[str]],
    filled_slots: Set[str],
    case: Optional[ClinicalCase],
    turn_id: str,
    dim_key: str,
    item: str,
) -> None:
    """Remove a specific extracted symptom token from turn history, slot registry, and case."""
    for turn in history:
        if turn.get("turn_id") == turn_id and "captured" in turn:
            cap = turn["captured"]
            if dim_key in cap and item in cap[dim_key]:
                cap[dim_key] = [x for x in cap[dim_key] if x != item]

    if dim_key in extracted_slots and item in extracted_slots[dim_key]:
        extracted_slots[dim_key] = [x for x in extracted_slots[dim_key] if x != item]
        if not extracted_slots[dim_key]:
            filled_slots.discard(dim_key)

    if case is not None:
        curr_vals = case.get_dimension_values(dim_key)
        if item in curr_vals:
            case.set_dimension_values(dim_key, [x for x in curr_vals if x != item])
        if isinstance(case.extraction_meta, dict) and "items" in case.extraction_meta:
            if dim_key in case.extraction_meta["items"]:
                case.extraction_meta["items"][dim_key] = [
                    x for x in case.extraction_meta["items"][dim_key]
                    if x.get("text") != item
                ]


def apply_undo_last_turn(
    history: List[Dict[str, Any]],
    extracted_slots: Dict[str, List[str]],
    filled_slots: Set[str],
    case: Optional[ClinicalCase],
) -> None:
    """Pop the last assistant + user turn pair and revert all tokens captured in that turn."""
    if len(history) < 2:
        return

    popped_turns = []
    while history and len(popped_turns) < 2:
        popped_turns.append(history.pop())

    for turn in popped_turns:
        if turn.get("role") == "user" and "captured" in turn:
            for dim_key, items in turn["captured"].items():
                for item in items:
                    if dim_key in extracted_slots and item in extracted_slots[dim_key]:
                        extracted_slots[dim_key] = [x for x in extracted_slots[dim_key] if x != item]
                        if not extracted_slots[dim_key]:
                            filled_slots.discard(dim_key)
                    if case is not None:
                        curr_vals = case.get_dimension_values(dim_key)
                        if item in curr_vals:
                            case.set_dimension_values(dim_key, [x for x in curr_vals if x != item])
                        if isinstance(case.extraction_meta, dict) and "items" in case.extraction_meta:
                            if dim_key in case.extraction_meta["items"]:
                                case.extraction_meta["items"][dim_key] = [
                                    x for x in case.extraction_meta["items"][dim_key]
                                    if x.get("text") != item
                                ]

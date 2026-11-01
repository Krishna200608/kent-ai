"""Deterministic offline fallback responses for intake dialogue flow.

Provides structured, empathetic, and clinical FSM-based response templates
when Ollama / LLaMA 3 is unreachable or in test/mock mode.
"""

from __future__ import annotations

from typing import Dict, List
from src.chatbot.state_machine import IntakeState

PATIENT_GREETING = (
    "Hello, I am Kent-AI, your clinical homeopathic intake assistant. "
    "I'm here to understand what is troubling you today. "
    "Please describe what primary symptoms or discomfort brought you in."
)

PRACTITIONER_GREETING = (
    "Kent-AI Practitioner Mode active. Ready for clinical intake — "
    "enter patient chief complaint, observations, or presenting symptoms."
)


def get_mock_response_for_state(
    state: IntakeState,
    intake_mode: str = "patient",
    extracted_slots: Dict[str, List[str]] | None = None,
) -> str:
    """Return deterministic, clinically focused offline fallback responses per state."""
    slots = extracted_slots or {}
    is_practitioner = (intake_mode or "patient").lower() == "practitioner"

    if is_practitioner:
        if state == IntakeState.REVIEW:
            summary_lines = []
            for k, v in slots.items():
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
        for k, v in slots.items():
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


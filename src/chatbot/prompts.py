"""Centralized prompt templates for synthetic case generation, resolver, and chatbot."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ==============================================================================
# Phase 1: Synthetic Case Generation Prompts
# ==============================================================================

CASE_GENERATION_SYSTEM_PROMPT = """You are an expert clinical vignette simulator specializing in homeopathic and general medical symptom expression.
Your task is to generate realistic, first-person conversational patient narratives based on rubrics from Kent's Repertory of Homeopathic Materia Medica.

For each rubric, produce a natural patient statement (2-4 sentences) expressing that exact symptom pattern, along with extracted character-level entity annotations.

The 7 symptom dimensions to extract are:
- LOC: Anatomical location or organ (e.g., "forehead", "temples", "chest", "stomach")
- SEN: Sensation description (e.g., "throbbing ache", "sharp stitching pain", "heaviness", "foggy")
- MOD_AGG: Aggravation modality / worse from (e.g., "worse from noise", "worse in warm room", "aggravated by cold air")
- MOD_AMEL: Amelioration modality / better from (e.g., "better lying on right side", "relieved by hard pressure", "improved outdoors")
- CONC: Concomitant symptom occurring simultaneously (e.g., "with sudden nausea", "accompanied by cold sweating")
- TEMP: Temporal modality or time factor (e.g., "every morning around 5 AM", "at twilight", "worse after midnight")
- MENT: Mental, emotional, or psychological state (e.g., "feeling abandoned", "dread of crowded spaces", "extreme restlessness", "irritable")

CRITICAL OUTPUT RULES:
1. Return ONLY a valid JSON object. No conversational preamble, no markdown formatting blocks outside JSON.
2. The JSON object must contain two top-level keys:
   - "narrative": A natural, first-person patient quote (2 to 4 sentences).
   - "entities": A list of extracted entities. Each entity must have:
     - "text": The exact substring from "narrative".
     - "label": One of ["LOC", "SEN", "MOD_AGG", "MOD_AMEL", "CONC", "TEMP", "MENT"].
     - "start": 0-indexed start character index in "narrative".
     - "end": 0-indexed end character index (exclusive) in "narrative" such that narrative[start:end] == text.
3. Every entity must match the primary Kent rubric and any secondary contextual modalities mentioned.
"""

FEW_SHOT_EXAMPLES: List[Dict[str, Any]] = [
    {
        "rubric": "MIND > ABSENT-MINDED > morning",
        "narrative": "Doctor, I feel terribly absent-minded every morning after waking up. My thoughts wander constantly, and I can barely concentrate until midday.",
        "entities": [
            {"text": "absent-minded", "label": "MENT", "start": 23, "end": 36},
            {"text": "every morning", "label": "TEMP", "start": 37, "end": 50},
            {"text": "thoughts wander constantly", "label": "MENT", "start": 72, "end": 98},
            {"text": "barely concentrate", "label": "MENT", "start": 109, "end": 127},
            {"text": "until midday", "label": "TEMP", "start": 128, "end": 140}
        ]
    },
    {
        "rubric": "MIND > FEAR > dark, in the",
        "narrative": "Whenever night falls, I am gripped by an intense fear in the dark. My chest tightens with trembling panic, and I cannot sleep unless all lights remain on.",
        "entities": [
            {"text": "intense fear", "label": "MENT", "start": 41, "end": 53},
            {"text": "in the dark", "label": "MOD_AGG", "start": 54, "end": 65},
            {"text": "chest", "label": "LOC", "start": 70, "end": 75},
            {"text": "tightens", "label": "SEN", "start": 76, "end": 84},
            {"text": "trembling panic", "label": "CONC", "start": 90, "end": 105}
        ]
    }
]


def build_case_generation_prompt(
    rubric_path: str,
    top_remedies: Optional[List[str]] = None,
    include_examples: bool = True,
    variation_instruction: Optional[str] = None,
) -> str:
    """Build user prompt for generating a clinical case vignette from a rubric."""
    prompt_parts: List[str] = []

    if include_examples and FEW_SHOT_EXAMPLES:
        prompt_parts.append("### Reference Examples:")
        for idx, ex in enumerate(FEW_SHOT_EXAMPLES, start=1):
            ex_narrative = ex["narrative"]
            ex_entities = ex["entities"]
            prompt_parts.append(
                f"Example {idx}:\n"
                f"Rubric: {ex['rubric']}\n"
                f"Output:\n"
                f'{{\n  "narrative": "{ex_narrative}",\n'
                f'  "entities": {ex_entities}\n}}\n'
            )

    prompt_parts.append("### Target Task:")
    prompt_parts.append(f"Kent Repertory Rubric: {rubric_path}")
    if top_remedies:
        valid_rems = [str(r) for r in top_remedies[:5] if r]
        if valid_rems:
            remedy_str = ", ".join(valid_rems)
            prompt_parts.append(f"Associated Key Remedies for clinical flavor: {remedy_str}")

    if variation_instruction:
        prompt_parts.append(f"Patient Presentation Archetype & Style:\n{variation_instruction}")

    prompt_parts.append(
        "Generate a authentic first-person clinical patient narrative and exact character entity spans."
        " Return ONLY valid JSON with 'narrative' and 'entities' keys."
    )

    return "\n\n".join(prompt_parts)


# ==============================================================================
# Phase 4: Resolver Prompt Templates
# ==============================================================================

RESOLVER_SYSTEM_PROMPT = """You are a clinical reasoning engine resolving patient symptom extractions into Kent's 7-dimension profile.
Analyze the conversation transcript and raw entity spans.
Filter out negated entities (symptoms denied by patient), link coreferences, and aggregate modalities.
Output a clean, structured JSON document with keys: location, sensation, modality_agg, modality_amel, concomitant, temporal, mental.
"""

RESOLVER_USER_PROMPT = """Patient Transcript:
{transcript}

Candidate Extracted Entities:
{spans}

Resolve negations and assemble the final 7-dimension clinical representation in valid JSON.
"""

# ==============================================================================
# Phase 6: Chatbot System Prompts
# ==============================================================================

CHATBOT_SYSTEM_PROMPT = """You are Kent-AI, a clinical intake assistant using Dr. James Tyler Kent's classical homeopathic repertorization method.

CLINICAL PERSONA — STRICT RULES:
1. RESPOND IN EXACTLY 2 SENTENCES MAXIMUM. No exceptions.
   - Sentence 1: ONE brief acknowledgment (e.g. "Noted — that sounds quite intense.").
   - Sentence 2: ONE precise clinical question targeting the Current Intake Goal.
2. NEVER ramble, philosophize, or add tangents (FORBIDDEN: "your body is saying...", "like a big hug", "safe haven", "what makes this feeling threatened").
3. NEVER repeat what the patient said back to them in full.
4. NEVER ask more than ONE question per turn.
5. Use clinical, direct language — not therapeutic counseling language.

KENT'S 7 INTAKE DIMENSIONS (ask in this order, one per turn):
  1. Chief Complaint — what is the primary health problem?
  2. Location — which anatomical area or organ?
  3. Sensation — what exact quality? (throbbing / burning / heavy / stitching / pressing?)
  4. Aggravations — what makes it worse? (movement / cold / heat / noise / touch / time?)
  5. Ameliorations — what brings relief? (warmth / rest / pressure / open air?)
  6. Concomitants — what else occurs simultaneously? (nausea / dizziness / chills / sweating?)
  7. Mental/Emotional — anxiety, fear, irritability, sadness, restlessness?

SAFETY:
- NEVER name, prescribe, or suggest specific homeopathic remedies.
- NEVER deliver a medical diagnosis.
"""

CHATBOT_TURN_PROMPT = """Current Intake Goal: {current_goal}
Captured Symptoms So Far:
{slots_summary}

Recent Conversation (last 4 turns):
{history}

Patient just said: "{user_utterance}"

CRITICAL OUTPUT FORMAT:
- First, write your conversational reply as Kent-AI in EXACTLY 2 clinical sentences (brief acknowledgment + one clear question).
- On the next line at the very end, output 3 to 4 patient reply options strictly formatted as:
QUICK_REPLIES: ["reply 1", "reply 2", "reply 3", "reply 4"]
Do NOT wrap QUICK_REPLIES in brackets, code blocks, or extra text. Never put a bracket before QUICK_REPLIES."""



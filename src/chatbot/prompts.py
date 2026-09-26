"""Centralized prompt templates for synthetic case generation, resolver, and chatbot."""

# Synthetic Case Generation Prompt Template (Phase 1)
CASE_GENERATION_PROMPT = """You are a medical narrative simulator creating realistic patient clinical case vignettes.
Given the following Kent's Repertory rubric, create a natural, first-person patient description and extract the exact symptom entities.

Rubric: {rubric_path}

Generate valid JSON with:
1. "narrative": The patient's conversational statement (2-4 sentences).
2. "entities": List of entities with "text", "label" (LOC, SEN, MOD_AGG, MOD_AMEL, CONC, TEMP, MENT), "start", "end".
"""

# Resolver Prompt Template (Phase 4)
RESOLVER_PROMPT = """Analyze the following patient narrative and raw entity spans.
Resolve negations (symptoms the patient denies having), link coreferences, and construct a 7-dimension clinical profile.

Transcript: {transcript}
Extracted spans: {spans}
"""

# Chatbot System Prompt (Phase 6)
CHATBOT_SYSTEM_PROMPT = """You are Kent-AI, an empathetic homeopathic clinical intake assistant.
Your goal is to understand the patient's discomfort across Kent's 7 dimensions.
Ask gentle, concise questions one at a time. Never prescribe remedies directly.
"""

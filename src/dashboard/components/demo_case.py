"""Demo Case loader for Kent-AI clinical evaluation (Phase 9 & UI Overhaul).

Provides realistic demonstration clinical cases for testing Review, Analysis,
and Repertorization without waiting for local LLM inference.
"""

from __future__ import annotations

from typing import Any, Dict
from src.models.case import ClinicalCase


def create_demo_case() -> ClinicalCase:
    """Create a realistic MIND demonstration case with 6/7 totality dimensions."""
    case = ClinicalCase(
        case_id="DEMO-MIND-001",
        patient_name="Demo Patient (Nocturnal Anxiety)",
        patient_age=38,
        patient_sex="Female",
        chief_complaint="Episodic nocturnal panic attacks with violent heart palpitations",
        clinical_summary="38-year-old female presenting with acute nocturnal anxiety and restlessness, worse alone and between 1 AM and 3 AM, ameliorated by moving in cool open air.",
        scope_chapter="MIND",
    )
    case.add_symptom("mental", "fear of darkness and death, intense restlessness when alone")
    case.add_symptom("location", "precordial chest and head")
    case.add_symptom("sensation", "violent palpitations, suffocative constriction in chest")
    case.add_symptom("modality_agg", "worse alone, worse warm closed room, worse after midnight")
    case.add_symptom("modality_amel", "better open fresh air, better walking about slowly")
    case.add_symptom("temporal", "after midnight, 1 AM to 3 AM")

    case.extraction_meta = {
        "source": "demo",
        "is_demo": True,
        "items": {
            "mental": [{"text": "fear of darkness and death", "confidence": 0.96}],
            "location": [{"text": "precordial chest and head", "confidence": 0.92}],
            "sensation": [{"text": "violent palpitations", "confidence": 0.94}],
            "modality_agg": [{"text": "worse alone", "confidence": 0.95}],
            "modality_amel": [{"text": "better open fresh air", "confidence": 0.91}],
            "temporal": [{"text": "after midnight", "confidence": 0.89}],
        },
    }
    return case


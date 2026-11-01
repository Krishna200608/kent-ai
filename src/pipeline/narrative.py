"""Clinical narrative processing helpers for chief complaint and totality completeness."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, List

from src.dashboard.dimensions import KENT_DIMENSIONS_ORDERED

if TYPE_CHECKING:
    from src.models.case import ClinicalCase


def derive_chief_complaint(text: str, profile_chief_complaint: str = "") -> str:
    """Derive a concise chief complaint string from SymptomProfile or raw text narrative.

    Preferences:
        1. Non-empty profile_chief_complaint (if provided).
        2. First sentence of text, stripped of clinician/doctor greetings,
           max 100 characters, whitespace collapsed, cut cleanly at a word boundary
           with an ellipsis if truncated.

    Args:
        text: Clinical narrative text entered by user.
        profile_chief_complaint: Pre-extracted chief complaint from SymptomProfile.

    Returns:
        Formatted chief complaint string (max 100 chars plus optional ellipsis).
    """
    if profile_chief_complaint and profile_chief_complaint.strip():
        cleaned_prof = " ".join(profile_chief_complaint.strip().split())
        if len(cleaned_prof) <= 100:
            return cleaned_prof
        truncated = cleaned_prof[:100]
        if " " in truncated:
            truncated = truncated.rsplit(" ", 1)[0]
        return truncated.rstrip(".,;:- ") + "..."

    if not text or not text.strip():
        return ""

    cleaned = text.strip()
    # Strip greetings like "Doctor,", "Dear Doctor,", "Hello doctor,"
    cleaned = re.sub(
        r"^(?:hello|hi|dear)?\s*(?:doctor|dr\.?)\s*[,:\-–—]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # Extract first sentence
    sentences = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    first_sentence = sentences[0].strip() if sentences else cleaned
    first_sentence = " ".join(first_sentence.split())

    if len(first_sentence) <= 100:
        return first_sentence

    cut = first_sentence[:100]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;:- ") + "..."


def missing_recommended_dimensions(case: ClinicalCase) -> List[str]:
    """Identify recommended symptom dimensions in Kent's totality that remain uncaptured.

    Uses `src.dashboard.dimensions.KENT_DIMENSIONS_ORDERED` as the single canonical
    source of truth.

    Args:
        case: Active ClinicalCase instance.

    Returns:
        List of human-readable labels for recommended dimensions that are still empty.
    """
    missing: List[str] = []
    for dim in KENT_DIMENSIONS_ORDERED:
        if dim.is_recommended:
            vals = case.dimensions.get(dim.key, [])
            if not vals:
                missing.append(dim.label)
    return missing

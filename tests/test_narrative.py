"""Unit tests for clinical narrative helpers (chief complaint derivation and missing dimensions)."""

from __future__ import annotations

import pytest

from src.models.case import ClinicalCase
from src.pipeline.narrative import derive_chief_complaint, missing_recommended_dimensions


def test_derive_chief_complaint_prefers_profile():
    """Verify that a non-empty profile_chief_complaint takes precedence over narrative text."""
    narrative = "Patient reports constant dull headache for two weeks."
    profile_cc = "Severe temporal migraine"
    result = derive_chief_complaint(narrative, profile_chief_complaint=profile_cc)
    assert result == "Severe temporal migraine"


def test_derive_chief_complaint_strips_greetings():
    """Verify greetings like 'Doctor,', 'Dear Doctor,', 'Hello doctor' are stripped."""
    text1 = "Doctor, I feel terribly anxious and depressed every morning."
    assert derive_chief_complaint(text1) == "I feel terribly anxious and depressed every morning."

    text2 = "Dear Doctor: Patient is suffering from sharp stabbing stomach pains."
    assert derive_chief_complaint(text2) == "Patient is suffering from sharp stabbing stomach pains."

    text3 = "Hello Dr. Arya, severe throbbing in temples worse from noise."
    # Matches 'Hello Dr.' prefix
    assert "severe throbbing in temples" in derive_chief_complaint(text3).lower()


def test_derive_chief_complaint_first_sentence_and_max_100_chars():
    """Verify extraction takes the first sentence, caps at 100 chars at word boundary with ellipsis."""
    # Multi-sentence
    multi = "First sentence about sharp knee pain. Second sentence about sleep."
    assert derive_chief_complaint(multi) == "First sentence about sharp knee pain."

    # Sentence longer than 100 chars
    long_sentence = (
        "Patient presents with an exceedingly prolonged and debilitating chronic bilateral cephalalgia "
        "accompanied by intense photophobia and vertigo that prevents working"
    )
    res = derive_chief_complaint(long_sentence)
    assert len(res) <= 104  # 100 + ellipsis
    assert res.endswith("...")
    # Cut at word boundary (no broken words)
    without_dots = res[:-3]
    assert not without_dots.endswith(" ")
    assert without_dots in long_sentence


def test_derive_chief_complaint_empty():
    """Verify empty or whitespace strings return empty string."""
    assert derive_chief_complaint("") == ""
    assert derive_chief_complaint("   ") == ""


def test_missing_recommended_dimensions():
    """Verify identifying uncaptured recommended dimensions against dimensions.py."""
    case = ClinicalCase()
    # On fresh case, both modality_amel and temporal are recommended and empty
    missing = missing_recommended_dimensions(case)
    assert "Better from (amelioration)" in missing
    assert "Time pattern" in missing

    # Fill modality_amel
    case.add_symptom("modality_amel", "better with warm drinks")
    missing_after = missing_recommended_dimensions(case)
    assert "Better from (amelioration)" not in missing_after
    assert "Time pattern" in missing_after

    # Fill temporal
    case.add_symptom("temporal", "worse at 3 AM")
    assert missing_recommended_dimensions(case) == []

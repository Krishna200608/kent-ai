"""Unit tests for clinical safety screening and red flag detection with negation awareness."""

from __future__ import annotations

import pytest

from src.pipeline.safety import screen_red_flags


def test_safety_positives_per_category():
    """Verify detection of representative positive matches across all 5 red flag categories."""
    cases = [
        ("Patient expresses suicidal ideation and wanting to end life.", "Self-harm or suicidal ideation"),
        ("Patient has sudden onset of crushing chest pain radiating to left arm.", "Chest pain"),
        ("Patient is gasping for air and has severe shortness of breath.", "Breathing difficulty"),
        ("Patient had a sudden convulsion and lost consciousness for two minutes.", "Loss of consciousness or seizure"),
        ("Patient presents with vomiting blood and profuse bleeding.", "Severe bleeding"),
    ]
    for text, expected_category in cases:
        flags = screen_red_flags(text)
        assert len(flags) >= 1, f"Expected red flag for: {text}"
        assert any(f.category == expected_category for f in flags)


def test_safety_negation_awareness():
    """Verify that negated occurrences within 4 tokens do NOT trigger red flags."""
    negated_cases = [
        "Patient has mild cough, but denies chest pain or palpitation.",
        "Reports chronic headache with no chest pain.",
        "Patient is depressed but denies suicidal thoughts or intent.",
        "Has fever and fatigue, without shortness of breath or breathing difficulty.",
        "Reports dizziness, but never lost consciousness or had a seizure.",
        "Complains of stomach pain, with no severe bleeding observed.",
    ]
    for text in negated_cases:
        flags = screen_red_flags(text)
        assert len(flags) == 0, f"Expected no flags for negated text: '{text}', got: {flags}"


def test_safety_no_false_positives_on_standard_vignettes():
    """Verify the four canonical clinical vignettes do not trigger any false-positive red flags."""
    vignettes = [
        "Doctor, I feel terribly anxious and depressed every morning, worse when alone. My thoughts race with fear and dread. I have no fever and no nausea.",
        "Patient complains of extreme absent-mindedness and difficulty concentrating, especially in the morning after waking up, with trembling hands and restless pacing.",
        "Patient reports overwhelming fear in the dark and in crowded places. Weeps easily upon any emotional upset, feels completely forsaken and abandoned, relieved by fresh open air.",
        "Patient is exceedingly irritable, cannot bear contradiction or noise, full of wrath and quick to anger over trifles, intensely restless at night.",
    ]
    for text in vignettes:
        flags = screen_red_flags(text)
        assert len(flags) == 0, f"False positive flag detected on vignette: {flags}"

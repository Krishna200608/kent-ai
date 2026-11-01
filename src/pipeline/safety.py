"""Clinical safety screening for acute red flags and urgent triage patterns.

# PENDING CLINICAL REVIEW BY SUPERVISOR
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

# PENDING CLINICAL REVIEW BY SUPERVISOR
RED_FLAG_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    (
        "Self-harm or suicidal ideation",
        re.compile(
            r"\b(suicid(?:e|al)|kill(?:ing)?\s+myself|end(?:ing)?\s+my\s+life|self[- ]harm|want\s+to\s+die)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Chest pain",
        re.compile(
            r"\b(chest\s+pain|pain\s+in\s+(?:the\s+)?chest|angina|cardiac\s+pain|crushing\s+chest\s+pressure)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Breathing difficulty",
        re.compile(
            r"\b(can'?t\s+breathe|cannot\s+breathe|gasping\s+for\s+air|severe\s+shortness\s+of\s+breath|respiratory\s+distress|stridor)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Loss of consciousness or seizure",
        re.compile(
            r"\b(lost\s+consciousness|blacked?\s+out|unconscious(?:ness)?|seizure|convulsion|fainted|syncope)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Severe bleeding",
        re.compile(
            r"\b(severe\s+bleeding|coughing\s+up\s+blood|hemorrhag(?:e|ic)|vomiting\s+blood|profuse\s+bleeding)\b",
            re.IGNORECASE,
        ),
    ),
]

NEGATION_CUES = frozenset(
    [
        "no",
        "not",
        "denies",
        "denied",
        "without",
        "never",
        "none",
        "ruled out",
        "rules out",
        "zero",
    ]
)


@dataclass(frozen=True)
class RedFlag:
    """Clinical red flag screening match for urgent evaluation."""

    category: str
    snippet: str

    def to_dict(self) -> dict[str, str]:
        """Convert to JSON-serializable dictionary."""
        return {"category": self.category, "snippet": self.snippet}


def _is_negated_match(text: str, start_pos: int) -> bool:
    """Check if a match at start_pos is preceded by a negation cue within preceding tokens."""
    preceding_text = text[:start_pos].rstrip()
    if not preceding_text:
        return False

    # Extract tokens from the preceding text (word tokens only)
    tokens = re.findall(r"\b[\w']+\b", preceding_text)
    if not tokens:
        return False

    # Check the preceding tokens (up to 6 tokens to cover compound negations like 'never lost consciousness or had a seizure')
    recent_tokens = [t.lower() for t in tokens[-6:]]
    for cue in NEGATION_CUES:
        if cue in recent_tokens:
            return True
        # Multi-word cues like "ruled out"
        cue_parts = cue.split()
        if len(cue_parts) > 1 and len(recent_tokens) >= len(cue_parts):
            for i in range(len(recent_tokens) - len(cue_parts) + 1):
                if recent_tokens[i : i + len(cue_parts)] == cue_parts:
                    return True
    return False


def screen_red_flags(text: str) -> List[RedFlag]:
    """Screen clinical narrative for urgent red flag patterns with negation awareness.

    Non-diagnostic: returns matched categories and snippets for clinician awareness.

    Args:
        text: Clinical narrative entered by the user.

    Returns:
        List of RedFlag instances detected in the text.
    """
    if not text or not text.strip():
        return []

    flags: List[RedFlag] = []
    seen_categories: set[str] = set()

    for category, pattern in RED_FLAG_PATTERNS:
        for match in pattern.finditer(text):
            start = match.start()
            if _is_negated_match(text, start):
                continue

            if category not in seen_categories:
                seen_categories.add(category)
                # Extract snippet: 30 chars before and after match, aligned to word boundaries
                snippet_start = max(0, start - 25)
                snippet_end = min(len(text), match.end() + 25)
                raw_snippet = text[snippet_start:snippet_end].strip()
                # Clean up leading/trailing incomplete words if sliced mid-word
                snippet = " ".join(raw_snippet.split())
                flags.append(RedFlag(category=category, snippet=snippet))
                break  # Record one representative snippet per category

    return flags

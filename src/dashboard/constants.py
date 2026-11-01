"""Single source of truth for Kent-AI clinical decision-support constants (Phase 14 & UI Overhaul).

Holds:
- 7 canonical dimensions (key, label, hint, order, recommended flag, paramount flag)
- Repertory grade weights and typography conventions
- Repertory scope definitions and rubric counts
- Configured LLM model display name and git version
- Formatting helpers for breadcrumbs and labels
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
from typing import Dict, List, Optional
import yaml


# -----------------------------------------------------------------------------
# App Version & Git Short SHA
# -----------------------------------------------------------------------------
APP_VERSION = "2.0.0"


def _get_git_sha() -> str:
    """Retrieve current git short SHA or fallback to fixed release tag."""
    try:
        root = Path(__file__).resolve().parent.parent.parent
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
            timeout=1.0,
        )
        return out.decode("ascii").strip()
    except Exception:
        return "81da876"


GIT_SHA = _get_git_sha()


# -----------------------------------------------------------------------------
# Configured Model Display Name (derived from configs/chatbot.yaml)
# -----------------------------------------------------------------------------
def _load_model_display_name() -> str:
    """Derive clean human-readable model name from configured chatbot.yaml."""
    cfg_path = Path(__file__).resolve().parent.parent.parent / "configs" / "chatbot.yaml"
    model_raw = "llama3:8b"
    if cfg_path.is_file():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                model_raw = data.get("chatbot", {}).get("model", model_raw)
        except Exception:
            pass

    # Normalize e.g. "llama3:8b" -> "Llama 3 8B", "llama3.1:8b" -> "Llama 3.1 8B"
    if "llama3.1" in model_raw.lower():
        return "Llama 3.1 8B"
    elif "llama3" in model_raw.lower():
        return "Llama 3 8B"
    elif "biomistral" in model_raw.lower():
        return "BioMistral 7B"
    elif "qwen" in model_raw.lower():
        return "Qwen 2.5 7B"
    return model_raw.replace(":", " ").title()


MODEL_DISPLAY_NAME = _load_model_display_name()


# -----------------------------------------------------------------------------
# Repertory Grade Weights & Repertory Conventions
# Grade 3 = bold, Grade 2 = italic, Grade 1 = roman
# -----------------------------------------------------------------------------
GRADE_WEIGHTS: Dict[int, float] = {
    3: 3.0,
    2: 2.0,
    1: 1.0,
}

GRADE_LABELS: Dict[int, str] = {
    3: "Grade 3 (Bold · Confirmed)",
    2: "Grade 2 (Italic · Qualified)",
    1: "Grade 1 (Roman · Observed)",
}


# -----------------------------------------------------------------------------
# Scope Definitions (Single Source of Truth)
# -----------------------------------------------------------------------------
SCOPE_MIND = "MIND focus"
SCOPE_ALL = "All chapters"

SCOPE_MIND_COUNT = 4933
SCOPE_ALL_COUNT = 74513

SCOPE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    SCOPE_MIND: {
        "label": "MIND focus",
        "short_label": "MIND",
        "count": SCOPE_MIND_COUNT,
        "caption": f"4,933 rubrics",
        "full_label": "MIND Chapter Focus (4,933 rubrics)",
        "chapter_id": 1,
    },
    SCOPE_ALL: {
        "label": "All chapters",
        "short_label": "All Chapters",
        "count": SCOPE_ALL_COUNT,
        "caption": f"74,513 rubrics",
        "full_label": "All 37 Chapters (74,513 rubrics)",
        "chapter_id": None,
    },
}


# -----------------------------------------------------------------------------
# Specificity Tag Thresholds
# -----------------------------------------------------------------------------
SPECIFICITY_SPECIFIC_MAX = 20
SPECIFICITY_BROAD_MIN = 80


# -----------------------------------------------------------------------------
# 7 Canonical Symptom Dimensions
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class CanonicalDimension:
    """Canonical clinical symptom dimension specification."""

    key: str
    label: str
    hint: str
    code: str
    internal_key: str
    is_recommended: bool = False
    is_paramount: bool = False


# Canonical Dimension Master Reference
CANONICAL_DIMENSIONS_ORDERED: List[CanonicalDimension] = [
    CanonicalDimension(
        key="mental",
        label="Mental/Emotional",
        hint="Mood, fears, behaviour",
        code="MENT",
        internal_key="mental",
        is_recommended=True,
        is_paramount=True,
    ),
    CanonicalDimension(
        key="location",
        label="Location",
        hint="Where in the body",
        code="LOC",
        internal_key="location",
        is_recommended=False,
    ),
    CanonicalDimension(
        key="sensation",
        label="Sensation",
        hint="What it feels like",
        code="SEN",
        internal_key="sensation",
        is_recommended=False,
    ),
    CanonicalDimension(
        key="worse",
        label="Worse from",
        hint="What aggravates it",
        code="MOD_AGG",
        internal_key="modality_agg",
        is_recommended=False,
    ),
    CanonicalDimension(
        key="better",
        label="Better from",
        hint="What relieves it",
        code="MOD_AMEL",
        internal_key="modality_amel",
        is_recommended=True,
    ),
    CanonicalDimension(
        key="concomitant",
        label="Concomitants",
        hint="Accompanying symptoms",
        code="CONC",
        internal_key="concomitant",
        is_recommended=False,
    ),
    CanonicalDimension(
        key="time",
        label="Time pattern",
        hint="When it occurs",
        code="TEMP",
        internal_key="temporal",
        is_recommended=True,
    ),
]

# Quick key-to-dimension mapping
CANONICAL_DIMENSION_MAP: Dict[str, CanonicalDimension] = {
    d.key: d for d in CANONICAL_DIMENSIONS_ORDERED
}
INTERNAL_TO_CANONICAL: Dict[str, str] = {
    d.internal_key: d.key for d in CANONICAL_DIMENSIONS_ORDERED
}
CANONICAL_TO_INTERNAL: Dict[str, str] = {
    d.key: d.internal_key for d in CANONICAL_DIMENSIONS_ORDERED
}
# Map legacy/internal database keys to canonical dimensions
for d in CANONICAL_DIMENSIONS_ORDERED:
    CANONICAL_DIMENSION_MAP[d.internal_key] = d


def get_canonical_dimensions(scope: str = SCOPE_MIND) -> List[CanonicalDimension]:
    """Return ordered canonical dimensions according to repertory scope.

    When scope is MIND, Mental/Emotional is ordered first and marked paramount.
    When scope is All Chapters, anatomical/physical order is used.
    """
    is_mind = "mind" in str(scope).lower()
    if is_mind:
        # Mental/Emotional first, then physical and modalities
        return CANONICAL_DIMENSIONS_ORDERED
    else:
        # Standard physical-generals sequence: Location, Sensation, Worse, Better, Concomitant, Time, Mental
        order = ["location", "sensation", "worse", "better", "concomitant", "time", "mental"]
        return [CANONICAL_DIMENSION_MAP[k] for k in order]


# -----------------------------------------------------------------------------
# Rubric Hierarchy Path Formatter
# Resolves breadcrumbs with ' › ' and repairs dropped trailing dot (e.g. '4 a.m' -> '4 a.m.')
# -----------------------------------------------------------------------------
_TIME_ABBR_RE = re.compile(r"\b([0-9]{1,2}(?::[0-9]{2})?\s*(?:a\.m|p\.m))\b(?!\.)", re.IGNORECASE)


def format_rubric_path(path: str) -> str:
    """Format repertory hierarchy path with ' › ' breadcrumbs and repair OCR trailing time dots.

    Does not mutate underlying database or data objects; runs solely at render time.
    Examples:
    - 'MIND > ANXIETY > night > 4 a.m' -> 'MIND › ANXIETY › night › 4 a.m.'
    - 'HEAD > PAIN > forehead' -> 'HEAD › PAIN › forehead'
    """
    if not path:
        return ""

    p = str(path).strip()
    # Normalize chevron separators
    p = p.replace(" > ", " › ").replace(">", " › ")
    # Clean redundant spaces around breadcrumb
    p = re.sub(r"\s*›\s*", " › ", p)

    # Repair dropped trailing dot on time abbreviations e.g. "4 a.m" -> "4 a.m."
    p = _TIME_ABBR_RE.sub(r"\1.", p)

    return p

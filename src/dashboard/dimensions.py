"""Canonical dimension metadata, terminology mappings, and pluralization helpers.

Single source of truth for clinical symptom dimensions across all Kent-AI dashboard workspaces.
Zero hardcoded dimension labels should exist outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class DimensionMeta:
    """Canonical clinical metadata for a Kent-AI symptom dimension."""

    key: str
    code: str
    label: str
    captures: str
    example: str
    badge_class: str
    canonical: str = ""

    @property
    def tooltip(self) -> str:
        """Formatted tooltip text for HUD tiles and chips."""
        return f"{self.label} ({self.code}): {self.captures}&#10;Example: \"{self.example}\""


# Canonical Dimension Reference (source of truth for wording across all tabs)
DIMENSION_MAP: Dict[str, DimensionMeta] = {
    "location": DimensionMeta(
        key="location",
        code="LOC",
        label="Location",
        captures="Body part/region",
        example="Right side of head",
        badge_class="badge-loc",
        canonical="Location",
    ),
    "sensation": DimensionMeta(
        key="sensation",
        code="SEN",
        label="Sensation",
        captures="Type of feeling",
        example="Pressing, throbbing, burning",
        badge_class="badge-sen",
        canonical="Sensation",
    ),
    "modality_agg": DimensionMeta(
        key="modality_agg",
        code="MOD_AGG",
        label="Worse from (aggravation)",
        captures="Aggravating factors or triggers",
        example="Worse in morning, worse cold, worse movement",
        badge_class="badge-agg",
        canonical="Modality",
    ),
    "modality_amel": DimensionMeta(
        key="modality_amel",
        code="MOD_AMEL",
        label="Better from (amelioration)",
        captures="Relieving or soothing factors",
        example="Better by pressure, better fresh open air",
        badge_class="badge-amel",
        canonical="Modality",
    ),
    "concomitant": DimensionMeta(
        key="concomitant",
        code="CONC",
        label="Concomitant",
        captures="Accompanying symptoms",
        example="With nausea and anxiety",
        badge_class="badge-conc",
        canonical="Concomitant",
    ),
    "temporal": DimensionMeta(
        key="temporal",
        code="TEMP",
        label="Time pattern",
        captures="Time patterns and periodicity",
        example="Worse at midnight, periodic",
        badge_class="badge-temp",
        canonical="Temporality",
    ),
    "mental": DimensionMeta(
        key="mental",
        code="MENT",
        label="Mental/Emotional",
        captures="Psychological state",
        example="Irritable, restless at night",
        badge_class="badge-ment",
        canonical="Mental/Emotional",
    ),
}

# Ordered tuple representation for sequential HUD and list rendering
KENT_DIMENSIONS_ORDERED: List[DimensionMeta] = list(DIMENSION_MAP.values())


def get_dimension(key: str) -> Optional[DimensionMeta]:
    """Retrieve canonical metadata for a symptom dimension key."""
    return DIMENSION_MAP.get(key)


def get_dimension_by_code(code: str) -> Optional[DimensionMeta]:
    """Retrieve canonical metadata by 3-4 letter uppercase dimension code."""
    for dim in DIMENSION_MAP.values():
        if dim.code == code:
            return dim
    return None


def get_engine_dimensions_summary() -> str:
    """Return formatted list of the 7 backend-extracted dimensions for Engine description."""
    labels = [d.label for d in KENT_DIMENSIONS_ORDERED]
    if len(labels) > 1:
        return ", ".join(labels[:-1]) + ", and " + labels[-1]
    return labels[0] if labels else ""


def pluralize(count: int, singular: str, plural: str, include_count: bool = True) -> str:
    """Format count with correct singular/plural inflection.

    Examples:
        pluralize(1, "remedy", "remedies") -> "1 remedy"
        pluralize(5, "remedy", "remedies") -> "5 remedies"
        pluralize(1, "rubric", "rubrics", include_count=False) -> "rubric"
        pluralize(0, "rubric", "rubrics", include_count=True) -> "0 rubrics"
    """
    word = singular if count == 1 else plural
    return f"{count} {word}" if include_count else word

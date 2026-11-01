"""Curated clinical vignettes for demonstration, testing, and one-click intake pre-population."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ClinicalVignette:
    """Pre-curated clinical consultation vignette for rapid testing and intake."""

    id: str
    title: str
    narrative: str
    description: str = ""


CLINICAL_VIGNETTES: List[ClinicalVignette] = [
    ClinicalVignette(
        id="case-1",
        title="Severe anxiety in morning, worse alone (MIND)",
        narrative=(
            "Doctor, I feel terribly anxious and depressed every morning, worse when alone. "
            "My thoughts race with fear and dread. I have no fever and no nausea."
        ),
        description="Morning anxiety aggravation with fear when alone; physical negatives explicitly noted.",
    ),
    ClinicalVignette(
        id="case-2",
        title="Absent-minded & forgetful on waking (MIND)",
        narrative=(
            "Patient complains of extreme absent-mindedness and difficulty concentrating, "
            "especially in the morning after waking up, with trembling hands and restless pacing."
        ),
        description="Cognitive clouding and forgetfulness on waking with restless physical tremors.",
    ),
    ClinicalVignette(
        id="case-3",
        title="Fear of dark & crowds with weeping (MIND)",
        narrative=(
            "Patient reports overwhelming fear in the dark and in crowded places. "
            "Weeps easily upon any emotional upset, feels completely forsaken and abandoned, "
            "relieved by fresh open air."
        ),
        description="Agoraphobia and fear of dark with tearfulness and open air amelioration.",
    ),
    ClinicalVignette(
        id="case-4",
        title="Extreme irritability & impatience with anger (MIND)",
        narrative=(
            "Patient is exceedingly irritable, cannot bear contradiction or noise, "
            "full of wrath and quick to anger over trifles, intensely restless at night."
        ),
        description="Hypersensitive irritability, anger on contradiction, and nocturnal restlessness.",
    ),
]

VIGNETTE_MAP: Dict[str, ClinicalVignette] = {v.title: v for v in CLINICAL_VIGNETTES}


def get_vignette_by_title(title: str) -> Optional[ClinicalVignette]:
    """Retrieve a vignette by its exact display title."""
    return VIGNETTE_MAP.get(title)

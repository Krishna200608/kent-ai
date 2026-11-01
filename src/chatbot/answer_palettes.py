"""Clinical answer palettes for guided symptom intake (Phase 14 / WP-C3).

Provides standardized, Kentian-aligned multi-select vocabulary palettes
for active dialogue states.

# PENDING CLINICAL REVIEW BY SUPERVISOR
"""

from __future__ import annotations

from typing import Dict, List
from src.chatbot.state_machine import IntakeState

# PENDING CLINICAL REVIEW BY SUPERVISOR
PALETTES: Dict[IntakeState, List[str]] = {
    IntakeState.LOCATION: [
        "Head & Temples",
        "Forehead & Vertex",
        "Eyes & Vision",
        "Throat & Larynx",
        "Chest & Respiratory",
        "Stomach & Epigastrium",
        "Abdomen & Bowels",
        "Lower Back & Spine",
        "Knees & Ankles",
        "Hands & Wrists",
    ],
    IntakeState.SENSATION: [
        "Throbbing & Pulsating",
        "Burning & Heat",
        "Sharp & Stabbing",
        "Dull Heaviness & Pressure",
        "Stitching & Pricking",
        "Tightness & Constriction",
        "Cramping & Spasmodic",
        "Numbness & Tingling",
    ],
    IntakeState.MODALITY: [
        "Worse from Motion",
        "Worse in Cold Air / Draft",
        "Worse in Heat / Warm Room",
        "Worse from Touch / Pressure",
        "Better from Absolute Rest",
        "Better from Warm Applications",
        "Better from Cold Compresses",
        "Better in Open Fresh Air",
    ],
    IntakeState.CONCOMITANT: [
        "Nausea & Retching",
        "Dizziness & Vertigo",
        "Chills & Shivering",
        "Cold Perspiration",
        "Great Weakness & Prostration",
        "Trembling & Shaking",
    ],
    IntakeState.TEMPORAL: [
        "Morning on Waking",
        "Forenoon (10-11 AM)",
        "Afternoon (3-5 PM)",
        "Evening (6-9 PM)",
        "Night after Midnight (2-3 AM)",
        "Periodic / Fixed Interval",
    ],
    IntakeState.MENTAL: [
        "Restless & Anxious",
        "Irritable & Easily Angered",
        "Weeping & Tearful",
        "Depressed & Low Spirits",
        "Fearful when Alone",
        "Apathetic & Indifferent",
    ],
}


def get_palette_for_state(state: IntakeState) -> List[str]:
    """Retrieve structured vocabulary palette for an intake state."""
    return list(PALETTES.get(state, []))


"""Single Source of Truth: Typed Clinical Case Object for Kent-AI.

Ensures seamless state consistency between Intake, Review, Repertorization, and Report.
No re-parsing from concatenated chat transcripts — all downstream scoring and retrieval
consume the validated, typed case directly.
"""

from __future__ import annotations

import datetime
import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


CANONICAL_DIMENSIONS = [
    "location",
    "sensation",
    "modality_agg",
    "modality_amel",
    "concomitant",
    "temporal",
    "mental",
]


@dataclass
class ClinicalCase:
    """Canonical patient consultation and homeopathic repertorization case."""

    case_id: str = field(
        default_factory=lambda: f"CASE-{datetime.date.today().year}-{uuid.uuid4().hex[:4].upper()}"
    )
    patient_name: str = "Anonymous Patient"
    patient_age: Optional[int] = None
    patient_sex: Optional[str] = None  # "Female", "Male", "Other", or None
    chief_complaint: str = ""
    status: str = "intake"  # "intake", "review", "analysis", "completed"
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    # 7 Kentian Dimensions (each is a list of multi-value strings)
    dimensions: Dict[str, List[str]] = field(
        default_factory=lambda: {k: [] for k in CANONICAL_DIMENSIONS}
    )

    # Conversational narrative and history
    transcript: str = ""
    dialogue_history: List[Dict[str, str]] = field(default_factory=list)

    # Manual or pipeline selected rubrics
    selected_rubric_ids: List[int] = field(default_factory=list)
    muted_rubric_ids: List[int] = field(default_factory=list)
    eliminatory_rubric_ids: List[int] = field(default_factory=list)

    # Consultation preferences & filters
    scope_chapter: Optional[str] = "MIND"  # "MIND" or None for all 37
    ranking_mode: str = "totality"  # "totality" (hits then score), "score", "coverage"

    # Serialized or attached PatientReport dict
    report_data: Optional[Dict[str, Any]] = None
    clinical_notes: str = ""
    clinical_summary: str = ""

    def __post_init__(self) -> None:
        # Guarantee all 7 dimensions exist as lists
        if not self.dimensions:
            self.dimensions = {k: [] for k in CANONICAL_DIMENSIONS}
        for k in CANONICAL_DIMENSIONS:
            if k not in self.dimensions or not isinstance(self.dimensions[k], list):
                self.dimensions[k] = list(self.dimensions.get(k, []))

    @property
    def section_id(self) -> Optional[int]:
        """Return Kent database section ID (1 for MIND, None for all chapters)."""
        if self.scope_chapter and "MIND" in self.scope_chapter.upper():
            return 1
        return None

    @property
    def demographics_string(self) -> str:
        """Formatted demographics string e.g. '35 yrs | Female' or 'Demographics unspecified'."""
        parts = []
        if self.patient_age is not None:
            parts.append(f"{self.patient_age} yrs")
        if self.patient_sex:
            parts.append(self.patient_sex)
        return " | ".join(parts) if parts else "Demographics unspecified"

    @property
    def filled_dimensions_count(self) -> int:
        """Count how many of the 7 Kent dimensions contain at least one symptom."""
        return sum(1 for k in CANONICAL_DIMENSIONS if self.dimensions.get(k))

    @property
    def total_symptoms_count(self) -> int:
        """Total number of symptom phrases captured across all dimensions."""
        return sum(len(self.dimensions.get(k, [])) for k in CANONICAL_DIMENSIONS)

    @property
    def is_ready_for_repertorization(self) -> bool:
        """A case is eligible for repertorization if at least 1 dimension is captured."""
        return self.filled_dimensions_count >= 1

    @property
    def is_blank(self) -> bool:
        """True when no dimensions are filled, no chief complaint, no transcript, and patient_name is 'Anonymous Patient'."""
        has_dims = any(bool(v) for v in self.dimensions.values())
        has_complaint = bool(self.chief_complaint and self.chief_complaint.strip())
        has_transcript = bool(self.transcript and self.transcript.strip())
        is_default_name = (self.patient_name or "").strip() == "Anonymous Patient"
        return not has_dims and not has_complaint and not has_transcript and is_default_name

    def add_symptom(self, dimension: str, text: str) -> None:
        """Add a symptom to a dimension, avoiding case-insensitive duplicates."""
        dim_key = dimension.lower().strip()
        cleaned_text = text.strip()
        if not cleaned_text:
            return
        if dim_key in self.dimensions:
            existing = [v.lower() for v in self.dimensions[dim_key]]
            if cleaned_text.lower() not in existing:
                self.dimensions[dim_key].append(cleaned_text)
                self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def remove_symptom(self, dimension: str, text: str) -> None:
        """Remove a symptom from a dimension."""
        dim_key = dimension.lower().strip()
        target = text.strip().lower()
        if dim_key in self.dimensions:
            self.dimensions[dim_key] = [
                v for v in self.dimensions[dim_key] if v.strip().lower() != target
            ]
            self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def set_dimension_values(self, dimension: str, values: List[str]) -> None:
        """Overwrite the list of symptoms for a given dimension."""
        dim_key = dimension.lower().strip()
        if dim_key in self.dimensions:
            # Deduplicate preserving order
            seen = set()
            clean_list = []
            for v in values:
                s = str(v).strip()
                if s and s.lower() not in seen:
                    seen.add(s.lower())
                    clean_list.append(s)
            self.dimensions[dim_key] = clean_list
            self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def get_search_queries(self) -> List[str]:
        """Synthesize high-yield rubric search queries directly from captured dimensions.

        Combines mental/emotional generals with specific physical modalities and sensations.
        """
        queries: List[str] = []

        # 1. Mental generals
        for m in self.dimensions.get("mental", []):
            queries.append(f"mind {m}")

        # 2. Location + Sensation combos
        locs = self.dimensions.get("location", [])
        sens = self.dimensions.get("sensation", [])
        for loc in locs:
            for s in sens:
                queries.append(f"{loc} {s}")

        # 3. Aggravation and Amelioration modalities
        for agg in self.dimensions.get("modality_agg", []):
            for loc in locs or ["general"]:
                queries.append(f"{loc} worse {agg}")

        for amel in self.dimensions.get("modality_amel", []):
            for loc in locs or ["general"]:
                queries.append(f"{loc} better {amel}")

        # 4. Temporal modalities
        for temp in self.dimensions.get("temporal", []):
            queries.append(f"time {temp}")

        # 5. Concomitants
        for conc in self.dimensions.get("concomitant", []):
            queries.append(f"concomitant {conc}")

        # Fallback to individual items if combinations were empty
        if not queries:
            for k in CANONICAL_DIMENSIONS:
                for item in self.dimensions.get(k, []):
                    queries.append(item)

        # Deduplicate queries preserving order
        unique_queries = []
        seen_q = set()
        for q in queries:
            q_clean = q.strip().lower()
            if q_clean and q_clean not in seen_q:
                seen_q.add(q_clean)
                unique_queries.append(q)

        return unique_queries[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize case to formatted JSON."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClinicalCase:
        """Instantiate ClinicalCase from dictionary."""
        clean_data = dict(data)
        return cls(**clean_data)

    @classmethod
    def from_json(cls, json_str: str) -> ClinicalCase:
        """Instantiate ClinicalCase from JSON string."""
        return cls.from_dict(json.loads(json_str))

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
    """Canonical patient consultation and homeopathic repertorization case.

    extraction_meta schema:
    {
        "source": "paste" | "chat" | "manual",
        "negated": [str],
        "items": {
            dim_key: [
                {
                    "text": str,
                    "confidence": float | None,
                    "start": int | None,
                    "end": int | None,
                    "origin": "text" | "chat" | "manual",
                }
            ]
        },
        "red_flags": [{"category": str, "snippet": str}],
    }
    """

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

    # Extraction provenance metadata (WP1)
    extraction_meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Guarantee all 7 dimensions exist as lists
        if not self.dimensions:
            self.dimensions = {k: [] for k in CANONICAL_DIMENSIONS}
        for k in CANONICAL_DIMENSIONS:
            if k not in self.dimensions or not isinstance(self.dimensions[k], list):
                self.dimensions[k] = list(self.dimensions.get(k, []))
        if not hasattr(self, "clinical_summary") or self.clinical_summary is None:
            self.clinical_summary = ""
        if not hasattr(self, "extraction_meta") or self.extraction_meta is None:
            self.extraction_meta = {}
        if not hasattr(self, "scope_chapter"):
            self.scope_chapter = "MIND"
        elif isinstance(self.scope_chapter, int) and self.scope_chapter == 1:
            self.scope_chapter = "MIND"
        elif str(self.scope_chapter).strip() == "1":
            self.scope_chapter = "MIND"

    def __getattr__(self, name: str) -> Any:
        if name == "clinical_summary":
            return ""
        if name == "scope_chapter":
            return "MIND"
        if name == "extraction_meta":
            return {}
        if name == "selected_rubric_ids":
            return []
        if name == "muted_rubric_ids":
            return []
        if name == "eliminatory_rubric_ids":
            return []
        if name == "ranking_mode":
            return "totality"
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    @property
    def section_id(self) -> Optional[int]:
        """Return Kent database section ID (1 for MIND, None for all chapters)."""
        scope = getattr(self, "scope_chapter", "MIND")
        if scope is None:
            return None
        if isinstance(scope, int):
            return scope if scope > 0 else None
        scope_str = str(scope).strip().upper()
        if "MIND" in scope_str or scope_str == "1":
            return 1
        if scope_str.isdigit():
            val = int(scope_str)
            return val if val > 0 else None
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
        has_user_turns = any(t.get("role") == "user" for t in self.dialogue_history)
        has_transcript = bool(self.transcript and self.transcript.strip() and (has_user_turns or not self.dialogue_history))
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

    def get_dimension_values(self, dimension: str) -> List[str]:
        """Return symptom strings captured for a dimension."""
        return list(self.dimensions.get(dimension.lower().strip(), []))

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

    def replace_text_extracted_items(
        self,
        new_text_items: Dict[str, List[Dict[str, Any]]],
        source: str = "paste",
        negated: Optional[List[str]] = None,
        red_flags: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        """Replace only origin=='text' items in extraction_meta and dimensions, keeping 'manual' and 'chat' items intact."""
        if not hasattr(self, "extraction_meta") or self.extraction_meta is None:
            self.extraction_meta = {}

        current_items = self.extraction_meta.get("items", {})
        merged_items: Dict[str, List[Dict[str, Any]]] = {}

        for k in CANONICAL_DIMENSIONS:
            # Preserve existing non-text items (manual, chat)
            preserved = [it for it in current_items.get(k, []) if it.get("origin") != "text"]
            # Add incoming text items (tagging origin='text' if omitted)
            incoming = []
            for it in new_text_items.get(k, []):
                item_dict = dict(it)
                item_dict.setdefault("origin", "text")
                incoming.append(item_dict)
            merged_items[k] = preserved + incoming

            # Rebuild self.dimensions[k] from merged_items preserving order and uniqueness
            seen = set()
            dim_values: List[str] = []
            for it in merged_items[k]:
                t = str(it.get("text", "")).strip()
                if t and t.lower() not in seen:
                    seen.add(t.lower())
                    dim_values.append(t)
            self.dimensions[k] = dim_values

        self.extraction_meta["source"] = source
        self.extraction_meta["items"] = merged_items
        self.extraction_meta["negated"] = list(negated or [])
        self.extraction_meta["red_flags"] = list(red_flags or [])
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize case to formatted JSON."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClinicalCase:
        """Instantiate ClinicalCase from dictionary, tolerating missing extraction_meta or extra keys."""
        clean_data = dict(data)
        if "extraction_meta" not in clean_data or clean_data["extraction_meta"] is None:
            clean_data["extraction_meta"] = {}
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in clean_data.items() if k in field_names}
        return cls(**filtered)

    @classmethod
    def from_json(cls, json_str: str) -> ClinicalCase:
        """Instantiate ClinicalCase from JSON string."""
        return cls.from_dict(json.loads(json_str))

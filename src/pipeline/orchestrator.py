"""End-to-end clinical pipeline connecting Resolver, ChromaDB, and Remedy Ranker (Phase 5)."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.models.resolver import SymptomProfile, SymptomResolver
from src.pipeline.report_generator import generate_json_report, generate_markdown_report
from src.search.embedder import RubricEmbedder
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore


@dataclass
class PatientReport:
    """Structured clinical report containing symptoms, rubrics, and remedies."""

    patient_id: str
    transcript: str
    dimensions: Dict[str, Any]
    matched_rubrics: List[Dict[str, Any]]
    ranked_remedies: List[Dict[str, Any]]
    search_queries: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert report to formatted JSON string."""
        return generate_json_report(self.to_dict())

    def to_markdown(self) -> str:
        """Convert report to formatted clinical Markdown."""
        return generate_markdown_report(self.to_dict())


class PipelineOrchestrator:
    """Coordinates full workflow from patient transcript to final report."""

    def __init__(
        self,
        resolver: Optional[SymptomResolver] = None,
        vector_store: Optional[RubricVectorStore] = None,
        ranker: Optional[RemedyRanker] = None,
        mock_mode: bool = False,
    ) -> None:
        self.mock_mode = mock_mode
        self.resolver = resolver or SymptomResolver(mock_mode=mock_mode)

        if vector_store:
            self.vector_store = vector_store
        else:
            embedder = RubricEmbedder(mock_mode=mock_mode)
            self.vector_store = RubricVectorStore(embedder=embedder)

        self.ranker = ranker or RemedyRanker()

    def process_transcript(
        self,
        transcript: str,
        patient_id: Optional[str] = None,
        top_rubrics_per_query: int = 3,
        top_remedies: int = 10,
        section_id: Optional[int] = None,
    ) -> PatientReport:
        """Execute end-to-end repertorization on transcript.
        
        Args:
            transcript: Patient symptom description or dialogue transcript.
            patient_id: Unique patient identifier (default auto-generated UUID).
            top_rubrics_per_query: Number of candidate rubrics to retrieve per generated query.
            top_remedies: Number of top candidate remedies to rank.
            section_id: Optional Kent chapter filter (e.g. 1 for MIND).
            
        Returns:
            Structured PatientReport instance.
        """
        pid = patient_id or f"PT-{uuid.uuid4().hex[:8].upper()}"

        # 1. Resolve symptoms and 7 dimensions
        profile: SymptomProfile = self.resolver.resolve(transcript)
        queries = profile.get_search_queries()

        # 2. Retrieve candidate rubrics across generated queries
        matched_rubrics_dict: Dict[int, Dict[str, Any]] = {}

        for query_str in queries:
            try:
                candidates = self.vector_store.query(
                    query_text=query_str,
                    top_k=top_rubrics_per_query,
                    section_id=section_id,
                )
                for cand in candidates:
                    r_id = cand["rubric_id"]
                    if r_id not in matched_rubrics_dict:
                        matched_rubrics_dict[r_id] = cand
                    else:
                        # Keep maximum similarity score
                        if cand["similarity"] > matched_rubrics_dict[r_id]["similarity"]:
                            matched_rubrics_dict[r_id] = cand
            except Exception:
                continue

        matched_rubrics = sorted(
            matched_rubrics_dict.values(),
            key=lambda x: x.get("similarity", 0.0),
            reverse=True,
        )

        # 3. Rank remedies according to classical totality
        ranked_remedies = self.ranker.rank(matched_rubrics, top_n=top_remedies)

        return PatientReport(
            patient_id=pid,
            transcript=transcript,
            dimensions=profile.to_dict(),
            matched_rubrics=matched_rubrics,
            ranked_remedies=ranked_remedies,
            search_queries=queries,
        )

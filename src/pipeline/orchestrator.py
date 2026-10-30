"""End-to-end clinical pipeline connecting Resolver, ChromaDB, and Remedy Ranker (Phase 5)."""

from __future__ import annotations

import datetime
import logging
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.data.kent_db import KentDB
from src.models.case import ClinicalCase
from src.models.symptom_ner import SymptomNER
from src.models.resolver import SymptomProfile, SymptomResolver
from src.pipeline.report_generator import generate_json_report, generate_markdown_report
from src.search.embedder import RubricEmbedder
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore

logger = logging.getLogger("orchestrator")


@dataclass
class PatientReport:
    """Structured clinical report containing symptoms, rubrics, and remedies."""

    patient_id: str
    transcript: str
    dimensions: Dict[str, Any]
    matched_rubrics: List[Dict[str, Any]]
    ranked_remedies: List[Dict[str, Any]]
    search_queries: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
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
        ner: Optional[SymptomNER] = None,
        resolver: Optional[SymptomResolver] = None,
        vector_store: Optional[RubricVectorStore] = None,
        ranker: Optional[RemedyRanker] = None,
        mock_mode: bool = False,
    ) -> None:
        self.mock_mode = mock_mode
        self.ner = ner or SymptomNER(mock_mode=mock_mode)
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

        # 1. Extract clinical entity spans using Bio_ClinicalBERT
        raw_entities: List[Dict[str, Any]] = []
        if self.ner is not None:
            try:
                raw_entities = self.ner.extract_entities(transcript)
            except Exception as err:
                logger.warning("NER extraction failed (%s), proceeding with empty entities.", err)
                raw_entities = []

        # 2. Resolve symptoms and 7 dimensions with negation & coreference handling
        profile: SymptomProfile = self.resolver.resolve(transcript, raw_entities=raw_entities)
        queries = profile.get_search_queries()

        # 3. Retrieve candidate rubrics across generated queries
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

        # 4. Rank remedies according to classical totality
        ranked_remedies = self.ranker.rank(matched_rubrics, top_n=top_remedies)

        return PatientReport(
            patient_id=pid,
            transcript=transcript,
            dimensions=profile.to_dict(),
            matched_rubrics=matched_rubrics,
            ranked_remedies=ranked_remedies,
            search_queries=queries,
            entities=raw_entities,
        )

    def repertorize_case(
        self,
        case: ClinicalCase,
        top_rubrics_per_query: int = 3,
        top_remedies: int = 20,
    ) -> PatientReport:
        """Execute clinical repertorization directly from a typed ClinicalCase object.

        Guarantees 100% data consistency: consumes case.dimensions directly,
        retrieves matching rubrics using case.get_search_queries() and case.selected_rubric_ids,
        filters out case.muted_rubric_ids, enforces case.eliminatory_rubric_ids,
        and applies case.section_id scope.
        """
        queries = case.get_search_queries()
        sec_id = case.section_id

        matched_rubrics_dict: Dict[int, Dict[str, Any]] = {}
        db = KentDB()

        # 1. Include manually selected rubrics from explorer or previous steps
        if case.selected_rubric_ids:
            for r_id in case.selected_rubric_ids:
                try:
                    r_id_int = int(r_id)
                    r_info = db.get_rubric_by_id(r_id_int)
                    if r_info:
                        matched_rubrics_dict[r_id_int] = {
                            "rubric_id": r_id_int,
                            "path": r_info.get("path", f"Rubric #{r_id_int}"),
                            "label": r_info.get("label", ""),
                            "section_id": r_info.get("section_id"),
                            "section_name": r_info.get("section_name", ""),
                            "similarity": 1.0,
                            "remedy_count": r_info.get("remedy_count", 0),
                            "matched_symptom": "Clinician Added",
                        }
                except Exception:
                    pass

        # 2. Query vector store across synthesized symptom queries
        for query_str in queries:
            try:
                candidates = self.vector_store.query(
                    query_text=query_str,
                    top_k=top_rubrics_per_query,
                    section_id=sec_id,
                )
                for cand in candidates:
                    r_id = cand["rubric_id"]
                    if r_id is None:
                        continue
                    cand["matched_symptom"] = query_str
                    if r_id not in matched_rubrics_dict:
                        matched_rubrics_dict[r_id] = cand
                    else:
                        if cand.get("similarity", 0) > matched_rubrics_dict[r_id].get("similarity", 0):
                            matched_rubrics_dict[r_id] = cand
            except Exception:
                continue

        # 3. Filter out muted rubrics
        muted_set = set(case.muted_rubric_ids or [])
        active_rubrics = [
            r for r_id, r in matched_rubrics_dict.items()
            if r_id not in muted_set
        ]

        # Sort by similarity descending
        active_rubrics.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

        # 4. Rank remedies according to case ranking_mode and eliminatory rubrics
        ranked_remedies = self.ranker.rank(
            active_rubrics,
            top_n=top_remedies,
            ranking_mode=case.ranking_mode,
            eliminatory_rubric_ids=case.eliminatory_rubric_ids,
        )

        report = PatientReport(
            patient_id=case.case_id,
            transcript=case.transcript or case.chief_complaint or "Structured clinical intake",
            dimensions=dict(case.dimensions),
            matched_rubrics=active_rubrics,
            ranked_remedies=ranked_remedies,
            search_queries=queries,
            entities=[],
        )
        case.report_data = report.to_dict()
        return report

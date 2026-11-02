"""Test ClinicalCase.section_id robustness across data types and missing attributes."""

from __future__ import annotations

import json
from src.models.case import ClinicalCase


def test_section_id_variations() -> None:
    """Verify section_id returns 1 for MIND variants and None for ALL/None."""
    # String variants
    assert ClinicalCase(scope_chapter="MIND").section_id == 1
    assert ClinicalCase(scope_chapter="mind").section_id == 1
    assert ClinicalCase(scope_chapter="MIND focus").section_id == 1
    assert ClinicalCase(scope_chapter="1").section_id == 1

    # Integer variants
    assert ClinicalCase(scope_chapter=1).section_id == 1

    # None and ALL variants
    assert ClinicalCase(scope_chapter=None).section_id is None
    assert ClinicalCase(scope_chapter="ALL").section_id is None
    assert ClinicalCase(scope_chapter="All chapters").section_id is None
    assert ClinicalCase(scope_chapter="").section_id is None


def test_section_id_missing_attribute_does_not_raise() -> None:
    """Verify that if scope_chapter is missing, section_id defaults safely without raising AttributeError."""
    case = ClinicalCase()
    del case.scope_chapter
    # Accessing section_id should not crash with AttributeError
    assert case.section_id == 1


def test_section_id_demo_case() -> None:
    """Verify that demo case has valid section_id."""
    from src.dashboard.components.demo_case import create_demo_case

    case = create_demo_case()
    assert case.section_id == 1


def test_repertorize_case_with_int_and_str_scopes() -> None:
    """Verify pipeline.repertorize_case works with ClinicalCase having int or str scope."""
    from src.pipeline.orchestrator import PipelineOrchestrator
    from src.search.embedder import RubricEmbedder
    from src.search.ranker import RemedyRanker
    from src.search.vector_store import RubricVectorStore

    embedder = RubricEmbedder(mock_mode=True)
    vector_store = RubricVectorStore(embedder=embedder, in_memory=True)
    ranker = RemedyRanker()
    pipeline = PipelineOrchestrator(
        ner=None,
        vector_store=vector_store,
        ranker=ranker,
        mock_mode=True,
    )

    case_int = ClinicalCase(scope_chapter=1)
    case_int.add_symptom("mental", "anxiety")
    report_int = pipeline.repertorize_case(case_int)
    assert report_int is not None

    case_str = ClinicalCase(scope_chapter="MIND")
    case_str.add_symptom("mental", "anxiety")
    report_str = pipeline.repertorize_case(case_str)
    assert report_str is not None

    case_none = ClinicalCase(scope_chapter=None)
    case_none.add_symptom("mental", "anxiety")
    report_none = pipeline.repertorize_case(case_none)
    assert report_none is not None


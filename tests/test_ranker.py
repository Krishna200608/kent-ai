"""Unit tests for RemedyRanker (Phase 5)."""

import pytest

from src.search.ranker import RemedyRanker


@pytest.fixture
def ranker():
    return RemedyRanker()


def test_rank_empty_input(ranker):
    assert ranker.rank([]) == []


def test_fetch_rubrics_remedies_batch(ranker):
    # Rubric 4 is ABSENT-MINDED, has multiple remedies
    batch = ranker._fetch_rubrics_remedies_batch([1, 4])
    assert 1 in batch
    assert 4 in batch
    assert len(batch[4]) > 0
    # Every remedy should have a valid grade
    for rem in batch[4]:
        assert rem["grade"] in [1, 2, 3]


def test_rank_remedies_ordering(ranker):
    # Test ranking with rubric 4
    results = ranker.rank([4], top_n=5)
    assert len(results) > 0
    assert "abbreviation" in results[0]
    assert "score" in results[0]
    assert "rubric_count" in results[0]
    assert results[0]["rubric_count"] == 1
    # Check that results are sorted by score descending
    if len(results) > 1:
        assert results[0]["score"] >= results[1]["score"]


def test_rank_multi_rubric_totality_coverage(ranker):
    # Rubric 1 (ABANDONED) and Rubric 4 (ABSENT-MINDED)
    matches = [
        {"rubric_id": 1, "similarity": 0.95, "path": "MIND > ABANDONED"},
        {"rubric_id": 4, "similarity": 0.90, "path": "MIND > ABSENT-MINDED"},
    ]
    results = ranker.rank(matches, top_n=10)
    assert len(results) > 0

    # If any remedy covers BOTH rubrics, it should be sorted before remedies covering only 1
    two_coverage = [r for r in results if r["rubric_count"] == 2]
    one_coverage = [r for r in results if r["rubric_count"] == 1]

    if two_coverage and one_coverage:
        assert two_coverage[0]["coverage_ratio"] == 1.0
        # The first item in results should be from two_coverage
        assert results[0]["rubric_count"] == 2


def test_repertorize_symptoms_report(ranker):
    matches = [
        {"rubric_id": 4, "similarity": 0.88, "path": "MIND > ABSENT-MINDED"}
    ]
    report = ranker.repertorize_symptoms(matches, top_remedies=3)
    assert report["total_rubrics_analyzed"] == 1
    assert len(report["ranked_remedies"]) <= 3
    assert report["top_remedy"] is not None

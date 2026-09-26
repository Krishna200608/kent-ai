"""Unit tests for dataset splitting and stratification."""

import pytest
from src.data.splitter import split_cases, compute_split_statistics


@pytest.fixture
def sample_cases():
    # 20 cases across 5 rubrics (4 cases each)
    cases = []
    for rubric_id in range(1, 6):
        for idx in range(1, 5):
            cases.append({
                "case_id": f"case_{rubric_id}_{idx}",
                "rubric_id": rubric_id,
                "narrative": f"Patient with symptom for rubric {rubric_id} variation {idx}",
                "entities": [
                    {"text": f"symptom {rubric_id}", "label": "MENT", "start": 13, "end": 22}
                ],
                "tokens": ["Patient", "with", "symptom", str(rubric_id)],
                "bio_tags": ["O", "O", "B-MENT", "I-MENT"],
            })
    return cases


def test_split_cases_proportions(sample_cases):
    train, val, test = split_cases(sample_cases, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
    
    assert len(train) + len(val) + len(test) == len(sample_cases)
    # Check approximately 80/10/10
    assert len(train) >= 12
    assert len(val) >= 1
    assert len(test) >= 1


def test_split_reproducibility(sample_cases):
    t1, v1, s1 = split_cases(sample_cases, seed=42)
    t2, v2, s2 = split_cases(sample_cases, seed=42)
    
    assert [c["case_id"] for c in t1] == [c["case_id"] for c in t2]
    assert [c["case_id"] for c in v1] == [c["case_id"] for c in v2]
    assert [c["case_id"] for c in s1] == [c["case_id"] for c in s2]


def test_split_ratio_validation(sample_cases):
    with pytest.raises(ValueError, match="must sum to 1.0"):
        split_cases(sample_cases, train_ratio=0.7, val_ratio=0.1, test_ratio=0.1)


def test_compute_split_statistics(sample_cases):
    train, val, test = split_cases(sample_cases, seed=42)
    stats = compute_split_statistics(train, val, test)
    
    assert stats["total_cases"] == 20
    assert "train" in stats
    assert "val" in stats
    assert "test" in stats
    assert stats["train"]["case_count"] == len(train)
    assert stats["train"]["entity_counts"]["MENT"] > 0

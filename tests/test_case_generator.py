"""Unit tests for CaseGenerator."""

import pytest
from src.data.case_generator import CaseGenerator, SyntheticCase


@pytest.fixture
def mock_generator():
    return CaseGenerator(mock_mode=True)


def test_synthetic_case_serialization():
    case = SyntheticCase(
        case_id="c_001",
        rubric_id=4,
        rubric_path="MIND > ABSENT-MINDED",
        narrative="I feel absent-minded today.",
        entities=[{"text": "absent-minded", "label": "MENT", "start": 7, "end": 20}],
        tokens=["I", "feel", "absent", "-", "minded", "today", "."],
        bio_tags=["O", "O", "B-MENT", "I-MENT", "I-MENT", "O", "O"],
        metadata={"model": "test"},
    )
    d = case.to_dict()
    assert d["case_id"] == "c_001"
    assert d["rubric_id"] == 4
    assert len(d["tokens"]) == 7

    reconstructed = SyntheticCase.from_dict(d)
    assert reconstructed.case_id == case.case_id
    assert reconstructed.rubric_path == case.rubric_path
    assert reconstructed.bio_tags == case.bio_tags


def test_generate_case_for_rubric_mock(mock_generator):
    case = mock_generator.generate_case_for_rubric(rubric_id=4)
    
    assert isinstance(case, SyntheticCase)
    assert case.rubric_id == 4
    assert "MIND" in case.rubric_path
    assert len(case.narrative) > 10
    assert len(case.tokens) > 0
    assert len(case.bio_tags) == len(case.tokens)
    assert any(tag.startswith("B-") for tag in case.bio_tags)


def test_generate_batch_mock(mock_generator):
    rubric_ids = [1, 2, 4]
    generated_cases = []
    
    cases = mock_generator.generate_batch(
        rubric_ids=rubric_ids,
        cases_per_rubric=2,
        on_case_callback=lambda c: generated_cases.append(c),
    )
    
    assert len(cases) == 6
    assert len(generated_cases) == 6
    assert {c.rubric_id for c in cases} == {1, 2, 4}

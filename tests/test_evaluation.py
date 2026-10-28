"""Unit tests for Phase C comprehensive academic evaluation suite (scripts/evaluate.py)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.evaluate import PipelineEvaluator, normalize_remedy_name, main


def test_normalize_remedy_name():
    assert normalize_remedy_name("Mur-ac.") == "mur-ac"
    assert normalize_remedy_name(" Bell. ") == "bell"
    assert normalize_remedy_name("Ars-alb") == "ars-alb"


def test_evaluator_generate_markdown_report():
    sample_results = {
        "dataset": "test.jsonl",
        "total_cases": 100,
        "elapsed_seconds": 12.5,
        "cases_per_second": 8.0,
        "mock_mode": True,
        "metrics": {
            "token_level_bio_f1": 0.8912,
            "token_accuracy": 0.8845,
            "bio_precision": 0.8820,
            "bio_recall": 0.9005,
            "top1_rubric_recall": 0.7200,
            "top5_rubric_recall": 0.8500,
            "top10_rubric_recall": 0.9100,
            "top20_rubric_recall": 0.9400,
            "mean_reciprocal_rank": 0.7321,
            "simillimum_acc_top1": 0.5200,
            "simillimum_acc_top3": 0.6800,
            "simillimum_acc_top5": 0.7600,
            "remedy_eval_cases": 95,
        },
        "per_dimension": {
            "MENT": {"precision": 0.91, "recall": 0.92, "f1": 0.915, "support": 150},
            "SEN": {"precision": 0.85, "recall": 0.88, "f1": 0.865, "support": 60},
        },
    }

    md = PipelineEvaluator.generate_markdown_report(sample_results)
    assert "# Kent-AI: Academic Benchmark Evaluation Report" in md
    assert "Token-level BIO F1" in md
    assert "89.12%" in md
    assert "94.00%" in md
    assert "0.7321" in md
    assert "76.00%" in md
    assert "`MENT`" in md
    assert "✅ Pass" in md


def test_evaluator_evaluate_dataset_mock(tmp_path):
    # Create mini mock test dataset
    test_file = tmp_path / "mini_test.jsonl"
    sample_record = {
        "case_id": "test_001",
        "rubric_id": 1,
        "rubric_path": "MIND > ABANDONED",
        "narrative": "Doctor, I feel terribly abandoned and lonely.",
        "entities": [
            {"text": "abandoned", "label": "MENT", "start": 23, "end": 32},
            {"text": "lonely", "label": "MENT", "start": 37, "end": 43},
        ],
        "tokens": ["Doctor", ",", "I", "feel", "terribly", "abandoned", "and", "lonely", "."],
        "bio_tags": ["O", "O", "O", "O", "O", "B-MENT", "O", "B-MENT", "O"],
        "metadata": {
            "top_remedies": ["Lach.", "Puls."],
        },
    }
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(sample_record) + "\n")

    evaluator = PipelineEvaluator(mock_mode=True)
    results = evaluator.evaluate_dataset(test_file=test_file, limit=1, show_progress=False)

    assert results["total_cases"] == 1
    assert "metrics" in results
    m = results["metrics"]
    assert 0.0 <= m["token_level_bio_f1"] <= 1.0
    assert 0.0 <= m["token_accuracy"] <= 1.0
    assert 0.0 <= m["top20_rubric_recall"] <= 1.0
    assert 0.0 <= m["mean_reciprocal_rank"] <= 1.0
    assert 0.0 <= m["simillimum_acc_top5"] <= 1.0


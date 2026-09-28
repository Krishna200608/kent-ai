"""Unit tests for ClinicalBERT NER training and inference (Phase 3)."""

import json
from pathlib import Path
import pytest
import numpy as np

from src.models.trainer import NERTrainer, set_seed
from src.models.symptom_ner import SymptomNER
from src.data.bio_tagger import BIOTagger


def test_ner_trainer_initialization_and_label_mapping():
    """Verify NERTrainer loads BIO schema with 15 tags and bidirectional mappings."""
    trainer = NERTrainer(seed=42)
    assert len(trainer.tags) == 15
    assert "O" in trainer.tags
    assert "B-LOC" in trainer.tags
    assert "I-MENT" in trainer.tags
    assert trainer.id2label[0] == "O"
    assert trainer.label2id["O"] == 0
    assert len(trainer.id2label) == len(trainer.label2id) == 15


def test_ner_trainer_compute_metrics_seqeval():
    """Verify compute_metrics correctly evaluates predictions ignoring -100."""
    trainer = NERTrainer(seed=42)
    # Shape: [batch_size=1, seq_len=4, num_labels=15]
    logits = np.zeros((1, 4, 15))
    # Predict tag at index 1: 'B-LOC'
    logits[0, 0, 1] = 5.0
    # Predict tag at index 2: 'I-LOC'
    logits[0, 1, 2] = 5.0
    # Predict tag at index 0: 'O'
    logits[0, 2, 0] = 5.0
    # Predict tag at index 0: 'O'
    logits[0, 3, 0] = 5.0

    # Ground truth labels matching prediction
    labels = np.array([[1, 2, 0, -100]])  # -100 is ignore_index

    metrics = trainer.compute_metrics((logits, labels))
    assert "f1" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert metrics["f1"] == 1.0
    assert metrics["precision"] == 1.0


def test_symptom_ner_mock_extraction():
    """Verify SymptomNER extracts entities from clinical text in mock mode."""
    ner = SymptomNER(mock_mode=True)
    text = "Severe throbbing in right temple, worse morning, with nausea and anxiety."
    entities = ner.extract_entities(text)

    assert len(entities) >= 4
    labels = {e["label"] for e in entities}
    assert "SEN" in labels  # throbbing
    assert "TEMP" in labels  # morning
    assert "CONC" in labels  # nausea
    assert "MENT" in labels  # anxiety

    for e in entities:
        assert "start" in e and "end" in e
        assert text[e["start"] : e["end"]].lower() == e["text"].lower()
        assert 0.0 <= e["confidence"] <= 1.0


def test_symptom_ner_empty_text():
    """Verify SymptomNER gracefully handles empty string or whitespace."""
    ner = SymptomNER(mock_mode=True)
    assert ner.extract_entities("") == []
    assert ner.extract_entities("   \n\t  ") == []


def test_trainer_prepare_dataset_synthetic(tmp_path):
    """Verify prepare_dataset_from_jsonl reads cases and produces valid tokenized Hugging Face Dataset."""
    dummy_cases = [
        {
            "case_id": "TEST-001",
            "transcript": "Patient feels anxious in the morning.",
            "entities": [
                {"text": "anxious", "label": "MENT", "start": 14, "end": 21},
                {"text": "morning", "label": "TEMP", "start": 29, "end": 36},
            ],
        },
        {
            "case_id": "TEST-002",
            "transcript": "Headache worse cold.",
            "entities": [
                {"text": "worse cold", "label": "MOD_AGG", "start": 9, "end": 19},
            ],
        },
    ]

    jsonl_file = tmp_path / "test_cases.jsonl"
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for c in dummy_cases:
            f.write(json.dumps(c) + "\n")

    trainer = NERTrainer(seed=42)
    dataset = trainer.prepare_dataset_from_jsonl(jsonl_file)

    assert len(dataset) == 2
    assert "input_ids" in dataset.column_names
    assert "attention_mask" in dataset.column_names
    assert "labels" in dataset.column_names
    assert len(dataset[0]["input_ids"]) == trainer.max_seq_length
    assert len(dataset[0]["labels"]) == trainer.max_seq_length

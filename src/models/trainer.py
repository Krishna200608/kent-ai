"""ClinicalBERT training and evaluation loop with early stopping and SeqEval metrics (Phase 3).

Fine-tunes emilyalsentzer/Bio_ClinicalBERT on the HomeoNER token classification task
with the 7 Kent symptom dimensions (15 BIO tags).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import seqeval.metrics
import torch
from datasets import Dataset
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    EarlyStoppingCallback,
    PreTrainedTokenizerFast,
    Trainer,
    TrainingArguments,
)

from src.config import get_model_config, get_project_root
from src.data.bio_tagger import BIOTagger

logger = logging.getLogger("trainer")


def set_seed(seed: int = 42) -> None:
    """Set random seeds across numpy and PyTorch for experimental reproducibility."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class NERTrainer:
    """Orchestrates Bio_ClinicalBERT fine-tuning and evaluation for HomeoNER."""

    DEFAULT_MODEL_NAME = "emilyalsentzer/Bio_ClinicalBERT"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
        output_dir: Optional[Union[str, Path]] = None,
        seed: int = 42,
    ) -> None:
        """Initialize trainer with configuration, label mappings, and seed.
        
        Args:
            config: Model configuration dictionary (defaults to configs/model.yaml).
            model_name: Base Hugging Face model identifier.
            output_dir: Destination path for trained model artifacts.
            seed: Random seed for deterministic reproducibility.
        """
        self.config = config or get_model_config()
        self.model_cfg = self.config.get("model", {})
        self.training_cfg = self.config.get("training", {})
        self.labels_cfg = self.config.get("labels", {})

        self.seed = seed or self.model_cfg.get("seed", 42)
        set_seed(self.seed)

        self.model_name = model_name or self.model_cfg.get("name", self.DEFAULT_MODEL_NAME)
        root = get_project_root()
        self.output_dir = Path(output_dir or (root / self.model_cfg.get("output_dir", "data/models/clinicalbert_homeoNER")))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.max_seq_length = int(self.model_cfg.get("max_seq_length", 256))

        # Build canonical BIO label mappings (15 tags)
        self.tags: List[str] = self.labels_cfg.get("tags", [
            "O",
            "B-LOC", "I-LOC",
            "B-SEN", "I-SEN",
            "B-MOD_AGG", "I-MOD_AGG",
            "B-MOD_AMEL", "I-MOD_AMEL",
            "B-CONC", "I-CONC",
            "B-TEMP", "I-TEMP",
            "B-MENT", "I-MENT",
        ])
        self.id2label: Dict[int, str] = {i: tag for i, tag in enumerate(self.tags)}
        self.label2id: Dict[str, int] = {tag: i for i, tag in enumerate(self.tags)}

        self.tagger = BIOTagger(categories=self.labels_cfg.get("categories", [
            "LOC", "SEN", "MOD_AGG", "MOD_AMEL", "CONC", "TEMP", "MENT"
        ]))

        self.tokenizer: Optional[PreTrainedTokenizerFast] = None
        self.model: Optional[AutoModelForTokenClassification] = None

    def get_tokenizer(self) -> PreTrainedTokenizerFast:
        """Lazily initialize and return the fast Hugging Face tokenizer."""
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_fast=True,
                model_max_length=self.max_seq_length,
            )
        return self.tokenizer

    def prepare_dataset_from_jsonl(
        self,
        file_path: Union[str, Path],
        max_samples: Optional[int] = None,
    ) -> Dataset:
        """Load and tokenize JSONL case dataset with subword offset alignment.
        
        Args:
            file_path: Path to jsonl file containing synthetic cases.
            max_samples: Optional limit on number of cases (useful for validation/testing).
            
        Returns:
            Hugging Face Dataset ready for Trainer consumption.
        """
        tokenizer = self.get_tokenizer()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if max_samples and idx >= max_samples:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        if not records:
            raise ValueError(f"No valid records found in {path}")

        # Extract texts and entities from records
        all_texts: List[str] = []
        all_entities: List[List[Dict[str, Any]]] = []
        for r in records:
            text = r.get("transcript") or r.get("text") or ""
            entities = r.get("entities") or []
            all_texts.append(text)
            all_entities.append(entities)

        # Batch tokenization with character offset mapping
        tokenized = tokenizer(
            all_texts,
            truncation=True,
            max_length=self.max_seq_length,
            padding="max_length",
            return_offsets_mapping=True,
        )

        all_input_ids = tokenized["input_ids"]
        all_attention_mask = tokenized["attention_mask"]
        all_offsets = tokenized["offset_mapping"]
        all_labels: List[List[int]] = []

        # Align character entity annotations with subword tokens
        for text, entities, offsets in zip(all_texts, all_entities, all_offsets):
            subword_labels = self.tagger.align_with_subwords(
                subword_offsets=offsets,
                entities=entities,
                text=text,
                ignore_index=-100,
                tag_to_id=self.label2id,
            )
            # Ensure label array matches input_ids length
            if len(subword_labels) < self.max_seq_length:
                subword_labels.extend([-100] * (self.max_seq_length - len(subword_labels)))
            else:
                subword_labels = subword_labels[: self.max_seq_length]
            all_labels.append(subword_labels)

        dataset_dict = {
            "input_ids": all_input_ids,
            "attention_mask": all_attention_mask,
            "labels": all_labels,
        }
        return Dataset.from_dict(dataset_dict)

    def compute_metrics(self, p: Any) -> Dict[str, float]:
        """Compute strict token and entity-level BIO metrics via seqeval.
        
        Ignores special token positions (-100).
        """
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2)

        true_predictions = [
            [self.id2label[p_idx] for (p_idx, l_idx) in zip(prediction, label) if l_idx != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [self.id2label[l_idx] for (p_idx, l_idx) in zip(prediction, label) if l_idx != -100]
            for prediction, label in zip(predictions, labels)
        ]

        f1 = seqeval.metrics.f1_score(true_labels, true_predictions)
        precision = seqeval.metrics.precision_score(true_labels, true_predictions)
        recall = seqeval.metrics.recall_score(true_labels, true_predictions)
        accuracy = seqeval.metrics.accuracy_score(true_labels, true_predictions)

        return {
            "f1": float(f1),
            "precision": float(precision),
            "recall": float(recall),
            "accuracy": float(accuracy),
        }

    def train(
        self,
        train_path: Union[str, Path],
        val_path: Union[str, Path],
        epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        learning_rate: Optional[float] = None,
    ) -> Dict[str, float]:
        """Execute full training and evaluation loop with early stopping.
        
        Args:
            train_path: Path to train.jsonl.
            val_path: Path to val.jsonl.
            epochs: Optional epoch override.
            batch_size: Optional batch size override.
            learning_rate: Optional learning rate override.
            
        Returns:
            Dictionary of final evaluation metrics.
        """
        tokenizer = self.get_tokenizer()
        logger.info("Preparing training dataset from %s...", train_path)
        train_dataset = self.prepare_dataset_from_jsonl(train_path)

        logger.info("Preparing validation dataset from %s...", val_path)
        val_dataset = self.prepare_dataset_from_jsonl(val_path)

        # Initialize model with classification head
        logger.info("Initializing %s for %d labels...", self.model_name, len(self.tags))
        self.model = AutoModelForTokenClassification.from_pretrained(
            self.model_name,
            num_labels=len(self.tags),
            id2label=self.id2label,
            label2id=self.label2id,
        )

        num_epochs = epochs or int(self.training_cfg.get("epochs", 10))
        per_device_batch_size = batch_size or int(self.training_cfg.get("batch_size", 16))
        lr = learning_rate or float(self.training_cfg.get("learning_rate", 2e-5))
        weight_decay = float(self.training_cfg.get("weight_decay", 0.01))
        warmup_ratio = float(self.training_cfg.get("warmup_ratio", 0.1))
        patience = int(self.training_cfg.get("early_stopping_patience", 3))

        use_fp16 = bool(self.training_cfg.get("fp16", True)) and torch.cuda.is_available()

        training_args = TrainingArguments(
            output_dir=str(self.output_dir / "checkpoints"),
            evaluation_strategy="epoch",
            save_strategy="epoch",
            learning_rate=lr,
            per_device_train_batch_size=per_device_batch_size,
            per_device_eval_batch_size=per_device_batch_size,
            num_train_epochs=num_epochs,
            weight_decay=weight_decay,
            warmup_ratio=warmup_ratio,
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=int(self.training_cfg.get("logging_steps", 50)),
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            greater_is_better=True,
            fp16=use_fp16,
            save_total_limit=int(self.training_cfg.get("save_total_limit", 2)),
            seed=self.seed,
            report_to="none",
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=tokenizer,
            compute_metrics=self.compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=patience)],
        )

        logger.info("Beginning fine-tuning (%d epochs, batch size %d, fp16=%s)...", num_epochs, per_device_batch_size, use_fp16)
        train_result = trainer.train()

        # Save final best model and tokenizer
        logger.info("Saving best model to %s...", self.output_dir)
        trainer.save_model(str(self.output_dir))
        tokenizer.save_pretrained(str(self.output_dir))

        # Final evaluation
        eval_metrics = trainer.evaluate()
        logger.info("Final Validation Metrics: %s", json.dumps(eval_metrics, indent=2))

        return eval_metrics

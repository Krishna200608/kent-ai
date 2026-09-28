#!/usr/bin/env python3
"""CLI Script: Fine-tune Bio_ClinicalBERT on HomeoNER task (Phase 3).

Trains Bio_ClinicalBERT token classifier using train.jsonl and val.jsonl datasets,
evaluates BIO span F1 via SeqEval, and exports best model checkpoints.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure project repository root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_model_config, get_project_root
from src.models.trainer import NERTrainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("train_ner")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fine-tune Bio_ClinicalBERT for 7-dimension HomeoNER symptom extraction."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/model.yaml",
        help="Path to model YAML configuration",
    )
    parser.add_argument(
        "--train-file",
        type=str,
        default="data/processed/train.jsonl",
        help="Path to training dataset JSONL",
    )
    parser.add_argument(
        "--val-file",
        type=str,
        default="data/processed/val.jsonl",
        help="Path to validation dataset JSONL",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save fine-tuned model checkpoints",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Override training epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Override batch size per device",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=None,
        help="Override learning rate",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    root = get_project_root()

    train_path = root / args.train_file
    val_path = root / args.val_file

    if not train_path.exists() or not val_path.exists():
        logger.error(
            "Dataset files missing! Expected:\n  Train: %s\n  Val: %s\n"
            "Please run Phase 1 case generation first: python scripts/generate_cases.py --split",
            train_path,
            val_path,
        )
        return 1

    config = get_model_config(root / args.config)
    trainer = NERTrainer(
        config=config,
        output_dir=args.output_dir,
        seed=args.seed,
    )

    logger.info("=" * 65)
    logger.info("Starting ClinicalBERT NER Training Pipeline")
    logger.info("Base Model: %s", trainer.model_name)
    logger.info("Train File: %s", train_path)
    logger.info("Val File:   %s", val_path)
    logger.info("Output Dir: %s", trainer.output_dir)
    logger.info("=" * 65)

    metrics = trainer.train(
        train_path=train_path,
        val_path=val_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )

    logger.info("Training complete! Final Evaluation Metrics:")
    logger.info(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

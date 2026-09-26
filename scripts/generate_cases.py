#!/usr/bin/env python3
"""CLI Script: Generate synthetic clinical cases with crash-safe checkpointing (Phase 1).

Generates clinical case vignettes for Kent's Repertory MIND rubrics using LLaMA 3 (via Ollama)
or deterministic mock mode, with real-time atomic checkpointing and auto-splitting.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_generation_config, get_project_root
from src.data.case_generator import CaseGenerator, SyntheticCase
from src.data.kent_db import KentDB, get_mind_rubrics
from src.data.splitter import split_and_save_jsonl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("generate_cases")


class GenerationRunner:
    """Manages stateful, crash-safe generation execution."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        mock_mode: bool = False,
        resume: bool = False,
        limit: Optional[int] = None,
        cases_per_rubric: Optional[int] = None,
        output_file: Optional[str] = None,
        checkpoint_file: Optional[str] = None,
    ) -> None:
        self.config = get_generation_config(config_path)
        self.mock_mode = mock_mode
        self.resume = resume
        self.limit = limit

        tgt_cfg = self.config.get("target_data", {})
        root = get_project_root()

        self.cases_per_rubric = cases_per_rubric or tgt_cfg.get("cases_per_rubric", 4)
        self.output_path = root / (output_file or tgt_cfg.get("output_file", "data/processed/mind_cases.jsonl"))
        self.checkpoint_path = root / (checkpoint_file or tgt_cfg.get("checkpoint_file", "data/processed/generation_checkpoint.json"))
        self.checkpoint_interval = tgt_cfg.get("checkpoint_interval", 25)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        self.generator = CaseGenerator(config=self.config, mock_mode=self.mock_mode)
        self.kent_db = KentDB()

        self.completed_rubric_ids: Set[int] = set()
        self.cases_generated_count: int = 0
        self.interrupted: bool = False

        # Register signal handlers for clean interrupt
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.warning("Interrupt signal received! Finishing current item and saving checkpoint...")
        self.interrupted = True

    def load_checkpoint(self) -> None:
        """Load state from checkpoint file if resuming."""
        if not self.resume or not self.checkpoint_path.exists():
            return

        try:
            with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.completed_rubric_ids = set(data.get("completed_rubric_ids", []))
            self.cases_generated_count = data.get("cases_generated_count", 0)
            logger.info(
                "Resumed from checkpoint: %d rubrics already completed (%d cases logged)",
                len(self.completed_rubric_ids),
                self.cases_generated_count,
            )
        except Exception as err:
            logger.warning("Failed to load checkpoint file (%s). Starting clean.", err)

    def save_checkpoint(self, last_rubric_id: Optional[int] = None) -> None:
        """Save atomic state checkpoint."""
        data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_completed_rubrics": len(self.completed_rubric_ids),
            "completed_rubric_ids": sorted(self.completed_rubric_ids),
            "cases_generated_count": self.cases_generated_count,
            "last_rubric_id": last_rubric_id,
        }
        temp_path = self.checkpoint_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp_path.replace(self.checkpoint_path)

    def run(self) -> int:
        """Execute case generation loop over MIND rubrics."""
        logger.info("=" * 60)
        logger.info("Starting Case Generation Pipeline (Phase 1)")
        logger.info("Backend: %s | Model: %s", self.generator.backend, self.generator.model)
        logger.info("Output: %s", self.output_path)
        logger.info("Checkpoint: %s", self.checkpoint_path)
        logger.info("=" * 60)

        self.load_checkpoint()

        mind_rubrics = self.kent_db.get_mind_rubrics()
        if self.limit:
            mind_rubrics = mind_rubrics[: self.limit]

        total_rubrics = len(mind_rubrics)
        pending_rubrics = [r for r in mind_rubrics if r["id"] not in self.completed_rubric_ids]

        logger.info(
            "Total Target Rubrics: %d | Pending: %d | Cases per Rubric: %d (Target Total: ~%d cases)",
            total_rubrics,
            len(pending_rubrics),
            self.cases_per_rubric,
            total_rubrics * self.cases_per_rubric,
        )

        if not pending_rubrics:
            logger.info("All rubrics already generated! Nothing to do.")
            return 0

        # Open output file in append mode
        start_time = time.time()
        cases_in_this_session = 0

        with open(self.output_path, "a", encoding="utf-8") as out_file:
            for idx, rubric in enumerate(pending_rubrics, start=1):
                if self.interrupted:
                    logger.info("Stopping generation loop cleanly.")
                    break

                r_id = rubric["id"]
                r_path = rubric.get("full_path") or self.kent_db.get_rubric_path(r_id)

                for c_idx in range(1, self.cases_per_rubric + 1):
                    try:
                        case = self.generator.generate_case_for_rubric(
                            rubric_id=r_id,
                            rubric_path=r_path,
                            case_idx=c_idx,
                        )
                        out_file.write(json.dumps(case.to_dict(), ensure_ascii=False) + "\n")
                        self.cases_generated_count += 1
                        cases_in_this_session += 1
                    except Exception as err:
                        logger.error(
                            "Error generating rubric ID %d ('%s') variation %d: %s",
                            r_id,
                            r_path,
                            c_idx,
                            err,
                        )
                        continue

                self.completed_rubric_ids.add(r_id)

                # Periodic checkpointing
                if (
                    cases_in_this_session > 0
                    and cases_in_this_session % self.checkpoint_interval == 0
                ):
                    out_file.flush()
                    self.save_checkpoint(last_rubric_id=r_id)
                    elapsed = time.time() - start_time
                    rate = cases_in_this_session / elapsed if elapsed > 0 else 0
                    logger.info(
                        "Progress: [%d/%d rubrics] | Total cases: %d | Rate: %.1f cases/sec",
                        len(self.completed_rubric_ids),
                        total_rubrics,
                        self.cases_generated_count,
                        rate,
                    )

            out_file.flush()
            self.save_checkpoint()

        elapsed = time.time() - start_time
        logger.info(
            "Generation session completed. Generated %d cases in %.2f seconds.",
            cases_in_this_session,
            elapsed,
        )
        return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate synthetic clinical cases from Kent MIND rubrics with crash-safe checkpointing."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/generation.yaml",
        help="Path to generation YAML configuration",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume generation from last saved checkpoint",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use deterministic mock generator for rapid offline validation/testing",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of rubrics to process (useful for testing)",
    )
    parser.add_argument(
        "--cases-per-rubric",
        type=int,
        default=None,
        help="Override number of cases generated per rubric",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override output JSONL file path",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Override checkpoint file path",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Automatically partition generated cases into train/val/test splits",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    runner = GenerationRunner(
        config_path=args.config,
        mock_mode=args.mock,
        resume=args.resume,
        limit=args.limit,
        cases_per_rubric=args.cases_per_rubric,
        output_file=args.output,
        checkpoint_file=args.checkpoint,
    )
    exit_code = runner.run()

    if args.split and exit_code == 0:
        logger.info("Executing dataset splitting into train/val/test partitions...")
        root = get_project_root()
        split_cfg = runner.config.get("splits", {})
        stats = split_and_save_jsonl(
            input_file=runner.output_path,
            train_file=root / split_cfg.get("train_file", "data/processed/train.jsonl"),
            val_file=root / split_cfg.get("val_file", "data/processed/val.jsonl"),
            test_file=root / split_cfg.get("test_file", "data/processed/test.jsonl"),
            train_ratio=split_cfg.get("train_ratio", 0.80),
            val_ratio=split_cfg.get("val_ratio", 0.10),
            test_ratio=split_cfg.get("test_ratio", 0.10),
            seed=split_cfg.get("seed", 42),
            stratify_by_rubric=split_cfg.get("stratify_by_rubric", True),
        )
        logger.info("Splits generated successfully:\n%s", json.dumps(stats, indent=2))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

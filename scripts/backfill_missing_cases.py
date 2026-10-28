#!/usr/bin/env python3
"""Targeted backfill utility: identifies and generates missing case variations.

Scans data/processed/mind_cases.jsonl, identifies rubrics with fewer than 4 variations,
generates only the missing variations with automated retry handling, and updates splits.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_cases import VARIATION_STYLES
from src.config import get_project_root, load_generation_config
from src.data.case_generator import CaseGenerator
from src.data.kent_db import KentDB
from src.data.splitter import split_and_save_jsonl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("backfill")


def run_backfill(
    cases_per_rubric: int = 4,
    output_file: Optional[Path] = None,
    max_retries: int = 3,
) -> int:
    root = get_project_root()
    output_path = output_file or (root / "data/processed/mind_cases.jsonl")
    checkpoint_path = root / "data/processed/generation_checkpoint.json"

    if not output_path.exists():
        logger.error("Dataset file %s does not exist.", output_path)
        return 1

    kent_db = KentDB()
    generator = CaseGenerator()

    # 1. Scan existing cases to find generated variations per rubric
    logger.info("Scanning %s for completed case variations...", output_path)
    existing_variations = defaultdict(set)
    total_existing = 0

    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total_existing += 1
            try:
                data = json.loads(line)
                r_id = data.get("rubric_id")
                c_idx = data.get("metadata", {}).get("case_idx")
                if r_id is not None and c_idx is not None:
                    existing_variations[int(r_id)].add(int(c_idx))
            except Exception as err:
                logger.warning("Failed to parse line: %s", err)

    mind_rubrics = kent_db.get_mind_rubrics()
    missing_tasks = []

    for rubric in mind_rubrics:
        r_id = rubric["id"]
        present = existing_variations.get(r_id, set())
        for c_idx in range(1, cases_per_rubric + 1):
            if c_idx not in present:
                missing_tasks.append((rubric, c_idx))

    logger.info("Found %d total cases currently logged in %s", total_existing, output_path.name)
    logger.info("Identified %d missing case variations across MIND rubrics.", len(missing_tasks))

    if not missing_tasks:
        logger.info("Corpus is 100% complete! No backfill needed.")
        return 0

    # 2. Generate and append missing variations with retries
    newly_generated = 0
    with open(output_path, "a", encoding="utf-8") as out_f:
        for rubric, c_idx in missing_tasks:
            r_id = rubric["id"]
            r_path = rubric.get("path") or rubric.get("full_path") or kent_db.get_rubric_path(r_id)
            logger.info("Generating Rubric %d (Var %d/4): %s", r_id, c_idx, r_path)

            success = False
            for attempt in range(1, max_retries + 1):
                try:
                    generator.seed = 42 + (attempt * 1013)
                    case = generator.generate_case_for_rubric(
                        rubric_id=r_id,
                        rubric_path=r_path,
                        case_idx=c_idx,
                        variation_instruction=VARIATION_STYLES.get(c_idx),
                    )
                    case.metadata["variation_style"] = VARIATION_STYLES.get(c_idx, "Standard")
                    out_f.write(json.dumps(case.to_dict(), ensure_ascii=False) + "\n")
                    out_f.flush()
                    newly_generated += 1
                    logger.info("  -> [OK] Generated on attempt %d.", attempt)
                    success = True
                    break
                except Exception as err:
                    logger.warning("  -> [RETRY %d/%d] Rubric %d Var %d: %s", attempt, max_retries, r_id, c_idx, err)
                    time.sleep(1.5 * attempt)

            if not success:
                logger.error("  -> [FAILED] Could not generate Rubric %d Var %d after %d attempts.", r_id, c_idx, max_retries)

    logger.info("Backfill generation phase complete. Successfully added %d cases.", newly_generated)

    # 3. Update checkpoint if exists
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                ckpt = json.load(f)
            ckpt["cases_generated_count"] = total_existing + newly_generated
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(ckpt, f, indent=2)
            logger.info("Updated checkpoint: total cases = %d", ckpt["cases_generated_count"])
        except Exception as err:
            logger.warning("Could not update checkpoint file: %s", err)

    # 4. Re-partition dataset splits
    logger.info("Re-partitioning dataset into train/val/test splits...")
    config = load_generation_config()
    split_cfg = config.get("splits", {})
    stats = split_and_save_jsonl(
        input_file=output_path,
        train_file=root / split_cfg.get("train_file", "data/processed/train.jsonl"),
        val_file=root / split_cfg.get("val_file", "data/processed/val.jsonl"),
        test_file=root / split_cfg.get("test_file", "data/processed/test.jsonl"),
        train_ratio=split_cfg.get("train_ratio", 0.80),
        val_ratio=split_cfg.get("val_ratio", 0.10),
        test_ratio=split_cfg.get("test_ratio", 0.10),
        seed=split_cfg.get("seed", 42),
        stratify_by_rubric=split_cfg.get("stratify_by_rubric", True),
    )
    logger.info("Splits re-generated successfully:\n%s", json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(run_backfill())


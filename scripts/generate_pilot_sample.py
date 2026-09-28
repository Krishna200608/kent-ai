#!/usr/bin/env python3
"""CLI Script: Generate Stratified Pilot Sample (100 Cases) across Kent's MIND Chapter.

Generates 100 clinical case vignettes (25 diverse rubrics x 4 clinical variations)
using local LLaMA 3 (via Ollama) with atomic checkpointing, temperature seeding,
and thermal cooldown between generations.
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
from typing import Any, Dict, List, Optional, Set

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_generation_config, get_project_root
from src.data.case_generator import CaseGenerator, SyntheticCase
from src.data.kent_db import KentDB, get_remedies, get_rubric_path

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "pilot_generation.log", mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("pilot_generator")

# 5 Core Psychiatric / Emotional Categories (5 representative rubrics each = 25 total)
STRATIFIED_CATEGORIES = {
    "1. Anxiety & Fear": [
        "MIND > ANXIETY > night",
        "MIND > ANXIETY > fear, with",
        "MIND > FEAR > death, of",
        "MIND > FEAR > crowd, in a",
        "MIND > ANXIETY > twilight, at",
    ],
    "2. Affective & Grief": [
        "MIND > SADNESS, mental depression > evening",
        "MIND > SADNESS, mental depression > morning",
        "MIND > GRIEF > ailments, from",
        "MIND > DESPAIR > recovery, of",
        "MIND > WEEPING > tearful mood > alone, when",
    ],
    "3. Cognitive & Intellect": [
        "MIND > FORGETFUL > words, of, speaking, while",
        "MIND > CONFUSION of mind > morning",
        "MIND > CONFUSION of mind > evening",
        "MIND > MISTAKES in calculating > speaking",
        "MIND > MEMORY, weakness of",
    ],
    "4. Behavioral & Volition": [
        "MIND > RESTLESSNESS, nervousness > night",
        "MIND > RESTLESSNESS, nervousness > anxious, etc",
        "MIND > HURRY > movements, in",
        "MIND > IRRITABILITY > morning",
        "MIND > ANGER, irascibility > contradiction, from",
    ],
    "5. Perceptual & Somatopsychic": [
        "MIND > DELUSIONS > images, phantoms, sees",
        "MIND > SENSITIVE, oversensitive > noise, to",
        "MIND > SENSITIVE, oversensitive > music, to",
        "MIND > SUSPICIOUS",
        "MIND > EXCITEMENT, emotional",
    ],
}

# Clinical variation styles to ensure semantic diversity across the 4 runs
VARIATION_STYLES = {
    1: "Present as a somatizing patient focusing on physical discomfort and bodily sensations linked to emotional distress.",
    2: "Present as a natural, conversational narrative describing daily life impact and interpersonal struggles.",
    3: "Present as an introverted, hesitant patient giving concise, understated descriptions with clear environmental modalities.",
    4: "Present as an acutely expressive patient in intense distress with vivid temporal triggers and prominent accompanying symptoms.",
}


class PilotRunner:
    """Orchestrates generation of the 100-case quality evaluation pilot."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        mock_mode: bool = False,
        resume: bool = False,
        cases_per_rubric: int = 4,
        output_file: str = "data/processed/pilot_100_cases.jsonl",
        checkpoint_file: str = "data/processed/pilot_checkpoint.json",
        cooldown_sec: float = 1.0,
    ) -> None:
        self.config = get_generation_config(config_path)
        self.mock_mode = mock_mode
        self.resume = resume
        self.cases_per_rubric = cases_per_rubric
        self.cooldown_sec = cooldown_sec

        root = get_project_root()
        self.output_path = root / output_file
        self.checkpoint_path = root / checkpoint_file
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        self.generator = CaseGenerator(config=self.config, mock_mode=self.mock_mode)
        self.kent_db = KentDB()

        self.completed_rubric_ids: Set[int] = set()
        self.cases_generated_count: int = 0
        self.interrupted: bool = False

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.warning("\n[INTERRUPT] Graceful shutdown requested! Saving checkpoint...")
        self.interrupted = True

    def load_checkpoint(self) -> None:
        """Load state from previous checkpoint file if resuming."""
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
            logger.warning("Could not read checkpoint (%s). Starting clean.", err)

    def save_checkpoint(self, last_rubric_id: Optional[int] = None) -> None:
        """Atomically persist generation checkpoint."""
        data = {
            "completed_rubric_ids": sorted(list(self.completed_rubric_ids)),
            "cases_generated_count": self.cases_generated_count,
            "last_rubric_id": last_rubric_id,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        temp_path = self.checkpoint_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp_path.replace(self.checkpoint_path)

    def resolve_stratified_rubrics(self) -> List[Dict[str, Any]]:
        """Fetch matching rubric records from SQLite database."""
        chosen_rubrics: List[Dict[str, Any]] = []
        with self.kent_db.connect() as conn:
            for cat_name, rubric_patterns in STRATIFIED_CATEGORIES.items():
                for pattern in rubric_patterns:
                    clean_kw = pattern.split(">")[-1].strip().split(",")[0].strip()
                    parent_kw = pattern.split(">")[1].strip() if ">" in pattern else clean_kw
                    
                    sql = """
                        SELECT r.id, r.label, r.path, r.depth, COUNT(rr.id) AS rem_count
                        FROM rubrics r
                        LEFT JOIN rubric_remedies rr ON r.id = rr.rubric_id
                        WHERE r.section_id = 1 AND r.path LIKE ?
                        GROUP BY r.id
                        ORDER BY rem_count DESC
                        LIMIT 1
                    """
                    row = conn.execute(sql, (f"%{clean_kw}%",)).fetchone()
                    if not row or row[0] in [r["id"] for r in chosen_rubrics]:
                        # Fallback to parent keyword
                        row = conn.execute(sql, (f"%{parent_kw}%",)).fetchone()
                    
                    if row and row[0] not in [r["id"] for r in chosen_rubrics]:
                        chosen_rubrics.append({
                            "id": row[0],
                            "label": row[1],
                            "path": row[2] or pattern,
                            "remedies": row[4],
                            "category": cat_name,
                        })

        # Ensure we have exactly 25 rubrics
        if len(chosen_rubrics) < 25:
            with self.kent_db.connect() as conn:
                fill_sql = """
                    SELECT r.id, r.label, r.path, r.depth, COUNT(rr.id) AS rem_count
                    FROM rubrics r
                    JOIN rubric_remedies rr ON r.id = rr.rubric_id
                    WHERE r.section_id = 1 AND r.depth >= 1
                    GROUP BY r.id
                    HAVING rem_count >= 10
                    ORDER BY r.id
                    LIMIT ?
                """
                for row in conn.execute(fill_sql, (50,)).fetchall():
                    if len(chosen_rubrics) >= 25:
                        break
                    if row[0] not in [r["id"] for r in chosen_rubrics]:
                        chosen_rubrics.append({
                            "id": row[0],
                            "label": row[1],
                            "path": row[2],
                            "remedies": row[4],
                            "category": "General MIND Rubric",
                        })

        return chosen_rubrics[:25]

    def run(self) -> int:
        """Execute pilot case generation."""
        logger.info("=" * 65)
        logger.info("  KENT-AI: STRATIFIED PILOT GENERATION (100 CLINICAL CASES)")
        logger.info("=" * 65)
        logger.info("Backend          : %s (%s)", self.generator.backend, self.generator.model)
        logger.info("Output File      : %s", self.output_path)
        logger.info("Checkpoint File  : %s", self.checkpoint_path)
        logger.info("Cases per Rubric : %d", self.cases_per_rubric)
        logger.info("Inter-Case Pause : %.1fs (thermal guard)", self.cooldown_sec)
        logger.info("=" * 65)

        self.load_checkpoint()
        target_rubrics = self.resolve_stratified_rubrics()
        pending = [r for r in target_rubrics if r["id"] not in self.completed_rubric_ids]

        logger.info(
            "Selected %d Stratified Rubrics (%d Pending | ~%d Total Cases Target)",
            len(target_rubrics),
            len(pending),
            len(target_rubrics) * self.cases_per_rubric,
        )

        if not pending:
            logger.info("All 100 pilot cases already generated in checkpoint! Nothing to do.")
            return 0

        session_start = time.time()
        cases_in_session = 0

        with open(self.output_path, "a", encoding="utf-8") as f_out:
            for idx, rubric in enumerate(pending, start=1):
                if self.interrupted:
                    logger.info("Interrupted. Saved progress up to rubric ID %s.", rubric["id"])
                    break

                r_id = rubric["id"]
                r_path = rubric["path"]
                r_cat = rubric.get("category", "MIND")
                logger.info(
                    "[%d/%d] Generating Rubric ID %d [%s]: '%s'",
                    idx,
                    len(pending),
                    r_id,
                    r_cat,
                    r_path,
                )

                for var_idx in range(1, self.cases_per_rubric + 1):
                    if self.interrupted:
                        break

                    t0 = time.time()
                    try:
                        case = self.generator.generate_case_for_rubric(
                            rubric_id=r_id,
                            rubric_path=r_path,
                            case_idx=var_idx,
                            variation_instruction=VARIATION_STYLES.get(var_idx),
                        )
                        # Enrich metadata with category and style
                        case.metadata["category"] = r_cat
                        case.metadata["variation_style"] = VARIATION_STYLES.get(var_idx, "Standard")

                        f_out.write(json.dumps(case.to_dict(), ensure_ascii=False) + "\n")
                        f_out.flush()

                        self.cases_generated_count += 1
                        cases_in_session += 1
                        dt = time.time() - t0

                        logger.info(
                            "   -> Variation %d/%d generated (%d tokens, %d entities) in %.1fs",
                            var_idx,
                            self.cases_per_rubric,
                            len(case.tokens),
                            len(case.entities),
                            dt,
                        )

                        # Gentle thermal cooldown
                        if self.cooldown_sec > 0:
                            time.sleep(self.cooldown_sec)

                    except Exception as err:
                        logger.error(
                            "   -> Error on rubric ID %d variation %d: %s",
                            r_id,
                            var_idx,
                            err,
                        )
                        continue

                self.completed_rubric_ids.add(r_id)
                self.save_checkpoint(last_rubric_id=r_id)

        total_time = time.time() - session_start
        rate = cases_in_session / total_time if total_time > 0 else 0
        logger.info("=" * 65)
        logger.info(
            "Pilot run complete! Generated %d cases in %.1f minutes (%.2f cases/min).",
            cases_in_session,
            total_time / 60.0,
            rate * 60.0,
        )
        logger.info("Output saved to: %s", self.output_path)
        logger.info("=" * 65)
        return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate 100 stratified pilot clinical cases for professor review."
    )
    parser.add_argument(
        "--cases-per-rubric",
        type=int,
        default=4,
        help="Number of clinical variations per rubric (default: 4, giving 25 * 4 = 100 cases)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume generation from last saved checkpoint",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use deterministic mock generator for rapid dry-run testing",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/pilot_100_cases.jsonl",
        help="Output JSONL file path",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="data/processed/pilot_checkpoint.json",
        help="Checkpoint JSON file path",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=1.0,
        help="Cooldown pause in seconds between cases to prevent laptop thermal throttling",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    runner = PilotRunner(
        mock_mode=args.mock,
        resume=args.resume,
        cases_per_rubric=args.cases_per_rubric,
        output_file=args.output,
        checkpoint_file=args.checkpoint,
        cooldown_sec=args.cooldown,
    )
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())

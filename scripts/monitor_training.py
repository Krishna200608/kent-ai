#!/usr/bin/env python3
"""Monitor HomeoNER Fine-Tuning Progress and Validation Metrics across any model."""

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def parse_args():
    parser = argparse.ArgumentParser(description="Monitor HomeoNER training progress")
    parser.add_argument(
        "--model-dir",
        type=str,
        default=None,
        help="Model directory to monitor (default: auto-detect most active model in data/models/)",
    )
    return parser.parse_args()


def find_latest_checkpoint_file(target_dir: Optional[str] = None) -> Optional[str]:
    """Find the most recently updated trainer_state.json across model directories."""
    if target_dir:
        pattern = os.path.join(target_dir, "checkpoints", "checkpoint-*", "trainer_state.json")
        states = sorted(glob.glob(pattern), key=os.path.getmtime)
        return states[-1] if states else None

    # Search all models in data/models
    all_states = sorted(
        glob.glob("data/models/*/checkpoints/checkpoint-*/trainer_state.json"),
        key=os.path.getmtime,
    )
    return all_states[-1] if all_states else None


def main():
    args = parse_args()

    print("=" * 65)
    print("  Kent-AI Phase 3: HomeoNER Training Monitor")
    print("=" * 65)

    # Check GPU process
    try:
        proc_out = subprocess.check_output(
            ["pgrep", "-fa", "scripts/train_ner.py"], text=True
        ).strip()
        print(f"Status: RUNNING (PID: {proc_out.split()[0]})")
    except subprocess.CalledProcessError:
        print("Status: NOT RUNNING / FINISHED")

    latest = find_latest_checkpoint_file(args.model_dir)
    if not latest:
        print("No checkpoints found.")
        return

    model_name = Path(latest).parents[2].name
    print(f"Active Model:      {model_name}")

    with open(latest) as f:
        data = json.load(f)

    epoch = data.get("epoch", 0.0)
    step = data.get("global_step", 0)
    max_steps = data.get("max_steps", 0)
    pct = (step / max_steps) * 100 if max_steps else 0.0

    print(f"Latest Checkpoint: {latest}")
    print(f"Epoch:             {epoch:.2f} / {data.get('num_train_epochs', 8)}")
    print(f"Global Steps:      {step} / {max_steps} ({pct:.1f}%)")
    print(f"Best Eval F1:      {data.get('best_metric', 0.0):.4f}")

    evals = [h for h in data.get("log_history", []) if "eval_loss" in h]
    if evals:
        print("\nValidation Progress History:")
        print(f"{'Epoch':<8} {'Eval Loss':<12} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
        print("-" * 68)
        for e in evals:
            print(
                f"{e.get('epoch', 0.0):<8.1f} "
                f"{float(e.get('eval_loss', 0)):<12.4f} "
                f"{float(e.get('eval_accuracy', 0)):<12.4f} "
                f"{float(e.get('eval_precision', 0)):<12.4f} "
                f"{float(e.get('eval_recall', 0)):<12.4f} "
                f"{float(e.get('eval_f1', 0)):<12.4f}"
            )
    print("=" * 65)


if __name__ == "__main__":
    main()


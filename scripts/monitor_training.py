#!/usr/bin/env python3
"""Monitor Bio_ClinicalBERT Fine-Tuning Progress and Validation Metrics."""

import glob
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    print("=" * 65)
    print("  Kent-AI Phase 3: Bio_ClinicalBERT HomeoNER Training Monitor")
    print("=" * 65)

    # Check GPU process
    try:
        proc_out = subprocess.check_output(
            ["pgrep", "-fa", "scripts/train_ner.py"], text=True
        ).strip()
        print(f"Status: RUNNING (PID: {proc_out.split()[0]})")
    except subprocess.CalledProcessError:
        print("Status: NOT RUNNING / FINISHED")

    # Check checkpoints
    states = sorted(
        glob.glob("data/models/clinicalbert_homeoNER/checkpoints/checkpoint-*/trainer_state.json")
    )
    if not states:
        print("No checkpoints saved yet.")
        return

    latest = states[-1]
    with open(latest) as f:
        data = json.load(f)

    epoch = data.get("epoch", 0.0)
    step = data.get("global_step", 0)
    max_steps = data.get("max_steps", 9870)
    pct = (step / max_steps) * 100 if max_steps else 0.0

    print(f"\nLatest Checkpoint: {latest}")
    print(f"Epoch:             {epoch:.2f} / 10.0")
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

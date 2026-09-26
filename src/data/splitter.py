"""Reproducible dataset partitioning into train, validation, and test splits.

Phase 1 target: Stratifies generated MIND clinical cases into 80/10/10 partitions
ensuring balanced rubric representation and clinical diversity across splits.
"""

from __future__ import annotations

import json
import logging
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def split_cases(
    cases: List[Dict[str, Any]],
    train_ratio: float = 0.80,
    val_ratio: float = 0.10,
    test_ratio: float = 0.10,
    seed: int = 42,
    stratify_by_rubric: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split dataset into reproducible train/val/test partitions.
    
    Args:
        cases: List of case dictionaries (each containing 'rubric_id', 'narrative', etc.).
        train_ratio: Proportion of cases for training (e.g. 0.80).
        val_ratio: Proportion of cases for validation (e.g. 0.10).
        test_ratio: Proportion of cases for testing (e.g. 0.10).
        seed: Random seed for deterministic reproducibility.
        stratify_by_rubric: If True, stratifies by rubric_id so each rubric's cases
                            are distributed proportionally across splits.
                            
    Returns:
        Tuple of (train_cases, val_cases, test_cases).
        
    Raises:
        ValueError: If ratios do not sum to ~1.0 or if cases list is empty.
    """
    if not cases:
        return [], [], []

    ratio_sum = train_ratio + val_ratio + test_ratio
    if abs(ratio_sum - 1.0) > 1e-4:
        raise ValueError(
            f"Split ratios must sum to 1.0, got {train_ratio} + {val_ratio} + {test_ratio} = {ratio_sum}"
        )

    rng = random.Random(seed)

    if not stratify_by_rubric:
        shuffled = list(cases)
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        return shuffled[:n_train], shuffled[n_train : n_train + n_val], shuffled[n_train + n_val :]

    # Compute exact global targets
    n_total = len(cases)
    target_train = int(round(n_total * train_ratio))
    target_val = int(round(n_total * val_ratio))
    target_test = n_total - target_train - target_val

    # Group cases by rubric_id
    rubric_groups: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for case in cases:
        r_id = case.get("rubric_id", -1)
        rubric_groups[r_id].append(case)

    train_cases: List[Dict[str, Any]] = []
    val_cases: List[Dict[str, Any]] = []
    test_cases: List[Dict[str, Any]] = []

    # Sort rubric IDs for deterministic ordering before shuffling groups
    sorted_rubrics = sorted(rubric_groups.keys())

    # Step 1: Base allocation to train for each rubric (guaranteeing representation)
    unassigned_cases: List[Dict[str, Any]] = []
    for r_id in sorted_rubrics:
        group = list(rubric_groups[r_id])
        rng.shuffle(group)
        k = len(group)
        # Guaranteed train portion
        base_train_count = int(k * train_ratio)
        if base_train_count > 0 and len(train_cases) + base_train_count <= target_train:
            train_cases.extend(group[:base_train_count])
            unassigned_cases.extend(group[base_train_count:])
        else:
            unassigned_cases.extend(group)

    # Step 2: Assign remaining cases to splits based on current deficit
    rng.shuffle(unassigned_cases)
    for case in unassigned_cases:
        deficits = {
            "train": target_train - len(train_cases),
            "val": target_val - len(val_cases),
            "test": target_test - len(test_cases),
        }
        # Choose split with largest remaining deficit
        best_split = max(deficits.keys(), key=lambda s: (deficits[s], rng.random()))
        if best_split == "train":
            train_cases.append(case)
        elif best_split == "val":
            val_cases.append(case)
        else:
            test_cases.append(case)

    # Final shuffle for each split
    rng.shuffle(train_cases)
    rng.shuffle(val_cases)
    rng.shuffle(test_cases)

    return train_cases, val_cases, test_cases



def compute_split_statistics(
    train_cases: List[Dict[str, Any]],
    val_cases: List[Dict[str, Any]],
    test_cases: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute summary statistics for generated dataset splits.
    
    Args:
        train_cases: List of train cases.
        val_cases: List of val cases.
        test_cases: List of test cases.
        
    Returns:
        Dictionary containing counts, entity distributions, and token metrics.
    """
    total = len(train_cases) + len(val_cases) + len(test_cases)

    def stats_for_split(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        rubrics = set(c.get("rubric_id") for c in cases)
        entity_counts: Counter[str] = Counter()
        token_lengths: List[int] = []

        for c in cases:
            for ent in c.get("entities", []):
                entity_counts[ent.get("label", "UNKNOWN")] += 1
            tokens = c.get("tokens", [])
            token_lengths.append(len(tokens) if tokens else len(c.get("narrative", "").split()))

        avg_tokens = sum(token_lengths) / len(token_lengths) if token_lengths else 0.0

        return {
            "case_count": len(cases),
            "ratio": round(len(cases) / total, 4) if total > 0 else 0.0,
            "unique_rubrics": len(rubrics),
            "avg_tokens_per_case": round(avg_tokens, 1),
            "entity_counts": dict(entity_counts),
            "total_entities": sum(entity_counts.values()),
        }

    return {
        "total_cases": total,
        "train": stats_for_split(train_cases),
        "val": stats_for_split(val_cases),
        "test": stats_for_split(test_cases),
    }


def split_and_save_jsonl(
    input_file: Union[Path, str],
    train_file: Union[Path, str],
    val_file: Union[Path, str],
    test_file: Union[Path, str],
    train_ratio: float = 0.80,
    val_ratio: float = 0.10,
    test_ratio: float = 0.10,
    seed: int = 42,
    stratify_by_rubric: bool = True,
) -> Dict[str, Any]:
    """Load cases from JSONL file, partition into splits, and save output files.
    
    Args:
        input_file: Path to source mind_cases.jsonl.
        train_file: Output path for train split.
        val_file: Output path for val split.
        test_file: Output path for test split.
        train_ratio: Training ratio (0.80).
        val_ratio: Validation ratio (0.10).
        test_ratio: Testing ratio (0.10).
        seed: Random seed.
        stratify_by_rubric: Whether to stratify by rubric.
        
    Returns:
        Summary statistics dictionary.
    """
    input_p = Path(input_file)
    if not input_p.exists():
        raise FileNotFoundError(f"Source cases file not found: {input_p}")

    cases: List[Dict[str, Any]] = []
    with open(input_p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))

    train, val, test = split_cases(
        cases=cases,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed,
        stratify_by_rubric=stratify_by_rubric,
    )

    for cases_list, out_path in [
        (train, Path(train_file)),
        (val, Path(val_file)),
        (test, Path(test_file)),
    ]:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for item in cases_list:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return compute_split_statistics(train, val, test)

#!/usr/bin/env python3
"""CLI Script: Comprehensive Academic Evaluation Suite (Phase C / Phase 5).

Evaluates the two-stage Kent-AI pipeline over the held-out test split (test.jsonl):
1. Token & Entity-Level HomeoNER Metrics via SeqEval across 7 symptom dimensions.
2. Rubric Retrieval Recall@K (K in {1, 5, 10, 20}) and Mean Reciprocal Rank (MRR).
3. Simillimum Remedy Indication Accuracy (Top-1, Top-3, Top-5).
4. Persists quantitative results to JSON and academic Markdown report.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure project repository root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import seqeval.metrics

from src.config import get_project_root
from src.data.bio_tagger import BIOTagger
from src.models.resolver import SymptomProfile, SymptomResolver
from src.models.symptom_ner import SymptomNER
from src.pipeline.orchestrator import PipelineOrchestrator
from src.search.embedder import RubricEmbedder
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("evaluate")


def normalize_remedy_name(name: str) -> str:
    """Normalize remedy abbreviation or full name for fuzzy clinical matching."""
    return name.strip().rstrip(".").lower()


class PipelineEvaluator:
    """Orchestrates comprehensive academic evaluation across all pipeline stages."""

    TARGETS = {
        "bio_f1": 0.88,
        "token_accuracy": 0.80,
        "top20_recall": 0.90,
        "mrr": 0.65,
    }

    DIMENSIONS = ["LOC", "SEN", "MOD_AGG", "MOD_AMEL", "CONC", "TEMP", "MENT"]

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        mock_mode: bool = False,
        device: Optional[str] = None,
    ) -> None:
        self.mock_mode = mock_mode
        self.tagger = BIOTagger(categories=self.DIMENSIONS)
        self.ner = SymptomNER(model_path=model_path, mock_mode=mock_mode, device=device)
        self.resolver = SymptomResolver(mock_mode=mock_mode)
        
        embedder = RubricEmbedder(mock_mode=mock_mode)
        self.vector_store = RubricVectorStore(embedder=embedder)
        self.ranker = RemedyRanker()

    def evaluate_dataset(
        self,
        test_file: str | Path,
        limit: Optional[int] = None,
        batch_size: int = 32,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """Run full evaluation suite on test dataset.
        
        Args:
            test_file: Path to test.jsonl.
            limit: Optional sample limit.
            batch_size: Evaluation batch size.
            show_progress: Whether to log periodic progress.
            
        Returns:
            Dictionary containing metrics, confusion breakdown, and metadata.
        """
        path = Path(test_file)
        if not path.exists():
            raise FileNotFoundError(f"Test dataset not found at {path}")

        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                if limit and len(records) >= limit:
                    break

        total_cases = len(records)
        if total_cases == 0:
            raise ValueError(f"No valid records found in {path}")

        logger.info("Evaluating on %d test cases from %s...", total_cases, path)
        start_time = time.time()

        # Data collection containers
        all_gold_bio: List[List[str]] = []
        all_pred_bio: List[List[str]] = []

        retrieval_hits_1 = 0
        retrieval_hits_5 = 0
        retrieval_hits_10 = 0
        retrieval_hits_20 = 0
        reciprocal_ranks: List[float] = []

        remedy_eval_cases = 0
        remedy_hits_1 = 0
        remedy_hits_3 = 0
        remedy_hits_5 = 0

        # Pre-fetch remedies for rubrics in test set to avoid repetitive DB hits
        unique_rubric_ids = list({r["rubric_id"] for r in records if "rubric_id" in r})
        rubric_remedies_map = self.ranker._fetch_rubrics_remedies_batch(unique_rubric_ids)

        for idx, case in enumerate(records):
            narrative = case.get("narrative", "")
            target_rubric_id = int(case.get("rubric_id", 0))
            gold_tokens = case.get("tokens", [])
            gold_bio = case.get("bio_tags", [])

            # -------------------------------------------------------------
            # Stage 1: HomeoNER Evaluation
            # -------------------------------------------------------------
            pred_entities = self.ner.extract_entities(narrative)
            
            # If gold tokens/BIO exist, align predicted entities to gold tokens
            if gold_tokens and gold_bio:
                _, pred_bio = self.tagger.tag_tokens(narrative, pred_entities)
                # Pad/truncate to match gold token length if slight mismatch
                if len(pred_bio) < len(gold_bio):
                    pred_bio.extend(["O"] * (len(gold_bio) - len(pred_bio)))
                else:
                    pred_bio = pred_bio[: len(gold_bio)]
                all_gold_bio.append(gold_bio)
                all_pred_bio.append(pred_bio)

            # -------------------------------------------------------------
            # Stage 2: Symptom Resolution & Search Query Synthesis
            # -------------------------------------------------------------
            profile: SymptomProfile = self.resolver.resolve(narrative, raw_entities=pred_entities)
            search_queries = profile.get_search_queries()
            if narrative and narrative not in search_queries:
                search_queries.append(narrative)

            # -------------------------------------------------------------
            # Stage 3: Dense Rubric Retrieval Evaluation
            # -------------------------------------------------------------
            # Pool candidates across queries
            cand_dict: Dict[int, Dict[str, Any]] = {}
            for q in search_queries[:5]:
                try:
                    cands = self.vector_store.query(q, top_k=20, section_id=1)
                    for cand in cands:
                        r_id = cand["rubric_id"]
                        if r_id not in cand_dict or cand["similarity"] > cand_dict[r_id]["similarity"]:
                            cand_dict[r_id] = cand
                except Exception:
                    continue

            # Sort pooled candidate matches by similarity
            ranked_cands = sorted(cand_dict.values(), key=lambda x: x.get("similarity", 0.0), reverse=True)
            retrieved_ids = [c["rubric_id"] for c in ranked_cands[:20]]

            # Rubric Recall & MRR
            if target_rubric_id in retrieved_ids:
                rank = retrieved_ids.index(target_rubric_id) + 1
                reciprocal_ranks.append(1.0 / rank)
                retrieval_hits_20 += 1
                if rank <= 10:
                    retrieval_hits_10 += 1
                if rank <= 5:
                    retrieval_hits_5 += 1
                if rank == 1:
                    retrieval_hits_1 += 1
            else:
                reciprocal_ranks.append(0.0)

            # -------------------------------------------------------------
            # Stage 4: Simillimum Remedy Accuracy Evaluation
            # -------------------------------------------------------------
            # Ground truth remedies: from case metadata or DB
            meta_remedies = case.get("metadata", {}).get("top_remedies", [])
            if not meta_remedies:
                db_rems = rubric_remedies_map.get(target_rubric_id, [])
                meta_remedies = [r["abbreviation"] for r in db_rems]

            if meta_remedies:
                remedy_eval_cases += 1
                gold_rems_norm = {normalize_remedy_name(r) for r in meta_remedies if r}

                ranked_remedies = self.ranker.rank(ranked_cands[:20], top_n=10)
                pred_rems_norm = [
                    normalize_remedy_name(r["abbreviation"])
                    for r in ranked_remedies
                    if r.get("abbreviation")
                ]

                # Check top-1, top-3, top-5 hits
                if any(r in gold_rems_norm for r in pred_rems_norm[:1]):
                    remedy_hits_1 += 1
                if any(r in gold_rems_norm for r in pred_rems_norm[:3]):
                    remedy_hits_3 += 1
                if any(r in gold_rems_norm for r in pred_rems_norm[:5]):
                    remedy_hits_5 += 1

            # Progress log every 100 cases
            if show_progress and (idx + 1) % 100 == 0:
                elapsed = time.time() - start_time
                logger.info("Processed %d / %d cases (%.1fs elapsed)...", idx + 1, total_cases, elapsed)

        elapsed_total = time.time() - start_time

        # -----------------------------------------------------------------
        # Compute SeqEval NER Metrics
        # -----------------------------------------------------------------
        bio_f1 = 0.0
        bio_precision = 0.0
        bio_recall = 0.0
        token_accuracy = 0.0
        classification_dict: Dict[str, Any] = {}

        if all_gold_bio and all_pred_bio:
            try:
                bio_f1 = float(seqeval.metrics.f1_score(all_gold_bio, all_pred_bio, zero_division=0))
                bio_precision = float(seqeval.metrics.precision_score(all_gold_bio, all_pred_bio, zero_division=0))
                bio_recall = float(seqeval.metrics.recall_score(all_gold_bio, all_pred_bio, zero_division=0))
                token_accuracy = float(seqeval.metrics.accuracy_score(all_gold_bio, all_pred_bio))
                classification_dict = seqeval.metrics.classification_report(
                    all_gold_bio, all_pred_bio, output_dict=True, zero_division=0
                )
            except Exception as err:
                logger.warning("SeqEval metric computation encountered warning: %s", err)

        # -----------------------------------------------------------------
        # Compute Retrieval & Remedy Metrics
        # -----------------------------------------------------------------
        top1_recall = float(retrieval_hits_1) / total_cases
        top5_recall = float(retrieval_hits_5) / total_cases
        top10_recall = float(retrieval_hits_10) / total_cases
        top20_recall = float(retrieval_hits_20) / total_cases
        mrr = float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0

        rem_acc_1 = (float(remedy_hits_1) / remedy_eval_cases) if remedy_eval_cases > 0 else 0.0
        rem_acc_3 = (float(remedy_hits_3) / remedy_eval_cases) if remedy_eval_cases > 0 else 0.0
        rem_acc_5 = (float(remedy_hits_5) / remedy_eval_cases) if remedy_eval_cases > 0 else 0.0

        results: Dict[str, Any] = {
            "dataset": str(path),
            "total_cases": total_cases,
            "elapsed_seconds": round(elapsed_total, 2),
            "cases_per_second": round(total_cases / max(0.001, elapsed_total), 2),
            "mock_mode": self.mock_mode,
            "metrics": {
                "token_level_bio_f1": round(bio_f1, 4),
                "token_accuracy": round(token_accuracy, 4),
                "bio_precision": round(bio_precision, 4),
                "bio_recall": round(bio_recall, 4),
                "top1_rubric_recall": round(top1_recall, 4),
                "top5_rubric_recall": round(top5_recall, 4),
                "top10_rubric_recall": round(top10_recall, 4),
                "top20_rubric_recall": round(top20_recall, 4),
                "mean_reciprocal_rank": round(mrr, 4),
                "simillimum_acc_top1": round(rem_acc_1, 4),
                "simillimum_acc_top3": round(rem_acc_3, 4),
                "simillimum_acc_top5": round(rem_acc_5, 4),
                "remedy_eval_cases": remedy_eval_cases,
            },
            "per_dimension": {},
            # Target thresholds for automated parsing
            "bio_f1": round(bio_f1, 4),
            "top20_recall": round(top20_recall, 4),
            "mrr": round(mrr, 4),
        }

        # Populate per-dimension breakdown
        for dim in self.DIMENSIONS:
            if dim in classification_dict:
                d_meta = classification_dict[dim]
                results["per_dimension"][dim] = {
                    "precision": round(float(d_meta.get("precision", 0.0)), 4),
                    "recall": round(float(d_meta.get("recall", 0.0)), 4),
                    "f1": round(float(d_meta.get("f1-score", 0.0)), 4),
                    "support": int(d_meta.get("support", 0)),
                }

        return results

    @classmethod
    def generate_markdown_report(cls, results: Dict[str, Any]) -> str:
        """Render academic benchmark evaluation report in GitHub-flavored Markdown."""
        m = results["metrics"]
        per_dim = results.get("per_dimension", {})

        md: List[str] = [
            "# Kent-AI: Academic Benchmark Evaluation Report",
            "",
            "> **Project**: Kent-AI — AI-Powered Clinical Assistant for Homeopathic Repertorization  ",
            f"> **Evaluation Dataset**: `{results.get('dataset', 'test.jsonl')}` (N = {results.get('total_cases', 0):,} cases)  ",
            f"> **Execution Mode**: {'Mock Mode (Offline Deterministic)' if results.get('mock_mode') else 'Production ClinicalBERT + ChromaDB HNSW'}  ",
            f"> **Throughput**: {results.get('cases_per_second', 0.0):.2f} cases/sec ({results.get('elapsed_seconds', 0.0):.1f}s total)  ",
            f"> **Date**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  ",
            "",
            "---",
            "",
            "## 1. Executive Summary & Exit Criteria Ledger",
            "",
            "| Pipeline Stage | Evaluation Metric | Measured | Target Threshold | Exit Status |",
            "| :--- | :--- | :--- | :--- | :--- |",
            f"| **ClinicalBERT NER** | Token-level BIO F1 | **{m['token_level_bio_f1'] * 100:.2f}%** | ≥ 88.0% | {'✅ Pass' if m['token_level_bio_f1'] >= 0.88 else '⚠️ Review'} |",
            f"| **ClinicalBERT NER** | Token Classification Accuracy | **{m['token_accuracy'] * 100:.2f}%** | ≥ 80.0% | {'✅ Pass' if m['token_accuracy'] >= 0.80 else '⚠️ Review'} |",
            f"| **ChromaDB Retrieval** | Top-20 Rubric Recall (Recall@20) | **{m['top20_rubric_recall'] * 100:.2f}%** | ≥ 90.0% | {'✅ Pass' if m['top20_rubric_recall'] >= 0.90 else '⚠️ Review'} |",
            f"| **ChromaDB Retrieval** | Mean Reciprocal Rank (MRR) | **{m['mean_reciprocal_rank']:.4f}** | ≥ 0.650 | {'✅ Pass' if m['mean_reciprocal_rank'] >= 0.65 else '⚠️ Review'} |",
            f"| **Repertory Ranker** | Simillimum Remedy Accuracy (Top-5) | **{m['simillimum_acc_top5'] * 100:.2f}%** | ≥ 70.0% | {'✅ Pass' if m['simillimum_acc_top5'] >= 0.70 else '⚠️ Review'} |",
            "",
            "---",
            "",
            "## 2. Stage 1: HomeoNER Entity Extraction Performance",
            "",
            "ClinicalBERT evaluates token-level entity boundaries across the 7 classical Kentian symptom dimensions:",
            "",
            "| Dimension Code | Clinical Significance | Precision | Recall | F1 Score | Gold Support |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        dim_descriptions = {
            "LOC": "Anatomical Location / Organ",
            "SEN": "Sensations / Pain Qualities",
            "MOD_AGG": "Aggravation Modalities (Worse from)",
            "MOD_AMEL": "Amelioration Modalities (Better from)",
            "CONC": "Concomitant Symptoms",
            "TEMP": "Time / Temporal Periodicity",
            "MENT": "Mental / Emotional State",
        }

        for dim in cls.DIMENSIONS:
            if dim in per_dim:
                d = per_dim[dim]
                desc = dim_descriptions.get(dim, dim)
                md.append(
                    f"| `{dim}` | {desc} | {d['precision'] * 100:.1f}% | {d['recall'] * 100:.1f}% | **{d['f1'] * 100:.1f}%** | {d['support']:,} |"
                )

        md.extend([
            "",
            "---",
            "",
            "## 3. Stage 2: Dense Semantic Rubric Retrieval",
            "",
            "Dense semantic vectors (`all-MiniLM-L6-v2`, 384 dimensions) query ChromaDB persistent index over 74,513 rubrics:",
            "",
            "| Metric | Formula | Achieved Score |",
            "| :--- | :--- | :--- |",
            f"| **Recall@1** | $\\mathbb{{I}}(\\text{{target}} = \\text{{rank}}_1)$ | **{m['top1_rubric_recall'] * 100:.2f}%** |",
            f"| **Recall@5** | $\\mathbb{{I}}(\\text{{target}} \\in \\text{{Top-5}})$ | **{m['top5_rubric_recall'] * 100:.2f}%** |",
            f"| **Recall@10** | $\\mathbb{{I}}(\\text{{target}} \\in \\text{{Top-10}})$ | **{m['top10_rubric_recall'] * 100:.2f}%** |",
            f"| **Recall@20** | $\\mathbb{{I}}(\\text{{target}} \\in \\text{{Top-20}})$ | **{m['top20_rubric_recall'] * 100:.2f}%** |",
            f"| **MRR** | $\\frac{{1}}{{|D|}} \\sum_{{i=1}}^{{|D|}} \\frac{{1}}{{\\text{{rank}}_i}}$ | **{m['mean_reciprocal_rank']:.4f}** |",
            "",
            "---",
            "",
            "## 4. Stage 3: Homeopathic Remedy Indication Accuracy",
            "",
            f"Evaluated on {m.get('remedy_eval_cases', 0):,} cases with documented remedy ground truth:",
            "",
            "| Evaluation Cutoff | Target Simillimum Capture Rate |",
            "| :--- | :--- |",
            f"| **Top-1 Remedy Accuracy** | **{m['simillimum_acc_top1'] * 100:.2f}%** |",
            f"| **Top-3 Remedy Accuracy** | **{m['simillimum_acc_top3'] * 100:.2f}%** |",
            f"| **Top-5 Remedy Accuracy** | **{m['simillimum_acc_top5'] * 100:.2f}%** |",
            "",
            "---",
            "",
            "## 5. Verification Command",
            "",
            "```powershell",
            f".venv\\Scripts\\python.exe scripts/evaluate.py --test-file {results.get('dataset', 'data/processed/test.jsonl')}",
            "```",
        ])

        return "\n".join(md)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Comprehensive Academic Evaluation Suite for Kent-AI Pipeline."
    )
    parser.add_argument(
        "--test-file",
        type=str,
        default="data/processed/test.jsonl",
        help="Path to evaluation test split (default: data/processed/test.jsonl)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="data/eval_metrics.json",
        help="Path to export structured JSON metrics",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="docs/Evaluation/test_benchmark_results.md",
        help="Path to export formatted Markdown evaluation report",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of test cases to evaluate",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for evaluation",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=False,
        help="Run in offline mock mode for fast testing without GPU weights",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device override ('cuda', 'cpu', or None for auto-detection)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    root = get_project_root()
    test_path = root / args.test_file

    logger.info("=" * 65)
    logger.info("Starting Kent-AI Academic Benchmark Evaluation")
    logger.info("Test File:   %s", test_path)
    logger.info("Output JSON: %s", args.output_json)
    logger.info("Output MD:   %s", args.output_md)
    logger.info("Sample Limit: %s | Mock Mode: %s", args.limit, args.mock)
    logger.info("=" * 65)

    evaluator = PipelineEvaluator(mock_mode=args.mock, device=args.device)
    results = evaluator.evaluate_dataset(
        test_file=test_path,
        limit=args.limit,
        batch_size=args.batch_size,
    )

    # Export structured JSON
    json_path = root / args.output_json
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info("Exported JSON metrics to %s", json_path)

    # Also mirror to data/processed/eval_results.json for eval-metric-parser compatibility
    eval_parser_path = root / "data/processed/eval_results.json"
    eval_parser_path.parent.mkdir(parents=True, exist_ok=True)
    with open(eval_parser_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Export Markdown report
    md_report = evaluator.generate_markdown_report(results)
    md_path = root / args.output_md
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    logger.info("Exported Markdown evaluation report to %s", md_path)

    # Print summary to console
    m = results["metrics"]
    print("\n" + "=" * 65)
    print("           KENT-AI ACADEMIC EVALUATION RESULTS")
    print("=" * 65)
    print(f"Total Cases Evaluated   : {results['total_cases']:,}")
    print(f"Token-Level BIO F1      : {m['token_level_bio_f1'] * 100:.2f}%")
    print(f"Token Accuracy          : {m['token_accuracy'] * 100:.2f}%")
    print(f"Top-1 Rubric Recall     : {m['top1_rubric_recall'] * 100:.2f}%")
    print(f"Top-5 Rubric Recall     : {m['top5_rubric_recall'] * 100:.2f}%")
    print(f"Top-10 Rubric Recall    : {m['top10_rubric_recall'] * 100:.2f}%")
    print(f"Top-20 Rubric Recall    : {m['top20_rubric_recall'] * 100:.2f}%")
    print(f"Mean Reciprocal Rank    : {m['mean_reciprocal_rank']:.4f}")
    print(f"Simillimum Remedy Top-1 : {m['simillimum_acc_top1'] * 100:.2f}%")
    print(f"Simillimum Remedy Top-3 : {m['simillimum_acc_top3'] * 100:.2f}%")
    print(f"Simillimum Remedy Top-5 : {m['simillimum_acc_top5'] * 100:.2f}%")
    print("=" * 65 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

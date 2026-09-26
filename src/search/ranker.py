"""Homeopathic remedy ranking by rubric intersection and grade weighting (Phase 5).

Implements classical Kentian repertorization:
1. Totality Coverage: Prioritizes remedies covering the maximum number of matched rubrics.
2. Grade Weighting: Accounts for Kent's 3 grades (Grade 3 = Bold / 3.0, Grade 2 = Italics / 2.0, Grade 1 = Plain / 1.0).
3. Specificity Weighting: Inverse remedy frequency so highly specific rubrics carry higher clinical differentiation.
4. Semantic Confidence Integration: Weights rubric contributions by vector cosine similarity.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from src.data.kent_db import get_connection, get_db_path

logger = logging.getLogger("remedy_ranker")


class RemedyRanker:
    """Ranks remedies according to classical homeopathic repertorization logic."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        grade_weights: Optional[Dict[int, float]] = None,
        apply_specificity: bool = True,
    ) -> None:
        self.db_path = db_path
        self.grade_weights = grade_weights or {3: 3.0, 2: 2.0, 1: 1.0}
        self.apply_specificity = apply_specificity

    def _fetch_rubrics_remedies_batch(
        self, rubric_ids: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Fetch all remedies and their grades for a batch of rubric IDs."""
        if not rubric_ids:
            return {}

        placeholders = ",".join("?" for _ in rubric_ids)
        sql = f"""
            SELECT 
                rr.rubric_id,
                rr.remedy_id,
                rr.normalized,
                rr.raw_token,
                COALESCE(rr.grade, rr.grade_candidate, 1) AS grade,
                r.abbreviation,
                r.full_name
            FROM rubric_remedies rr
            LEFT JOIN remedies r ON rr.remedy_id = r.id
            WHERE rr.rubric_id IN ({placeholders})
        """

        rubric_to_remedies: Dict[int, List[Dict[str, Any]]] = {r_id: [] for r_id in rubric_ids}

        with get_connection(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, [int(r_id) for r_id in rubric_ids])
            rows = cur.fetchall()

            for row in rows:
                r_id = row["rubric_id"]
                rubric_to_remedies[r_id].append({
                    "rubric_id": r_id,
                    "remedy_id": row["remedy_id"],
                    "normalized": row["normalized"],
                    "raw_token": row["raw_token"],
                    "grade": int(row["grade"]),
                    "abbreviation": row["abbreviation"] or row["normalized"] or row["raw_token"],
                    "full_name": row["full_name"] or row["normalized"] or row["raw_token"],
                })

        return rubric_to_remedies

    def rank(
        self,
        rubric_matches: List[Union[int, Dict[str, Any]]],
        top_n: int = 20,
        min_coverage: int = 1,
    ) -> List[Dict[str, Any]]:
        """Compute intersection and weighted total scores for candidate remedies.
        
        Args:
            rubric_matches: List of rubric IDs or candidate dicts (e.g. from RubricVectorStore.query).
            top_n: Maximum number of ranked remedies to return.
            min_coverage: Minimum number of rubrics a remedy must cover to be included.
            
        Returns:
            List of ranked remedy dictionaries sorted by (coverage DESC, score DESC).
        """
        if not rubric_matches:
            return []

        # Standardize input to list of dicts with rubric_id, similarity, path
        standardized_rubrics: List[Dict[str, Any]] = []
        for item in rubric_matches:
            if isinstance(item, int):
                standardized_rubrics.append({
                    "rubric_id": item,
                    "similarity": 1.0,
                    "path": f"Rubric #{item}",
                })
            elif isinstance(item, dict):
                r_id = item.get("rubric_id") or item.get("id")
                if r_id is not None:
                    standardized_rubrics.append({
                        "rubric_id": int(r_id),
                        "similarity": float(item.get("similarity", 1.0)),
                        "path": str(item.get("path") or f"Rubric #{r_id}"),
                    })

        total_rubrics_count = len(standardized_rubrics)
        if total_rubrics_count == 0:
            return []

        rubric_ids = [r["rubric_id"] for r in standardized_rubrics]
        rubric_meta = {r["rubric_id"]: r for r in standardized_rubrics}

        # Fetch remedies
        rubrics_remedies = self._fetch_rubrics_remedies_batch(rubric_ids)

        # Aggregate remedy scores across matching rubrics
        # Key: remedy key (abbreviation or remedy_id)
        remedy_stats: Dict[str, Dict[str, Any]] = {}

        for r_id, remedies in rubrics_remedies.items():
            r_info = rubric_meta.get(r_id, {})
            sim = r_info.get("similarity", 1.0)
            path = r_info.get("path", "")
            remedy_count_in_rubric = len(remedies)

            # Specificity weight: penalize massive rubrics (e.g. 500 remedies), boost narrow rubrics
            # w_spec in (0, 1]
            w_spec = 1.0
            if self.apply_specificity and remedy_count_in_rubric > 0:
                w_spec = 1.0 / math.sqrt(max(1.0, float(remedy_count_in_rubric) / 5.0))

            for rem in remedies:
                abbr = rem["abbreviation"]
                if not abbr:
                    continue

                grade = rem["grade"]
                grade_wt = self.grade_weights.get(grade, 1.0)
                contribution = grade_wt * sim * w_spec

                if abbr not in remedy_stats:
                    remedy_stats[abbr] = {
                        "remedy_id": rem["remedy_id"],
                        "abbreviation": abbr,
                        "full_name": rem["full_name"],
                        "score": 0.0,
                        "rubric_count": 0,
                        "rubrics_covered": [],
                    }

                remedy_stats[abbr]["score"] += contribution
                remedy_stats[abbr]["rubric_count"] += 1
                remedy_stats[abbr]["rubrics_covered"].append({
                    "rubric_id": r_id,
                    "path": path,
                    "grade": grade,
                    "similarity": round(sim, 3),
                    "contribution": round(contribution, 3),
                })

        # Filter by minimum coverage
        candidates = [
            rem for rem in remedy_stats.values()
            if rem["rubric_count"] >= min_coverage
        ]

        # Compute coverage ratio and round score
        for c in candidates:
            c["coverage_ratio"] = round(c["rubric_count"] / float(total_rubrics_count), 3)
            c["score"] = round(c["score"], 3)

        # Sort by primary key: rubric_count DESC, secondary key: score DESC
        candidates.sort(
            key=lambda x: (x["rubric_count"], x["score"]),
            reverse=True,
        )

        return candidates[:top_n]

    def repertorize_symptoms(
        self,
        query_rubrics: List[Dict[str, Any]],
        top_remedies: int = 10,
    ) -> Dict[str, Any]:
        """Produce full clinical repertorization report for a set of symptom rubrics.
        
        Args:
            query_rubrics: Matched candidate rubrics from retrieval.
            top_remedies: Top N remedies to present.
            
        Returns:
            Dictionary containing totality summary, ranked remedies, and rubric breakdown.
        """
        ranked = self.rank(query_rubrics, top_n=top_remedies)
        
        return {
            "total_rubrics_analyzed": len(query_rubrics),
            "rubrics": query_rubrics,
            "ranked_remedies": ranked,
            "top_remedy": ranked[0]["abbreviation"] if ranked else None,
        }

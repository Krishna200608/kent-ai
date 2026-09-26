#!/usr/bin/env python3
"""CLI Script: Build ChromaDB vector index over Kent Repertory rubrics (Phase 2).

Generates dense 384-dimensional semantic embeddings (all-MiniLM-L6-v2) for all 74,513
rubrics and persists the vector index into ChromaDB with HNSW cosine distance.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_chromadb_config, get_project_root
from src.data.kent_db import KentDB, get_connection
from src.search.embedder import RubricEmbedder
from src.search.vector_store import RubricVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("build_embeddings")


def fetch_all_rubrics(
    db: KentDB,
    section_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Retrieve rubrics enriched with section name and remedy count."""
    logger.info("Fetching rubrics from repertory.sqlite...")
    query = """
        SELECT 
            r.id,
            r.section_id,
            s.name as section_name,
            r.depth,
            r.label,
            r.path,
            (SELECT COUNT(*) FROM rubric_remedies rr WHERE rr.rubric_id = r.id) as remedy_count
        FROM rubrics r
        JOIN sections s ON r.section_id = s.id
    """
    params: List[Any] = []
    if section_id is not None:
        query += " WHERE r.section_id = ?"
        params.append(section_id)

    query += " ORDER BY r.id ASC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    with get_connection() as conn:
        conn.row_factory = None
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()

    rubrics = []
    for row in rows:
        rubrics.append({
            "id": row[0],
            "section_id": row[1],
            "section_name": row[2],
            "depth": row[3],
            "label": row[4],
            "path": row[5] or f"{row[2]} > {row[4]}",
            "remedy_count": row[6],
        })

    logger.info("Loaded %d rubrics for embedding indexing.", len(rubrics))
    return rubrics


def run_build(
    config_path: Optional[str] = None,
    section_id: Optional[int] = None,
    limit: Optional[int] = None,
    batch_size: int = 256,
    mock_mode: bool = False,
    persist_dir: Optional[str] = None,
) -> int:
    """Build and persist rubric embeddings."""
    logger.info("=" * 60)
    logger.info("Starting ChromaDB Rubric Index Builder (Phase 2)")
    logger.info("Mock Mode: %s | Batch Size: %d", mock_mode, batch_size)
    logger.info("=" * 60)

    db = KentDB()
    rubrics = fetch_all_rubrics(db=db, section_id=section_id, limit=limit)
    if not rubrics:
        logger.warning("No rubrics found to index.")
        return 0

    embedder = RubricEmbedder(mock_mode=mock_mode)
    vector_store = RubricVectorStore(
        persist_dir=persist_dir,
        embedder=embedder,
    )

    start_time = time.time()
    total_rubrics = len(rubrics)
    indexed_count = 0

    for start_idx in range(0, total_rubrics, batch_size):
        end_idx = min(start_idx + batch_size, total_rubrics)
        batch = rubrics[start_idx:end_idx]

        vector_store.add_rubrics(batch, batch_size=batch_size)
        indexed_count += len(batch)

        elapsed = time.time() - start_time
        rate = indexed_count / elapsed if elapsed > 0 else 0
        logger.info(
            "Progress: [%d/%d rubrics] (%.1f%%) | Rate: %.1f rubrics/sec",
            indexed_count,
            total_rubrics,
            (indexed_count / total_rubrics) * 100,
            rate,
        )

    total_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info(
        "Successfully indexed %d rubrics in %.2f seconds (%.1f rubrics/sec).",
        indexed_count,
        total_time,
        indexed_count / total_time if total_time > 0 else 0,
    )
    logger.info("Total collection count: %d", vector_store.count())
    logger.info("=" * 60)

    # Verification test query
    test_query = "splitting headache from sun"
    logger.info("Testing sample semantic query: '%s'", test_query)
    results = vector_store.query(test_query, top_k=5)
    for i, r in enumerate(results, 1):
        logger.info(
            "  %d. [Sim: %.3f] %s (remedies: %d)",
            i,
            r["similarity"],
            r["path"],
            r["remedy_count"],
        )

    return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build ChromaDB vector index over Kent Repertory rubrics."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/chromadb.yaml",
        help="Path to chromadb YAML configuration",
    )
    parser.add_argument(
        "--section-id",
        type=int,
        default=None,
        help="Restrict indexing to a specific Kent section ID (e.g. 1 for MIND)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of rubrics to index (useful for testing)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=256,
        help="Batch size for embedding calculation and upserting",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use deterministic mock embeddings for offline verification",
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default=None,
        help="Override ChromaDB persistent storage directory",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    return run_build(
        config_path=args.config,
        section_id=args.section_id,
        limit=args.limit,
        batch_size=args.batch_size,
        mock_mode=args.mock,
        persist_dir=args.persist_dir,
    )


if __name__ == "__main__":
    sys.exit(main())

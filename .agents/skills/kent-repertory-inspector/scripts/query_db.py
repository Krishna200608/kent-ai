#!/usr/bin/env python3
"""Database Query & Audit Utility for Kent's Repertory (SQLite).

Provides fast CLI queries, sanity validation, hierarchical path resolution,
and data quality audits over `data/raw/repertory.sqlite`.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure repository root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]  # .agent/skills/kent-repertory-inspector/scripts -> REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Guard Windows terminal encoding issues
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from src.data.kent_db import (
        get_connection,
        get_db_path,
        get_mind_rubrics,
        get_remedies,
        get_rubric_by_id,
        get_rubric_path,
        get_sections,
        search_rubrics,
    )
except ImportError:
    get_connection = None
    get_db_path = None


def resolve_database_path(custom_path: Optional[str] = None) -> Path:
    """Resolve database path with fallback logic."""
    if custom_path:
        p = Path(custom_path).resolve()
        if p.is_file():
            return p
        raise FileNotFoundError(f"Database not found at specified path: {p}")

    if get_db_path is not None:
        try:
            return get_db_path()
        except FileNotFoundError:
            pass

    candidates = [
        REPO_ROOT / "data" / "raw" / "repertory.sqlite",
        REPO_ROOT / "data" / "raw" / "kent_public_edition" / "repertory.sqlite",
        REPO_ROOT / "kent_public_edition" / "repertory.sqlite",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()

    raise FileNotFoundError(
        "Could not find repertory.sqlite in standard paths. "
        "Set KENT_DB_PATH or supply --db-path."
    )


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    """Open read-only sqlite connection."""
    uri = db_path.as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def print_stats(db_path: Path) -> None:
    """Print complete repertory database statistics."""
    conn = connect_readonly(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM sections")
    total_sections = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rubrics")
    total_rubrics = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM remedies")
    total_remedies = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rubric_remedies")
    total_associations = cur.fetchone()[0]

    cur.execute("SELECT MAX(depth) FROM rubrics")
    max_depth = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rubrics WHERE section_id = 1")
    mind_rubrics = cur.fetchone()[0]

    cur.execute("""
        SELECT s.name, COUNT(r.id) as r_count
        FROM sections s
        LEFT JOIN rubrics r ON r.section_id = s.id
        GROUP BY s.id
        ORDER BY r_count DESC
        LIMIT 5
    """)
    top_sections = cur.fetchall()

    conn.close()

    print("\n### Kent's Repertory Database Statistics")
    print(f"**Database File**: `{db_path}`")
    print(f"**File Size**: {db_path.stat().st_size:,} bytes ({db_path.stat().st_size / (1024 * 1024):.1f} MB)\n")

    print("| Metric | Value | Reference / Schema |")
    print("|---|---|---|")
    print(f"| **Total Sections** | {total_sections:,} | `sections` table |")
    print(f"| **Total Rubrics** | {total_rubrics:,} | `rubrics` table |")
    print(f"| **MIND Rubrics (Section 1)** | {mind_rubrics:,} | Target for Phase 1 (4,933) |")
    print(f"| **Total Remedies in Dictionary** | {total_remedies:,} | `remedies` table |")
    print(f"| **Rubric-Remedy Links** | {total_associations:,} | `rubric_remedies` join table |")
    print(f"| **Maximum Rubric Hierarchy Depth** | {max_depth} | `depth` column (0=root) |\n")

    print("#### Top 5 Largest Sections by Rubric Count:")
    print("| Rank | Section Name | Rubric Count |")
    print("|---|---|---|")
    for idx, row in enumerate(top_sections, 1):
        print(f"| {idx} | {row['name']} | {row['r_count']:,} |")
    print()


def verify_mind_rubrics(db_path: Path) -> bool:
    """Verify that MIND rubrics count matches exactly 4,933."""
    conn = connect_readonly(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM rubrics WHERE section_id = 1")
    count = cur.fetchone()[0]
    conn.close()

    expected = 4933
    is_valid = (count == expected)

    print("\n### MIND Rubrics Verification (Phase 0/1 Baseline)")
    print("| Item | Value |")
    print("|---|---|")
    print(f"| Target Count | **{expected:,}** |")
    print(f"| Found Count | **{count:,}** |")
    print(f"| Verification Status | {'[PASS] OK' if is_valid else '[FAIL] MISMATCH'} |")

    if not is_valid:
        print(f"\n> [!CAUTION]\n> MIND rubric count mismatch! Expected {expected}, got {count}.\n")
        return False
    else:
        print("\n> [!NOTE]\n> Verified exactly 4,933 MIND rubrics present in Section 1.\n")
        return True


def inspect_rubric(db_path: Path, rubric_id: int) -> None:
    """Resolve full hierarchical path and non-null remedies for a rubric ID."""
    conn = connect_readonly(db_path)
    cur = conn.cursor()

    # Rubric details
    cur.execute("""
        SELECT r.id, r.parent_id, r.section_id, s.name as section_name,
               r.depth, r.label, r.path, r.text, r.order_index
        FROM rubrics r
        LEFT JOIN sections s ON r.section_id = s.id
        WHERE r.id = ?
    """, (rubric_id,))
    rubric = cur.fetchone()

    if not rubric:
        conn.close()
        print(f"\n[ERROR]: Rubric ID {rubric_id} not found in database.")
        sys.exit(1)

    # Path resolution
    path = rubric["path"]
    if not path:
        # Fallback recursive resolution
        components = [rubric["label"]]
        parent_id = rubric["parent_id"]
        while parent_id is not None:
            cur.execute("SELECT id, parent_id, label FROM rubrics WHERE id = ?", (parent_id,))
            p = cur.fetchone()
            if not p:
                break
            components.append(p["label"])
            parent_id = p["parent_id"]
        path = f"{rubric['section_name']} > " + " > ".join(reversed(components))

    # Remedies query
    cur.execute("""
        SELECT 
            rr.id AS rubric_remedy_id,
            rr.rubric_id,
            rr.remedy_id,
            rr.normalized,
            rr.raw_token,
            rr.ordinal,
            COALESCE(rr.grade, rr.grade_candidate, 1) AS grade,
            rr.grade AS grade_reviewed,
            rr.grade_candidate,
            rr.grade_basis,
            r.abbreviation,
            r.full_name
        FROM rubric_remedies rr
        LEFT JOIN remedies r ON rr.remedy_id = r.id
        WHERE rr.rubric_id = ?
        ORDER BY grade DESC, rr.ordinal ASC
    """, (rubric_id,))
    remedies = cur.fetchall()
    conn.close()

    print(f"\n### Rubric Inspection: ID {rubric_id}")
    print(f"- **Path**: `{path}`")
    print(f"- **Section**: {rubric['section_name']} (ID: {rubric['section_id']})")
    print(f"- **Label**: `{rubric['label']}`")
    print(f"- **Depth**: {rubric['depth']}")
    print(f"- **Total Remedies**: {len(remedies)}\n")

    if not remedies:
        print("> [!NOTE]\n> No remedies associated with this rubric.\n")
        return

    grade_names = {3: "Grade 3 (Bold/Keynote)", 2: "Grade 2 (Italic)", 1: "Grade 1 (Plain)", 4: "Grade 4"}
    print("| Ordinal | Abbr | Full Remedy Name | Normalized | Effective Grade | Raw Token | Basis |")
    print("|---|---|---|---|---|---|---|")
    for r in remedies:
        abbr = r["abbreviation"] or r["normalized"] or "-"
        full_name = r["full_name"] or "(unresolved)"
        grade_str = grade_names.get(r["grade"], f"Grade {r['grade']}")
        basis = r["grade_basis"] or "-"
        print(f"| {r['ordinal']} | **{abbr}** | {full_name} | `{r['normalized']}` | {grade_str} | `{r['raw_token']}` | {basis} |")
    print()


def check_null_grades(db_path: Path) -> None:
    """Audit the rubric_remedies table for NULL remedy grades and report distribution."""
    conn = connect_readonly(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM rubric_remedies")
    total_rows = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rubric_remedies WHERE grade IS NULL")
    null_reviewed_grade = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rubric_remedies WHERE grade_candidate IS NULL")
    null_candidate_grade = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rubric_remedies WHERE grade IS NULL AND grade_candidate IS NULL")
    both_null = cur.fetchone()[0]

    cur.execute("""
        SELECT grade_candidate, COUNT(*) as count
        FROM rubric_remedies
        GROUP BY grade_candidate
        ORDER BY (grade_candidate IS NULL), grade_candidate
    """)
    candidate_dist = cur.fetchall()

    cur.execute("""
        SELECT COALESCE(grade, grade_candidate, 1) as effective_grade, COUNT(*) as count
        FROM rubric_remedies
        GROUP BY effective_grade
        ORDER BY effective_grade
    """)
    effective_dist = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM rubric_remedies WHERE remedy_id IS NULL")
    unresolved_remedies = cur.fetchone()[0]

    conn.close()

    print("\n### Remedy Grade & Quality Audit (`rubric_remedies`)")
    print(f"**Total Associations**: {total_rows:,}\n")

    print("#### 1. Grade Nullity Distribution")
    print("| Field | Populated | NULL Count | % NULL | Resolution Behavior |")
    print("|---|---|---|---|---|")
    print(f"| `grade` (Human-reviewed) | {total_rows - null_reviewed_grade:,} | {null_reviewed_grade:,} | {(null_reviewed_grade / total_rows) * 100:.2f}% | Falls back to `grade_candidate` |")
    print(f"| `grade_candidate` (OCR-detected) | {total_rows - null_candidate_grade:,} | {null_candidate_grade:,} | {(null_candidate_grade / total_rows) * 100:.2f}% | Falls back to default Grade 1 |")
    print(f"| Both NULL (`COALESCE` default 1) | - | {both_null:,} | {(both_null / total_rows) * 100:.2f}% | Assigned Grade 1 (Plain text) |")
    print(f"| Unresolved remedies (`remedy_id` NULL) | {total_rows - unresolved_remedies:,} | {unresolved_remedies:,} | {(unresolved_remedies / total_rows) * 100:.2f}% | Preserves OCR token & normalized str |\n")

    print("#### 2. Auto-Detected Candidate Breakdown (`grade_candidate`)")
    print("| Grade Candidate | Interpretation | Count | % of Total |")
    print("|---|---|---|---|")
    for r in candidate_dist:
        g = r["grade_candidate"]
        lbl = f"Grade {g}" if g is not None else "NULL (Undetermined typography)"
        interp = "Bold / Capitals" if g == 3 else "Italics" if g == 2 else "Plain text" if g == 1 else "Defaulted to Roman"
        print(f"| {lbl} | {interp} | {r['count']:,} | {(r['count'] / total_rows) * 100:.2f}% |")
    print()

    print("#### 3. Effective Resolved Grades (`COALESCE(grade, grade_candidate, 1)`)")
    print("| Effective Grade | Kent Typography | Count | % of Total |")
    print("|---|---|---|---|")
    for r in effective_dist:
        g = r["effective_grade"]
        interp = "Grade 3 (Bold / Capitals)" if g == 3 else "Grade 2 (Italics)" if g == 2 else "Grade 1 (Roman / Plain)"
        print(f"| Grade {g} | {interp} | {r['count']:,} | {(r['count'] / total_rows) * 100:.2f}% |")
    print()
    print("> [!NOTE]\n> Grade resolution strictly follows the formula: `COALESCE(grade, grade_candidate, 1)`.\n")


def search_db(db_path: Path, query_str: str, section_id: Optional[int] = None) -> None:
    """Search rubrics by query string."""
    conn = connect_readonly(db_path)
    cur = conn.cursor()

    sec_filter = "AND r.section_id = ?" if section_id else ""
    params: List[Any] = [f"%{query_str}%", f"%{query_str}%"]
    if section_id:
        params.append(section_id)

    cur.execute(f"""
        SELECT r.id, s.name as section_name, r.path, r.label,
               (SELECT COUNT(*) FROM rubric_remedies rr WHERE rr.rubric_id = r.id) as rem_count
        FROM rubrics r
        JOIN sections s ON r.section_id = s.id
        WHERE (r.path LIKE ? OR r.label LIKE ?) {sec_filter}
        ORDER BY r.id
        LIMIT 15
    """, params)
    rows = cur.fetchall()
    conn.close()

    print(f"\n### Search Results for: `{query_str}` (Limit 15)")
    if not rows:
        print("No matching rubrics found.")
        return

    print("| ID | Section | Rubric Path | Remedies |")
    print("|---|---|---|---|")
    for r in rows:
        print(f"| {r['id']} | {r['section_name']} | `{r['path']}` | {r['rem_count']} |")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query, validate, and audit Kent's Repertory SQLite database."
    )
    parser.add_argument("--db-path", type=str, default=None, help="Custom path to repertory.sqlite")
    parser.add_argument("--stats", action="store_true", help="Print section counts, rubric totals, and remedy stats")
    parser.add_argument("--verify-mind", action="store_true", help="Confirm count of MIND rubrics equals 4,933")
    parser.add_argument("--rubric-id", type=int, default=None, help="Resolve complete path and remedies for a rubric ID")
    parser.add_argument("--check-null-grades", action="store_true", help="Audit table for NULL remedy grades distribution")
    parser.add_argument("--search", type=str, default=None, help="Search rubrics by keyword")
    parser.add_argument("--section-id", type=int, default=None, help="Filter search to section ID (e.g. 1 for MIND)")

    args = parser.parse_args()

    try:
        db_path = resolve_database_path(args.db_path)
    except FileNotFoundError as err:
        print(f"[ERROR]: {err}", file=sys.stderr)
        return 1

    actions_executed = 0

    if args.stats:
        print_stats(db_path)
        actions_executed += 1

    if args.verify_mind:
        ok = verify_mind_rubrics(db_path)
        actions_executed += 1
        if not ok:
            return 1

    if args.rubric_id is not None:
        inspect_rubric(db_path, args.rubric_id)
        actions_executed += 1

    if args.check_null_grades:
        check_null_grades(db_path)
        actions_executed += 1

    if args.search is not None:
        search_db(db_path, args.search, args.section_id)
        actions_executed += 1

    if actions_executed == 0:
        # Default behavior: run stats and verify mind
        print_stats(db_path)
        ok = verify_mind_rubrics(db_path)
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

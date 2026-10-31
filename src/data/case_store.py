"""SQLite Persistence Layer for Clinical Cases in Kent-AI.

Provides industry-grade case persistence, loading, searching, and resumption.
Follows classical repertory software architecture (Homeorep, RadarOpus).
"""

from __future__ import annotations

import datetime
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.models.case import ClinicalCase

logger = logging.getLogger("case_store")

_DEFAULT_CASE_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "cases.sqlite"


def get_case_db_path(explicit_path: Optional[Union[str, Path]] = None) -> Path:
    """Return resolved path to the cases SQLite database."""
    if explicit_path:
        return Path(explicit_path).resolve()
    _DEFAULT_CASE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_CASE_DB_PATH


def init_case_db(db_path: Optional[Union[str, Path]] = None) -> None:
    """Initialize cases SQLite database and tables."""
    target_path = get_case_db_path(db_path)
    with sqlite3.connect(target_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clinical_cases (
                case_id TEXT PRIMARY KEY,
                patient_name TEXT NOT NULL,
                patient_age INTEGER,
                patient_sex TEXT,
                chief_complaint TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                scope_chapter TEXT,
                ranking_mode TEXT,
                dimensions_json TEXT NOT NULL,
                transcript TEXT,
                history_json TEXT,
                selected_rubrics_json TEXT,
                muted_rubrics_json TEXT,
                eliminatory_rubrics_json TEXT,
                report_json TEXT,
                clinical_notes TEXT,
                clinical_summary TEXT
            )
            """
        )
        # Safe migration if table existed without clinical_summary
        cur.execute("PRAGMA table_info(clinical_cases)")
        cols = [r[1] for r in cur.fetchall()]
        if "clinical_summary" not in cols:
            cur.execute("ALTER TABLE clinical_cases ADD COLUMN clinical_summary TEXT")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_cases_updated_at ON clinical_cases(updated_at DESC)")
        conn.commit()


def save_case(case: ClinicalCase, db_path: Optional[Union[str, Path]] = None) -> str:
    """Save or update a ClinicalCase instance in SQLite."""
    if case.is_blank:
        return case.case_id
    init_case_db(db_path)
    target_path = get_case_db_path(db_path)
    case.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    sql = """
        INSERT INTO clinical_cases (
            case_id, patient_name, patient_age, patient_sex, chief_complaint,
            status, created_at, updated_at, scope_chapter, ranking_mode,
            dimensions_json, transcript, history_json, selected_rubrics_json,
            muted_rubrics_json, eliminatory_rubrics_json, report_json, clinical_notes,
            clinical_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(case_id) DO UPDATE SET
            patient_name=excluded.patient_name,
            patient_age=excluded.patient_age,
            patient_sex=excluded.patient_sex,
            chief_complaint=excluded.chief_complaint,
            status=excluded.status,
            updated_at=excluded.updated_at,
            scope_chapter=excluded.scope_chapter,
            ranking_mode=excluded.ranking_mode,
            dimensions_json=excluded.dimensions_json,
            transcript=excluded.transcript,
            history_json=excluded.history_json,
            selected_rubrics_json=excluded.selected_rubrics_json,
            muted_rubrics_json=excluded.muted_rubrics_json,
            eliminatory_rubrics_json=excluded.eliminatory_rubrics_json,
            report_json=excluded.report_json,
            clinical_notes=excluded.clinical_notes,
            clinical_summary=excluded.clinical_summary
    """

    params = (
        case.case_id,
        case.patient_name,
        case.patient_age,
        case.patient_sex,
        case.chief_complaint,
        case.status,
        case.created_at,
        case.updated_at,
        case.scope_chapter,
        case.ranking_mode,
        json.dumps(case.dimensions),
        case.transcript,
        json.dumps(case.dialogue_history),
        json.dumps(case.selected_rubric_ids),
        json.dumps(case.muted_rubric_ids),
        json.dumps(case.eliminatory_rubric_ids),
        json.dumps(case.report_data) if case.report_data else None,
        case.clinical_notes,
        case.clinical_summary or "",
    )

    with sqlite3.connect(target_path) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()

    return case.case_id


def get_case(case_id: str, db_path: Optional[Union[str, Path]] = None) -> Optional[ClinicalCase]:
    """Retrieve a ClinicalCase by ID."""
    init_case_db(db_path)
    target_path = get_case_db_path(db_path)

    with sqlite3.connect(target_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM clinical_cases WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if not row:
            return None

        return ClinicalCase(
            case_id=row["case_id"],
            patient_name=row["patient_name"],
            patient_age=row["patient_age"],
            patient_sex=row["patient_sex"],
            chief_complaint=row["chief_complaint"] or "",
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            scope_chapter=row["scope_chapter"],
            ranking_mode=row["ranking_mode"] or "totality",
            dimensions=json.loads(row["dimensions_json"]) if row["dimensions_json"] else {},
            transcript=row["transcript"] or "",
            dialogue_history=json.loads(row["history_json"]) if row["history_json"] else [],
            selected_rubric_ids=json.loads(row["selected_rubrics_json"]) if row["selected_rubrics_json"] else [],
            muted_rubric_ids=json.loads(row["muted_rubrics_json"]) if row["muted_rubrics_json"] else [],
            eliminatory_rubric_ids=json.loads(row["eliminatory_rubrics_json"]) if row["eliminatory_rubrics_json"] else [],
            report_data=json.loads(row["report_json"]) if row["report_json"] else None,
            clinical_notes=row["clinical_notes"] or "",
            clinical_summary=(
                row["clinical_summary"]
                if "clinical_summary" in row.keys() and row["clinical_summary"]
                else ((json.loads(row["report_json"]).get("clinical_summary", "")) if row["report_json"] else "")
            ),
        )


def list_cases(limit: int = 50, db_path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """List recent patient consultation cases with summary metadata."""
    init_case_db(db_path)
    target_path = get_case_db_path(db_path)

    with sqlite3.connect(target_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                case_id, patient_name, patient_age, patient_sex, chief_complaint,
                status, created_at, updated_at, scope_chapter, dimensions_json, report_json
            FROM clinical_cases
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()

        summaries = []
        for r in rows:
            dims = json.loads(r["dimensions_json"]) if r["dimensions_json"] else {}
            dim_count = sum(1 for v in dims.values() if v)
            total_symptoms = sum(len(v) for v in dims.values() if isinstance(v, list))

            top_remedy = None
            if r["report_json"]:
                try:
                    rep = json.loads(r["report_json"])
                    rems = rep.get("ranked_remedies", [])
                    if rems:
                        top_remedy = f"{rems[0].get('abbreviation')} ({rems[0].get('score', 0):.2f})"
                except Exception:
                    pass

            summaries.append({
                "case_id": r["case_id"],
                "patient_name": r["patient_name"],
                "demographics": f"{r['patient_age'] or '?'}{r['patient_sex'][0] if r['patient_sex'] else ''}",
                "chief_complaint": r["chief_complaint"],
                "status": r["status"],
                "updated_at": r["updated_at"],
                "dimensions_captured": dim_count,
                "total_symptoms": total_symptoms,
                "top_remedy": top_remedy or "—",
            })

        return summaries


def delete_case(case_id: str, db_path: Optional[Union[str, Path]] = None) -> bool:
    """Delete a case by ID."""
    init_case_db(db_path)
    target_path = get_case_db_path(db_path)
    with sqlite3.connect(target_path) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM clinical_cases WHERE case_id = ?", (case_id,))
        conn.commit()
        return cur.rowcount > 0


def generate_case_id(db_path: Optional[Union[str, Path]] = None) -> str:
    """Generate a clean, readable case ID (e.g. CASE-2026-001) using MAX numeric suffix."""
    init_case_db(db_path)
    target_path = get_case_db_path(db_path)
    year = datetime.date.today().year
    prefix = f"CASE-{year}-"
    start_pos = len(prefix) + 1

    with sqlite3.connect(target_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COALESCE(MAX(CAST(SUBSTR(case_id, ?) AS INTEGER)), 0) + 1
            FROM clinical_cases
            WHERE case_id LIKE ?
            """,
            (start_pos, f"{prefix}%"),
        )
        next_n = cur.fetchone()[0]
        return f"CASE-{year}-{next_n:03d}"


def purge_blank_cases(db_path: Optional[Union[str, Path]] = None) -> int:
    """Delete cases with dimensions_captured == 0 and an empty chief_complaint.

    Returns the number of deleted cases.
    """
    init_case_db(db_path)
    target_path = get_case_db_path(db_path)

    with sqlite3.connect(target_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT case_id, dimensions_json, chief_complaint FROM clinical_cases")
        rows = cur.fetchall()

        to_delete = []
        for r in rows:
            chief = (r["chief_complaint"] or "").strip()
            if chief:
                continue
            dims_str = r["dimensions_json"]
            has_dims = False
            if dims_str:
                try:
                    dims = json.loads(dims_str)
                    has_dims = any(bool(v) for v in dims.values())
                except Exception:
                    pass
            if not has_dims:
                to_delete.append(r["case_id"])

        if to_delete:
            cur.executemany("DELETE FROM clinical_cases WHERE case_id = ?", [(cid,) for cid in to_delete])
            conn.commit()

        return len(to_delete)

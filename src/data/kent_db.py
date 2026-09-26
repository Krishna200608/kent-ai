"""SQLite Data Access Layer for Kent's Repertory of Homoeopathic Materia Medica.

This module provides high-performance, read-only access to digitized Kent's
Repertory rubrics, hierarchical trees, and remedy associations.
"""

from __future__ import annotations

import contextlib
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union


def get_db_path(explicit_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve the path to the Kent repertory SQLite database file.
    
    Search order:
    1. Explicit path parameter (if provided)
    2. KENT_DB_PATH environment variable
    3. data/raw/repertory.sqlite (relative to repository root)
    4. kent_public_edition/repertory.sqlite (relative to repository root)
    
    Returns:
        Absolute Path to existing repertory.sqlite database.
        
    Raises:
        FileNotFoundError: If the database cannot be located in standard paths.
    """
    if explicit_path:
        path = Path(explicit_path).resolve()
        if path.is_file():
            return path
        raise FileNotFoundError(f"Specified database file not found: {path}")

    env_path = os.environ.get("KENT_DB_PATH")
    if env_path:
        path = Path(env_path).resolve()
        if path.is_file():
            return path
        raise FileNotFoundError(f"Database from KENT_DB_PATH not found: {path}")

    current = Path(__file__).resolve().parent
    # Traverse upwards to find repo root
    search_dirs = [current] + list(current.parents)
    for directory in search_dirs:
        candidate_raw = directory / "data" / "raw" / "repertory.sqlite"
        if candidate_raw.is_file():
            return candidate_raw.resolve()
        candidate_raw_bundle = directory / "data" / "raw" / "kent_public_edition" / "repertory.sqlite"
        if candidate_raw_bundle.is_file():
            return candidate_raw_bundle.resolve()
        candidate_public = directory / "kent_public_edition" / "repertory.sqlite"
        if candidate_public.is_file():
            return candidate_public.resolve()

    raise FileNotFoundError(
        "Could not find repertory.sqlite in data/raw/ or kent_public_edition/. "
        "Set KENT_DB_PATH environment variable or initialize the data layer."
    )


@contextlib.contextmanager
def get_connection(
    db_path: Optional[Union[str, Path]] = None,
) -> Generator[sqlite3.Connection, None, None]:
    """Provide a read-only SQLite database connection context.
    
    Args:
        db_path: Optional path override for repertory.sqlite.
        
    Yields:
        Read-only sqlite3.Connection with Row row_factory and query_only mode.
    """
    resolved_path = get_db_path(db_path)
    uri_path = resolved_path.as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri_path, uri=True, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    try:
        yield conn
    finally:
        conn.close()


@dataclass(frozen=True)
class Section:
    """Represents a major anatomical/symptom chapter section in Kent's Repertory."""
    id: int
    name: str
    printed_start: Optional[int]
    printed_end: Optional[int]
    pdf_start: Optional[int]
    pdf_end: Optional[int]
    group_name: Optional[str]
    rubric_count: int


@dataclass(frozen=True)
class Rubric:
    """Represents an individual clinical rubric in the repertory tree."""
    id: int
    parent_id: Optional[int]
    section_id: int
    depth: int
    label: str
    path: str
    text: Optional[str]
    start_pdf_page: Optional[int]
    end_pdf_page: Optional[int]
    order_index: Optional[int]


@dataclass(frozen=True)
class RemedyEntry:
    """Represents a homeopathic remedy associated with a rubric."""
    remedy_id: Optional[int]
    rubric_id: int
    abbreviation: Optional[str]
    full_name: Optional[str]
    normalized: Optional[str]
    grade: int  # 3 = Bold/Caps, 2 = Italic, 1 = Plain/Roman
    grade_basis: Optional[str]
    confidence: Optional[float]


class KentDB:
    """Object-oriented interface to the Kent repertory database."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = get_db_path(db_path)

    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Open a context-managed read-only connection."""
        return get_connection(self.db_path)

    def get_sections(self) -> List[Dict[str, Any]]:
        """Return all sections ordered by printed book sequence."""
        return get_sections(self.db_path)

    def get_rubrics(
        self,
        section_id: int,
        parent_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Fetch rubrics belonging to a section with optional parent filter."""
        return get_rubrics(section_id, parent_id, limit, offset, self.db_path)

    def get_rubric_by_id(self, rubric_id: int) -> Optional[Dict[str, Any]]:
        """Fetch single rubric by primary key."""
        return get_rubric_by_id(rubric_id, self.db_path)

    def get_rubric_path(self, rubric_id: int) -> str:
        """Resolve full hierarchical path string for rubric."""
        return get_rubric_path(rubric_id, self.db_path)

    def get_remedies(self, rubric_id: int) -> List[Dict[str, Any]]:
        """Fetch all remedies associated with a rubric."""
        return get_remedies(rubric_id, self.db_path)

    def get_mind_rubrics(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve rubrics belonging to Section 1 (MIND)."""
        return get_mind_rubrics(limit, offset, self.db_path)

    def search_rubrics(
        self,
        query: str,
        section_id: Optional[int] = None,
        limit: int = 40,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search rubrics by text query."""
        return search_rubrics(query, section_id, limit, offset, self.db_path)


# Module-level functional API


def get_sections(
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Return all 37 sections of Kent's Repertory with rubric counts.
    
    Args:
        db_path: Optional path to SQLite database.
        
    Returns:
        List of dictionaries with section details and rubric counts.
    """
    sql = """
        SELECT s.id, s.name, s.printed_start, s.printed_end,
               s.pdf_start, s.pdf_end, s.group_name,
               (SELECT COUNT(*) FROM rubrics r WHERE r.section_id = s.id) AS rubric_count
        FROM sections s
        ORDER BY s.id
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]


def get_rubrics(
    section_id: int,
    parent_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Fetch rubrics belonging to a given section with optional parent filtering.
    
    Args:
        section_id: Section ID (1 = MIND, 2 = VERTIGO, etc.)
        parent_id: If provided, return only direct children of this rubric ID.
                   If explicitly set to -1, returns top-level rubrics (parent_id IS NULL).
        limit: Maximum rubrics to return. None returns all.
        offset: Row offset for pagination.
        db_path: Optional path to SQLite database.
        
    Returns:
        List of rubric dictionaries.
    """
    params: List[Any] = [int(section_id)]
    sql = ["SELECT * FROM rubrics WHERE section_id = ?"]

    if parent_id is not None:
        if parent_id == -1:
            sql.append("AND parent_id IS NULL")
        else:
            sql.append("AND parent_id = ?")
            params.append(int(parent_id))

    sql.append("ORDER BY order_index, id")

    if limit is not None:
        sql.append("LIMIT ? OFFSET ?")
        params.extend([int(limit), max(0, int(offset))])

    query = " ".join(sql)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_rubric_by_id(
    rubric_id: int,
    db_path: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve a single rubric record by its primary key.
    
    Args:
        rubric_id: Rubric primary key ID.
        db_path: Optional path to SQLite database.
        
    Returns:
        Rubric dictionary, or None if not found.
    """
    sql = "SELECT * FROM rubrics WHERE id = ?"
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (int(rubric_id),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_rubric_path(
    rubric_id: int,
    db_path: Optional[Union[str, Path]] = None,
) -> str:
    """Retrieve the full hierarchical path string for a given rubric.
    
    If the database row contains a pre-populated 'path' column, that is used;
    otherwise, the path is traversed recursively to the root.
    
    Args:
        rubric_id: Rubric primary key ID.
        db_path: Optional path to SQLite database.
        
    Returns:
        Path string in the format "SECTION > PARENT > CHILD".
        
    Raises:
        KeyError: If the rubric_id does not exist.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, parent_id, label, path FROM rubrics WHERE id = ?", (int(rubric_id),))
        row = cursor.fetchone()
        if not row:
            raise KeyError(f"Rubric ID {rubric_id} not found in database.")
        
        if row["path"]:
            return str(row["path"])

        # Fallback recursive traversal if path column is empty
        path_components = [row["label"]]
        current_parent = row["parent_id"]
        visited = {row["id"]}

        while current_parent is not None and current_parent not in visited:
            visited.add(current_parent)
            cursor.execute("SELECT id, parent_id, label FROM rubrics WHERE id = ?", (current_parent,))
            parent_row = cursor.fetchone()
            if not parent_row:
                break
            path_components.append(parent_row["label"])
            current_parent = parent_row["parent_id"]

        return " > ".join(reversed(path_components))


def get_remedies(
    rubric_id: int,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all homeopathic remedies associated with a given rubric.
    
    Remedy grades are mapped according to classical Kent Repertory conventions:
    - Grade 3: Bold / Capitals (highest prominence / clinically confirmed)
    - Grade 2: Italics (moderately verified)
    - Grade 1: Roman / Plain text (clinical observation)
    
    Args:
        rubric_id: Rubric primary key ID.
        db_path: Optional path to SQLite database.
        
    Returns:
        List of dictionaries with remedy details and assigned grades.
    """
    sql = """
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
            rr.confidence,
            r.abbreviation,
            r.full_name
        FROM rubric_remedies rr
        LEFT JOIN remedies r ON rr.remedy_id = r.id
        WHERE rr.rubric_id = ?
        ORDER BY rr.ordinal, rr.id
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (int(rubric_id),))
        return [dict(row) for row in cursor.fetchall()]


def get_mind_rubrics(
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all rubrics under Section 1 (MIND).
    
    In Kent's Repertory, Section 1 corresponds to mental and emotional symptoms,
    comprising exactly 4,933 rubrics in the digitized reference edition.
    
    Args:
        limit: Optional maximum number of rubrics to return.
        offset: Offset index for pagination.
        db_path: Optional path to SQLite database.
        
    Returns:
        List of rubric dictionaries belonging to MIND.
    """
    return get_rubrics(section_id=1, parent_id=None, limit=limit, offset=offset, db_path=db_path)


def search_rubrics(
    query: str,
    section_id: Optional[int] = None,
    limit: int = 40,
    offset: int = 0,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Search repertory rubrics by path and description.
    
    Leverages SQLite FTS5 index (rubric_search) for fast prefix token matching,
    with automatic fallback to LIKE pattern matching.
    
    Args:
        query: User search string (e.g., 'fear dark', 'anxiety evening').
        section_id: Optional section ID filter.
        limit: Maximum results to return (capped at 500).
        offset: Pagination offset.
        db_path: Optional path to SQLite database.
        
    Returns:
        List of matching rubric dictionaries.
    """
    query_clean = query.strip()
    if not query_clean:
        return []

    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    # Clean tokens for FTS5 prefix search
    terms = re.findall(r"\w+", query_clean, re.UNICODE)
    fts_expression = " AND ".join('"' + term.replace('"', '""') + '"*' for term in terms)

    section_sql = " AND d.section_id = ?" if section_id is not None else ""
    section_args = [int(section_id)] if section_id is not None else []

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if fts_expression:
            try:
                fts_query = f"""
                    SELECT d.*, s.name AS section_name
                    FROM rubric_search
                    JOIN rubrics d ON d.id = rubric_search.rowid
                    LEFT JOIN sections s ON s.id = d.section_id
                    WHERE rubric_search MATCH ?{section_sql}
                    ORDER BY rubric_search.rank, d.id
                    LIMIT ? OFFSET ?
                """
                cursor.execute(fts_query, [fts_expression] + section_args + [limit, offset])
                return [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass  # Fall back to LIKE query

        # Fallback LIKE search
        like_term = "%" + query_clean.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        like_query = f"""
            SELECT d.*, s.name AS section_name
            FROM rubrics d
            LEFT JOIN sections s ON s.id = d.section_id
            WHERE (d.path LIKE ? ESCAPE '\\' OR d.label LIKE ? ESCAPE '\\'){section_sql}
            ORDER BY d.id
            LIMIT ? OFFSET ?
        """
        cursor.execute(like_query, [like_term, like_term] + section_args + [limit, offset])
        return [dict(row) for row in cursor.fetchall()]

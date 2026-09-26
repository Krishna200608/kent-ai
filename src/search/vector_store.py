"""ChromaDB persistent vector store for semantic rubric matching."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


class RubricVectorStore:
    """ChromaDB interface for indexing and querying Kent rubrics."""

    def __init__(self, persist_dir: Optional[Path | str] = None) -> None:
        self.persist_dir = persist_dir

    def query(self, query_text: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Query top-K semantically relevant rubrics."""
        raise NotImplementedError("Phase 2 implementation pending.")

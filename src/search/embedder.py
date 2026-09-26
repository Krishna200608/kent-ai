"""Dense sentence embedding generator using sentence-transformers (all-MiniLM-L6-v2)."""

from __future__ import annotations

from typing import List, Optional
import numpy as np


class RubricEmbedder:
    """Computes dense vector representations of rubric path strings."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate normalized vector embeddings for a batch of strings."""
        raise NotImplementedError("Phase 2 implementation pending.")

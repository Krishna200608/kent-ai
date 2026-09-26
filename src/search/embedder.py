"""Dense sentence embedding generator using sentence-transformers (all-MiniLM-L6-v2).

Phase 2 target: Generates 384-dimensional dense semantic vectors for all 74,513
Kent Repertory rubrics to enable semantic similarity search and hybrid retrieval.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union
import numpy as np

from src.config import get_chromadb_config

logger = logging.getLogger(__name__)


class RubricEmbedder:
    """Computes dense vector representations of rubric path strings."""

    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
        mock_mode: bool = False,
    ) -> None:
        """Initialize embedder with model and device configuration.
        
        Args:
            model_name: HuggingFace model identifier. Defaults to all-MiniLM-L6-v2.
            device: 'cpu', 'cuda', or 'auto'.
            normalize_embeddings: If True, vectors have unit length (L2 norm = 1.0).
            mock_mode: If True, uses deterministic pseudo-embeddings for testing.
        """
        cfg = get_chromadb_config().get("embedding_model", {})
        self.model_name = model_name or cfg.get("name", self.DEFAULT_MODEL)
        self.normalize_embeddings = (
            normalize_embeddings if normalize_embeddings is not None else cfg.get("normalize_embeddings", True)
        )
        self.device = device or cfg.get("device", "auto")
        self.mock_mode = mock_mode

        self._model = None

    @property
    def model(self):
        """Lazy loader for SentenceTransformer model."""
        if self._model is None and not self.mock_mode:
            try:
                import torch
                from sentence_transformers import SentenceTransformer

                if self.device == "auto":
                    resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
                else:
                    resolved_device = self.device

                logger.info(
                    "Loading sentence-transformer '%s' on %s...",
                    self.model_name,
                    resolved_device,
                )
                self._model = SentenceTransformer(self.model_name, device=resolved_device)
            except ImportError as err:
                logger.warning(
                    "sentence-transformers not installed. Falling back to mock embeddings mode. (%s)",
                    err,
                )
                self.mock_mode = True

        return self._model

    def _generate_mock_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate deterministic normalized unit vectors for testing without weights."""
        vectors = np.zeros((len(texts), self.EMBEDDING_DIM), dtype=np.float32)
        for i, text in enumerate(texts):
            # Deterministic hash-based pseudo random seed
            h = abs(hash(text))
            rng = np.random.RandomState(h % (2**31 - 1))
            v = rng.randn(self.EMBEDDING_DIM).astype(np.float32)
            if self.normalize_embeddings:
                norm = np.linalg.norm(v)
                v = v / norm if norm > 0 else v
            vectors[i] = v
        return vectors

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 256,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """Generate normalized vector embeddings for a list of strings.
        
        Args:
            texts: List of text strings to embed.
            batch_size: Encoding batch size.
            show_progress_bar: If True, display tqdm progress bar.
            
        Returns:
            np.ndarray of shape (len(texts), EMBEDDING_DIM).
        """
        if not texts:
            return np.empty((0, self.EMBEDDING_DIM), dtype=np.float32)

        if self.mock_mode or self.model is None:
            return self._generate_mock_embeddings(texts)

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string for semantic vector search.
        
        Args:
            query: User symptom query or narrative phrase.
            
        Returns:
            1D numpy array of shape (EMBEDDING_DIM,).
        """
        return self.embed_texts([query])[0]

"""ChromaDB persistent vector store for semantic rubric matching.

Phase 2 target: Indexes all 74,513 Kent Repertory rubrics with HNSW cosine distance
and provides top-K semantic similarity lookup with section filtering.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from src.config import get_chromadb_config, get_project_root
from src.search.embedder import RubricEmbedder

logger = logging.getLogger(__name__)


class MockVectorCollection:
    """In-memory fallback collection for testing without chromadb library."""

    def __init__(self, name: str, space: str = "cosine") -> None:
        self.name = name
        self.space = space
        self.ids: List[str] = []
        self.documents: List[str] = []
        self.embeddings: List[np.ndarray] = []
        self.metadatas: List[Dict[str, Any]] = []

    def count(self) -> int:
        return len(self.ids)

    def upsert(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float] | np.ndarray],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        for idx, doc, emb, meta in zip(ids, documents, embeddings, metadatas):
            if idx in self.ids:
                pos = self.ids.index(idx)
                self.documents[pos] = doc
                self.embeddings[pos] = np.array(emb, dtype=np.float32)
                self.metadatas[pos] = meta
            else:
                self.ids.append(idx)
                self.documents.append(doc)
                self.embeddings.append(np.array(emb, dtype=np.float32))
                self.metadatas.append(meta)

    def query(
        self,
        query_embeddings: List[List[float] | np.ndarray],
        n_results: int = 20,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.ids:
            return {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}

        q_vec = np.array(query_embeddings[0], dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scores: List[Tuple[float, int]] = []
        for idx, (emb, meta) in enumerate(zip(self.embeddings, self.metadatas)):
            if where:
                match = True
                for k, v in where.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            e_norm = np.linalg.norm(emb)
            normed_emb = emb / e_norm if e_norm > 0 else emb
            cosine_sim = float(np.dot(q_vec, normed_emb))
            # Cosine distance = 1.0 - cosine_similarity
            cosine_dist = max(0.0, 1.0 - cosine_sim)
            scores.append((cosine_dist, idx))

        scores.sort(key=lambda x: x[0])
        top_matches = scores[:n_results]

        return {
            "ids": [[self.ids[idx] for _, idx in top_matches]],
            "distances": [[dist for dist, _ in top_matches]],
            "metadatas": [[self.metadatas[idx] for _, idx in top_matches]],
            "documents": [[self.documents[idx] for _, idx in top_matches]],
        }


class RubricVectorStore:
    """ChromaDB interface for indexing and querying Kent Repertory rubrics."""

    def __init__(
        self,
        persist_dir: Optional[Path | str] = None,
        collection_name: Optional[str] = None,
        embedder: Optional[RubricEmbedder] = None,
        in_memory: bool = False,
    ) -> None:
        """Initialize ChromaDB client and collection.
        
        Args:
            persist_dir: Directory where ChromaDB index is persisted.
            collection_name: Name of ChromaDB collection.
            embedder: RubricEmbedder instance for generating vectors.
            in_memory: If True, uses ephemeral in-memory storage (e.g. for testing).
        """
        cfg = get_chromadb_config()
        v_cfg = cfg.get("vector_store", {})

        root = get_project_root()
        default_dir = root / v_cfg.get("persist_directory", "data/embeddings/kent_rubrics")
        self.persist_dir = Path(persist_dir) if persist_dir else default_dir
        self.collection_name = collection_name or v_cfg.get("collection_name", "kent_rubrics")
        self.distance_metric = v_cfg.get("distance_metric", "cosine")
        self.in_memory = in_memory

        self.embedder = embedder or RubricEmbedder()
        self.client = None
        self.collection = None
        self._init_collection()

    def _init_collection(self) -> None:
        """Initialize or connect to ChromaDB persistent collection."""
        try:
            import chromadb
            from chromadb.config import Settings

            if self.in_memory:
                self.client = chromadb.EphemeralClient()
            else:
                self.persist_dir.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(path=str(self.persist_dir))

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.distance_metric},
            )
            logger.info(
                "Connected to ChromaDB collection '%s' (records: %d, dir: %s)",
                self.collection_name,
                self.collection.count(),
                self.persist_dir,
            )
        except ImportError as err:
            logger.warning(
                "chromadb not installed. Falling back to MockVectorCollection in memory. (%s)",
                err,
            )
            self.collection = MockVectorCollection(
                name=self.collection_name,
                space=self.distance_metric,
            )

    def count(self) -> int:
        """Return total number of indexed rubrics."""
        return self.collection.count()

    def add_rubrics(
        self,
        rubrics: List[Dict[str, Any]],
        embeddings: Optional[np.ndarray] = None,
        batch_size: int = 500,
        show_progress: bool = False,
    ) -> int:
        """Index a list of rubric records into ChromaDB.
        
        Args:
            rubrics: List of rubric dicts (keys: 'id', 'path', 'label', 'section_id', etc.).
            embeddings: Optional precomputed embeddings array of shape (len(rubrics), 384).
            batch_size: Upsert batch size.
            show_progress: If True, display progress.
            
        Returns:
            Number of successfully added/updated rubrics.
        """
        if not rubrics:
            return 0

        # Construct textual representations for embeddings
        documents: List[str] = []
        ids: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for r in rubrics:
            r_id = r["id"]
            path = r.get("path") or r.get("full_path", "")
            label = r.get("label", "")
            doc_text = f"{path} - {label}".strip(" -")
            documents.append(doc_text)
            ids.append(f"rubric_{r_id}")
            metadatas.append({
                "rubric_id": int(r_id),
                "section_id": int(r.get("section_id", 0)),
                "section_name": str(r.get("section_name", "")),
                "depth": int(r.get("depth", 0)),
                "path": str(path),
                "label": str(label),
                "remedy_count": int(r.get("remedy_count", 0)),
            })

        # Compute embeddings if not provided
        if embeddings is None:
            embeddings = self.embedder.embed_texts(
                documents,
                batch_size=min(batch_size, 256),
                show_progress_bar=show_progress,
            )

        # Batch upsert to ChromaDB
        total = len(ids)
        for start_idx in range(0, total, batch_size):
            end_idx = min(start_idx + batch_size, total)
            batch_ids = ids[start_idx:end_idx]
            batch_docs = documents[start_idx:end_idx]
            batch_embs = embeddings[start_idx:end_idx].tolist()
            batch_metas = metadatas[start_idx:end_idx]

            self.collection.upsert(
                ids=batch_ids,
                documents=batch_docs,
                embeddings=batch_embs,
                metadatas=batch_metas,
            )

        return total

    def query(
        self,
        query_text: str,
        top_k: int = 20,
        section_id: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Query top-K semantically relevant rubrics for a patient complaint.
        
        Args:
            query_text: Natural language symptom (e.g. 'splitting headache from sun exposure').
            top_k: Number of candidate rubrics to retrieve.
            section_id: Optional filter to restrict search to a specific Kent chapter.
            score_threshold: Minimum cosine similarity score [0.0, 1.0].
            
        Returns:
            List of result dicts sorted by similarity descending.
        """
        query_emb = self.embedder.embed_query(query_text)
        where_filter = {"section_id": int(section_id)} if section_id is not None else None

        results = self.collection.query(
            query_embeddings=[query_emb.tolist()],
            n_results=top_k,
            where=where_filter,
        )

        candidates: List[Dict[str, Any]] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return candidates

        ids_list = results["ids"][0]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(ids_list)
        metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(ids_list)
        docs = results["documents"][0] if "documents" in results else [""] * len(ids_list)

        for r_id, dist, meta, doc in zip(ids_list, distances, metas, docs):
            # For cosine distance d in [0, 2], similarity is 1.0 - d
            similarity = round(max(0.0, min(1.0, 1.0 - float(dist))), 4)
            if score_threshold is not None and similarity < score_threshold:
                continue

            candidates.append({
                "rubric_id": meta.get("rubric_id"),
                "path": meta.get("path") or doc,
                "label": meta.get("label"),
                "section_id": meta.get("section_id"),
                "section_name": meta.get("section_name"),
                "depth": meta.get("depth"),
                "remedy_count": meta.get("remedy_count", 0),
                "similarity": similarity,
                "distance": round(float(dist), 4),
            })

        # Sort by similarity descending
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return candidates

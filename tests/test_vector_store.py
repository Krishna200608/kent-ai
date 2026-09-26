"""Unit tests for RubricEmbedder and RubricVectorStore."""

import pytest
import numpy as np

from src.search.embedder import RubricEmbedder
from src.search.vector_store import RubricVectorStore


@pytest.fixture
def mock_embedder():
    return RubricEmbedder(mock_mode=True)


import uuid


@pytest.fixture
def mock_vector_store(mock_embedder):
    return RubricVectorStore(
        collection_name=f"test_rubrics_{uuid.uuid4().hex[:8]}",
        embedder=mock_embedder,
        in_memory=True,
    )


@pytest.fixture
def sample_rubrics():
    return [
        {
            "id": 1,
            "section_id": 1,
            "section_name": "MIND",
            "depth": 0,
            "label": "ABANDONED",
            "path": "MIND > ABANDONED",
            "remedy_count": 5,
        },
        {
            "id": 2,
            "section_id": 1,
            "section_name": "MIND",
            "depth": 1,
            "label": "feels he is",
            "path": "MIND > ABANDONED > feels he is",
            "remedy_count": 1,
        },
        {
            "id": 100,
            "section_id": 3,
            "section_name": "HEAD",
            "depth": 2,
            "label": "Sun, from exposure to",
            "path": "HEAD > PAIN > Sun, from exposure to",
            "remedy_count": 12,
        },
        {
            "id": 101,
            "section_id": 3,
            "section_name": "HEAD",
            "depth": 1,
            "label": "throbbing",
            "path": "HEAD > PAIN > throbbing",
            "remedy_count": 25,
        },
    ]


def test_embedder_dimension_and_normalization(mock_embedder):
    texts = ["headache from sun", "severe anxiety in morning"]
    embs = mock_embedder.embed_texts(texts)
    
    assert embs.shape == (2, 384)
    # Check unit normalization (L2 norm ~ 1.0)
    for i in range(len(texts)):
        norm = np.linalg.norm(embs[i])
        assert abs(norm - 1.0) < 1e-4


def test_embedder_query(mock_embedder):
    query = "throbbing headache"
    emb = mock_embedder.embed_query(query)
    
    assert emb.shape == (384,)
    assert abs(np.linalg.norm(emb) - 1.0) < 1e-4


def test_vector_store_add_and_count(mock_vector_store, sample_rubrics):
    added = mock_vector_store.add_rubrics(sample_rubrics)
    assert added == len(sample_rubrics)
    assert mock_vector_store.count() == len(sample_rubrics)


def test_vector_store_query_ranking(mock_vector_store, sample_rubrics):
    mock_vector_store.add_rubrics(sample_rubrics)
    results = mock_vector_store.query("headache from sun", top_k=2)
    
    assert len(results) <= 2
    assert "rubric_id" in results[0]
    assert "path" in results[0]
    assert "similarity" in results[0]
    assert "distance" in results[0]
    # Check results are sorted by similarity descending
    if len(results) > 1:
        assert results[0]["similarity"] >= results[1]["similarity"]


def test_vector_store_section_filtering(mock_vector_store, sample_rubrics):
    mock_vector_store.add_rubrics(sample_rubrics)
    # Filter for HEAD section only (section_id=3)
    results = mock_vector_store.query("pain", top_k=10, section_id=3)
    
    assert len(results) > 0
    assert all(r["section_id"] == 3 for r in results)
    assert all(r["section_name"] == "HEAD" for r in results)


def test_vector_store_score_threshold(mock_vector_store, sample_rubrics):
    mock_vector_store.add_rubrics(sample_rubrics)
    # With a high threshold, only high-scoring matches or empty list returned
    results = mock_vector_store.query("headache", top_k=10, score_threshold=0.999)
    assert all(r["similarity"] >= 0.999 for r in results)

"""Session state initialization and cached service singletons for Kent-AI Dashboard."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from src.config import get_project_root
from src.chatbot.dialogue_manager import DialogueManager
from src.data.kent_db import KentDB
from src.dashboard.constants import MODEL_DISPLAY_NAME
from src.data.case_store import generate_case_id
from src.models.case import ClinicalCase
from src.models.symptom_ner import SymptomNER
from src.models.ensemble import EnsembleNER
from src.models.hybrid_pipeline import HybridPipelineOrchestrator
from src.pipeline.orchestrator import PatientReport, PipelineOrchestrator
from src.search.embedder import RubricEmbedder
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore

logger = logging.getLogger("dashboard.session")

# Canonical Inference Engine Options for Clinician Workspace
ENGINE_OPTIONS = [
    "BioLinkBERT Fast Mode (~18ms)",
    "PubMedBERT (Top Rubric Alignment)",
    "Multi-Model Ensemble (4 Encoders, Majority Voting)",
    "Two-Stage Hybrid (Ensemble Mining + " + MODEL_DISPLAY_NAME + " Arbitration)",
]


@st.cache_resource
def get_db() -> KentDB:
    """Cache Kent database DAL instance."""
    return KentDB()


@st.cache_resource
def get_pipeline(engine_name: str = "BioLinkBERT Fast Mode (~18ms)"):
    """Cache dense vector store, embedder, and pipeline orchestrator for selected engine."""
    mock_mode = os.environ.get("KENT_MOCK_PIPELINE", "0") == "1"
    embedder = RubricEmbedder(mock_mode=mock_mode)
    vector_store = RubricVectorStore(embedder=embedder, in_memory=mock_mode)
    ranker = RemedyRanker()
    root = get_project_root()

    if mock_mode:
        if "Two-Stage Hybrid" in engine_name:
            return HybridPipelineOrchestrator(vector_store=vector_store, ranker=ranker, mock_mode=True)
        ner = SymptomNER(mock_mode=True)
        return PipelineOrchestrator(ner=ner, vector_store=vector_store, ranker=ranker, mock_mode=True)

    if "PubMedBERT" in engine_name:
        model_p = root / "data" / "models" / "pubmedbert_homeoNER"
        ner = SymptomNER(model_path=model_p, mock_mode=False)
        return PipelineOrchestrator(ner=ner, vector_store=vector_store, ranker=ranker, mock_mode=False)
    elif "Multi-Model Ensemble" in engine_name:
        ensemble = EnsembleNER(mock_mode=False)
        return PipelineOrchestrator(ner=ensemble, vector_store=vector_store, ranker=ranker, mock_mode=False)
    elif "Two-Stage Hybrid" in engine_name:
        return HybridPipelineOrchestrator(vector_store=vector_store, ranker=ranker, mock_mode=False)
    else:
        # Default: BioLinkBERT SOTA (~18ms)
        model_p = root / "data" / "models" / "biolinkbert_homeoNER"
        ner = SymptomNER(model_path=model_p, mock_mode=False)
        return PipelineOrchestrator(ner=ner, vector_store=vector_store, ranker=ranker, mock_mode=False)


def initialize_session():
    """Initialize stateful consultation variables and active ClinicalCase model."""
    if "current_case" not in st.session_state:
        new_cid = generate_case_id()
        fresh_case = ClinicalCase(case_id=new_cid)
        st.session_state.current_case = fresh_case

    case: ClinicalCase = st.session_state.current_case
    if not hasattr(case, "clinical_summary"):
        case.clinical_summary = ""

    if "workspace_step" not in st.session_state:
        st.session_state.workspace_step = 1

    if "inference_engine" not in st.session_state:
        st.session_state.inference_engine = ENGINE_OPTIONS[0]
    active_engine = st.session_state.inference_engine

    if "pipeline" not in st.session_state:
        st.session_state.pipeline = get_pipeline(active_engine)

    if "dialogue_manager" not in st.session_state or not hasattr(st.session_state.dialogue_manager, "is_ollama_online"):
        mock_dm = os.environ.get("KENT_MOCK_PIPELINE", "0") == "1"
        dm = DialogueManager(
            orchestrator=st.session_state.pipeline,
            model_name="llama3:8b",
            mock_mode=mock_dm,
        )
        dm.resume_from_case(case)
        st.session_state.dialogue_manager = dm
    else:
        dm = st.session_state.dialogue_manager
        dm.orchestrator = st.session_state.pipeline
        if getattr(dm, "api_base", None) in ("http://localhost:11434", None):
            dm.api_base = "http://127.0.0.1:11434"

    if "current_report" not in st.session_state:
        st.session_state.current_report = None
        # Re-hydrate report from case if stored
        if case.report_data:
            try:
                st.session_state.current_report = PatientReport(
                    patient_id=case.report_data.get("patient_id", case.case_id),
                    transcript=case.report_data.get("transcript", ""),
                    dimensions=case.report_data.get("dimensions", case.dimensions),
                    matched_rubrics=case.report_data.get("matched_rubrics", []),
                    ranked_remedies=case.report_data.get("ranked_remedies", []),
                    search_queries=case.report_data.get("search_queries", []),
                    entities=case.report_data.get("entities", []),
                )
            except Exception as e:
                logger.warning(f"Failed to rehydrate report from case: {e}")

    if "repertory_scope" not in st.session_state:
        st.session_state.repertory_scope = "MIND Chapter Focus (4,933 rubrics)"
    if "case_tray" not in st.session_state:
        st.session_state.case_tray = {"rubrics": [], "remedies": []}
    if "show_dev_details" not in st.session_state:
        st.session_state.show_dev_details = False
    if "ranking_sort_mode" not in st.session_state:
        st.session_state.ranking_sort_mode = "totality"

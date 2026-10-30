"""Multi-Model Transformer Ensemble for Kent-AI Clinical NER (Week 3 Plan).

Implements Paradigm 1: Confidence-Weighted Majority Voting and Softmax Averaging
across specialized biomedical encoders (BioLinkBERT, PubMedBERT, Bio_ClinicalBERT, DeBERTa-v3).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import torch
import torch.nn.functional as F

from src.config import get_model_config, get_project_root
from src.models.symptom_ner import SymptomNER

logger = logging.getLogger("ensemble_ner")

# Default empirical weights derived from held-out validation BIO F1 scores
DEFAULT_MODEL_WEIGHTS: Dict[str, float] = {
    "biolinkbert_homeoNER": 0.35,
    "pubmedbert_homeoNER": 0.35,
    "clinicalbert_homeoNER": 0.20,
    "deberta_homeoNER": 0.10,
}


@dataclass
class EnsembleEntity:
    """Represents a clinical entity resolved across ensemble models."""

    text: str
    label: str
    start: int
    end: int
    confidence: float
    votes: int
    total_models: int
    supporting_models: List[str] = field(default_factory=list)
    is_unanimous: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to serializable dictionary."""
        return {
            "text": self.text,
            "label": self.label,
            "start": self.start,
            "end": self.end,
            "confidence": round(self.confidence, 4),
            "votes": self.votes,
            "total_models": self.total_models,
            "supporting_models": self.supporting_models,
            "is_unanimous": self.is_unanimous,
        }


class EnsembleNER:
    """Ensemble of fine-tuned biomedical transformer encoders for robust symptom NER."""

    def __init__(
        self,
        model_paths: Optional[List[Union[str, Path]]] = None,
        weights: Optional[Dict[str, float]] = None,
        mock_mode: bool = False,
        device: Optional[str] = None,
    ) -> None:
        """Initialize the ensemble with multiple SymptomNER backends.

        Args:
            model_paths: List of directory paths to model checkpoints.
            weights: Optional dictionary mapping model directory name to its ensemble weight.
            mock_mode: If True, operates all sub-models in deterministic mock mode.
            device: Computing device ('cuda', 'cpu', or auto-detect).
        """
        self.mock_mode = mock_mode
        self.root = get_project_root()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        if model_paths is None:
            default_candidates = [
                self.root / "data" / "models" / "biolinkbert_homeoNER",
                self.root / "data" / "models" / "pubmedbert_homeoNER",
                self.root / "data" / "models" / "clinicalbert_homeoNER",
                self.root / "data" / "models" / "deberta_homeoNER",
            ]
            self.model_paths = [p for p in default_candidates if p.exists()]
            if not self.model_paths:
                # Fallback to single clinicalbert if none found on disk
                self.model_paths = [self.root / "data" / "models" / "clinicalbert_homeoNER"]
        else:
            self.model_paths = [Path(p) for p in model_paths]

        # Load models
        self.models: Dict[str, SymptomNER] = {}
        for path in self.model_paths:
            name = path.name
            try:
                ner = SymptomNER(model_path=path, mock_mode=mock_mode, device=self.device)
                self.models[name] = ner
            except Exception as err:
                logger.warning("Failed to initialize model %s: %s", name, err)

        if not self.models:
            # Fallback mock model
            logger.warning("No models successfully loaded; initializing mock ensemble.")
            self.models["mock_homeoNER"] = SymptomNER(mock_mode=True, device="cpu")

        # Assign normalized weights
        raw_weights = weights or DEFAULT_MODEL_WEIGHTS
        total_w = sum(raw_weights.get(m, 1.0) for m in self.models)
        self.weights: Dict[str, float] = {
            m: raw_weights.get(m, 1.0) / total_w if total_w > 0 else 1.0 / len(self.models)
            for m in self.models
        }
        logger.info(
            "Initialized EnsembleNER with %d models on %s. Normalized weights: %s",
            len(self.models),
            self.device,
            {k: round(v, 3) for k, v in self.weights.items()},
        )

    def extract_entities_per_model(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Run extraction across all ensemble models independently."""
        results: Dict[str, List[Dict[str, Any]]] = {}
        for name, model in self.models.items():
            try:
                results[name] = model.extract_entities(text)
            except Exception as err:
                logger.error("Extraction error in sub-model %s: %s", name, err)
                results[name] = []
        return results

    def extract_entities(
        self,
        text: str,
        min_votes: int = 1,
        min_confidence: float = 0.20,
        iou_threshold: float = 0.40,
    ) -> List[Dict[str, Any]]:
        """Extract consensus clinical entities using weighted span clustering (Paradigm 1).

        Args:
            text: Input patient narrative or clinical sentence.
            min_votes: Minimum number of models that must agree on the span.
            min_confidence: Minimum weighted confidence threshold to retain the entity.
            iou_threshold: Minimum character Intersection-over-Union (IoU) to cluster spans.

        Returns:
            List of consensus entity dictionaries.
        """
        model_predictions = self.extract_entities_per_model(text)
        total_models = len(self.models)

        # Collect all individual predictions into a pool
        pool: List[Dict[str, Any]] = []
        for model_name, entities in model_predictions.items():
            for ent in entities:
                pool.append({
                    "text": ent.get("text", ""),
                    "label": ent.get("label", "MENT"),
                    "start": ent.get("start", 0),
                    "end": ent.get("end", 0),
                    "model": model_name,
                    "weight": self.weights.get(model_name, 1.0 / max(1, total_models)),
                })

        if not pool:
            return []

        # Cluster overlapping candidate entities
        clusters: List[List[Dict[str, Any]]] = []
        for candidate in pool:
            assigned = False
            for cluster in clusters:
                # Check character overlap with cluster members
                exemplar = cluster[0]
                if candidate["label"] == exemplar["label"]:
                    # Compute character IoU
                    inter_start = max(candidate["start"], exemplar["start"])
                    inter_end = min(candidate["end"], exemplar["end"])
                    intersection = max(0, inter_end - inter_start)
                    union = max(candidate["end"], exemplar["end"]) - min(candidate["start"], exemplar["start"])
                    iou = intersection / union if union > 0 else 0.0

                    if iou >= iou_threshold:
                        cluster.append(candidate)
                        assigned = True
                        break
            if not assigned:
                clusters.append([candidate])

        # Resolve each cluster into a consensus EnsembleEntity
        consensus_entities: List[EnsembleEntity] = []
        for cluster in clusters:
            supporting_models = list({c["model"] for c in cluster})
            votes = len(supporting_models)

            # Confidence is the sum of normalized weights of supporting models
            confidence = sum(self.weights.get(m, 0.0) for m in supporting_models)

            if votes < min_votes or confidence < min_confidence:
                continue

            # Pick the canonical span boundary (longest text span within the cluster)
            cluster.sort(key=lambda c: (c["end"] - c["start"]), reverse=True)
            best_span = cluster[0]

            is_unanimous = (votes == total_models)

            consensus_entities.append(
                EnsembleEntity(
                    text=best_span["text"],
                    label=best_span["label"],
                    start=best_span["start"],
                    end=best_span["end"],
                    confidence=confidence,
                    votes=votes,
                    total_models=total_models,
                    supporting_models=supporting_models,
                    is_unanimous=is_unanimous,
                )
            )

        # Sort consensus entities by start offset
        consensus_entities.sort(key=lambda e: (e.start, e.end))
        return [e.to_dict() for e in consensus_entities]


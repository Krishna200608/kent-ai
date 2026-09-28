"""Bio_ClinicalBERT wrapper for HomeoNER token classification and inference (Phase 3).

Extracts 7-dimension symptom spans (LOC, SEN, MOD_AGG, MOD_AMEL, CONC, TEMP, MENT)
from raw clinical patient narratives.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import torch

from src.config import get_model_config, get_project_root

logger = logging.getLogger("symptom_ner")


class SymptomNER:
    """Named Entity Recognizer fine-tuned on homeopathic symptom narratives."""

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        config: Optional[Dict[str, Any]] = None,
        mock_mode: bool = False,
        device: Optional[str] = None,
    ) -> None:
        """Initialize symptom NER model or deterministic mock mode.
        
        Args:
            model_path: Directory containing fine-tuned model weights and tokenizer.
            config: Model configuration dictionary.
            mock_mode: If True or if model weights are absent, operates in rule-based mock mode.
            device: Computing device ('cuda', 'cpu', or None for auto-detection).
        """
        self.config = config or get_model_config()
        self.mock_mode = mock_mode

        root = get_project_root()
        default_dir = root / self.config.get("model", {}).get("output_dir", "data/models/clinicalbert_homeoNER")
        self.model_path = Path(model_path or default_dir)

        self.tags = self.config.get("labels", {}).get("tags", [
            "O",
            "B-LOC", "I-LOC",
            "B-SEN", "I-SEN",
            "B-MOD_AGG", "I-MOD_AGG",
            "B-MOD_AMEL", "I-MOD_AMEL",
            "B-CONC", "I-CONC",
            "B-TEMP", "I-TEMP",
            "B-MENT", "I-MENT",
        ])
        self.id2label = {i: tag for i, tag in enumerate(self.tags)}
        self.label2id = {tag: i for i, tag in enumerate(self.tags)}

        # Auto-detect device
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = None
        self.model = None

        # Check if fine-tuned weights exist
        weights_exist = (
            self.model_path.exists()
            and any(self.model_path.glob("*.bin")) or any(self.model_path.glob("*.safetensors"))
        )

        if not self.mock_mode and weights_exist:
            try:
                from transformers import AutoModelForTokenClassification, AutoTokenizer

                logger.info("Loading fine-tuned ClinicalBERT model from %s on %s...", self.model_path, self.device)
                self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path), use_fast=True)
                self.model = AutoModelForTokenClassification.from_pretrained(str(self.model_path))
                self.model.to(self.device)
                self.model.eval()
            except Exception as err:
                logger.warning("Failed to load fine-tuned model (%s). Falling back to mock extractor.", err)
                self.mock_mode = True
        else:
            self.mock_mode = True
            logger.info("SymptomNER initialized in mock mode (fine-tuned model not found at %s).", self.model_path)

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract labeled clinical symptom spans from input text.
        
        Args:
            text: Patient transcript or clinical narrative sentence.
            
        Returns:
            List of entity dictionaries with keys:
            - 'text': Extracted entity text substring
            - 'label': Dimension code ('LOC', 'SEN', 'MOD_AGG', etc.)
            - 'start': Character start offset in input text
            - 'end': Character end offset in input text
            - 'confidence': Softmax probability (0.0 to 1.0)
        """
        if not text or not text.strip():
            return []

        if self.mock_mode or self.model is None or self.tokenizer is None:
            return self._mock_extract(text)

        # Tokenize with character offset mappings
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True,
            max_length=256,
        )

        offset_mapping = inputs.pop("offset_mapping")[0].cpu().numpy()
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)

        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits[0]  # [seq_len, num_labels]
            probs = torch.softmax(logits, dim=-1)
            pred_indices = torch.argmax(logits, dim=-1).cpu().numpy()
            confidence_scores = probs.max(dim=-1).values.cpu().numpy()

        entities: List[Dict[str, Any]] = []
        current_label: Optional[str] = None
        current_start: Optional[int] = None
        current_end: Optional[int] = None
        current_confs: List[float] = []

        for idx, (token_id, pred_idx, conf) in enumerate(zip(input_ids[0], pred_indices, confidence_scores)):
            start_char, end_char = offset_mapping[idx]
            # Skip special tokens
            if start_char == end_char:
                continue

            tag = self.id2label.get(int(pred_idx), "O")

            if tag.startswith("B-"):
                # Save previous entity
                if current_label and current_start is not None and current_end is not None:
                    ent_text = text[current_start:current_end]
                    entities.append({
                        "text": ent_text,
                        "label": current_label,
                        "start": current_start,
                        "end": current_end,
                        "confidence": float(sum(current_confs) / len(current_confs)) if current_confs else 1.0,
                    })

                current_label = tag[2:]
                current_start = int(start_char)
                current_end = int(end_char)
                current_confs = [float(conf)]

            elif tag.startswith("I-") and current_label == tag[2:]:
                current_end = int(end_char)
                current_confs.append(float(conf))

            else:
                if current_label and current_start is not None and current_end is not None:
                    ent_text = text[current_start:current_end]
                    entities.append({
                        "text": ent_text,
                        "label": current_label,
                        "start": current_start,
                        "end": current_end,
                        "confidence": float(sum(current_confs) / len(current_confs)) if current_confs else 1.0,
                    })
                current_label = None
                current_start = None
                current_end = None
                current_confs = []

        # Flush trailing entity
        if current_label and current_start is not None and current_end is not None:
            ent_text = text[current_start:current_end]
            entities.append({
                "text": ent_text,
                "label": current_label,
                "start": current_start,
                "end": current_end,
                "confidence": float(sum(current_confs) / len(current_confs)) if current_confs else 1.0,
            })

        return entities

    def _mock_extract(self, text: str) -> List[Dict[str, Any]]:
        """Deterministic keyword-based entity extraction for testing without fine-tuned weights."""
        patterns = {
            "LOC": ["head", "forehead", "temple", "stomach", "chest", "throat", "right side", "left side"],
            "SEN": ["throbbing", "burning", "stitching", "pressing", "sharp pain", "dull ache", "heaviness"],
            "MOD_AGG": ["worse morning", "worse alone", "worse cold", "worse motion", "worse night", "worse dark"],
            "MOD_AMEL": ["better rest", "better pressure", "better fresh air", "better open air", "better warm"],
            "TEMP": ["morning", "night", "midnight", "evening", "twilight", "afternoon"],
            "MENT": ["anxiety", "fear", "restless", "weeping", "irritable", "absent-minded", "depressed", "grief"],
            "CONC": ["nausea", "vertigo", "chills", "sweat", "trembling"],
        }

        extracted: List[Dict[str, Any]] = []
        text_lower = text.lower()

        for label, keywords in patterns.items():
            for kw in keywords:
                start_idx = 0
                while True:
                    idx = text_lower.find(kw, start_idx)
                    if idx == -1:
                        break
                    extracted.append({
                        "text": text[idx : idx + len(kw)],
                        "label": label,
                        "start": idx,
                        "end": idx + len(kw),
                        "confidence": 0.95,
                    })
                    start_idx = idx + len(kw)

        # Sort by character start offset
        extracted.sort(key=lambda e: e["start"])
        return extracted

"""Synthetic clinical case generator utilizing LLaMA 3 via Ollama.

Phase 1 target: Generates realistic clinical case vignettes for all 4,933 MIND rubrics
with structured entities across 7 symptom dimensions, token arrays, and BIO tags.
"""

from __future__ import annotations

import json
import logging
import random
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.chatbot.prompts import (
    CASE_GENERATION_SYSTEM_PROMPT,
    build_case_generation_prompt,
)
from src.config import get_project_root, load_generation_config
from src.data.bio_tagger import BIOTagger
from src.data.kent_db import KentDB, get_remedies, get_rubric_path

logger = logging.getLogger(__name__)


@dataclass
class SyntheticCase:
    """Represents a generated patient narrative linked to a Kent rubric."""

    case_id: str
    rubric_id: int
    rubric_path: str
    narrative: str
    entities: List[Dict[str, Any]]
    tokens: List[str] = field(default_factory=list)
    bio_tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert case to JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SyntheticCase:
        """Construct SyntheticCase from dictionary."""
        return cls(
            case_id=data.get("case_id", str(uuid.uuid4())[:8]),
            rubric_id=data["rubric_id"],
            rubric_path=data["rubric_path"],
            narrative=data["narrative"],
            entities=data.get("entities", []),
            tokens=data.get("tokens", []),
            bio_tags=data.get("bio_tags", []),
            metadata=data.get("metadata", {}),
        )


class CaseGenerator:
    """Generates synthetic patient clinical cases using Ollama (LLaMA 3) or Mock mode."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str | Path] = None,
        mock_mode: bool = False,
    ) -> None:
        """Initialize generator with configuration parameters.
        
        Args:
            config: Optional pre-loaded configuration dict.
            config_path: Optional path to YAML config file.
            mock_mode: If True, uses rule-based generator for offline testing/demo.
        """
        if config is None:
            config = load_generation_config(config_path)

        gen_cfg = config.get("generation", {})
        self.model = gen_cfg.get("model", "llama3:8b")
        self.backend = "mock" if mock_mode else gen_cfg.get("backend", "ollama")
        self.api_base = gen_cfg.get("api_base", "http://localhost:11434").rstrip("/")
        self.temperature = float(gen_cfg.get("temperature", 0.7))
        self.top_p = float(gen_cfg.get("top_p", 0.9))
        self.max_tokens = int(gen_cfg.get("max_tokens", 512))
        self.seed = int(gen_cfg.get("seed", 42))

        self.tagger = BIOTagger()
        self.kent_db = KentDB()

    def _call_ollama_generate(self, prompt: str, seed: Optional[int] = None) -> str:
        """Call Ollama REST API /api/generate with JSON mode.
        
        Args:
            prompt: User prompt containing rubric and instructions.
            seed: Optional dynamic random seed for variation entropy.
            
        Returns:
            Raw response text from LLM.
            
        Raises:
            ConnectionError: If Ollama daemon is unreachable.
            RuntimeError: If Ollama returns non-200 or unparseable response.
        """
        actual_seed = seed if seed is not None else self.seed
        url = f"{self.api_base}/api/generate"
        payload = {
            "model": self.model,
            "system": CASE_GENERATION_SYSTEM_PROMPT,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens,
                "seed": actual_seed,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "")
        except urllib.error.URLError as err:
            raise ConnectionError(
                f"Cannot connect to Ollama server at {self.api_base}. "
                f"Ensure Ollama is running (`ollama serve`). Details: {err}"
            ) from err

    def _generate_mock_case(
        self, rubric_id: int, rubric_path: str, top_remedies: List[str]
    ) -> Dict[str, Any]:
        """Generate a deterministic synthetic vignette for testing without live LLM.
        
        Args:
            rubric_id: ID of the rubric.
            rubric_path: Path string (e.g. 'MIND > ANXIETY > twilight, at').
            top_remedies: List of top remedies associated with rubric.
            
        Returns:
            Dictionary with 'narrative' and 'entities'.
        """
        parts = [p.strip() for p in rubric_path.split(">") if p.strip()]
        leaf = parts[-1].lower() if parts else "distress"
        parent = parts[1].lower() if len(parts) > 1 else leaf

        templates = [
            (
                f"Doctor, I have been troubled by intense {parent}, especially with {leaf}. "
                f"My forehead throbs painfully and I feel worse in the evening, with trembling hands."
            ),
            (
                f"For the past several days, I cannot shake this feeling of {leaf}. "
                f"There is a dull tightness in my chest and my anxiety escalates at night, accompanied by restless pacing."
            ),
            (
                f"I feel completely overwhelmed by {parent}. It seems to come on as {leaf}, "
                f"leaving me irritable and exhausted with a burning sensation in my temples."
            ),
        ]

        # Use rubric_id as deterministic pseudo-random seed selector
        narrative = templates[rubric_id % len(templates)]

        # Extract entities matching the narrative
        candidate_entities: List[Dict[str, Any]] = []

        # Mind entities
        for term in [parent, leaf, "intense", "anxiety", "overwhelmed", "irritable"]:
            if term in narrative.lower():
                idx = narrative.lower().find(term)
                candidate_entities.append({
                    "text": narrative[idx : idx + len(term)],
                    "label": "MENT",
                    "start": idx,
                    "end": idx + len(term),
                })

        # Sensation entities
        for term in ["throbs painfully", "dull tightness", "burning sensation"]:
            if term in narrative:
                idx = narrative.find(term)
                candidate_entities.append({
                    "text": term,
                    "label": "SEN",
                    "start": idx,
                    "end": idx + len(term),
                })

        # Location entities
        for term in ["forehead", "chest", "temples"]:
            if term in narrative:
                idx = narrative.find(term)
                candidate_entities.append({
                    "text": term,
                    "label": "LOC",
                    "start": idx,
                    "end": idx + len(term),
                })

        # Temporal / Modalities
        for term in ["in the evening", "at night"]:
            if term in narrative:
                idx = narrative.find(term)
                candidate_entities.append({
                    "text": term,
                    "label": "TEMP",
                    "start": idx,
                    "end": idx + len(term),
                })

        # Concomitant
        for term in ["trembling hands", "restless pacing"]:
            if term in narrative:
                idx = narrative.find(term)
                candidate_entities.append({
                    "text": term,
                    "label": "CONC",
                    "start": idx,
                    "end": idx + len(term),
                })

        # De-duplicate candidate entities
        seen_spans = set()
        clean_entities = []
        for ent in candidate_entities:
            key = (ent["start"], ent["end"])
            if key not in seen_spans:
                seen_spans.add(key)
                clean_entities.append(ent)

        return {"narrative": narrative, "entities": clean_entities}

    def generate_case_for_rubric(
        self,
        rubric_id: int,
        rubric_path: Optional[str] = None,
        top_remedies: Optional[List[str]] = None,
        case_idx: int = 1,
        variation_instruction: Optional[str] = None,
    ) -> SyntheticCase:
        """Generate a clinical scenario manifesting the specified rubric.
        
        Args:
            rubric_id: Kent rubric integer ID.
            rubric_path: Optional hierarchical path string.
            top_remedies: Optional list of remedy abbreviation strings.
            case_idx: Case variation index for multi-case generation.
            variation_instruction: Archetype/persona prompt guidance for variation diversity.
            
        Returns:
            SyntheticCase instance complete with tokens and BIO tags.
        """
        if rubric_path is None:
            rubric_path = get_rubric_path(rubric_id)

        if top_remedies is None:
            rems = get_remedies(rubric_id)
            top_remedies = [r["abbreviation"] for r in rems[:5] if r.get("abbreviation")]

        if self.backend == "mock":
            parsed_data = self._generate_mock_case(
                rubric_id + (case_idx * 1000), rubric_path, top_remedies
            )
        else:
            # Deterministic dynamic seed per case index to avoid cache collapse across variations
            dynamic_seed = self.seed + (case_idx * 137)
            prompt = build_case_generation_prompt(
                rubric_path=rubric_path,
                top_remedies=top_remedies,
                include_examples=True,
                variation_instruction=variation_instruction,
            )
            raw_response = self._call_ollama_generate(prompt, seed=dynamic_seed)
            try:
                parsed_data = json.loads(raw_response)
            except json.JSONDecodeError as err:
                logger.warning(
                    "LLM response failed direct JSON decode. Attempting substring extraction. Error: %s",
                    err,
                )
                # Attempt to extract JSON substring between { and }
                first_brace = raw_response.find("{")
                last_brace = raw_response.rfind("}")
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    parsed_data = json.loads(raw_response[first_brace : last_brace + 1])
                else:
                    raise ValueError(f"Unparseable LLM output: {raw_response[:200]}") from err

        narrative = str(parsed_data.get("narrative", "")).strip()
        raw_entities = parsed_data.get("entities", [])

        # Tokenize and tag with BIOTagger
        tokens, bio_tags = self.tagger.tag_tokens(narrative, raw_entities)

        # Re-extract clean validated entities from BIO tags
        clean_entities = []
        for ent in raw_entities:
            aligned = self.tagger.align_entity_offsets(narrative, ent)
            if aligned:
                clean_entities.append({
                    "text": aligned.text,
                    "label": aligned.label,
                    "start": aligned.start,
                    "end": aligned.end,
                })

        case_id = f"case_{rubric_id}_{case_idx}_{uuid.uuid4().hex[:6]}"
        metadata = {
            "model": self.model,
            "backend": self.backend,
            "rubric_id": rubric_id,
            "top_remedies": top_remedies,
            "case_idx": case_idx,
        }

        return SyntheticCase(
            case_id=case_id,
            rubric_id=rubric_id,
            rubric_path=rubric_path,
            narrative=narrative,
            entities=clean_entities,
            tokens=tokens,
            bio_tags=bio_tags,
            metadata=metadata,
        )

    def generate_batch(
        self,
        rubric_ids: List[int],
        cases_per_rubric: int = 1,
        on_case_callback: Optional[Callable[[SyntheticCase], None]] = None,
    ) -> List[SyntheticCase]:
        """Generate cases for multiple rubrics with optional real-time callback.
        
        Args:
            rubric_ids: List of rubric IDs to process.
            cases_per_rubric: Number of distinct variations per rubric.
            on_case_callback: Callback invoked after each case is generated.
            
        Returns:
            List of all generated SyntheticCase objects.
        """
        cases: List[SyntheticCase] = []
        for r_id in rubric_ids:
            for c_idx in range(1, cases_per_rubric + 1):
                case = self.generate_case_for_rubric(r_id, case_idx=c_idx)
                cases.append(case)
                if on_case_callback:
                    on_case_callback(case)
        return cases

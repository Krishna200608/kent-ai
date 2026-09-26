"""LLaMA 3 post-processor resolving negation, coreference, and assembling 7-dim JSON (Phase 4).

This module ingests messy clinical transcripts and raw NER entity spans, and uses LLaMA 3
(via local Ollama) or deterministic heuristics to resolve:
1. Negation detection (identifying symptoms denied by patient)
2. Coreference resolution (linking pronouns/references to clinical anchors)
3. 7-dimension structuring (Location, Sensation, Modality Agg, Modality Amel, Concomitant, Temporal, Mental)
4. Semantic query generation for dense retrieval in ChromaDB.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.chatbot.prompts import RESOLVER_SYSTEM_PROMPT, RESOLVER_USER_PROMPT
from src.config import get_generation_config

logger = logging.getLogger("symptom_resolver")


@dataclass
class SymptomProfile:
    """Structured 7-dimensional clinical symptom profile."""

    chief_complaint: str = ""
    location: List[str] = field(default_factory=list)
    sensation: List[str] = field(default_factory=list)
    modality_agg: List[str] = field(default_factory=list)
    modality_amel: List[str] = field(default_factory=list)
    concomitant: List[str] = field(default_factory=list)
    temporal: List[str] = field(default_factory=list)
    mental: List[str] = field(default_factory=list)
    negated: List[str] = field(default_factory=list)
    raw_entities: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to serializable dictionary."""
        return asdict(self)

    def get_search_queries(self) -> List[str]:
        """Generate targeted semantic query strings for ChromaDB vector search.
        
        Synthesizes composite queries like:
        - "forehead throbbing worse from sun"
        - "anxiety in morning"
        """
        queries: List[str] = []
        loc = " ".join(self.location) if self.location else ""
        sens = " ".join(self.sensation) if self.sensation else ""
        aggs = self.modality_agg
        amels = self.modality_amel
        times = self.temporal
        mentals = self.mental
        concs = self.concomitant

        # 1. Primary physical symptom (Location + Sensation)
        if loc and sens:
            queries.append(f"{loc} {sens}".strip())
        elif loc:
            queries.append(loc)
        elif sens:
            queries.append(sens)

        # 2. Location + Modalities
        for agg in aggs:
            q = f"{loc} {sens} worse from {agg}".strip() if (loc or sens) else f"worse from {agg}"
            queries.append(q)

        for amel in amels:
            q = f"{loc} {sens} better from {amel}".strip() if (loc or sens) else f"better from {amel}"
            queries.append(q)

        # 3. Location + Temporal
        for t in times:
            q = f"{loc} {sens} {t}".strip() if (loc or sens) else t
            queries.append(q)

        # 4. Concomitants
        for c in concs:
            q = f"{loc} with {c}".strip() if loc else c
            queries.append(q)

        # 5. Mental symptoms
        for m in mentals:
            queries.append(f"mind {m}")

        # Fallback to chief complaint if no queries were formed
        if not queries and self.chief_complaint:
            queries.append(self.chief_complaint)

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            cleaned = " ".join(q.split())
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                unique_queries.append(cleaned)

        return unique_queries


class SymptomResolver:
    """Takes ClinicalBERT entity spans and dialogue transcript to produce clean symptom profiles."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.1,
        mock_mode: bool = False,
    ) -> None:
        cfg = get_generation_config()
        gen_cfg = cfg.get("generation", {})

        self.model_name = model_name or gen_cfg.get("model", "llama3:8b")
        self.api_base = api_base or gen_cfg.get("api_base", "http://localhost:11434")
        self.temperature = temperature
        self.mock_mode = mock_mode

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama /api/generate with JSON format."""
        url = f"{self.api_base}/api/generate"
        payload = {
            "model": self.model_name,
            "system": RESOLVER_SYSTEM_PROMPT,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "num_predict": 512,
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
            logger.warning("Ollama unreachable at %s: %s. Using rule-based fallback.", self.api_base, err)
            return ""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Safely parse LLM output into a dictionary."""
        if not response_text:
            return {}

        cleaned = response_text.strip()
        # Remove potential markdown code blocks
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning("Failed to decode JSON from resolver output: %s", e)
            # Try to find JSON block via regex
            match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            return {}

    def _mock_resolve(
        self, transcript: str, raw_entities: Optional[List[Dict[str, Any]]] = None
    ) -> SymptomProfile:
        """Rule-based resolution for testing and fallback."""
        profile = SymptomProfile(
            chief_complaint=transcript.split(".")[0].strip() if transcript else "",
            raw_entities=raw_entities or [],
        )

        # Basic negation keywords
        negation_patterns = [
            r"\b(?:no|not|never|without|denies|denied|free of)\s+([a-zA-Z\s\-]+?)(?:[,.]|$|\bbut\b|\band\b)",
        ]
        negated_spans = set()
        for pat in negation_patterns:
            for match in re.finditer(pat, transcript, re.IGNORECASE):
                negated_spans.add(match.group(1).strip().lower())

        if raw_entities:
            for ent in raw_entities:
                text = ent.get("text", "").strip()
                label = ent.get("label", "").upper()
                if not text:
                    continue

                # Check if entity is negated
                is_negated = any(neg in text.lower() or text.lower() in neg for neg in negated_spans)
                if is_negated:
                    if text not in profile.negated:
                        profile.negated.append(text)
                    continue

                if label == "LOC" and text not in profile.location:
                    profile.location.append(text)
                elif label == "SEN" and text not in profile.sensation:
                    profile.sensation.append(text)
                elif label == "MOD_AGG" and text not in profile.modality_agg:
                    profile.modality_agg.append(text)
                elif label == "MOD_AMEL" and text not in profile.modality_amel:
                    profile.modality_amel.append(text)
                elif label == "CONC" and text not in profile.concomitant:
                    profile.concomitant.append(text)
                elif label == "TEMP" and text not in profile.temporal:
                    profile.temporal.append(text)
                elif label == "MENT" and text not in profile.mental:
                    profile.mental.append(text)

        return profile

    def resolve(
        self,
        transcript: str,
        raw_entities: Optional[List[Dict[str, Any]]] = None,
    ) -> SymptomProfile:
        """Produce structured 7-dimension symptom dictionary from transcript and entities.
        
        Args:
            transcript: Full patient intake narrative or dialogue turns.
            raw_entities: Optional list of entity dicts with keys 'text', 'label', 'start', 'end'.
            
        Returns:
            Structured SymptomProfile object with resolved dimensions and search queries.
        """
        raw_entities = raw_entities or []

        if self.mock_mode:
            return self._mock_resolve(transcript, raw_entities)

        # Format spans for prompt
        spans_text = json.dumps(raw_entities, indent=2) if raw_entities else "None provided."
        user_prompt = RESOLVER_USER_PROMPT.format(
            transcript=transcript,
            spans=spans_text,
        )

        response_text = self._call_ollama(user_prompt)
        parsed = self._parse_response(response_text)

        if not parsed:
            logger.info("Falling back to deterministic rule-based resolution.")
            return self._mock_resolve(transcript, raw_entities)

        def _to_list(val: Any) -> List[str]:
            if isinstance(val, list):
                return [str(v).strip() for v in val if str(v).strip()]
            if isinstance(val, str) and val.strip():
                return [val.strip()]
            return []

        profile = SymptomProfile(
            chief_complaint=str(parsed.get("chief_complaint", "")).strip() or transcript.split(".")[0].strip(),
            location=_to_list(parsed.get("location")),
            sensation=_to_list(parsed.get("sensation")),
            modality_agg=_to_list(parsed.get("modality_agg")),
            modality_amel=_to_list(parsed.get("modality_amel")),
            concomitant=_to_list(parsed.get("concomitant")),
            temporal=_to_list(parsed.get("temporal")),
            mental=_to_list(parsed.get("mental")),
            negated=_to_list(parsed.get("negated")),
            raw_entities=raw_entities,
        )

        return profile

"""Clinical Case Summarizer for Kent-AI.

Generates concise, physician-facing clinical case summaries (HPI / Physician Brief)
synthesizing patient dialogue transcripts and Kent's 7-dimension totality slots.
Uses local LLM (LLaMA 3:8B via Ollama) with robust clinically-grounded extractive fallback.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional
import urllib.request

from src.models.case import ClinicalCase

logger = logging.getLogger("case_summarizer")


class CaseSummarizer:
    """Generates objective, physician-facing clinical summaries from patient intake."""

    def __init__(
        self,
        api_base: str = "http://127.0.0.1:11434",
        model_name: str = "llama3:8b",
        timeout: float = 40.0,
    ) -> None:
        self.api_base = api_base
        self.model_name = model_name
        self.timeout = timeout

    def generate_summary(
        self,
        case: ClinicalCase,
        use_llm: bool = True,
    ) -> str:
        """Generate a concise, professional clinical case summary explaining the patient to a doctor.

        Args:
            case: Active ClinicalCase instance with dimensions and transcript.
            use_llm: If True, attempts dynamic LLM synthesis; falls back to extractive composer.

        Returns:
            Concise 3-4 sentence clinical narrative suitable for medical handover.
        """
        if not case.is_ready_for_repertorization and not case.transcript and not case.chief_complaint:
            return "Patient consultation initiated. No clinical symptoms recorded yet."

        if use_llm:
            try:
                llm_summary = self._call_llm_summary(case)
                if llm_summary and len(llm_summary.strip()) > 30:
                    return llm_summary.strip()
            except Exception as err:
                logger.info("LLM summary generation unavailable (%s); falling back to extractive synthesis.", err)

        return self._generate_extractive_summary(case)

    def _call_llm_summary(self, case: ClinicalCase) -> Optional[str]:
        """Call Ollama /api/generate with clinical prompt and return sanitized summary."""
        prompt = self._build_prompt(case)
        url = f"{self.api_base.rstrip('/')}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.25,
                "num_predict": 220,
                "stop": ["\n\n\n", "DOCTOR:", "PATIENT:", "REMEDY:"],
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data.get("response", "").strip()
            return self._sanitize_llm_output(raw_text)

    def _build_prompt(self, case: ClinicalCase) -> str:
        """Construct structured clinical briefing prompt for LLaMA 3."""
        dims = case.dimensions or {}
        location_str = ", ".join(dims.get("location", [])) or "None reported"
        sensation_str = ", ".join(dims.get("sensation", [])) or "None reported"
        agg_str = ", ".join(dims.get("modality_agg", [])) or "None reported"
        amel_str = ", ".join(dims.get("modality_amel", [])) or "None reported"
        conc_str = ", ".join(dims.get("concomitant", [])) or "None reported"
        temp_str = ", ".join(dims.get("temporal", [])) or "None reported"
        mental_str = ", ".join(dims.get("mental", [])) or "None reported"

        demographics_info = case.demographics_string
        if demographics_info == "Demographics unspecified":
            demographics_info = "Age & sex unspecified"

        # Format transcript or history
        transcript_sample = case.transcript.strip()
        if not transcript_sample and case.dialogue_history:
            turns = []
            for t in case.dialogue_history[-6:]:
                role = "Patient" if t.get("role") == "user" else "Assistant"
                turns.append(f"{role}: {t.get('content', '')}")
            transcript_sample = "\n".join(turns)

        return (
            "You are an expert clinical documentation specialist in classical homeopathy.\n"
            "Synthesize the following patient intake conversation and extracted symptom dimensions "
            "into a concise, objective, 3-4 sentence clinical case summary (Physician Brief / HPI) for the attending doctor.\n\n"
            f"PATIENT PROFILE:\n"
            f"- Demographics: {demographics_info}\n"
            f"- Chief Complaint: {case.chief_complaint or 'Clinical Consultation'}\n\n"
            "KENT'S 7 TOTALITY DIMENSIONS:\n"
            f"- Location: {location_str}\n"
            f"- Sensation: {sensation_str}\n"
            f"- Worse from (Aggravation): {agg_str}\n"
            f"- Better from (Amelioration): {amel_str}\n"
            f"- Concomitants: {conc_str}\n"
            f"- Time Pattern: {temp_str}\n"
            f"- Mental / Emotional: {mental_str}\n\n"
            "FULL INTAKE TRANSCRIPT:\n"
            f"{transcript_sample or 'Structured symptom dimensions captured as listed above.'}\n\n"
            "REQUIREMENTS:\n"
            "1. Write in standard clinical narrative tone directly to the consulting physician (like a clinical handoff or SOAP Subjective section).\n"
            "2. Synthesize the primary physical complaints, sensations, key modalities (worse/better), concomitants, and prominent mental/emotional characteristics.\n"
            "3. Ensure 100% factual grounding in the patient's reported statements. Do not hallucinate external symptoms or speculate diagnoses.\n"
            "4. Length: Exactly 3 to 4 concise, cohesive sentences.\n"
            "5. Output ONLY the summary paragraph. No conversational opening, no bullet points, no 'Here is the summary'."
        )

    @staticmethod
    def _sanitize_llm_output(text: str) -> str:
        """Strip conversational preamble, markdown headers, and meta commentary."""
        if not text:
            return ""

        # Remove leading boilerplate e.g. "Here is a 3-4 sentence summary:", "Summary:", "**Clinical Summary:**"
        cleaned = re.sub(
            r"^(?:here\s+is\s+(?:a\s+)?(?:concise\s+)?clinical\s+summary.*?:|clinical\s+summary\s*:|physician\s+brief\s*:|\*\*clinical\s+summary\*\*:?)\s*",
            "",
            text.strip(),
            flags=re.IGNORECASE,
        )

        # Remove markdown quotes or code blocks
        cleaned = re.sub(r"^```(?:markdown)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip(' "\'\n\r')

        return cleaned

    @staticmethod
    def _generate_extractive_summary(case: ClinicalCase) -> str:
        """Deterministically compose an objective, grammatical clinical summary from captured dimensions."""
        dims = case.dimensions or {}
        sentences: List[str] = []

        # Sentence 1: Presentation & Demographics
        demo_parts = []
        if case.patient_age:
            demo_parts.append(f"{case.patient_age}-year-old")
        if case.patient_sex:
            demo_parts.append(case.patient_sex.lower())
        demo_str = " ".join(demo_parts) if demo_parts else "patient"

        locs = dims.get("location", [])
        sens = dims.get("sensation", [])
        cc = case.chief_complaint.strip() if case.chief_complaint else ""

        if sens and locs:
            s1 = f"The {demo_str} presents with {', '.join(sens)} localized to the {', '.join(locs)}."
        elif sens:
            s1 = f"The {demo_str} presents with {', '.join(sens)}."
        elif locs:
            s1 = f"The {demo_str} presents with symptoms localized to the {', '.join(locs)}."
        elif cc:
            s1 = f"The {demo_str} presents for consultation regarding {cc}."
        else:
            s1 = f"The {demo_str} presented for homeopathic consultation."
        sentences.append(s1)

        # Sentence 2: Modalities & Temporality
        aggs = dims.get("modality_agg", [])
        amels = dims.get("modality_amel", [])
        temps = dims.get("temporal", [])

        mod_clauses = []
        if aggs:
            mod_clauses.append(f"aggravated by {', '.join(aggs)}")
        if amels:
            mod_clauses.append(f"ameliorated by {', '.join(amels)}")
        if temps:
            mod_clauses.append(f"exhibiting a time pattern of {', '.join(temps)}")

        if mod_clauses:
            s2 = f"Symptoms are {' and '.join(mod_clauses)}."
            sentences.append(s2)

        # Sentence 3: Concomitants & Physical generals
        concs = dims.get("concomitant", [])
        if concs:
            s3 = f"Associated concomitant symptoms include {', '.join(concs)}."
            sentences.append(s3)

        # Sentence 4: Mental / Emotional disposition
        mentals = dims.get("mental", [])
        if mentals:
            s4 = f"Mental and emotional evaluation reveals {', '.join(mentals)}."
            sentences.append(s4)

        if not sentences:
            return "Patient presented for classical homeopathic intake with symptoms under evaluation."

        return " ".join(sentences)

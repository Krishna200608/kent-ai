"""BIO token auto-tagger converting entity character spans to token-level NER tags.

Used in Phase 1 to convert LLaMA 3 character offsets into token arrays and BIO tags
compatible with HuggingFace Bio_ClinicalBERT token classification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


class BIOTagger:
    """Aligns entity character spans with whitespace/subword tokens."""

    def __init__(self, categories: Optional[List[str]] = None) -> None:
        self.categories = categories or [
            "LOC", "SEN", "MOD_AGG", "MOD_AMEL", "CONC", "TEMP", "MENT"
        ]

    def tag_tokens(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Tokenize text and generate parallel BIO label sequence.
        
        Args:
            text: Narrative clinical sentence or paragraph.
            entities: List of dicts with 'start', 'end', 'label'.
            
        Returns:
            Tuple of (tokens, bio_tags).
        """
        raise NotImplementedError("Phase 1 implementation pending.")

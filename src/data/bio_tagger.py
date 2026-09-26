"""BIO token auto-tagger converting entity character spans to token-level NER tags.

Used in Phase 1 to convert LLaMA 3 character offsets into token arrays and BIO tags
compatible with HuggingFace Bio_ClinicalBERT token classification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TokenSpan:
    """Represents a token and its character offsets in original text."""
    token: str
    start: int
    end: int


@dataclass
class EntitySpan:
    """Normalized character entity annotation."""
    text: str
    label: str
    start: int
    end: int


class BIOTagger:
    """Aligns character entity spans with word/punctuation and subword tokens."""

    DEFAULT_CATEGORIES = [
        "LOC",
        "SEN",
        "MOD_AGG",
        "MOD_AMEL",
        "CONC",
        "TEMP",
        "MENT",
    ]

    # Regex matching alphanumeric words, contractions, or individual punctuation marks
    TOKEN_REGEX = re.compile(r"\w+|[^\w\s]")

    def __init__(
        self,
        categories: Optional[List[str]] = None,
        allow_unknown_labels: bool = False,
    ) -> None:
        """Initialize tagger with allowed categories.
        
        Args:
            categories: List of symptom categories. Defaults to the 7 Kent dimensions.
            allow_unknown_labels: If True, does not raise error on unknown labels.
        """
        self.categories = set(categories or self.DEFAULT_CATEGORIES)
        self.allow_unknown_labels = allow_unknown_labels
        self.tag_schema = ["O"]
        for cat in sorted(self.categories):
            self.tag_schema.extend([f"B-{cat}", f"I-{cat}"])

    def tokenize_with_offsets(self, text: str) -> List[TokenSpan]:
        """Split text into tokens while preserving exact character offsets.
        
        Args:
            text: Raw input text.
            
        Returns:
            List of TokenSpan objects with token string and character slice [start, end].
        """
        tokens: List[TokenSpan] = []
        for match in self.TOKEN_REGEX.finditer(text):
            tokens.append(
                TokenSpan(
                    token=match.group(0),
                    start=match.start(),
                    end=match.end(),
                )
            )
        return tokens

    def align_entity_offsets(
        self, text: str, entity: Dict[str, Any]
    ) -> Optional[EntitySpan]:
        """Verify and repair character offsets if LLM generation drifted slightly.
        
        Args:
            text: Full narrative string.
            entity: Entity dictionary containing 'text', 'label', and optional 'start', 'end'.
            
        Returns:
            Aligned EntitySpan or None if entity text could not be located in narrative.
        """
        ent_text = entity.get("text", "").strip()
        label = entity.get("label", "").strip()
        if not ent_text or not label:
            return None

        if not self.allow_unknown_labels and label not in self.categories:
            return None

        start = entity.get("start")
        end = entity.get("end")

        # 1. Check if provided offsets are already exact
        if (
            isinstance(start, int)
            and isinstance(end, int)
            and 0 <= start < end <= len(text)
            and text[start:end] == ent_text
        ):
            return EntitySpan(text=ent_text, label=label, start=start, end=end)

        # 2. Check near provided start if within small offset drift
        if isinstance(start, int) and 0 <= start <= len(text):
            search_window_start = max(0, start - 15)
            search_window_end = min(len(text), start + len(ent_text) + 15)
            window = text[search_window_start:search_window_end]
            local_idx = window.find(ent_text)
            if local_idx != -1:
                real_start = search_window_start + local_idx
                return EntitySpan(
                    text=ent_text,
                    label=label,
                    start=real_start,
                    end=real_start + len(ent_text),
                )

        # 3. Global search for exact substring
        idx = text.find(ent_text)
        if idx != -1:
            return EntitySpan(
                text=ent_text,
                label=label,
                start=idx,
                end=idx + len(ent_text),
            )

        # 4. Case-insensitive fallback search
        lower_idx = text.lower().find(ent_text.lower())
        if lower_idx != -1:
            actual_text = text[lower_idx : lower_idx + len(ent_text)]
            return EntitySpan(
                text=actual_text,
                label=label,
                start=lower_idx,
                end=lower_idx + len(ent_text),
            )

        return None

    def tag_tokens(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Tokenize text and generate parallel BIO label sequence.
        
        Args:
            text: Narrative clinical sentence or paragraph.
            entities: List of dicts with 'text', 'label', and optional 'start', 'end'.
            
        Returns:
            Tuple of (tokens, bio_tags).
        """
        token_spans = self.tokenize_with_offsets(text)
        if not token_spans:
            return [], []

        # Validate and align all entity spans
        aligned_entities: List[EntitySpan] = []
        for ent in entities:
            aligned = self.align_entity_offsets(text, ent)
            if aligned:
                aligned_entities.append(aligned)

        # Sort entities by start position and length (longer spans preferred if identical start)
        aligned_entities.sort(key=lambda e: (e.start, -(e.end - e.start)))

        tokens: List[str] = []
        bio_tags: List[str] = []

        for tok in token_spans:
            tokens.append(tok.token)

            # Find matching entity (if any)
            matched_ent: Optional[EntitySpan] = None
            for ent in aligned_entities:
                # Token overlaps entity span
                if max(tok.start, ent.start) < min(tok.end, ent.end):
                    matched_ent = ent
                    break

            if matched_ent is None:
                bio_tags.append("O")
            else:
                # If this token is the beginning of the entity, use B-, else I-
                # Beginning condition: token start <= entity start, or previous token was not part of this entity
                is_first_token = tok.start <= matched_ent.start or (
                    len(bio_tags) > 0
                    and (
                        bio_tags[-1] == "O"
                        or not bio_tags[-1].endswith(f"-{matched_ent.label}")
                    )
                )

                prefix = "B" if is_first_token else "I"
                bio_tags.append(f"{prefix}-{matched_ent.label}")

        return tokens, bio_tags

    def extract_spans_from_bio(
        self, tokens: List[str], bio_tags: List[str]
    ) -> List[Dict[str, Any]]:
        """Reconstruct entity spans from parallel tokens and BIO tags.
        
        Args:
            tokens: List of token strings.
            bio_tags: List of corresponding BIO tags.
            
        Returns:
            List of dicts with 'text', 'label', 'token_start', 'token_end'.
        """
        spans: List[Dict[str, Any]] = []
        current_label: Optional[str] = None
        current_tokens: List[str] = []
        start_idx: int = 0

        for i, (tok, tag) in enumerate(zip(tokens, bio_tags)):
            if tag.startswith("B-"):
                if current_label and current_tokens:
                    spans.append({
                        "text": " ".join(current_tokens),
                        "label": current_label,
                        "token_start": start_idx,
                        "token_end": i,
                    })
                current_label = tag[2:]
                current_tokens = [tok]
                start_idx = i
            elif tag.startswith("I-") and current_label == tag[2:]:
                current_tokens.append(tok)
            else:
                if current_label and current_tokens:
                    spans.append({
                        "text": " ".join(current_tokens),
                        "label": current_label,
                        "token_start": start_idx,
                        "token_end": i,
                    })
                current_label = None
                current_tokens = []

        if current_label and current_tokens:
            spans.append({
                "text": " ".join(current_tokens),
                "label": current_label,
                "token_start": start_idx,
                "token_end": len(tokens),
            })

        return spans

    def align_with_subwords(
        self,
        subword_offsets: List[Tuple[int, int]],
        entities: List[Dict[str, Any]],
        text: str,
        ignore_index: int = -100,
        mask_continuation_subwords: bool = False,
        tag_to_id: Optional[Dict[str, int]] = None,
    ) -> List[int | str]:
        """Align character entity spans with HuggingFace FastTokenizer offset mappings.
        
        Args:
            subword_offsets: List of (start_char, end_char) from tokenizer offset_mapping.
            entities: List of raw entity dicts.
            text: Original text string.
            ignore_index: PyTorch label ignore index for special tokens (default -100).
            mask_continuation_subwords: If True, set subsequent subwords of an entity to ignore_index.
            tag_to_id: Optional mapping of BIO string tags to integer label IDs.
            
        Returns:
            List of BIO tag strings or integer IDs aligned with subword tokens.
        """
        aligned_entities: List[EntitySpan] = []
        for ent in entities:
            aligned = self.align_entity_offsets(text, ent)
            if aligned:
                aligned_entities.append(aligned)

        labels: List[int | str] = []
        prev_entity: Optional[EntitySpan] = None

        for start, end in subword_offsets:
            # Special tokens ([CLS], [SEP], [PAD]) typically have (0, 0) offsets
            if start == end:
                labels.append(ignore_index if tag_to_id else "O")
                continue

            matched_ent: Optional[EntitySpan] = None
            for ent in aligned_entities:
                if max(start, ent.start) < min(end, ent.end):
                    matched_ent = ent
                    break

            if matched_ent is None:
                tag = "O"
                prev_entity = None
            else:
                if matched_ent is not prev_entity:
                    tag = f"B-{matched_ent.label}"
                    prev_entity = matched_ent
                else:
                    if mask_continuation_subwords:
                        labels.append(ignore_index)
                        continue
                    tag = f"I-{matched_ent.label}"

            if tag_to_id is not None:
                labels.append(tag_to_id.get(tag, 0))
            else:
                labels.append(tag)

        return labels

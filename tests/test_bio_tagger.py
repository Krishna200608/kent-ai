"""Unit tests for BIOTagger."""

import pytest
from src.data.bio_tagger import BIOTagger, TokenSpan, EntitySpan


@pytest.fixture
def tagger():
    return BIOTagger()


def test_tokenize_with_offsets(tagger):
    text = "Doctor, I have severe throbbing pain in my forehead."
    tokens = tagger.tokenize_with_offsets(text)
    
    assert len(tokens) > 0
    # First token is "Doctor"
    assert tokens[0].token == "Doctor"
    assert tokens[0].start == 0
    assert tokens[0].end == 6
    assert text[tokens[0].start:tokens[0].end] == "Doctor"
    
    # Comma is captured as punctuation
    assert tokens[1].token == ","
    assert tokens[1].start == 6
    assert tokens[1].end == 7


def test_align_entity_offsets_exact(tagger):
    text = "I feel terribly anxious in the evening."
    entity = {"text": "anxious", "label": "MENT", "start": 16, "end": 23}
    aligned = tagger.align_entity_offsets(text, entity)
    
    assert aligned is not None
    assert aligned.text == "anxious"
    assert aligned.label == "MENT"
    assert aligned.start == 16
    assert aligned.end == 23


def test_align_entity_offsets_drift_repair(tagger):
    text = "I feel terribly anxious in the evening."
    # Drifted by 2 characters
    entity = {"text": "anxious", "label": "MENT", "start": 14, "end": 21}
    aligned = tagger.align_entity_offsets(text, entity)
    
    assert aligned is not None
    assert aligned.start == 16
    assert aligned.end == 23
    assert text[aligned.start:aligned.end] == "anxious"


def test_tag_tokens_single_and_multiword(tagger):
    text = "Doctor, I feel severe anxiety in the morning and sharp throbbing in my temples."
    entities = [
        {"text": "anxiety", "label": "MENT", "start": 23, "end": 30},
        {"text": "in the morning", "label": "TEMP", "start": 31, "end": 45},
        {"text": "sharp throbbing", "label": "SEN", "start": 50, "end": 65},
        {"text": "temples", "label": "LOC", "start": 72, "end": 79},
    ]
    tokens, bio_tags = tagger.tag_tokens(text, entities)

    assert len(tokens) == len(bio_tags)
    assert "Doctor" in tokens
    assert bio_tags[tokens.index("Doctor")] == "O"
    
    # anxiety -> B-MENT
    anx_idx = tokens.index("anxiety")
    assert bio_tags[anx_idx] == "B-MENT"

    # in the morning -> B-TEMP, I-TEMP, I-TEMP
    in_idx = tokens.index("in")
    assert bio_tags[in_idx] == "B-TEMP"
    assert bio_tags[in_idx + 1] == "I-TEMP"
    assert bio_tags[in_idx + 2] == "I-TEMP"

    # sharp throbbing -> B-SEN, I-SEN
    sharp_idx = tokens.index("sharp")
    assert bio_tags[sharp_idx] == "B-SEN"
    assert bio_tags[sharp_idx + 1] == "I-SEN"

    # temples -> B-LOC
    temples_idx = tokens.index("temples")
    assert bio_tags[temples_idx] == "B-LOC"


def test_extract_spans_from_bio(tagger):
    tokens = ["I", "have", "burning", "pain", "in", "forehead"]
    bio_tags = ["O", "O", "B-SEN", "I-SEN", "O", "B-LOC"]
    
    spans = tagger.extract_spans_from_bio(tokens, bio_tags)
    assert len(spans) == 2
    assert spans[0]["text"] == "burning pain"
    assert spans[0]["label"] == "SEN"
    assert spans[0]["token_start"] == 2
    assert spans[0]["token_end"] == 4
    assert spans[1]["text"] == "forehead"
    assert spans[1]["label"] == "LOC"


def test_align_with_subwords_and_ignore_index(tagger):
    text = "burning pain"
    entities = [{"text": "burning pain", "label": "SEN", "start": 0, "end": 12}]
    # Subword offsets mimicking HuggingFace tokenizer with [CLS] and [SEP]
    subword_offsets = [
        (0, 0),    # [CLS]
        (0, 4),    # "burn"
        (4, 7),    # "##ing"
        (8, 12),   # "pain"
        (0, 0),    # [SEP]
    ]
    
    tag_to_id = {"O": 0, "B-SEN": 1, "I-SEN": 2}
    labels = tagger.align_with_subwords(
        subword_offsets=subword_offsets,
        entities=entities,
        text=text,
        ignore_index=-100,
        tag_to_id=tag_to_id,
    )
    
    assert labels[0] == -100  # [CLS] ignored
    assert labels[1] == 1     # "burn" -> B-SEN
    assert labels[2] == 2     # "##ing" -> I-SEN
    assert labels[3] == 2     # "pain" -> I-SEN
    assert labels[4] == -100  # [SEP] ignored

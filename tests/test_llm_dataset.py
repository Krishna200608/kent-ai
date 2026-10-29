"""Unit tests for generative LLM dataset formatting, cleaning, and grounding verification."""

import json
from pathlib import Path

import pytest

from src.models.llm_dataset import (
    CANONICAL_DIMENSIONS,
    calculate_grounding_rate,
    clean_llm_json_response,
    extract_7dim_slots_from_case,
    format_case_to_messages,
    load_instruction_dataset,
    normalize_dimension_key,
)


@pytest.fixture
def sample_case():
    return {
        "case_id": "test_001",
        "narrative": "Doctor, I have severe throbbing pain in my forehead every morning around 7 AM.",
        "entities": [
            {"text": "forehead", "label": "LOC", "start": 44, "end": 52},
            {"text": "severe throbbing pain", "label": "SEN", "start": 21, "end": 42},
            {"text": "every morning around 7 AM", "label": "TEMP", "start": 53, "end": 78},
        ],
        "rubric_path": "HEAD > PAIN > morning > 7 a.m.",
    }


def test_extract_7dim_slots_from_case(sample_case):
    slots = extract_7dim_slots_from_case(sample_case)
    assert set(slots.keys()) == set(CANONICAL_DIMENSIONS)
    assert slots["LOC"] == ["forehead"]
    assert slots["SEN"] == ["severe throbbing pain"]
    assert slots["TEMP"] == ["every morning around 7 AM"]
    assert slots["MOD_AGG"] == []
    assert slots["MOD_AMEL"] == []
    assert slots["CONC"] == []
    assert slots["MENT"] == []


def test_normalize_dimension_key():
    assert normalize_dimension_key("location") == "LOC"
    assert normalize_dimension_key("LOC") == "LOC"
    assert normalize_dimension_key("aggravation") == "MOD_AGG"
    assert normalize_dimension_key("MOD_AGG") == "MOD_AGG"
    assert normalize_dimension_key("amelioration") == "MOD_AMEL"
    assert normalize_dimension_key("concomitant") == "CONC"
    assert normalize_dimension_key("temporal") == "TEMP"
    assert normalize_dimension_key("mental") == "MENT"
    assert normalize_dimension_key("unknown_key") is None


def test_format_case_to_messages(sample_case):
    messages = format_case_to_messages(sample_case)
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"
    
    # Assistant content must be valid JSON
    parsed = json.loads(messages[2]["content"])
    assert parsed["LOC"] == ["forehead"]
    assert parsed["SEN"] == ["severe throbbing pain"]
    assert parsed["TEMP"] == ["every morning around 7 AM"]


def test_clean_llm_json_response_direct():
    raw = '{"LOC": ["temples"], "SEN": ["sharp ache"], "MOD_AGG": [], "MOD_AMEL": [], "CONC": [], "TEMP": [], "MENT": []}'
    parsed, is_clean = clean_llm_json_response(raw)
    assert is_clean is True
    assert parsed is not None
    assert parsed["LOC"] == ["temples"]
    assert parsed["SEN"] == ["sharp ache"]


def test_clean_llm_json_response_markdown():
    raw = """```json
{
  "LOC": ["stomach"],
  "SEN": ["burning"],
  "MOD_AGG": ["after eating"],
  "MOD_AMEL": [],
  "CONC": [],
  "TEMP": [],
  "MENT": []
}
```"""
    parsed, is_clean = clean_llm_json_response(raw)
    assert parsed is not None
    assert parsed["LOC"] == ["stomach"]
    assert parsed["MOD_AGG"] == ["after eating"]


def test_clean_llm_json_response_conversational_wrapping():
    raw = """Here is the extracted clinical information:
    {
      "LOC": ["chest"],
      "SEN": ["constriction"],
      "MOD_AGG": [],
      "MOD_AMEL": [],
      "CONC": ["palpitations"],
      "TEMP": [],
      "MENT": ["anxiety"]
    }
    I hope this helps your clinical analysis!"""
    parsed, is_clean = clean_llm_json_response(raw)
    assert is_clean is False
    assert parsed is not None
    assert parsed["LOC"] == ["chest"]
    assert parsed["CONC"] == ["palpitations"]
    assert parsed["MENT"] == ["anxiety"]


def test_calculate_grounding_rate():
    narrative = "The patient reports severe migraine in temples aggravated by bright sunlight."
    extracted = {
        "LOC": ["temples"],
        "SEN": ["severe migraine"],
        "MOD_AGG": ["bright sunlight"],
        "MOD_AMEL": ["dark room"],  # Hallucinated / not in narrative!
        "CONC": [],
        "TEMP": [],
        "MENT": [],
    }
    ratio, grounded, total = calculate_grounding_rate(extracted, narrative)
    assert total == 4
    assert grounded == 3
    assert ratio == 0.75


def test_load_instruction_dataset(tmp_path):
    sample_file = tmp_path / "test_cases.jsonl"
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(json.dumps({"case_id": "1", "narrative": "Case 1", "entities": []}) + "\n")
        f.write(json.dumps({"case_id": "2", "narrative": "Case 2", "entities": []}) + "\n")
        f.write(json.dumps({"case_id": "3", "narrative": "Case 3", "entities": []}) + "\n")

    cases = load_instruction_dataset(sample_file, max_samples=2)
    assert len(cases) == 2
    assert cases[0]["case_id"] == "1"
    assert cases[1]["case_id"] == "2"

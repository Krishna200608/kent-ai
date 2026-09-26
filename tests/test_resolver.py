"""Unit tests for SymptomProfile and SymptomResolver (Phase 4)."""

import pytest

from src.models.resolver import SymptomProfile, SymptomResolver


def test_symptom_profile_serialization():
    profile = SymptomProfile(
        chief_complaint="Throbbing headache on forehead",
        location=["forehead"],
        sensation=["throbbing"],
        modality_agg=["sun exposure"],
        modality_amel=["cold application"],
        concomitant=["nausea"],
        temporal=["morning"],
        mental=["irritability"],
        negated=["vomiting"],
    )
    d = profile.to_dict()
    assert d["chief_complaint"] == "Throbbing headache on forehead"
    assert "forehead" in d["location"]
    assert "throbbing" in d["sensation"]
    assert "vomiting" in d["negated"]


def test_symptom_profile_search_queries_generation():
    profile = SymptomProfile(
        location=["forehead", "temples"],
        sensation=["throbbing"],
        modality_agg=["sun", "warm room"],
        modality_amel=["cold compress"],
        concomitant=["nausea"],
        temporal=["morning"],
        mental=["anxiety"],
    )
    queries = profile.get_search_queries()
    assert len(queries) >= 5
    assert any("forehead temples throbbing" in q for q in queries)
    assert any("worse from sun" in q for q in queries)
    assert any("better from cold compress" in q for q in queries)
    assert any("mind anxiety" in q for q in queries)


def test_resolver_mock_extraction_and_negation():
    resolver = SymptomResolver(mock_mode=True)
    transcript = "Patient reports throbbing pain in forehead worse from sun. Denies nausea and no fever."
    raw_entities = [
        {"text": "forehead", "label": "LOC", "start": 32, "end": 40},
        {"text": "throbbing pain", "label": "SEN", "start": 16, "end": 30},
        {"text": "sun", "label": "MOD_AGG", "start": 52, "end": 55},
        {"text": "nausea", "label": "CONC", "start": 64, "end": 70},
        {"text": "fever", "label": "CONC", "start": 79, "end": 84},
    ]

    profile = resolver.resolve(transcript, raw_entities)
    assert "forehead" in profile.location
    assert "throbbing pain" in profile.sensation
    assert "sun" in profile.modality_agg
    # Nausea and fever should be marked as negated
    assert "nausea" in profile.negated or "fever" in profile.negated
    assert "nausea" not in profile.concomitant
    assert "fever" not in profile.concomitant


def test_resolver_json_parsing_resilience():
    resolver = SymptomResolver(mock_mode=True)
    raw_md = """```json
    {
      "chief_complaint": "Splitting headache",
      "location": ["temples"],
      "sensation": ["splitting"],
      "modality_agg": ["noise"],
      "negated": ["blurred vision"]
    }
    ```"""
    parsed = resolver._parse_response(raw_md)
    assert parsed["chief_complaint"] == "Splitting headache"
    assert parsed["location"] == ["temples"]
    assert parsed["modality_agg"] == ["noise"]
    assert parsed["negated"] == ["blurred vision"]

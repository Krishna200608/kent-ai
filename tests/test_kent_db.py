"""Unit tests for Kent Repertory SQLite database access layer and configuration."""

import pytest
from pathlib import Path

from src.config import (
    get_project_root,
    get_model_config,
    get_generation_config,
    get_chromadb_config,
    get_chatbot_config,
    load_config,
)
from src.data.kent_db import (
    KentDB,
    get_connection,
    get_db_path,
    get_mind_rubrics,
    get_remedies,
    get_rubric_by_id,
    get_rubric_path,
    get_rubrics,
    get_sections,
    search_rubrics,
)


class TestConfigSystem:
    """Test YAML configuration loader and defaults."""

    def test_project_root_detection(self):
        root = get_project_root()
        assert root.is_dir()
        assert (root / "configs").is_dir()

    def test_load_all_configs(self):
        model_cfg = get_model_config()
        assert "model" in model_cfg
        assert model_cfg["model"]["name"] == "emilyalsentzer/Bio_ClinicalBERT"
        assert len(model_cfg["labels"]["tags"]) == 15

        gen_cfg = get_generation_config()
        assert "generation" in gen_cfg
        assert gen_cfg["target_data"]["section_id"] == 1
        assert gen_cfg["target_data"]["rubric_count"] == 4933

        chroma_cfg = get_chromadb_config()
        assert chroma_cfg["vector_store"]["collection_name"] == "kent_rubrics"

        bot_cfg = get_chatbot_config()
        assert "GREETING" in bot_cfg["state_machine"]["states"]
        assert "DONE" in bot_cfg["state_machine"]["terminal_states"]


class TestKentDBReader:
    """Test SQLite data access layer for Kent's Repertory."""

    def test_get_db_path(self):
        db_path = get_db_path()
        assert db_path.is_file()
        assert db_path.name == "repertory.sqlite"

    def test_connection_context(self):
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

    def test_get_sections(self):
        sections = get_sections()
        assert len(sections) == 37, f"Expected 37 sections, got {len(sections)}"
        first_section = sections[0]
        assert first_section["id"] == 1
        assert first_section["name"] == "MIND"
        assert first_section["rubric_count"] == 4933

        # Verify all sections have required fields
        for sec in sections:
            assert "id" in sec
            assert "name" in sec
            assert "rubric_count" in sec
            assert sec["rubric_count"] > 0

    def test_get_mind_rubrics_count(self):
        """Phase 0 Primary Exit Criteria: MIND section contains exactly 4933 rubrics."""
        mind_rubrics = get_mind_rubrics()
        assert len(mind_rubrics) == 4933

    def test_get_mind_rubrics_pagination(self):
        page1 = get_mind_rubrics(limit=10, offset=0)
        page2 = get_mind_rubrics(limit=10, offset=10)
        assert len(page1) == 10
        assert len(page2) == 10
        assert page1[0]["id"] != page2[0]["id"]

    def test_get_rubric_by_id(self):
        rubric = get_rubric_by_id(1)
        assert rubric is not None
        assert rubric["id"] == 1
        assert rubric["section_id"] == 1
        assert rubric["label"] == "ABANDONED"
        assert rubric["depth"] == 0

        # Non-existent rubric
        non_existent = get_rubric_by_id(9999999)
        assert non_existent is None

    def test_get_rubric_path(self):
        path1 = get_rubric_path(1)
        assert path1 == "MIND > ABANDONED"

        path2 = get_rubric_path(2)
        assert path2 == "MIND > ABANDONED > feels he is"

        with pytest.raises(KeyError):
            get_rubric_path(9999999)

    def test_get_rubrics_hierarchy(self):
        # Top-level rubrics in MIND
        root_rubrics = get_rubrics(section_id=1, parent_id=-1)
        assert len(root_rubrics) > 0
        for r in root_rubrics:
            assert r["parent_id"] is None

        # Child rubrics of rubric 1
        children = get_rubrics(section_id=1, parent_id=1)
        assert len(children) >= 1
        assert any(c["id"] == 2 for c in children)

    def test_get_remedies_structure_and_grades(self):
        # Rubric 4: 'ABSENT-MINDED' has known remedies
        remedies = get_remedies(4)
        assert len(remedies) > 0

        # Check all entries have basic fields and valid grades
        for rem in remedies:
            assert "rubric_id" in rem
            assert "grade" in rem
            assert rem["grade"] in [1, 2, 3], f"Invalid grade {rem['grade']} for remedy {rem}"
            assert rem["normalized"] is not None or rem["raw_token"] is not None

        # Check that resolved remedies contain abbreviations and full names
        resolved = [r for r in remedies if r["remedy_id"] is not None]
        assert len(resolved) > 0
        for r in resolved:
            assert r["abbreviation"] is not None
            assert r["full_name"] is not None

    def test_search_rubrics(self):
        results = search_rubrics("fear dark", section_id=1, limit=5)
        assert len(results) > 0
        for res in results:
            assert res["section_id"] == 1
            assert "dark" in res["path"].lower() or "fear" in res["path"].lower()

    def test_kent_db_class_interface(self):
        db = KentDB()
        assert len(db.get_sections()) == 37
        assert len(db.get_mind_rubrics()) == 4933
        assert db.get_rubric_path(1) == "MIND > ABANDONED"
        assert len(db.get_remedies(4)) > 0

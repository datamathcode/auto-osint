"""
Unit tests for the research playbook module.
"""

import pathlib

import frontmatter
import pytest

from src.python import research_playbook


@pytest.fixture
def playbook_path(tmp_path, monkeypatch):
    """Point the module at a temporary MDX file."""
    path = pathlib.Path(tmp_path) / "research_playbook.mdx"
    monkeypatch.setattr(research_playbook, "RESEARCH_PLAYBOOK_PATH", path)
    return path


class TestResearchPlaybook:
    """Test suite for the research playbook loader/saver."""

    def test_default_playbook_has_expected_sections(self):
        """Test the default playbook structure."""
        playbook = research_playbook.create_default_playbook()

        assert playbook["version"] == "1.0.0"
        assert "funding" in playbook
        assert "intellectual_property" in playbook
        assert playbook["funding"]["suggested_tools"][0] == "SEC filings"
        assert playbook["default_confidence_thresholds"]["final"] == 0.9

    def test_load_falls_back_to_default_when_missing(self, playbook_path):
        """Test that a missing file yields the default playbook."""
        assert not playbook_path.exists()

        playbook = research_playbook.load()

        assert playbook == research_playbook.create_default_playbook()

    def test_save_then_load_round_trips(self, playbook_path):
        """Test saving metadata and loading it back."""
        metadata = {
            "version": "2.0.0",
            "funding": {"suggested_tools": ["SEC filings", "annual reports"]},
        }

        research_playbook.save(metadata)

        assert playbook_path.exists()
        assert research_playbook.load()["version"] == "2.0.0"
        assert research_playbook.load()["funding"]["suggested_tools"] == [
            "SEC filings",
            "annual reports",
        ]

    def test_get_tool_suggestions_for_known_claim_type(self, playbook_path):
        """Test tool lookup for a claim type present in the file."""
        research_playbook.save(
            {"version": "1.0.0", "funding": {"suggested_tools": ["SEC filings"]}}
        )

        assert research_playbook.get_tool_suggestions("funding") == ["SEC filings"]

    def test_get_tool_suggestions_for_unknown_claim_type(self, playbook_path):
        """Test tool lookup for a claim type that is not in the file."""
        research_playbook.save({"version": "1.0.0"})

        assert research_playbook.get_tool_suggestions("unknown") == []


class TestCheckedInPlaybook:
    """Assert the shipped MDX carries the front matter the loader expects."""

    def test_checked_in_file_has_front_matter(self):
        """The repository playbook must load real metadata, not an empty dict."""
        metadata = frontmatter.loads(
            pathlib.Path(
                "src/python/research_playbook.mdx"
            ).read_text(encoding="utf-8")
        ).metadata

        assert metadata["version"]
        assert metadata["funding"]["suggested_tools"]
        assert metadata["intellectual_property"]["suggested_tools"]
        assert metadata["default_questioning_strategies"]
        assert metadata["default_confidence_thresholds"]["final"] > 0

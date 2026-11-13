"""
Unit tests for the evidence migration script.

Tests verify migration logic, confidence handling, and verification.
"""

from unittest.mock import Mock, patch

import pytest

from src.python.migrations.migrate_evidence_to_confidence import EvidenceMigration


class TestEvidenceMigration:
    """Test suite for EvidenceMigration class."""

    def test_migration_init(self):
        """Test migration initialization."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)

        assert migration.session == mock_session

    def test_is_structured_with_confidence_and_independence(self):
        """Test detection of structured evidence."""
        migration = EvidenceMigration(Mock())

        evidence = Mock()
        evidence.confidence = 0.8
        evidence.independence_score = 0.9
        evidence.independence_check_details = {"test": "data"}

        assert migration._is_structured(evidence) is True

    def test_is_structured_without_confidence(self):
        """Test detection of unstructured evidence (no confidence)."""
        migration = EvidenceMigration(Mock())

        evidence = Mock()
        evidence.confidence = None
        evidence.independence_score = 0.9
        evidence.independence_check_details = {"test": "data"}

        assert migration._is_structured(evidence) is False

    def test_is_structured_without_independence(self):
        """Test detection of unstructured evidence (no independence)."""
        migration = EvidenceMigration(Mock())

        evidence = Mock()
        evidence.confidence = 0.8
        evidence.independence_score = None
        evidence.independence_check_details = {"test": "data"}

        assert migration._is_structured(evidence) is False

    def test_is_structured_without_details(self):
        """Test detection of unstructured evidence (no details)."""
        migration = EvidenceMigration(Mock())

        evidence = Mock()
        evidence.confidence = 0.8
        evidence.independence_score = 0.9
        evidence.independence_check_details = None

        assert migration._is_structured(evidence) is False

    def test_migrate_no_evidence(self):
        """Test migration when no evidence entries exist."""
        mock_session = Mock()
        mock_session.query.return_value.all.return_value = []

        stats = EvidenceMigration(mock_session).migrate_evidence()

        assert stats["total"] == 0
        assert stats["success"] == 0
        assert stats["failed"] == 0
        assert stats["skipped"] == 0

    def test_migrate_all_structured(self):
        """Test migration when all entries are already structured."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)

        mock_session.query.return_value.all.return_value = [Mock(), Mock()]

        with patch.object(EvidenceMigration, "_is_structured", return_value=True):
            stats = migration.migrate_evidence()

        assert stats["total"] == 2
        assert stats["success"] == 0
        assert stats["skipped"] == 2
        assert stats["failed"] == 0

    def test_migrate_single_unstructured_entry(self):
        """Test migrating one entry without a confidence module."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)

        evidence = Mock()
        evidence.id = 1
        evidence.confidence = None
        evidence.independence_score = None
        evidence.independence_check_details = None
        evidence.chain_of_custody = []
        evidence.claim = "raw claim string"

        mock_session.query.return_value.all.return_value = [evidence]

        with patch.object(EvidenceMigration, "_is_structured", return_value=False):
            stats = migration.migrate_evidence(confidence_module=None)

        assert stats["total"] == 1
        assert stats["success"] == 1
        assert stats["skipped"] == 0
        assert stats["failed"] == 0
        assert evidence.confidence == 0.5
        assert evidence.independence_score == 0.5
        assert evidence.independence_check_details is not None
        mock_session.commit.assert_called_once()

    def test_migrate_failure_is_counted(self):
        """Test that a per-entry failure is counted and rolled back."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)

        evidence = Mock()
        evidence.id = 1
        evidence.confidence = None
        evidence.independence_score = None
        evidence.independence_check_details = None
        evidence.claim = "raw claim string"
        evidence.chain_of_custody = Mock()
        evidence.chain_of_custody.append.side_effect = RuntimeError("append failed")

        mock_session.query.return_value.all.return_value = [evidence]

        with patch.object(EvidenceMigration, "_is_structured", return_value=False):
            stats = migration.migrate_evidence(confidence_module=None)

        assert stats["total"] == 1
        assert stats["success"] == 0
        assert stats["failed"] == 1
        mock_session.rollback.assert_called_once()

    def test_verify_migration(self):
        """Test migration verification."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)

        mock_session.query.return_value.all.return_value = [Mock(), Mock()]

        with patch.object(EvidenceMigration, "_is_structured", return_value=True):
            stats = migration.verify_migration()

        assert stats["total"] == 2
        assert stats["structured"] == 2
        assert stats["unstructured"] == 0
        assert stats["structured_rate"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

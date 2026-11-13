"""
Unit tests for evidence migration script.

Tests verify migration logic, confidence calculation, and verification.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

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
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)
        
        evidence = Mock()
        evidence.confidence = 0.8
        evidence.independence_score = 0.9
        evidence.independence_check_details = {"test": "data"}
        
        assert migration._is_structured(evidence) == True

    def test_is_structured_without_confidence(self):
        """Test detection of unstructured evidence (no confidence)."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)
        
        evidence = Mock()
        evidence.confidence = None
        evidence.independence_score = 0.9
        evidence.independence_check_details = {"test": "data"}
        
        assert migration._is_structured(evidence) == False

    def test_is_structured_without_independence(self):
        """Test detection of unstructured evidence (no independence)."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)
        
        evidence = Mock()
        evidence.confidence = 0.8
        evidence.independence_score = None
        evidence.independence_check_details = {"test": "data"}
        
        assert migration._is_structured(evidence) == False

    def test_is_structured_without_details(self):
        """Test detection of unstructured evidence (no details)."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)
        
        evidence = Mock()
        evidence.confidence = 0.8
        evidence.independence_score = 0.9
        evidence.independence_check_details = None
        
        assert migration._is_structured(evidence) == False

    @patch('src.python.migrations.migrate_evidence_to_confidence.EvidenceMigration._is_structured')
    def test_migrate_no_evidence(self, mock_is_structured):
        """Test migration when no evidence entries exist."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)
        
        mock_session.query.return_value.all.return_value = []
        
        stats = migration.migrate_evidence()
        
        assert stats["total"] == 0
        assert stats["success"] == 0
        assert stats["failed"] == 0
        assert stats["skipped"] == 0

    @patch('src.python.migrations.migrate_evidence_to_confidence.EvidenceMigration._is_structured')
    def test_migrate_all_structured(self, mock_is_structured):
        """Test migration when all entries are already structured."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)
        
        # All entries are structured
        mock_evidence = Mock()
        mock_is_structured.return_value = True
        
        mock_session.query.return_value.all.return_value = [mock_evidence, mock_evidence]
        
        stats = migration.migrate_evidence()
        
        assert stats["total"] == 2
        assert stats["success"] == 0
        assert stats["skipped"] == 2
        assert stats["failed"] == 0

    @patch('src.python.migrations.migrate_evidence_to_confidence.EvidenceMigration._is_structured')
    @patch('src.python.migrations.migrate_evidence_to_confidence.EvidenceMigration.session.commit')
    def test_migrate_single_entry_with_confidence_module(self, mock_commit, mock_is_structured):
        """Test migration of single entry with confidence module."""
        from src.python.confidence_quantization import quantify_confidence
        
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)
        
        # Entry is not structured
        mock_is_structured.return_value = False
        
        mock_evidence = Mock()
        mock_evidence.id = 1
        mock_evidence.confidence = None
        mock_evidence.independence_score = None
        mock_evidence.independence_check_details = None
        mock_evidence.chain_of_custody = []
        
        mock_session.query.return_value.all.return_value = [mock_evidence]
        
        stats = migration.migrate_evidence(confidence_module=None)
        
        assert stats["total"] == 1
        assert stats["success"] == 1
        assert stats["skipped"] == 0
        assert stats["failed"] == 0
        mock_commit.assert_called_once()

    @patch('src.python.migrations.migrate_evidence_to_confidence.EvidenceMigration._is_structured')
    @patch('src.python.migrations.migrate_evidence_to_confidence.EvidenceMigration.session.commit')
    def test_migrate_single_entry_with_confidence_module_fails(self, mock_commit, mock_is_structured):
        """Test migration error handling."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)
        
        # Entry is not structured
        mock_is_structured.return_value = False
        
        mock_evidence = Mock()
        mock_evidence.id = 1
        mock_evidence.confidence = None
        mock_evidence.independence_score = None
        mock_evidence.independence_check_details = None
        mock_evidence.chain_of_custody = []
        
        mock_session.query.return_value.all.return_value = [mock_evidence]
        
        # Simulate error during migration
        mock_session.query.side_effect = Exception("Database error")
        
        stats = migration.migrate_evidence()
        
        assert stats["total"] == 1
        assert stats["success"] == 0
        assert stats["failed"] == 1

    def test_verify_migration(self):
        """Test migration verification."""
        mock_session = Mock()
        migration = EvidenceMigration(mock_session)
        
        mock_evidence1 = Mock()
        mock_evidence1.confidence = 0.8
        mock_evidence1.independence_score = 0.9
        mock_evidence1.independence_check_details = {"test": "data"}
        
        mock_evidence2 = Mock()
        mock_evidence2.confidence = 0.5
        mock_evidence2.independence_score = 0.6
        mock_evidence2.independence_check_details = {"test": "data"}
        
        mock_session.query.return_value.all.return_value = [mock_evidence1, mock_evidence2]
        
        stats = migration.verify_migration()
        
        assert stats["total"] == 2
        assert stats["structured"] == 2
        assert stats["unstructured"] == 0
        assert stats["structured_rate"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Integration test: copy evidence between databases, then migrate it with the
confidence module. Exercises the real ORM, real SQLite files, and the real
migration script — no mocked sessions.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.confidence_quantization as confidence_module
import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.agents.base import AgentBase
from src.python.database import init_db
from src.python.migrations.migrate_evidence_to_confidence import (
    EvidenceMigration,
    transfer_evidence,
)
from src.python.models.evidence import Evidence
from src.python.models.investigation import Investigation


class RecordingAgent(AgentBase):
    """Concrete agent that only records what it is told."""

    def execute(self, context):
        return {"status": "success"}


@pytest.fixture
def source_db(tmp_path):
    url = f"sqlite:///{tmp_path / 'source.db'}"
    engine = create_engine(url)
    init_db(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        investigation = Investigation(
            target_name="Example Corp",
            claim_under_investigation="Example Corp is funded by Acme",
            status="completed",
        )
        session.add(investigation)
        session.commit()

        session.add_all(
            [
                Evidence(
                    source="SYNINT:WhoisAgent",
                    claim="Registered to Acme in 2020",
                    confidence=0.0,
                    independence_score=0.0,
                    independence_check_details=None,
                    corroborating_sources=[],
                    contradictions=[],
                    links=["https://example.com/1"],
                    chain_of_custody=[],
                    investigation_id=investigation.id,
                ),
                Evidence(
                    source="SYNINT:WhoisAgent",
                    claim="Directors overlap with Acme board",
                    confidence=0.0,
                    independence_score=0.0,
                    independence_check_details=None,
                    corroborating_sources=[],
                    contradictions=[],
                    links=[],
                    chain_of_custody=[],
                    investigation_id=investigation.id,
                ),
                Evidence(
                    source="SYNINT:WhoisAgent",
                    claim="Already structured claim",
                    confidence=0.8,
                    independence_score=0.9,
                    independence_check_details={"financial_interest": False},
                    corroborating_sources=[],
                    contradictions=[],
                    links=[],
                    chain_of_custody=[],
                    investigation_id=investigation.id,
                ),
            ]
        )
        session.commit()
    return url


class TestFullInvestigationWithConfidence:
    def test_agent_scores_evidence_with_module(self, tmp_path):
        """AgentBase.store_evidence uses the confidence module when scores are omitted."""
        engine = create_engine(f"sqlite:///{tmp_path / 'agent.db'}")
        init_db(engine)
        Session = sessionmaker(bind=engine)

        with Session() as session:
            session.add(
                Investigation(
                    target_name="T",
                    claim_under_investigation="C",
                    status="in_progress",
                )
            )
            session.commit()

            agent = RecordingAgent(
                name="TestAgent",
                investigation_id=1,
                confidence_module=confidence_module,
            )
            agent.set_evidence_storage(session)
            evidence_id = agent.store_evidence(
                source="SYNINT:WhoisAgent", claim="Some claim"
            )
            session.commit()

            stored = session.get(Evidence, evidence_id)
            # Placeholder module: 0.0 confidence, 0.0 independence for a source
            # with no conflicts declared. Assert against the module itself so
            # the test tracks the contract rather than a hard-coded number.
            assert stored.confidence == confidence_module.quantify_confidence(
                prior_probability=0.5, likelihood=0.7, evidence="Some claim"
            )
            assert stored.independence_score == confidence_module.calculate_independence_score(
                financial_interest=False,
                organizational_tie=False,
                personal_relationship=False,
                promotional_purpose=False,
            )

    def test_declared_conflict_lowers_independence_score(self, tmp_path):
        """Independence details supplied by the caller must reach the scorer."""
        engine = create_engine(f"sqlite:///{tmp_path / 'conflict.db'}")
        init_db(engine)
        Session = sessionmaker(bind=engine)

        with Session() as session:
            session.add(
                Investigation(
                    target_name="T",
                    claim_under_investigation="C",
                    status="in_progress",
                )
            )
            session.commit()

            agent = RecordingAgent(
                name="TestAgent",
                investigation_id=1,
                confidence_module=confidence_module,
            )
            agent.set_evidence_storage(session)

            clean_id = agent.store_evidence(
                source="A",
                claim="No conflicts",
                independence_check_details={"financial_interest": False},
            )
            conflicted_id = agent.store_evidence(
                source="B",
                claim="Publisher funds the target",
                independence_check_details={"financial_interest": True},
            )
            session.commit()

            assert session.get(Evidence, conflicted_id).independence_score == 0.5
            assert session.get(Evidence, clean_id).independence_score == 0.0

    def test_transfer_then_migrate_end_to_end(self, source_db, tmp_path):
        """Copy source DB into a fresh DB, then migrate every row to structured."""
        target_url = f"sqlite:///{tmp_path / 'target.db'}"

        result = transfer_evidence(source_db, target_url, run_migration=True)

        assert result["investigations_copied"] == 1
        assert result["evidence_copied"] == 3
        assert result["migration"]["total"] == 3
        assert result["migration"]["success"] == 2  # the two unstructured rows
        assert result["migration"]["skipped"] == 1  # already structured
        assert result["migration"]["failed"] == 0
        assert result["verification"]["structured"] == 3
        assert result["verification"]["structured_rate"] == 100.0

        # The target really holds the rows, with investigation IDs remapped.
        engine = create_engine(target_url)
        Session = sessionmaker(bind=engine)
        with Session() as session:
            investigation = session.query(Investigation).one()
            rows = session.query(Evidence).all()

            assert investigation.target_name == "Example Corp"
            assert len(rows) == 3
            assert {row.investigation_id for row in rows} == {investigation.id}
            assert all(row.confidence == 0.5 for row in rows if row.claim != "Already structured claim")
            migrated = [row for row in rows if row.claim != "Already structured claim"]
            assert all(
                any(entry.get("action") == "migration_to_confidence" for entry in row.chain_of_custody)
                for row in migrated
            )

    def test_transfer_without_migration_keeps_raw_rows(self, source_db, tmp_path):
        """--no-migrate copies rows and leaves confidence untouched."""
        target_url = f"sqlite:///{tmp_path / 'target_raw.db'}"

        result = transfer_evidence(source_db, target_url, run_migration=False)

        assert result["evidence_copied"] == 3
        assert "migration" not in result

        engine = create_engine(target_url)
        Session = sessionmaker(bind=engine)
        with Session() as session:
            raw = session.query(Evidence).filter(Evidence.confidence == 0.0).count()
            assert raw == 2

    def test_migration_verification_on_target(self, source_db, tmp_path):
        """A second migration pass finds nothing left to migrate."""
        target_url = f"sqlite:///{tmp_path / 'target_twice.db'}"
        transfer_evidence(source_db, target_url, run_migration=True)

        engine = create_engine(target_url)
        Session = sessionmaker(bind=engine)
        with Session() as session:
            second = EvidenceMigration(session).migrate_evidence()

        assert second["success"] == 0
        assert second["skipped"] == 3

    def test_transfer_remaps_cross_references(self, tmp_path):
        """Corroborating/contradicting IDs must point at the copied rows."""
        source_url = f"sqlite:///{tmp_path / 'refs_source.db'}"
        target_url = f"sqlite:///{tmp_path / 'refs_target.db'}"

        engine = create_engine(source_url)
        init_db(engine)
        Session = sessionmaker(bind=engine)
        with Session() as session:
            investigation = Investigation(
                target_name="Refs", claim_under_investigation="C", status="completed"
            )
            session.add(investigation)
            session.commit()

            placeholder = Evidence(
                source="X", claim="deleted", confidence=0.5, independence_score=0.5,
                independence_check_details={}, corroborating_sources=[],
                contradictions=[], links=[], chain_of_custody=[],
                investigation_id=investigation.id,
            )
            first = Evidence(
                source="A", claim="first", confidence=0.5, independence_score=0.5,
                independence_check_details={}, corroborating_sources=[],
                contradictions=[], links=[], chain_of_custody=[],
                investigation_id=investigation.id,
            )
            second = Evidence(
                source="B", claim="second", confidence=0.5, independence_score=0.5,
                independence_check_details={}, corroborating_sources=[],
                contradictions=[], links=[], chain_of_custody=[],
                investigation_id=investigation.id,
            )
            session.add_all([placeholder, first, second])
            session.commit()

            # Delete the first row so the copied IDs cannot coincide with the
            # source IDs (source: 2, 3 -> target: 1, 2).
            session.delete(placeholder)
            # The second row corroborates and contradicts the first.
            second.corroborating_sources = [first.id]
            second.contradictions = [first.id]
            session.commit()
            source_ids = (first.id, second.id)

        transfer_evidence(source_url, target_url, run_migration=False)

        target_engine = create_engine(target_url)
        TargetSession = sessionmaker(bind=target_engine)
        with TargetSession() as session:
            rows = session.query(Evidence).order_by(Evidence.id).all()

        copied_ids = [row.id for row in rows]
        assert copied_ids != list(source_ids), "IDs should be reassigned by the target"
        copied_second = rows[1]
        assert copied_second.corroborating_sources == [rows[0].id]
        assert copied_second.contradictions == [rows[0].id]


class TestMigrationCLI:
    def test_cli_returns_non_zero_when_rows_fail(self, monkeypatch, tmp_path):
        from src.python.migrations import migrate_evidence_to_confidence as module

        monkeypatch.setattr(
            module,
            "transfer_evidence",
            lambda *a, **k: {"investigations_copied": 1, "evidence_copied": 2,
                             "migration": {"total": 2, "success": 1, "failed": 1}},
        )

        exit_code = module.main(
            ["--source-url", "sqlite:///a.db", "--target-url", "sqlite:///b.db"]
        )

        assert exit_code == 1

    def test_cli_returns_zero_on_clean_run(self, monkeypatch):
        from src.python.migrations import migrate_evidence_to_confidence as module

        monkeypatch.setattr(
            module,
            "transfer_evidence",
            lambda *a, **k: {"investigations_copied": 1, "evidence_copied": 1,
                             "migration": {"total": 1, "success": 1, "failed": 0}},
        )

        assert module.main(
            ["--source-url", "sqlite:///a.db", "--target-url", "sqlite:///b.db"]
        ) == 0

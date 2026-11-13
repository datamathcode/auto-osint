"""
Tests for the self-audit module: questions, gaps, weight, bias, API.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.audit import (
    LOW_CONFIDENCE_THRESHOLD,
    bias_analysis,
    check_questions,
    compile_questions,
    critical_gaps,
    missing_source_types,
    run_audit,
    unqueried_tools,
    weight_analysis,
)
from src.python.database import get_db, init_db
from src.python.main import app
from src.python.models.evidence import Evidence
from src.python.models.investigation import Investigation
from src.python.models.openosint_result import OpenOSINTResult


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'audit.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        db.add(
            Investigation(
                target_name="Acme Corp",
                target_id="acme",
                claim_under_investigation="Investigate funding for Acme Corp",
                status="completed",
            )
        )
        db.commit()
    return Session


def add_evidence(session, claim, source="SYNINT:WhoisAgent", confidence=0.8,
                 corroborating=None, contradictions=None, links=None):
    row = Evidence(
        source=source,
        claim=claim,
        confidence=confidence,
        independence_score=0.7,
        independence_check_details={},
        corroborating_sources=corroborating or [],
        contradictions=contradictions or [],
        links=links or [],
        chain_of_custody=[],
        investigation_id=1,
        timestamp=datetime(2026, 1, 1),
    )
    session.add(row)
    session.commit()
    return row


class TestQuestions:
    def test_templates_by_claim_type(self):
        assert "Who funds the target?" in compile_questions("Investigate funding", "funding")
        assert "Which platforms does the target use?" in compile_questions(
            "Find social accounts", "social_presence"
        )

    def test_first_question_echoes_claim(self):
        questions = compile_questions("Acme is funded by Beta", "funding")

        assert questions[0].startswith("What evidence supports: Acme is funded")

    def test_questions_matched_against_evidence(self, session):
        db = session()
        add_evidence(db, "Acme receives funding from Beta")
        questions = compile_questions("Investigate funding", "funding")

        checked = check_questions(questions, db.query(Evidence).all())

        answered = [item["question"] for item in checked if item["answered"]]
        assert "Who funds the target?" in answered
        assert "Is the funding documented in a primary filing?" not in answered
        db.close()

    def test_no_evidence_answers_nothing(self):
        questions = compile_questions("Investigate funding", "funding")

        checked = check_questions(questions, [])

        assert all(not item["answered"] for item in checked)


class TestSourceCoverage:
    def test_missing_source_types(self, session):
        db = session()
        add_evidence(db, "Acme receives funding", source="SYNINT:WhoisAgent")
        evidence = db.query(Evidence).all()

        missing = missing_source_types("funding", evidence, [])

        assert "sec" in missing
        assert "registry" in missing
        db.close()

    def test_matching_source_clears_gap(self, session):
        db = session()
        add_evidence(db, "Acme filed with SEC", source="SEC-EDGAR")
        evidence = db.query(Evidence).all()

        missing = missing_source_types("funding", evidence, [])

        assert "sec" not in missing
        db.close()

    def test_unqueried_tools(self, session):
        db = session()
        db.add(
            OpenOSINTResult(
                tool="search_username", target="acme", result={}, source="sherlock",
                error=None, investigation_id=1,
            )
        )
        db.commit()
        results = db.query(OpenOSINTResult).all()

        assert unqueried_tools("social_presence", results) == []
        assert unqueried_tools("general", results) == ["search_email"]
        db.close()


class TestWeightAndBias:
    def test_low_confidence_flagged(self, session):
        db = session()
        add_evidence(db, "weak claim", confidence=0.2)
        weight = weight_analysis(db.query(Evidence).all())

        assert weight["low_confidence"] is True
        assert weight["net_confidence"] == 0.2
        db.close()

    def test_corroboration_counts(self, session):
        db = session()
        add_evidence(db, "a", corroborating=[2, 3], contradictions=[4])
        weight = weight_analysis(db.query(Evidence).all())

        assert weight["corroborating_links"] == 2
        assert weight["contradicting_links"] == 1
        db.close()

    def test_single_source_flag(self, session):
        db = session()
        add_evidence(db, "a")
        add_evidence(db, "b")
        weight = weight_analysis(db.query(Evidence).all())

        assert weight["single_source"] is True
        db.close()

    def test_bias_detects_dominance(self, session):
        db = session()
        for index in range(3):
            add_evidence(db, f"claim {index}", source="one-blog")
        add_evidence(db, "other", source="SEC-EDGAR")

        bias = bias_analysis(db.query(Evidence).all())

        assert bias["dominated_by"] == ["one-blog"]
        assert bias["primary_sources"] == 1
        db.close()

    def test_bias_secondary_heavy(self, session):
        db = session()
        add_evidence(db, "a", source="blog")
        add_evidence(db, "b", source="twitter")
        add_evidence(db, "c", source="SEC-EDGAR")

        bias = bias_analysis(db.query(Evidence).all())

        assert bias["secondary_heavy"] is True
        db.close()


class TestCriticalGaps:
    def test_no_evidence_is_critical(self):
        gaps = critical_gaps("funding", [], {"low_confidence": True, "net_confidence": 0,
                                            "single_source": False, "evidence_count": 0},
                             ["sec"], ["who funds"])

        assert any("unsupported" in gap for gap in gaps)
        assert any("No funding primary sources" in gap for gap in gaps)
        assert any("remain unanswered" in gap for gap in gaps)

    def test_low_confidence_gap(self, session):
        db = session()
        add_evidence(db, "weak", confidence=0.2)
        weight = weight_analysis(db.query(Evidence).all())

        gaps = critical_gaps("general", db.query(Evidence).all(), weight, [], [])

        assert any(f"below {LOW_CONFIDENCE_THRESHOLD}" in gap for gap in gaps)
        db.close()


class TestRunAudit:
    def test_report_persisted_on_investigation(self, session):
        db = session()
        add_evidence(db, "Acme receives funding", confidence=0.3)

        report = run_audit(db, 1)

        assert report["claim_type"] == "funding"
        assert report["unanswered_questions"]
        assert report["gaps"]
        assert report["critical_gap_count"] == len(report["gaps"])

        stored = db.get(Investigation, 1).audit_report
        assert stored["investigation_id"] == 1
        assert stored["gaps"] == report["gaps"]
        db.close()

    def test_unknown_investigation_raises(self, session):
        db = session()
        with pytest.raises(ValueError, match="not found"):
            run_audit(db, 99)
        db.close()


class TestAuditAPI:
    @pytest.fixture
    def client(self, session):
        Session = session

        def override_get_db():
            db = Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        try:
            yield TestClient(app), Session
        finally:
            app.dependency_overrides.clear()

    def test_get_audit(self, client):
        test_client, Session = client
        with Session() as db:
            add_evidence(db, "Acme receives funding")

        response = test_client.get("/api/audit/1")

        assert response.status_code == 200
        body = response.json()
        assert body["claim_type"] == "funding"
        assert "gaps" in body and "weight" in body and "bias" in body

    def test_missing_investigation(self, client):
        test_client, _ = client

        assert test_client.get("/api/audit/999").status_code == 404

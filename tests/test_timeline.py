"""
Tests for timeline reconstruction, contradiction detection, persistence, and API.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.database import get_db, init_db
from src.python.main import app
from src.python.models.evidence import Evidence
from src.python.models.investigation import Investigation
from src.python.models.openosint_result import OpenOSINTResult
from src.python.models.timeline_event import TimelineEvent
from src.python.timeline import (
    build_timeline,
    detect_temporal_contradictions,
    event_role,
    extract_event_date,
    extract_event_year,
    persist_timeline,
)


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'timeline.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        db.add(
            Investigation(
                target_name="Example Corp",
                target_id="example.com",
                claim_under_investigation="Example Corp funding history",
                status="completed",
            )
        )
        db.commit()
    return Session


def add_evidence(session, claim, source="SYNINT:WhoisAgent", confidence=0.8, custody=None,
                 timestamp=None, links=None):
    row = Evidence(
        source=source,
        claim=claim,
        confidence=confidence,
        independence_score=0.7,
        independence_check_details={},
        corroborating_sources=[],
        contradictions=[],
        links=links or [],
        chain_of_custody=custody or [],
        investigation_id=1,
        timestamp=timestamp or datetime(2026, 1, 15, 12, 0, 0),
    )
    session.add(row)
    session.commit()
    return row


class TestExtraction:
    def test_event_date(self):
        assert extract_event_date("Filed on 2020-03-04 with the registry") == datetime(2020, 3, 4)
        assert extract_event_date("no date here") is None

    def test_invalid_date_returns_none(self):
        assert extract_event_date("2020-13-45") is None

    def test_event_year(self):
        assert extract_event_year("Acme was founded in 1999") == 1999
        assert extract_event_year("nothing") is None

    def test_roles(self):
        assert event_role("Published an article about Acme") == "publication"
        assert event_role("Acme filed its 10-K") == "publication"
        assert event_role("Acme owns the domain") == "statement"
        assert event_role("anything", action="collected") == "collection"


class TestBuildTimeline:
    def test_events_are_sorted_and_typed(self, session):
        db = session()
        add_evidence(db, "Acme was founded in 1999", custody=[{"action": "initial_capture",
                                                               "timestamp": "2026-01-15T12:00:05"}])
        add_evidence(
            db,
            "Published a press release on 2021-06-01",
            source="SYNINT:PressAgent",
            confidence=0.6,
            timestamp=datetime(2026, 1, 16, 9, 0, 0),
        )
        db.add(
            OpenOSINTResult(
                tool="search_username",
                target="example.com",
                result={"count": 1},
                source="sherlock",
                error=None,
                investigation_id=1,
                timestamp=datetime(2026, 1, 14, 8, 0, 0),
            )
        )
        db.commit()

        timeline = build_timeline(db, 1)

        timestamps = [event["timestamp"] for event in timeline["events"]]
        assert timestamps == sorted(timestamps)
        roles = {event["role"] for event in timeline["events"]}
        assert {"statement", "publication", "collection", "observation"} <= roles
        assert timeline["date_range"]["start"] == timestamps[0]
        assert timeline["date_range"]["end"] == timestamps[-1]
        assert timeline["groups"] == sorted(set(timeline["groups"]))
        assert all(event["color"].startswith("#") for event in timeline["events"])
        db.close()

    def test_statement_uses_date_from_claim(self, session):
        db = session()
        add_evidence(db, "Acme acquired Beta on 2020-05-06")
        db.commit()

        timeline = build_timeline(db, 1)

        assert timeline["events"][0]["timestamp"].startswith("2020-05-06")
        db.close()

    def test_custody_entries_become_collection_events(self, session):
        db = session()
        add_evidence(
            db,
            "Acme owns the domain",
            custody=[
                {"action": "captured", "timestamp": "2026-01-15T12:00:01"},
                {"discovery_type": "whois", "timestamp": "2026-01-15T12:00:02"},
                {"no_action": True},
            ],
        )
        db.commit()

        timeline = build_timeline(db, 1)
        collection = [event for event in timeline["events"] if event["role"] == "collection"]

        assert len(collection) == 2
        assert collection[0]["title"] == "Collected: captured"
        db.close()

    def test_failed_result_has_zero_confidence(self, session):
        db = session()
        db.add(
            OpenOSINTResult(
                tool="search_breach", target="a@b.c", result={}, source="hibp",
                error="key missing", investigation_id=1,
                timestamp=datetime(2026, 1, 1),
            )
        )
        db.commit()

        timeline = build_timeline(db, 1)

        assert timeline["events"][0]["confidence"] == 0.0
        db.close()

    def test_missing_investigation_raises(self, session):
        db = session()
        with pytest.raises(ValueError, match="not found"):
            build_timeline(db, 999)
        db.close()


class TestContradictions:
    def test_same_source_conflicting_years(self):
        events = [
            {"role": "statement", "title": "Acme founded in 1999", "source": "A"},
            {"role": "statement", "title": "Acme founded in 2004", "source": "A"},
        ]

        contradictions = detect_temporal_contradictions(events)

        assert len(contradictions) == 1
        assert sorted(contradictions[0]["years"]) == [1999, 2004]
        assert contradictions[0]["subject"] == "acme"

    def test_different_sources_do_not_conflict(self):
        events = [
            {"role": "statement", "title": "Acme founded in 1999", "source": "A"},
            {"role": "statement", "title": "Acme founded in 2004", "source": "B"},
        ]

        assert detect_temporal_contradictions(events) == []

    def test_same_year_is_not_a_contradiction(self):
        events = [
            {"role": "statement", "title": "Acme founded in 1999", "source": "A"},
            {"role": "publication", "title": "Acme article 1999", "source": "A"},
        ]

        assert detect_temporal_contradictions(events) == []

    def test_detected_through_build(self, session):
        db = session()
        add_evidence(db, "Acme founded in 1999")
        add_evidence(db, "Acme founded in 2004")
        db.commit()

        timeline = build_timeline(db, 1)

        assert timeline["contradictions"]
        db.close()


class TestPersistence:
    def test_persist_replaces_rows(self, session):
        db = session()
        add_evidence(db, "Acme owns the domain")
        db.commit()
        timeline = build_timeline(db, 1)

        first = persist_timeline(db, 1, timeline)
        second = persist_timeline(db, 1, timeline)

        assert first == second == len(timeline["events"])
        assert db.query(TimelineEvent).count() == first
        db.close()


class TestTimelineAPI:
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

    def test_get_timeline(self, client):
        test_client, Session = client
        with Session() as db:
            add_evidence(db, "Acme founded in 1999")

        response = test_client.get("/api/timeline/1")

        assert response.status_code == 200
        body = response.json()
        assert body["investigation_id"] == 1
        assert body["events"]
        assert "contradictions" in body

    def test_persist_query_parameter(self, client):
        test_client, Session = client
        with Session() as db:
            add_evidence(db, "Acme owns the domain")

        response = test_client.get("/api/timeline/1", params={"persist": "true"})

        assert response.status_code == 200
        assert response.json()["persisted"] >= 1
        with Session() as db:
            assert db.query(TimelineEvent).count() >= 1

    def test_missing_investigation(self, client):
        test_client, _ = client

        assert test_client.get("/api/timeline/999").status_code == 404

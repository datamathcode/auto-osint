"""
Tests for entity graph construction, centrality, filtering, persistence, and API.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.database import get_db, init_db
from src.python.graph import (
    build_graph,
    classify_entity,
    classify_relationship,
    compute_node_metrics,
    extract_entities,
    filter_graph,
    persist_graph,
)
from src.python.main import app
from src.python.models.entity_graph import EntityGraph
from src.python.models.evidence import Evidence
from src.python.models.investigation import Investigation


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'graph.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        db.add(
            Investigation(
                target_name="Acme Corp",
                target_id="acme",
                claim_under_investigation="Acme Corp funding and ownership",
                status="completed",
            )
        )
        db.commit()
    return Session


def add_claim(session, claim, source="SYNINT:WhoisAgent", confidence=0.8):
    row = Evidence(
        source=source,
        claim=claim,
        confidence=confidence,
        independence_score=0.7,
        independence_check_details={},
        corroborating_sources=[],
        contradictions=[],
        links=[],
        chain_of_custody=[],
        investigation_id=1,
        timestamp=datetime(2026, 1, 1),
    )
    session.add(row)
    session.commit()
    return row


class TestExtraction:
    def test_entities_skip_capitalised_stopwords(self):
        entities = extract_entities("The Acme Corp acquired Beta Labs in March 2020")

        assert "Acme Corp" in entities
        assert "Beta Labs" in entities
        assert "The" not in entities
        assert "March" not in entities

    def test_entity_classification(self):
        assert classify_entity("Acme Corp") == "organization"
        assert classify_entity("Jane Doe") == "person"

    def test_relationship_classification(self):
        assert classify_relationship("Acme Corp owns Beta Labs") == "ownership"
        assert classify_relationship("Acme Corp funded Beta Labs") == "funding"
        assert classify_relationship("Jane Doe joined the board of Acme Corp") == "association"
        assert classify_relationship("Acme Corp exists") == "association"


class TestCentrality:
    def test_path_graph_betweenness(self):
        metrics = compute_node_metrics(
            ["a", "b", "c"], [("a", "b"), ("b", "c")]
        )

        assert metrics["b"]["degree"] == 2
        assert metrics["b"]["betweenness"] > metrics["a"]["betweenness"]
        assert metrics["a"]["betweenness"] == 0.0

    def test_isolated_node_has_zero_metrics(self):
        metrics = compute_node_metrics(["a"], [])

        assert metrics["a"] == {"degree": 0, "betweenness": 0.0}


class TestBuildGraph:
    def test_nodes_edges_and_metrics(self, session):
        db = session()
        add_claim(db, "Acme Corp acquired Beta Labs")
        add_claim(db, "Acme Corp funded Gamma Inc")
        add_claim(db, "Jane Doe joined the board of Acme Corp")
        db.commit()

        graph = build_graph(db, 1)

        labels = {node["label"] for node in graph["nodes"]}
        assert {"Acme Corp", "Beta Labs", "Gamma Inc"} <= labels
        types = {edge["type"] for edge in graph["edges"]}
        assert {"ownership", "funding", "association"} <= types
        assert all(edge["color"].startswith("#") for edge in graph["edges"])
        assert graph["metrics"]["Acme Corp"]["degree"] >= 1

        acme = next(node for node in graph["nodes"] if node["label"] == "Acme Corp")
        assert acme["type"] == "organization"
        assert acme["evidence_ids"]
        db.close()

    def test_repeated_pair_merges_evidence(self, session):
        db = session()
        add_claim(db, "Acme Corp acquired Beta Labs")
        add_claim(db, "Acme Corp owns Beta Labs")
        db.commit()

        graph = build_graph(db, 1)

        assert len(graph["edges"]) == 1
        assert len(graph["edges"][0]["evidence_ids"]) == 2
        db.close()

    def test_claim_without_entities_falls_back_to_target(self, session):
        db = session()
        add_claim(db, "no named entity here at all")
        db.commit()

        graph = build_graph(db, 1)

        assert [node["label"] for node in graph["nodes"]] == ["Acme Corp"]
        db.close()

    def test_missing_investigation_raises(self, session):
        db = session()
        with pytest.raises(ValueError, match="not found"):
            build_graph(db, 999)
        db.close()


class TestFiltering:
    def test_filter_by_edge_type(self, session):
        db = session()
        add_claim(db, "Acme Corp acquired Beta Labs")
        add_claim(db, "Acme Corp funded Gamma Inc")
        db.commit()
        graph = build_graph(db, 1)

        filtered = filter_graph(graph, edge_type="ownership")

        assert all(edge["type"] == "ownership" for edge in filtered["edges"])
        assert {node["label"] for node in filtered["nodes"]} == {"Acme Corp", "Beta Labs"}
        db.close()

    def test_filter_by_min_degree(self, session):
        db = session()
        add_claim(db, "Acme Corp acquired Beta Labs")
        db.commit()
        graph = build_graph(db, 1)

        filtered = filter_graph(graph, min_degree=1)

        assert all(node["degree"] >= 1 for node in filtered["nodes"])
        db.close()


class TestPersistence:
    def test_persist_replaces_snapshot(self, session):
        db = session()
        add_claim(db, "Acme Corp acquired Beta Labs")
        db.commit()
        graph = build_graph(db, 1)

        first = persist_graph(db, 1, graph)
        second = persist_graph(db, 1, graph)

        assert db.query(EntityGraph).count() == 1
        row = db.get(EntityGraph, second)
        assert row.nodes
        assert row.edges
        assert first != second or row.id == second
        db.close()


class TestGraphAPI:
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

    def test_get_graph(self, client):
        test_client, Session = client
        with Session() as db:
            add_claim(db, "Acme Corp acquired Beta Labs")

        response = test_client.get("/api/graph/1")

        assert response.status_code == 200
        body = response.json()
        assert body["nodes"]
        assert body["edges"]
        assert body["edge_colors"]["ownership"].startswith("#")

    def test_filters_and_persist(self, client):
        test_client, Session = client
        with Session() as db:
            add_claim(db, "Acme Corp acquired Beta Labs")
            add_claim(db, "Acme Corp funded Gamma Inc")

        response = test_client.get(
            "/api/graph/1", params={"edge_type": "funding", "persist": "true"}
        )

        assert response.status_code == 200
        body = response.json()
        assert all(edge["type"] == "funding" for edge in body["edges"])
        assert body["persisted"] >= 1
        with Session() as db:
            assert db.query(EntityGraph).count() == 1

    def test_missing_investigation(self, client):
        test_client, _ = client

        assert test_client.get("/api/graph/999").status_code == 404

"""
Network graph construction.

Extracts entity nodes and typed relationships from evidence claims, then
computes degree and betweenness centrality (Brandes, unweighted).
"""

import logging
import re
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models.entity_graph import EntityGraph
from .models.evidence import Evidence
from .models.investigation import Investigation

logger = logging.getLogger(__name__)

EDGE_TYPES = {
    "ownership": ("owns", "owned", "acquired", "acquisition", "subsidiary", "wholly", "stake"),
    "funding": ("fund", "funded", "funding", "invest", "invested", "grant", "donor", "backer"),
    "association": ("board", "director", "partner", "member", "associated", "overlap", "met", "worked"),
}

EDGE_COLORS = {
    "ownership": "#ef4444",
    "funding": "#10b981",
    "association": "#3b82f6",
    "temporal": "#8b5cf6",
    "unknown": "#6b7280",
}

ORG_SUFFIXES = ("corp", "corporation", "inc", "llc", "ltd", "plc", "gmbh", "foundation", "fund", "group", "labs")
STOPWORDS = {
    "the", "this", "that", "these", "those", "a", "an", "and", "or", "but",
    "in", "on", "at", "by", "for", "with", "from", "to", "of", "as", "is",
    "was", "were", "has", "have", "had", "it", "its", "their", "they",
    "published", "reported", "filed", "evidence", "claim", "found", "registered",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
}
NAME_PATTERN = re.compile(r"\b([A-Z][a-zA-Z0-9&.\-]*(?:\s+[A-Z][a-zA-Z0-9&.\-]*)*)\b")


def classify_entity(name: str) -> str:
    """Classify a node as organization or person."""
    lowered = name.lower()
    if any(lowered.endswith(suffix) or f" {suffix}" in lowered for suffix in ORG_SUFFIXES):
        return "organization"
    return "person"


def extract_entities(text: str) -> List[str]:
    """Extract candidate entity names from a claim."""
    entities: List[str] = []
    for match in NAME_PATTERN.finditer(text or ""):
        words = [word for word in match.group(1).split() if word.strip("&.-")]
        # Drop leading/trailing stopwords so "The Acme Corp" yields "Acme Corp".
        while words and words[0].lower().strip(".,") in STOPWORDS:
            words.pop(0)
        while words and words[-1].lower().strip(".,") in STOPWORDS:
            words.pop()

        candidate = " ".join(words).strip().strip(".")
        if not candidate or len(candidate) < 2:
            continue
        if candidate.isdigit():
            continue
        if candidate not in entities:
            entities.append(candidate)
    return entities


def classify_relationship(text: str) -> str:
    """Classify the relationship expressed by a claim."""
    lowered = (text or "").lower()
    for edge_type, keywords in EDGE_TYPES.items():
        if any(keyword in lowered for keyword in keywords):
            return edge_type
    return "association"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def compute_node_metrics(
    nodes: List[str], edges: List[Tuple[str, str]]
) -> Dict[str, Dict[str, float]]:
    """
    Degree and betweenness centrality for an undirected graph.

    Betweenness uses Brandes' algorithm for unweighted graphs.
    """
    adjacency: Dict[str, List[str]] = defaultdict(list)
    for source, target in edges:
        if source == target:
            continue
        if target not in adjacency[source]:
            adjacency[source].append(target)
        if source not in adjacency[target]:
            adjacency[target].append(source)

    betweenness = {node: 0.0 for node in nodes}

    for source in nodes:
        stack: List[str] = []
        predecessors: Dict[str, List[str]] = {node: [] for node in nodes}
        sigma = {node: 0.0 for node in nodes}
        distance = {node: -1 for node in nodes}
        sigma[source] = 1.0
        distance[source] = 0
        queue = deque([source])

        while queue:
            vertex = queue.popleft()
            stack.append(vertex)
            for neighbour in adjacency[vertex]:
                if distance[neighbour] < 0:
                    queue.append(neighbour)
                    distance[neighbour] = distance[vertex] + 1
                if distance[neighbour] == distance[vertex] + 1:
                    sigma[neighbour] += sigma[vertex]
                    predecessors[neighbour].append(vertex)

        delta = {node: 0.0 for node in nodes}
        while stack:
            vertex = stack.pop()
            for predecessor in predecessors[vertex]:
                if sigma[vertex]:
                    delta[predecessor] += (
                        sigma[predecessor] / sigma[vertex] * (1 + delta[vertex])
                    )
            if vertex != source:
                betweenness[vertex] += delta[vertex]

    if len(nodes) > 2:
        # Undirected graph: each pair counted twice; normalise too.
        scale = 2.0 / ((len(nodes) - 1) * (len(nodes) - 2))
        betweenness = {node: value * scale / 2 for node, value in betweenness.items()}

    metrics: Dict[str, Dict[str, float]] = {}
    for node in nodes:
        degree = len(adjacency.get(node, []))
        metrics[node] = {
            "degree": degree,
            "betweenness": round(betweenness.get(node, 0.0), 4),
        }
    return metrics


def build_graph(session: Any, investigation_id: int) -> Dict[str, Any]:
    """Build the entity graph for one investigation."""
    investigation = session.get(Investigation, investigation_id)
    if investigation is None:
        raise ValueError(f"Investigation {investigation_id} not found")

    evidence = (
        session.query(Evidence)
        .filter(Evidence.investigation_id == investigation_id)
        .order_by(Evidence.id)
        .all()
    )

    node_evidence: Dict[str, List[int]] = defaultdict(list)
    edge_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for row in evidence:
        entities = extract_entities(row.claim)
        if not entities:
            continue

        for entity in entities:
            node_evidence[entity].append(row.id)

        # Relate consecutive entities in a claim with the claim's edge type.
        edge_type = classify_relationship(row.claim)
        for source, target in zip(entities, entities[1:], strict=False):
            if source == target:
                continue
            key = (source, target)
            if key in edge_map:
                edge_map[key]["evidence_ids"].append(row.id)
                continue
            edge_map[key] = {
                "source": _slug(source),
                "target": _slug(target),
                "source_label": source,
                "target_label": target,
                "type": edge_type,
                "label": edge_type,
                "color": EDGE_COLORS.get(edge_type, EDGE_COLORS["unknown"]),
                "evidence_ids": [row.id],
            }

    if not node_evidence and investigation.target_name:
        node_evidence[investigation.target_name] = []

    nodes = sorted(node_evidence)
    edges = list(edge_map.values())
    metrics = compute_node_metrics(
        nodes, [(edge["source_label"], edge["target_label"]) for edge in edges]
    )

    node_payload = [
        {
            "id": _slug(name),
            "label": name,
            "type": classify_entity(name),
            "evidence_ids": node_evidence[name],
            "degree": metrics[name]["degree"],
            "betweenness": metrics[name]["betweenness"],
        }
        for name in nodes
    ]

    return {
        "investigation_id": investigation_id,
        "nodes": node_payload,
        "edges": edges,
        "edge_types": sorted({edge["type"] for edge in edges}),
        "metrics": metrics,
    }


def persist_graph(session: Any, investigation_id: int, graph: Dict[str, Any]) -> int:
    """Store a graph snapshot, replacing any previous one."""
    session.query(EntityGraph).filter(
        EntityGraph.investigation_id == investigation_id
    ).delete()

    row = EntityGraph(
        investigation_id=investigation_id,
        nodes=graph["nodes"],
        edges=graph["edges"],
        metrics=graph["metrics"],
        built_at=datetime.utcnow(),
    )
    session.add(row)
    session.commit()
    return row.id


def filter_graph(
    graph: Dict[str, Any],
    edge_type: Optional[str] = None,
    min_degree: int = 0,
) -> Dict[str, Any]:
    """Filter edges by type and keep only the nodes those edges connect."""
    edges = [
        edge
        for edge in graph["edges"]
        if edge_type is None or edge["type"] == edge_type
    ]
    keep = {edge["source"] for edge in edges} | {edge["target"] for edge in edges}
    nodes = [
        node
        for node in graph["nodes"]
        if node["id"] in keep and node["degree"] >= min_degree
    ]
    kept_ids = {node["id"] for node in nodes}
    edges = [edge for edge in edges if edge["source"] in kept_ids and edge["target"] in kept_ids]

    return {**graph, "nodes": nodes, "edges": edges}

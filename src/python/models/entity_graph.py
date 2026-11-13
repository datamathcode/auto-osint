"""
Entity network graph model.

Nodes and edges are stored as JSON on one row per investigation; the graph is a
derived read model, rebuilt from evidence on demand.
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer

from .base import Base


class EntityGraph(Base):
    """Stored snapshot of an investigation's entity graph."""

    __tablename__ = "entity_graph"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(Integer, ForeignKey("investigation.id"), nullable=False)
    nodes = Column(JSON, nullable=False)
    edges = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=True)
    built_at = Column(DateTime, default=datetime.utcnow, nullable=False)

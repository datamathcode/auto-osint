"""
Timeline event model.
"""

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, Text

from .base import Base


class TimelineEvent(Base):
    """One reconstructed event in an investigation timeline."""

    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(Integer, ForeignKey("investigation.id"), nullable=False)
    timestamp = Column(DateTime, nullable=True)
    role = Column(Text, nullable=False)  # statement | publication | observation | collection
    title = Column(Text, nullable=False)
    detail = Column(Text, nullable=True)
    source = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    links = Column(JSON, nullable=True)
    evidence_id = Column(Integer, nullable=True)
    group_name = Column(Text, nullable=True)

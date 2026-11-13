"""
Investigation model for auto-osint.
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, Text

from .base import Base


class Investigation(Base):
    """Investigation summary model."""
    __tablename__ = "investigation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_name = Column(Text, nullable=False)
    target_id = Column(Text, nullable=True)
    claim_under_investigation = Column(Text, nullable=False)
    status = Column(Text, nullable=False)  # in_progress, completed, failed
    stages_completed = Column(JSON, nullable=True)  # [quick, standard, deep]
    total_sources = Column(Integer, default=0)
    corroborated_sources = Column(Integer, default=0)
    contradictory_sources = Column(Integer, default=0)
    net_confidence_score = Column(Float, default=0.0)  # Weighted average
    investigation_notes = Column(Text, nullable=True)
    playbook_update = Column(Text, nullable=True)  # Reference to playbook version
    audit_report = Column(JSON, nullable=True)  # Latest self-audit report
    scope = Column(JSON, nullable=True)  # Requested scope: dates, platforms, data types, budget

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

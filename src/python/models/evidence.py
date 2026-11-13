"""
Evidence model for auto-osint.
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, Text

from .base import Base


class Evidence(Base):
    """Evidence entry model."""
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    claim = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # Bayesian posterior (0.0-1.0)
    independence_score = Column(Float, nullable=False)  # 0.0-1.0
    independence_check_details = Column(JSON, nullable=True)
    corroborating_sources = Column(JSON, nullable=True)  # List of evidence IDs
    contradictions = Column(JSON, nullable=True)  # List of evidence IDs
    links = Column(JSON, nullable=True)  # List of URLs or file paths
    chain_of_custody = Column(JSON, nullable=True)  # Immutable log of evidence collection

    investigation_id = Column(Integer, ForeignKey("investigation.id"), nullable=False)

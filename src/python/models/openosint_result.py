"""
OpenOSINT results model for auto-osint.
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OpenOSINTResult(Base):
    """OpenOSINT tool results model."""
    __tablename__ = "openosint_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool = Column(Text, nullable=False)
    target = Column(Text, nullable=False)
    result = Column(JSON, nullable=False)  # Structured results from tool
    source = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    error = Column(Text, nullable=True)

    investigation_id = Column(Integer, ForeignKey("investigation.id"), nullable=False)

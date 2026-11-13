"""
Shared SQLAlchemy declarative base.

All models must use this single Base. Separate declarative_base() instances
give each module its own MetaData, so cross-model foreign keys cannot resolve
and Base.metadata.create_all() raises NoReferencedTableError.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

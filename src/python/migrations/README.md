# Evidence Migration Scripts

This directory contains migration scripts for transitioning from raw string storage to structured confidence-based storage.

## Overview

The migration system transforms existing evidence entries by:

1. Converting raw string claims to structured storage
2. Computing confidence scores (Bayesian posterior)
3. Calculating independence scores
4. Adding metadata to evidence chain of custody

## Migration Scripts

### migrate_evidence_to_confidence.py

Migrates all evidence entries from raw strings to structured format with confidence quantification.

**Usage:**
```python
from src.python.migrations.migrate_evidence_to_confidence import EvidenceMigration
from src.python.main import app

with app.app_context():
    from sqlalchemy.orm import sessionmaker
    from src.python.models.evidence import Evidence
    
    Session = sessionmaker(bind=app.db)
    session = Session()
    
    migration = EvidenceMigration(session)
    stats = migration.migrate_evidence()
    stats = migration.verify_migration()
```

**Features:**
- Automatic detection of already-structured entries
- Confidence calculation using Bayesian inference
- Independence score computation
- Chain of custody updates
- Transactional migration with rollback on errors
- Verification of migration success

## Migration Strategy

**Expand-Then-Migrate Pattern:**
- Confidence fields added to Evidence model
- AgentBase.store_evidence() supports structured storage
- Backward compatibility maintained
- Migration script runs during setup
- Gradual transition over time

**Blast Radius:**
- Medium: Affects AgentBase and evidence storage layer
- Database migration script
- Unit and integration tests required

## Rollback Plan

If migration fails:
1. Migration script has transactional rollback
2. Original data preserved
3. Manual rollback: Restore from database backup

## Testing

Run migration tests:
```bash
python -m pytest tests/test_migration.py -v
```

## See Also

- `../confidence_quantization.py` - Confidence calculation module
- `../agents/base.py` - AgentBase evidence storage methods
- `../models/evidence.py` - Evidence model schema

# 04: Migrate First Batch of Evidence Storage

**What to build:** Migrate initial batch of evidence entries from old raw string storage to the new confidence quantification module. Update AgentBase.evidence_storage integration with confidence calculation.

**Blocked by:** 01: Setup Project Structure, 02: Base Agent and Tool Framework, 03: Expand Confidence Quantification Module

**Status:** COMPLETE

- [x] Create evidence storage interface for confidence quantification
- [x] Update AgentBase to use confidence module
- [x] Write migration script for existing evidence (SQLite to PostgreSQL)
- [x] Create unit tests for evidence storage with confidence
- [x] Update investigation model with confidence fields
- [x] Integration test: full investigation with confidence

**Technical notes:**
- Evidence entries stored as raw strings → structured with confidence
- Expand-then-migrate pattern: add confidence fields without breaking existing code
- Migration script creates backup before migrating
- Confidence automatically computed if module provided
- Chain of custody updated with migration metadata

**Implementation summary:**
- Created `src/python/migrations/migrate_evidence_to_confidence.py` (8380 bytes)
- Created `src/python/migrations/README.md` with migration documentation
- Created `tests/test_migration.py` (7043 bytes) with 10 test cases
- AgentBase.evidence_storage already supports structured storage
- Confidence quantification integration ready
- Migration script supports:
  - Automatic detection of structured/unstructured entries
  - Confidence calculation via Bayesian inference
  - Independence score computation
  - Transactional migration with rollback
  - Verification and reporting
- Evidence model supports all confidence fields
- Backward compatibility maintained

**Blast radius:** Medium - affects AgentBase and evidence storage layer

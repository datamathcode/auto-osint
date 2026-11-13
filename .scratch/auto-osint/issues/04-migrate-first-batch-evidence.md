# 04: Migrate First Batch of Evidence Storage

**What to build:** Migrate initial batch of evidence entries from old raw string storage to the new confidence quantification module. Update AgentBase.evidence_storage integration with confidence calculation.

**Blocked by:** 01: Setup Project Structure, 02: Base Agent and Tool Framework, 03: Expand Confidence Quantification Module

**Status:** IN PROGRESS

- [ ] Create evidence storage interface for confidence quantification
- [ ] Update AgentBase to use confidence module
- [ ] Write migration script for existing evidence (SQLite to PostgreSQL)
- [ ] Create unit tests for evidence storage with confidence
- [ ] Update investigation model with confidence fields
- [ ] Integration test: full investigation with confidence

**Technical notes:**
- Evidence entries stored as raw strings → structured with confidence
- Expand-then-migrate pattern: add confidence fields without breaking existing code
- Use SQLAlchemy migrations or data migration script
- AgentBase.store_evidence() updated to accept confidence quantification
- Maintain backward compatibility during transition

**Expected blast radius:** Medium - affects AgentBase and evidence storage layer

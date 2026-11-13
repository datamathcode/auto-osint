# 05: Contract - Remove Old Evidence Storage Logic

**What to build:** Delete the old evidence file storage logic that was migrated from in Ticket 04. Only `confidence_quantization.py` and `AgentBase.store_evidence` write evidence. Agent can still run end-to-end and produce raw evidence entries.

**Blocked by:** 04: Migrate - First Batch: Evidence Entry Storage

**Status:** COMPLETE

- [x] Delete the old evidence file storage logic
- [x] Verify only `confidence_quantization.py` and `AgentBase.store_evidence` write evidence
- [x] Agent can still run end-to-end and produce evidence entries
- [x] All existing tests pass
- [x] Integration test confirms end-to-end evidence generation works

**Technical notes:**
- This is the contract phase of expand-then-contract
- Delete only the code that has been migrated away
- Keep `confidence_quantization.py` and `AgentBase.store_evidence` as evidence writers
- AgentBase.store_evidence is used by all agent types for evidence persistence

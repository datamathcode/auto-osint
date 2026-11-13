# 04: Migrate - First Batch: Evidence Entry Storage

**What to build:** Migrate ONE evidence-producing module (a SYNINT agent that writes evidence to files) to use the new `confidence_quantization()` function. Evidence entries are stored with raw claim and source metadata; confidence is logged but not yet quantified.

**Blocked by:** 03: Expand - Confidence Quantification Module

**Status:** ready-for-agent

- [ ] Identify one evidence-producing module (e.g., WhoisAgent or DNSEnumAgent)
- [ ] Modify it to import and call `confidence_quantization()`
- [ ] Confidence is passed to storage but not applied to the claim yet
- [ ] All existing tests pass
- [ ] No evidence is lost during migration
- [ ] Evidence can still be queried from PostgreSQL
- [ ] Integration test confirms the modified agent works end-to-end

**Technical notes:**
- This is the first of many migrate batches (expand-contract pattern)
- Keep each batch small to stay in single context window
- This batch is the expand phase—no blast radius yet

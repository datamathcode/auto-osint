# 03: Expand - Confidence Quantification Module

**What to build:** A new Python module `confidence_quantization.py` alongside existing evidence collection. This is a placeholder with zero callers—no blast radius. Evidence entries are stored as raw strings only.

**Blocked by:** 02: Base Agent and Tool Framework

**Status:** ready-for-agent

- [ ] New Python module `src/python/confidence_quantization.py`
- [ ] Placeholder functions that log "confidence not yet implemented" to stderr
- [ ] No evidence storage logic yet—agent continues using old evidence writer
- [ ] Zero blast radius: no existing callers yet
- [ ] Unit tests that verify functions log expected messages

**Technical notes:**
- Module should be importable but don't wire it into the agent yet
- Keep it simple—just logging functions for now
- This sets up the architecture for later migration (expand-then-migrate pattern)

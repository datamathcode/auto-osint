# 13: Self-Auditing and Gap Detection

**What to build:** Self-auditing module that identifies gaps (questions not answered, sources not queried), analyzes evidence weight (are there critical gaps undermining conclusions?), and detects bias (are findings over-weighting certain source types?). Gaps are logged in investigation summary and displayed to user. Network/timeline visualizations show gap warnings where applicable.

**Blocked by:** 09: Base LLM Orchestration Layer, 10: Recursive Improvement Loop

**Status:** COMPLETE

- [ ] Gap detection module:
  - Compiles list of questions the claim raises
  - Checks which questions have answers in evidence
  - Identifies missing source types (e.g., no corporate filings found)
  - Flags unqueried platforms based on claim type
- [ ] Evidence weight analysis:
  - Calculates net confidence score
  - Compares corroborated vs. contradictory sources
  - Flags low confidence scores (<0.4)
  - Identifies critical gaps that undermine conclusions
- [ ] Bias detection:
  - Analyzes source type distribution (primary vs. secondary)
  - Flags over-weighting of certain source types
  - Identifies repeated patterns in contradictions
- [ ] Gap detection results are logged in `investigation_summary` table
- [ ] UI displays gap warnings prominently
- [ ] Network/timeline visualizations show gap indicators where applicable
- [ ] End-to-end test: run investigation with deliberate gaps, verify detection

**Technical notes:**
- Gap detection uses heuristic rules plus playbook context
- Evidence weight analysis uses Bayesian posterior scores
- Bias detection is qualitative, not quantitative
- Gap warnings are shown in dossier summary and visualizations

**Implementation summary:**
- `src/python/audit.py`
  - `compile_questions()` — question templates per claim type, plus a
    claim-specific question.
  - `check_questions()` — marks a question answered when its keywords appear in
    stored evidence.
  - `missing_source_types()` / `unqueried_tools()` — expected source categories
    and tools per claim type, diffed against what ran.
  - `weight_analysis()` — net confidence, corroborating vs contradicting links,
    low-confidence (<0.4) and single-source flags.
  - `bias_analysis()` — source shares, dominance (>=70% from one source),
    primary vs secondary balance.
  - `critical_gaps()` — the gaps that undermine the conclusion.
  - `run_audit()` — persists the report to the new
    `Investigation.audit_report` JSON column (no `investigation_summary` table
    exists in this repo).
- `GET /api/audit/{investigation_id}` returns the report.
- Dossier page renders a prominent red "Gap warnings" panel above the timeline
  and entity network, showing the gap list, net confidence, and source dominance.

**Verification (2026-11-13):**
- `tests/test_audit.py` (18 tests): question templates and matching, source
  coverage, unqueried tools, weight flags, corroboration counts, bias dominance
  and secondary-heavy detection, critical gaps, report persistence, and the API
  (including 404).
- Full suite: 188 passed, ruff clean; `tsc --noEmit` and `next build` succeed.

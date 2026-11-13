# 13: Self-Auditing and Gap Detection

**What to build:** Self-auditing module that identifies gaps (questions not answered, sources not queried), analyzes evidence weight (are there critical gaps undermining conclusions?), and detects bias (are findings over-weighting certain source types?). Gaps are logged in investigation summary and displayed to user. Network/timeline visualizations show gap warnings where applicable.

**Blocked by:** 09: Base LLM Orchestration Layer, 10: Recursive Improvement Loop

**Status:** ready-for-agent

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

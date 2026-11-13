# auto-osint Design Document — Design Review Feedback Applied

**Date:** 2026-11-12  
**Document:** `docs/superpowers/specs/2026-11-12-auto-osint-design.md`

---

## Summary

The design document has been updated with user feedback from builder review. All 4 open design questions have been resolved and integrated.

---

## Changes Applied

### 1. Confidence Algorithm (Resolved)

**Before:**
- Document defined confidence levels (Low/Medium/High) but left algorithm unspecified.

**After:**
- **Bayesian inference model** with full specification:
  - P(H|E) = P(E|H) × P(H) / P(E)
  - Prior P(H) from playbook/learning
  - Likelihood P(E|H) = source quality weight × independence_score
  - Posterior P(H|E) after each corroborating source
  - Confidence levels mapped: >0.7 = High, 0.4–0.7 = Medium, <0.4 = Low

**Location:** Updated "Confidence Quantification" section; added Bayesian algorithm details; updated data structures to include numeric Bayesian posterior confidence.

---

### 2. Independence Testing (Resolved)

**Before:**
- Document mentioned "independent sources" but didn't define independence test.

**After:**
- **Complete independence test specification:**
  - **Core test:** Would the author or publisher gain or lose from this claim being believed? Are they connected to the subject? Did the subject have a hand in producing or approving the content?
  - **Independent if "no" to all three questions**
  - **Fails if:**
    - No financial interest (rules out company blogs, press releases, sponsored content, affiliate reviews)
    - No organizational tie (rules out news offices of universities or organizations affiliated with subject)
    - No personal relationship (rules out subject, family members, collaborators, close associates)
    - No promotional purpose (rules out content written to sell, recruit, fundraise, or win arguments)
  - **Supporting checks:**
    - Original vs. derivative (follow citations to origin)
    - Editorial oversight (editor, peer review, corrections policy)
    - Disclosed conflicts (reputable sources state funding/affiliations)
    - Track record (accuracy on similar claims)
    - Corroboration (other independent sources confirm by separate routes)
  - **Independence scoring (0.0–1.0):**
    - Pass independence test → score 1.0
    - Partial independence → score 0.5–0.9
    - Failed independence → score < 0.5

**Location:** Updated "Independence Testing" section with full specification; added independence_check_details JSON object to evidence structure.

---

### 3. Persistence Strategy (Resolved)

**Before:**
- Document mentioned SQLite for investigation storage (SYNINT pattern).

**After:**
- **Hybrid persistence approach:**
  - PostgreSQL for structured data (evidence entries, playbooks, investigation summaries)
  - Local filesystem for large artifacts (HTML reports, PDF dossiers, visualizations, media)
  - PostgreSQL holds searchable structured data; filesystem holds unstructured outputs and archives

**Location:** Updated "Backend" architecture section to specify PostgreSQL + filesystem hybrid.

---

### 4. Legal/Ethical Guardrails (Resolved)

**Before:**
- Document mentioned prompts and safeguards against over-collection, but left implementation details to builder.

**After:**
- **Pre-built safeguards specified:**
  1. Scope configuration (time ranges, platforms, data types)
  2. Rate limiting per OSINT tool/API
  3. Explicit warnings against over-collection
  4. Chain-of-custody logging for all evidence collection
- Users remain responsible for compliance.

**Location:** Updated "Legal and Ethical" constraint with specific safeguards.

---

### 5. Visualization Tech Stack (Resolved)

**Before:**
- Document listed D3.js or React Flow as options.

**After:**
- **Chosen stack:**
  - React Flow for network graphs
  - D3.js for timeline mapping
- Rationale: React Flow for React integration; D3.js for flexible timeline visualization.

**Location:** Added "Visualization Tech Stack" to Design Decisions Applied section.

---

### 6. Execution Model (Resolved)

**Before:**
- Document listed questions about parallel vs. sequential execution and exploration vs. exploitation.

**After:**
- **Specified model:**
  - Concurrent run-all (default parallel execution)
  - Staged pipeline: quick → standard → deep
  - Exploration vs. exploitation balance via playbook-based depth escalation

**Location:** Added "Execution Model" to Design Decisions Applied section.

---

### 7. Recursive Improvement Frequency (Resolved)

**Before:**
- Document left question about how often playbook updates occur.

**After:**
- **Specified:** Update playbook after every investigation (both successful and unsuccessful) to capture learning from gaps and failures.

**Location:** Added "Recursive Improvement Frequency" to Design Decisions Applied section.

---

### 8. Design Decisions Applied Section (New)

Added comprehensive "Design Decisions Applied" section that documents all resolved decisions:
1. Confidence algorithm (Bayesian)
2. Independence testing (full specification)
3. Persistence strategy (PostgreSQL + filesystem)
4. Legal/Ethical guardrails (pre-built safeguards)
5. Visualization tech stack (React Flow + D3.js)
6. Execution model (concurrent run-all, staged pipeline)
7. Recursive improvement frequency (after every investigation)

---

### 9. Open Design Questions (Updated)

Reduced open questions to only 3 tunable parameters:
1. **LLM Provider Selection:** System is provider-agnostic; actual choice during deployment.
2. **Confidence Thresholds:** Map Bayesian posterior to Low/Medium/High (e.g., >0.7 = High, 0.4–0.7 = Medium, <0.4 = Low) — configurable parameters.
3. **Source Quality Weights:** Prior probabilities for source types (academic vs. news vs. filings) — configurable in playbook.

---

## What's Left to the Builder

**Implementation Tasks (no architectural ambiguity):**
1. Initialize Next.js/Vite project with TypeScript
2. Configure Python backend (FastAPI/Flask + PostgreSQL)
3. Implement base Agent class with execute, observe, store_evidence, update_confidence
4. Implement base Tool class with timeout enforcement, error handling
5. Integrate SYNINT agents (shell wrappers) and OpenOSINT tools (API clients)
6. Implement Bayesian confidence calculation
7. Implement independence test scoring
8. Implement recursive improvement loop (post-investigation analysis → playbook update)
9. Build React Flow + D3.js components for network/timeline visualization
10. Create dossier renderer with confidence visualization
11. Add pre-built safeguards (scope config, rate limiting, warnings)

**Tunable Configuration (implementation preferences, not architecture):**
- Actual LLM provider to use
- Exact confidence thresholds for Low/Medium/High mapping
- Source quality weights for Bayesian prior probabilities

---

## Next Steps

1. ✅ Design document finalized with all user feedback applied
2. ⏭️ Move to planning phase: invoke superpowers:writing-plans for implementation plan
3. ⏭️ Begin implementation with foundational framework (agents, tools, integration)
4. ⏭️ Iterative builds: collection → reasoning → UI
5. ⏭️ End-to-end testing with real investigative scenarios

---

**Design is now complete and ready for planning.** The document contains sufficient detail for a builder to start implementation without waiting for additional clarification.

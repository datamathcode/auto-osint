# auto-osint Design Document

**Date:** 2026-11-12  
**Project:** auto-osint — Agentic Recursive OSINT Research with Data Journalism Rigor  
**Status:** Draft for builder review

---

## Intent and The Why

You want an autonomous agent that can conduct deep OSINT research on public figures, answering complex claims with investigative rigor. The system should not just query static OSINT toolkits — it should recursively research, adapt its methods based on findings, and produce a substantive dossier with confidence quantification, pattern detection, timeline mapping, network visualization, and self-auditing of investigation gaps.

The key insight: **OSINT work is not just collecting data — it's reasoning across sources, following leads, detecting contradictions, and synthesizing a defensible verdict.** Existing OSINT frameworks (SYNINT, OpenOSINT) excel at collection but don't integrate recursive self-improvement or data journalism patterns. Auto-osint bridges that gap.

---

## Goals

- **Primary Goal:** Build an autonomous OSINT research agent that recursively investigates claims about public figures, produces a comprehensive dossier with evidence and counter-evidence, and maintains methodological rigor throughout.
- **Investigative Depth:** Match or exceed the rigor of professional investigative journalism — tracing money flows, associations, work history, ownership structures, timelines, and contradictions.
- **Data Journalism Rigor:** Quantify confidence in every finding, detect patterns across time, visualize relationships, and identify investigation gaps.
- **Recursive Self-Improvement:** The agent should learn from completed investigations, refine its research methods, and improve future iterations.
- **Verifiable Output:** Every finding must link to specific sources with confidence scores, enabling human analysts to verify or challenge conclusions.
- **Extensibility:** Pluggable OSINT collection engines following SYNINT/OpenOSINT patterns, easily extensible with new data sources.

---

## Non-Goals

- **No built-in AI model:** The system must work with external LLM providers (Anthropic, OpenAI, Ollama, etc.) via APIs or local models.
- **No real-time surveillance:** Research is retrospective, based on publicly available historical data.
- **No legal advice:** The system does not provide legal guidance on how to use findings; users remain responsible for compliance with applicable law.
- **No multi-user access control:** The prototype is for single-user, local-first operation.
- **No dark-web or encrypted messenger access:** Limited to publicly available surface-web and indexed data.

---

## Anti-Goals

- **Static workflows:** No pre-baked query chains. The agent must decide which tools to run, order them based on findings, and iterate autonomously.
- **Hallucination-focused approach:** The system should minimize hallucinations by relying on tool outputs, not LLM inference.
- **One-shot investigations:** Investigations should be resumable, configurable, and capable of depth escalation (quick → standard → deep stages).
- **Monolithic output:** The dossier must be modular, with separate sections for evidence, counter-evidence, confidence, gaps, and visualizations.

---

## Constraints

- **Platform:** Local-first web interface with TypeScript/JavaScript frontend, shell backend for OSINT tools, Python backend for processing/pattern detection.
- **Tech Stack:** TypeScript, JavaScript, MDX (documentation), Shell, CSS, HTML.
- **Foundational Systems:** Build on SYNINT (collection, agents, stages) and OpenOSINT (MCP tools, web UI patterns).
- **API Dependencies:** Must work with external LLM APIs (Anthropic, OpenAI, Ollama) and OSINT tool APIs (HIBP, Shodan, ipinfo.io, etc.).
- **Execution Time:** Each investigation should complete in a configurable time window (default: 5–60 minutes), with progressive depth.
- **Resource Limits:** Bounded parallel queries, timeouts per tool, memory limits for accumulated evidence.
- **Legal and Ethical:** All collection must respect ToS and applicable laws. The system includes pre-built safeguards: (1) scope configuration (time ranges, platforms, data types), (2) rate limiting per OSINT tool/API, (3) explicit warnings against over-collection, (4) chain-of-custody logging for all evidence collection. Users remain responsible for compliance.

---

## Architectural Decisions

### Core Architecture

**Layered Agent System with Recursive Self-Improvement Loop**

1. **Collection Layer (Python/Shell):**
   - Pluggable OSINT collection engines following SYNINT/OpenOSINT patterns
   - Async, timeout-protected tool invocations
   - Evidence and entity registry with append-only chain-of-custody
   - Integration with SYNINT agents (46 default) and OpenOSINT tools (11 core)

2. **Reasoning Layer (TypeScript + Python):**
   - Agentic LLM orchestration (LangChain or custom)
   - Multi-step reasoning loop: plan → execute → observe → adapt
   - Confidence quantification per finding
   - Pattern detection and timeline reconstruction
   - Network graph construction and analysis

3. **Recursive Improvement Layer (Python):**
   - Agent analyzes investigation outcomes after completion
   - Refines research plan, tool selection, and questioning strategy
   - Learns from successful patterns and failed branches
   - Stores improvements in a structured knowledge base for future investigations

4. **UI/UX Layer (TypeScript/HTML/CSS):**
   - Local web interface (Next.js or Vite-based)
   - Real-time streaming of investigation progress
   - Interactive dossier viewer with confidence visualization
   - Network and timeline graphs (D3.js or React Flow)
   - Editable configuration and investigation parameters

### Data Structures

**Evidence Entry:**
- source (type: registry, platform, document)
- timestamp (collection, publication)
- claim (what was found)
- confidence (low/medium/high, numeric Bayesian posterior)
- independence_score (0.0–1.0 based on independence test)
- independence_check_details (JSON object with evidence for each core test)
  - financial_interest: boolean
  - organizational_tie: boolean
  - personal_relationship: boolean
  - promotional_purpose: boolean
- corroborating_sources (list of IDs)
- contradictions (list of IDs)
- links (URLs, file paths)
- chain_of_custody (immutable log)

**Investigation Summary:**
- target_name, target_id (entity)
- claim_under_investigation
- status (in_progress/completed)
- stages_completed (quick/standard/deep)
- total_sources, corroborated_sources, contradictory_sources
- net_confidence_score (weighted average of evidence confidence)
- investigation_notes (agent reflections)
- playbook_update (reference to latest playbook version used)

**Research Playbook (MDX structure):**
- version
- last_updated
- sections by claim type (funding, associations, education, work history, etc.)
  - suggested_tools: list of tool IDs
  - questioning_strategies: list of prompts
  - depth_escalation_rules: conditions for deeper queries
  - confidence_thresholds: target confidence ranges per stage
- learning_summary: previous successful patterns and gaps identified
- source_quality_weights: prior probabilities for source types

### Recursive Self-Improvement Loop

**Post-Investigation Analysis:**
1. Agent reviews investigation outcomes
2. Identifies gaps: which sources would have been useful, what leads were not followed
3. Identifies successful patterns: which tool ordering, which queries led to strong corroborations
4. Updates a "research playbook" (structured MDX document):
   - Suggested tool selection by claim type (e.g., "funding" → SEC filings, corporate registries)
   - Questioning strategies (e.g., "follow associations" → check board membership, shared entities)
   - Depth escalation rules (e.g., if no direct evidence, expand to associations, then extended network)
   - Confidence thresholds (e.g., low confidence: 1 source, medium: 2+ independent sources, high: 3+ independent sources)

5. Next investigation reads playbook and uses it as a starting point, then adapts based on findings.

### Data Journalism Patterns

**Confidence Quantification (Bayesian Inference):**
- **Bayesian model:** P(H|E) = P(E|H) × P(H) / P(E), where:
  - H = hypothesis (the claim)
  - E = evidence (source, independence_score)
  - Prior P(H) = base rate from playbook/learning
  - Likelihood P(E|H) = source quality weight × independence_score
  - Posterior P(H|E) = updated belief after each corroborating source
- **Independence scoring (0.0–1.0):**
  - Pass independence test (no gain/loss, no tie, no hand in content) → score 1.0
  - Partial independence (some supporting checks fail) → score 0.5–0.9
  - Failed independence (any core question answered "yes") → score < 0.5
- **Confidence levels:**
  - High: posterior > 0.7
  - Medium: 0.4 ≤ posterior ≤ 0.7
  - Low: posterior < 0.4
- **Weighting:**
  - Primary sources (original research, corporate filings, government documents) = higher prior
  - Secondary sources (news, interviews) = moderate prior
  - Tertiary sources (summaries, blogs) = lower prior
  - Source quality weight adjusts likelihood based on editorial standards, accuracy track record

**Pattern Detection:**
- Temporal: Event sequences, frequency analysis, contradictions over time
- Network: Entity relationships (ownership, board membership, shared entities)
- Geographic: Location patterns, travel, residence history
- Financial: Funding flows, asset ownership, tax filings

**Timeline Mapping:**
- Event reconstruction with source verification
- Explicit event roles (statement, publication, observation, collection)
- Temporal contradictions and resolution attempts

**Network Visualization:**
- Entity graph with edge types (ownership, association, funding)
- Centrality metrics (degree, betweenness)
- Visual layout with D3.js or React Flow

**Self-Auditing:**
- Gap detection: which questions were not answered, which sources were not queried
- Evidence weight analysis: are there critical gaps that undermine conclusions?
- Bias detection: are findings over-weighting certain source types?

### OSINT Integration Strategy

**Hybrid Approach:**
- Use SYNINT agents for structured, staged collection (WhoisAgent, DNSEnumAgent, MetadataExtractionAgent, etc.)
- Use OpenOSINT tools for cross-platform OSINT gathering (search_username, search_email, search_breach, search_ip, etc.)
- Extend both systems with custom agents/tools for:
  - Corporate registry searches (SEC 13F, business filings)
  - Financial data (tax, donations, portfolio)
  - Academic and credential data
  - Speech/interview transcripts

**Pluggable Architecture:**
- Base Agent class with common methods: execute, observe, store_evidence, update_confidence
- Tool base class with timeout enforcement, rate limiting, error handling
- Registry pattern for agents and tools (discovery via configuration files)

### Dossier Output Structure

```
AUTO-OSINT DOSSIER: <Target Name>

TARGET: <Entity Name>
CLAIM UNDER INVESTIGATION: "<Exact claim>"
STATUS: COMPLETED
RESEARCH COMPLETION DATE: <ISO-8601>
STAGES COMPLETED: [quick, standard, deep]
TOTAL SOURCES: <Number>
CORROBORATED SOURCES: <Number>
CONTRADICTORY SOURCES: <Number>
NET CONFIDENCE SCORE: <0.0–1.0>

┌─────────────────────────────────────────────────────────────┐
│ SUMMARY                                                        │
├─────────────────────────────────────────────────────────────┤
│ <Human-readable summary of findings, verdict, and confidence>│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ EVIDENCE                                                    │
├─────────────────────────────────────────────────────────────┤
│ <Evidence entries with confidence, sources, and links>      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ COUNTER-EVIDENCE                                             │
├─────────────────────────────────────────────────────────────┤
│ <Contradictory findings with source citations>              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TIMELINE MAP                                                 │
├─────────────────────────────────────────────────────────────┤
│ <Visual timeline with events, sources, and confidence>      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ NETWORK GRAPH                                                │
├─────────────────────────────────────────────────────────────┤
│ <Visual network of entities with relationships>             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ INVESTIGATION GAPS                                            │
├─────────────────────────────────────────────────────────────┤
│ <Identified gaps, unanswered questions, and weaknesses>     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ RECURSIVE IMPROVEMENT LOG                                    │
├─────────────────────────────────────────────────────────────┤
│ <Agent's reflections, successful patterns, and playbook      │
│   updates for future investigations>                       │
└─────────────────────────────────────────────────────────────┘
```

### Platform and Tooling

**Frontend:**
- Framework: Next.js or Vite + React
- Styling: Tailwind CSS (per agenticskills.io/web-development)
- Visualization: D3.js or React Flow for graphs/timelines
- MDX: React-native MDX for dossier rendering (interactive, extensible)

**Backend:**
- Python: FastAPI or Flask for API endpoints
- LangChain or similar for agent orchestration
- asyncio for async tool execution
- PostgreSQL for structured data (evidence entries, playbooks, investigation summaries)
- Local filesystem for large artifacts (HTML reports, PDF dossiers, visualizations, media)

**OSINT Tools:**
- Shell wrappers around SYNINT/OpenOSINT binaries
- API clients (ipinfo.io, Shodan, HIBP, etc.)
- Async timeout enforcement per tool
- Rate limiting and error handling

**Build and Deploy:**
- Package manager: npm/uv (Python)
- Deployment: Vercel (per agenticskills.io recommendations) or local Docker container
- Configuration: MDX-based playbook, JSON config for API keys and tool settings

---

## What's Left to the Builder

### Immediate Implementation Tasks

1. **Setup Project Structure:**
   - Initialize Next.js/Vite project
   - Configure TypeScript/JavaScript backend
   - Set up Python environment for OSINT processing
   - Configure build tooling (npm scripts, uv)

2. **Implement Base Agent Framework:**
   - Agent base class with execute, observe, store_evidence, update_confidence
   - Tool base class with timeout enforcement, error handling
   - Registry pattern for agent and tool discovery

3. **Integrate SYNINT/OpenOSINT:**
   - Shell wrappers for SYNINT agents (quick/standard/deep stages)
   - API clients for OpenOSINT tools (email, username, breach, whois, etc.)
   - Extend with custom agents/tools for corporate registry, financial, academic data

4. **Build Recursive Improvement Loop:**
   - Post-investigation analysis framework
   - Research playbook storage (MDX format)
   - Update playbook based on successful patterns and gaps

5. **Implement Data Journalism Patterns:**
   - Confidence scoring algorithm
   - Pattern detection (temporal, network, geographic, financial)
   - Timeline reconstruction
   - Network graph construction and visualization

6. **Create UI/UX:**
   - Local web interface with real-time progress streaming
   - Dossier viewer with confidence visualization
   - Graph/timeline interactive components
   - Editable configuration and investigation parameters

### Design Decisions Applied

The following decisions have been finalized and integrated into the design:

1. **Confidence Algorithm:** Bayesian inference model where confidence is updated based on:
   - Prior probability from playbook/learning
   - Likelihood from source quality and independence scoring
   - Posterior probability after each corroborating source
   - Confidence outputs mapped to Low/Medium/High categories

2. **Independence Testing:**
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

3. **Persistence Strategy:**
   - PostgreSQL for long-term investigation storage (evidence entries, playbooks, investigation summaries)
   - Local filesystem for large artifacts (HTML reports, PDF dossiers, visualizations, media)
   - Hybrid approach: PostgreSQL holds structured data; filesystem holds unstructured outputs and archives

4. **Legal/Ethical Guardrails:**
   - Pre-built safeguards in agent prompt (scope of investigation configuration)
   - Rate limiting per OSINT tool/API
   - Explicit warnings against over-collection
   - Configurable "scope" field in investigation definition (time ranges, platforms, data types)
   - Chain-of-custody logging for all evidence collection

5. **Visualization Tech Stack:** React Flow for network graphs; D3.js for timeline mapping (chosen for React integration and flexibility)

6. **Execution Model:** Concurrent run-all (default), staged pipeline (quick/standard/deep), exploration vs. exploitation balance via playbook-based depth escalation

7. **Recursive Improvement Frequency:** Update playbook after every investigation (both successful and unsuccessful) to capture learning from gaps and failures

### Open Design Questions

The following decisions remain open based on implementation preferences:

1. **LLM Provider Selection:** System design is provider-agnostic; actual selection (Anthropic, OpenAI, Ollama, etc.) can be chosen during initial deployment.

2. **Confidence Thresholds:** Map Bayesian posterior probabilities to Low/Medium/High categories (e.g., >0.7 = High, 0.4–0.7 = Medium, <0.4 = Low) — these are tunable configuration parameters.

3. **Source Quality Weights:** In Bayesian inference, prior probabilities for different source types (e.g., academic papers vs. news articles vs. corporate filings) — define weights in playbook configuration.

---

## Success Criteria

The project is considered complete when:

1. **Functional Research Agent:**
   - The agent can take a claim about a public figure and autonomously research it across multiple OSINT sources
   - The agent can recursively refine its approach based on findings

2. **Data Journalism Rigor:**
   - Every finding has a quantified confidence score
   - Timeline mapping is functional and source-verified
   - Network graphs visualize entity relationships
   - Investigation gaps are identified and documented

3. **Recursive Improvement:**
   - The agent analyzes completed investigations and updates a research playbook
   - Subsequent investigations use the playbook and adapt based on results

4. **Substantive Dossier:**
   - The dossier includes summary, evidence, counter-evidence, timeline, network graph, gaps, and improvement log
   - All findings link to specific sources with confidence scores
   - The dossier is human-readable and verifiable

5. **Extensibility:**
   - New OSINT collection engines can be added following SYNINT/OpenOSINT patterns
   - New data sources can be integrated without major architectural changes

---

## Notes and References

- SYNINT: https://github.com/gs-ai/SYNINT
- OpenOSINT: https://github.com/OpenOSINT/OpenOSINT
- Autoresearch pattern: https://github.com/karpathy/autoresearch
- Agentic OSINT paper: https://arxiv.org/html/2607.03233v1
- Web dev skills: https://agenticskills.io/category/web-development

---

**Next Steps:**
1. Review this design document and address any questions
2. Create a formal plan (superpowers:writing-plans) for implementation
3. Begin implementation with foundational framework (agents, tools, integration)
4. Iterate with alpha builds focusing on one layer at a time (collection → reasoning → UI)
5. End-to-end testing with real investigative scenarios

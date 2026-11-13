# 11: Timeline Reconstruction and Visualization

**What to build:** Timeline reconstruction module that parses evidence entries with temporal metadata. D3.js component renders interactive timeline of events, sources, and confidence scores. Timeline displays statements, publications, observations, collection events.

**Blocked by:** 09: Base LLM Orchestration Layer, 10: Recursive Improvement Loop

**Status:** ready-for-agent

- [ ] Timeline reconstruction module:
  - Parses evidence entries for temporal metadata (timestamp, event type)
  - Extracts event roles (statement, publication, observation, collection)
  - Detects temporal contradictions
  - Groups related events
- [ ] Database query to retrieve timeline events for investigation
- [ ] D3.js React component for timeline visualization:
  - Interactive timeline with scroll
  - Event types color-coded by role
  - Source badges on each event
  - Confidence indicators (color, size)
  - Click event to see source details
- [ ] Timeline is rendered in dossier viewer
- [ ] End-to-end test: generate timeline from synthetic investigation, display in UI

**Technical notes:**
- D3.js with React bindings for seamless integration
- Timeline scales with number of events (responsive)
- Events with high confidence highlighted
- Timeline is part of dossier output (HTML/MDX)
- Store timeline data in `timeline_events` table

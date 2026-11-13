# 11: Timeline Reconstruction and Visualization

**What to build:** Timeline reconstruction module that parses evidence entries with temporal metadata. D3.js component renders interactive timeline of events, sources, and confidence scores. Timeline displays statements, publications, observations, collection events.

**Blocked by:** 09: Base LLM Orchestration Layer, 10: Recursive Improvement Loop

**Status:** COMPLETE

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

**Implementation summary:**
- `src/python/timeline.py`
  - `build_timeline(session, investigation_id)` — events from evidence claims
    (role `statement`/`publication`, using an explicit `YYYY-MM-DD` in the claim
    when present), chain-of-custody entries (role `collection`), and
    `openosint_results` rows (role `observation`). Sorted by time, with groups,
    role colours, and a date range.
  - `detect_temporal_contradictions()` — same source, shared subject word,
    different years.
  - `persist_timeline()` — replaces rows in the new `timeline_events` table.
- `models/timeline_event.py` + registered on the shared Base.
- `GET /api/timeline/{investigation_id}` (`?persist=true` writes the table).
- Frontend: `app/components/Timeline.tsx` (D3, interactive, colour by role,
  radius by confidence, source badges, click-to-inspect) and
  `app/dossiers/[id]/page.tsx`, which renders the timeline, contradictions, and
  evidence table from `/api/dossiers` + `/api/timeline`.

**Verification (2026-11-13):**
- `tests/test_timeline.py` (17 tests): date/year extraction, role classification,
  chronological ordering, claim-date handling, custody→collection mapping,
  failed-result confidence, contradiction detection (positive and negative
  cases), persistence replacement, and the API including `persist=true` and 404.
- Full suite: 155 passed, ruff clean.
- `npx tsc --noEmit` and `npx next build` succeed; `/dossiers/[id]` builds as a
  dynamic route (19.6 kB).

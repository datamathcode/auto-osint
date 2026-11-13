# 16: UI - Dossier Viewer with Confidence Visualization

**What to build:** MDX-based dossier renderer that displays summary, evidence table with confidence color-coded, counter-evidence section, timeline visualization, network graph visualization, investigation gaps section, recursive improvement log. All findings link to source URLs with confidence badges.

**Blocked by:** 11: Timeline Reconstruction and Visualization, 12: Network Graph Construction and Visualization, 13: Self-Auditing and Gap Detection

**Status:** COMPLETE

- [ ] Dossier API endpoints:
  - `GET /dossiers/<id>` - full dossier data
  - `GET /dossiers/<id>/evidence` - evidence table
  - `GET /dossiers/<id>/timeline` - timeline data for D3.js
  - `GET /dossiers/<id>/graph` - graph data for React Flow
  - `GET /dossiers/<id>/gaps` - gap detection results
  - `GET /dossiers/<id>/playbook-update` - latest playbook version
- [ ] React dossier viewer component:
  - Summary section with verdict and net confidence score
  - Evidence table with:
    - Source name and URL
    - Claim
    - Confidence score (color-coded badge)
    - Independence score
    - Links to corroborating/contradictory sources
  - Counter-evidence section
  - Timeline visualization (D3.js component)
  - Network graph visualization (React Flow component)
  - Investigation gaps section
  - Recursive improvement log
- [ ] Confidence badges: high (green), medium (yellow), low (red)
- [ ] All findings link to source URLs
- [ ] Evidence table is paginated if large
- [ ] Dossier can be exported as PDF
- [ ] End-to-end test: generate dossier from synthetic investigation, display all sections

**Technical notes:**
- MDX for dossier content (allows interactive components)
- Tailwind CSS for styling and layout
- D3.js and React Flow components embedded in MDX
- Export to PDF using `react-pdf` or similar
- Confidence badges use color scheme: green > 0.7, yellow 0.4–0.7, red < 0.4

**Implementation summary:**
- Dossier API (`src/python/routers/dossiers.py`):
  - `GET /api/dossiers/{id}` — verdict (`supported` >=0.7, `inconclusive`
    >=0.4, otherwise `unsupported`), summary counts (high/medium/low,
    counter-evidence), evidence, counter-evidence, and tool results.
  - `GET /api/dossiers/{id}/evidence` — paginated (offset/limit, total, has_more).
  - `GET /api/dossiers/{id}/timeline`, `/graph`, `/gaps`,
    `/playbook-update` — thin views over timeline, graph, audit, and learning.
- Viewer (`app/dossiers/[id]/page.tsx`):
  - verdict badge, net-confidence badge, high/medium/low and counter-evidence
    counters, gap warnings, timeline, temporal contradictions, entity network,
    paginated evidence table (confidence badges, independence, corroborating and
    contradictory references, source links), counter-evidence section, and the
    recursive improvement log.
  - `ConfidenceBadge` (green >=0.7, yellow 0.4–0.7, red <0.4),
    `EvidenceTable` (10-row pages with "show more"), `PrintButton`.

**Verification (2026-11-13):**
- `tests/test_dossier_api.py` (9 tests): verdict thresholds, full payload with
  counter-evidence, pagination maths, timeline/graph/gaps/playbook subroutes,
  and 404s for unknown investigations on every subroute.
- Full suite: 218 passed, ruff clean; `tsc --noEmit` clean; `next build` emits
  the dossier route.

**Deviations:**
- Dossier routes live under `/api/dossiers/...` rather than bare `/dossiers/...`
  to match the existing API prefix.
- PDF export uses the browser's print-to-PDF via a button; `react-pdf` is not
  installed, so no server-side PDF renderer exists.
- Sections are React components rather than MDX-embedded components; the
  content model is the same.

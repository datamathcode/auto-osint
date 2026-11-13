# 12: Network Graph Construction and Visualization

**What to build:** Network graph construction module that extracts entities and relationships from evidence. React Flow component renders interactive network graph with entity nodes and edge types (ownership, association, funding). Graph includes centrality metrics (degree, betweenness). Graph is rendered in dossier viewer.

**Blocked by:** 09: Base LLM Orchestration Layer, 10: Recursive Improvement Loop

**Status:** COMPLETE

- [ ] Network graph construction module:
  - Extracts entities from evidence (person, organization, entity names)
  - Identifies relationships: ownership, association, funding, temporal
  - Assigns edge types based on evidence source
  - Computes centrality metrics (degree, betweenness)
- [ ] Database query to retrieve graph data for investigation
- [ ] React Flow React component for network visualization:
  - Interactive nodes and edges
  - Node labels with entity names
  - Edge types color-coded
  - Centrality metrics displayed
  - Zoom and pan support
  - Click node to see entity details and evidence links
- [ ] Network graph is rendered in dossier viewer
- [ ] End-to-end test: generate graph from synthetic investigation, display in UI

**Technical notes:**
- React Flow for React-first graph visualization
- Force-directed layout algorithm for initial positioning
- Interactive filtering (by edge type, centrality threshold)
- Graph is part of dossier output (HTML/MDX)
- Store graph data in `entity_graph` table with edges and nodes

**Implementation summary:**
- `src/python/graph.py`
  - `extract_entities()` — capitalised-name extraction with stopword trimming
    ("The Acme Corp" → "Acme Corp"); `classify_entity()` marks organizations by
    suffix (Corp/Inc/LLC/Ltd/…).
  - `classify_relationship()` — ownership / funding / association keyword
    classifier; edges carry type, colour, and evidence IDs.
  - `compute_node_metrics()` — degree plus betweenness via Brandes' algorithm
    (unweighted, undirected, normalised).
  - `build_graph()`, `filter_graph(edge_type=, min_degree=)`, and
    `persist_graph()` into the new `entity_graph` table.
- `models/entity_graph.py` registered on the shared Base.
- `GET /api/graph/{investigation_id}` with `edge_type`, `min_degree`, `persist`.
- Frontend: `app/components/Graph.tsx` — React Flow (`@xyflow/react`) with
  d3-force initial layout, colour-coded edges, minimap, pan/zoom, and a
  click-to-inspect panel showing degree/betweenness and evidence IDs.
  `app/dossiers/[id]/page.tsx` now renders timeline, entity network,
  contradictions, and evidence.

**Verification (2026-11-13):**
- `tests/test_graph.py` (15 tests): entity extraction (stopwords, org suffixes),
  relationship typing, betweenness on a path graph, graph construction and merge
  of repeated pairs, target fallback, filtering by type/degree, snapshot
  replacement, and the API including filters, `persist`, and 404.
- Full suite: 170 passed, ruff clean.
- `tsc --noEmit` clean; `next build` emits `/dossiers/[id]` at 73 kB.

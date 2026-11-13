# 12: Network Graph Construction and Visualization

**What to build:** Network graph construction module that extracts entities and relationships from evidence. React Flow component renders interactive network graph with entity nodes and edge types (ownership, association, funding). Graph includes centrality metrics (degree, betweenness). Graph is rendered in dossier viewer.

**Blocked by:** 09: Base LLM Orchestration Layer, 10: Recursive Improvement Loop

**Status:** ready-for-agent

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

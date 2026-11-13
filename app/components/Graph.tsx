"use client";

import * as d3 from "d3";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import { useEffect, useMemo, useState } from "react";

export type GraphNode = {
  id: string;
  label: string;
  type: string;
  degree: number;
  betweenness: number;
  evidence_ids: number[];
};

export type GraphEdge = {
  source: string;
  target: string;
  type: string;
  label: string;
  color: string;
  evidence_ids: number[];
};

type Props = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  height?: number;
};

const EDGE_COLORS: Record<string, string> = {
  ownership: "#ef4444",
  funding: "#10b981",
  association: "#3b82f6",
  temporal: "#8b5cf6",
  unknown: "#6b7280",
};

const NODE_COLORS: Record<string, string> = {
  organization: "#1d4ed8",
  person: "#0f766e",
};

/**
 * Interactive entity graph. Positions come from a d3 force simulation, then
 * React Flow handles pan, zoom, minimap and selection.
 */
export default function Graph({ nodes, edges, height = 460 }: Props) {
  const [selected, setSelected] = useState<GraphNode | null>(null);

  const layout = useMemo(() => {
    if (nodes.length === 0) return [] as Array<GraphNode & { x: number; y: number }>;

    const simulationNodes = nodes.map((node) => ({ ...node, x: 0, y: 0 }));
    const links = edges.map((edge) => ({ source: edge.source, target: edge.target }));

    const simulation = d3
      .forceSimulation(simulationNodes as unknown as d3.SimulationNodeDatum[])
      .force(
        "link",
        d3
          .forceLink(links)
          .id((datum) => (datum as unknown as GraphNode).id)
          .distance(120),
      )
      .force("charge", d3.forceManyBody().strength(-320))
      .force("center", d3.forceCenter(320, 240))
      .stop();

    for (let i = 0; i < 250; i += 1) simulation.tick();

    return simulationNodes;
  }, [nodes, edges]);

  const flowNodes: Node[] = layout.map((node) => ({
    id: node.id,
    position: { x: node.x ?? 0, y: node.y ?? 0 },
    data: { label: node.label },
    style: {
      background: NODE_COLORS[node.type] ?? "#374151",
      color: "#ffffff",
      border: "1px solid #ffffff",
      borderRadius: 6,
      fontSize: 11,
      padding: 6,
      width: 110 + Math.min(node.degree, 6) * 10,
    },
  }));

  const flowEdges: Edge[] = edges.map((edge) => ({
    id: `${edge.source}-${edge.target}-${edge.type}`,
    source: edge.source,
    target: edge.target,
    label: edge.label,
    animated: edge.type === "funding",
    style: { stroke: edge.color || (EDGE_COLORS[edge.type] ?? "#6b7280"), strokeWidth: 1.6 },
    labelStyle: { fontSize: 9, fill: "#374151" },
  }));

  useEffect(() => {
    setSelected(null);
  }, [nodes]);

  if (nodes.length === 0) {
    return <p className="text-sm text-gray-600">No entities were extracted for this investigation.</p>;
  }

  return (
    <div>
      <div style={{ height, border: "1px solid #e5e7eb", borderRadius: 8 }}>
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          fitView
          onNodeClick={(_event, node) => {
            const found = nodes.find((candidate) => candidate.id === node.id) ?? null;
            setSelected(found);
          }}
        >
          <Background />
          <Controls />
          <MiniMap pannable zoomable />
        </ReactFlow>
      </div>

      <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-600">
        {Object.entries(EDGE_COLORS).map(([type, color]) => (
          <span key={type} className="inline-flex items-center gap-1">
            <span aria-hidden style={{ backgroundColor: color }} className="inline-block h-2.5 w-4 rounded" />
            {type}
          </span>
        ))}
      </div>

      {selected && (
        <aside className="mt-3 rounded border border-gray-200 p-3 text-sm">
          <div className="font-semibold">{selected.label}</div>
          <div className="text-gray-600">
            {selected.type} · degree {selected.degree} · betweenness{" "}
            {selected.betweenness.toFixed(2)}
          </div>
          <div className="text-gray-600">
            evidence: {selected.evidence_ids.length > 0 ? selected.evidence_ids.join(", ") : "none"}
          </div>
        </aside>
      )}
    </div>
  );
}

"use client";

import * as d3 from "d3";
import { useEffect, useRef, useState } from "react";

export type TimelineEvent = {
  role: "statement" | "publication" | "observation" | "collection" | string;
  title: string;
  detail?: string;
  timestamp: string;
  source?: string | null;
  confidence: number;
  links?: string[];
  group?: string;
  color?: string;
};

type Props = {
  events: TimelineEvent[];
  height?: number;
};

const ROLE_COLORS: Record<string, string> = {
  statement: "#3b82f6",
  publication: "#8b5cf6",
  observation: "#10b981",
  collection: "#f59e0b",
};

const WIDTH = 960;
const MARGIN = { top: 40, right: 40, bottom: 60, left: 40 };

/**
 * Interactive D3 timeline: one row per event group (source), events placed by
 * time, colour-coded by role, radius scaled by confidence, click for details.
 */
export default function Timeline({ events, height = 420 }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [selected, setSelected] = useState<TimelineEvent | null>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    if (events.length === 0) {
      svg
        .append("text")
        .attr("x", WIDTH / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#6b7280")
        .text("No timeline events");
      return;
    }

    const parsed = events.map((event) => ({
      ...event,
      date: new Date(event.timestamp),
    }));

    const groups = Array.from(new Set(parsed.map((event) => event.group ?? event.role)));
    const innerHeight = height - MARGIN.top - MARGIN.bottom;

    const x = d3
      .scaleTime()
      .domain(d3.extent(parsed, (event) => event.date) as [Date, Date])
      .nice()
      .range([MARGIN.left, WIDTH - MARGIN.right]);

    const y = d3
      .scaleBand<string>()
      .domain(groups)
      .range([MARGIN.top, MARGIN.top + innerHeight])
      .padding(0.4);

    // Axis
    const axis = d3
      .axisBottom(x)
      .ticks(6)
      .tickFormat(d3.timeFormat("%Y-%m-%d") as (value: Date | d3.NumberValue) => string);

    const axisGroup = svg
      .append("g")
      .attr("transform", `translate(0, ${height - MARGIN.bottom})`)
      .call(axis as unknown as (selection: d3.Selection<SVGGElement, unknown, null, undefined>) => void);

    axisGroup.selectAll("text").style("font-size", "11px").style("fill", "#6b7280");
    axisGroup.selectAll("line").style("stroke", "#e5e7eb");

    // Group lanes and labels
    svg
      .append("g")
      .selectAll("rect")
      .data(groups)
      .join("rect")
      .attr("x", MARGIN.left)
      .attr("y", (group) => y(group) ?? 0)
      .attr("width", WIDTH - MARGIN.left - MARGIN.right)
      .attr("height", y.bandwidth())
      .attr("fill", (_, index) => (index % 2 === 0 ? "#f9fafb" : "#ffffff"));

    svg
      .append("g")
      .selectAll("text")
      .data(groups)
      .join("text")
      .attr("x", MARGIN.left - 8)
      .attr("y", (group) => (y(group) ?? 0) + y.bandwidth() / 2)
      .attr("text-anchor", "end")
      .attr("dominant-baseline", "middle")
      .attr("font-size", 11)
      .attr("fill", "#374151")
      .text((group) => (group.length > 18 ? `${group.slice(0, 18)}…` : group));

    // Events
    const node = svg
      .append("g")
      .selectAll("circle")
      .data(parsed)
      .join("circle")
      .attr("cx", (event) => x(event.date))
      .attr("cy", (event) => (y(event.group ?? event.role) ?? 0) + y.bandwidth() / 2)
      .attr("r", (event) => 5 + Math.max(0, Math.min(1, event.confidence)) * 9)
      .attr("fill", (event) => event.color ?? ROLE_COLORS[event.role] ?? "#6b7280")
      .attr("fill-opacity", 0.85)
      .attr("stroke", "#ffffff")
      .attr("stroke-width", 1.5)
      .style("cursor", "pointer")
      .on("click", (_event, datum) => setSelected(datum));

    node.append("title").text((event) => `${event.title}\n${event.source ?? ""}`);

    // Source badges
    svg
      .append("g")
      .selectAll("text")
      .data(parsed.filter((event) => Boolean(event.source)))
      .join("text")
      .attr("x", (event) => x(event.date))
      .attr("y", (event) => (y(event.group ?? event.role) ?? 0) + y.bandwidth() / 2 - 14)
      .attr("text-anchor", "middle")
      .attr("font-size", 9)
      .attr("fill", "#6b7280")
      .text((event) => (event.source as string).slice(0, 14));

    return () => {
      svg.selectAll("*").remove();
    };
  }, [events, height]);

  return (
    <div className="w-full">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="img"
        aria-label="Investigation timeline"
        style={{ width: "100%", height: "auto" }}
      />

      <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-600">
        {Object.entries(ROLE_COLORS).map(([role, color]) => (
          <span key={role} className="inline-flex items-center gap-1">
            <span
              aria-hidden
              style={{ backgroundColor: color }}
              className="inline-block h-2.5 w-2.5 rounded-full"
            />
            {role}
          </span>
        ))}
      </div>

      {selected && (
        <aside className="mt-3 rounded border border-gray-200 p-3 text-sm">
          <div className="font-semibold">{selected.title}</div>
          <div className="text-gray-600">
            {new Date(selected.timestamp).toLocaleString()} · {selected.role}
            {selected.source ? ` · ${selected.source}` : ""} · confidence{" "}
            {selected.confidence.toFixed(2)}
          </div>
          {selected.detail && <p className="mt-1 text-gray-700">{selected.detail}</p>}
          {selected.links && selected.links.length > 0 && (
            <ul className="mt-1 list-disc pl-5">
              {selected.links.map((link) => (
                <li key={link}>
                  <a className="text-blue-600 underline" href={link} target="_blank" rel="noreferrer">
                    {link}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </aside>
      )}
    </div>
  );
}

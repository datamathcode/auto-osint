"use client";

import { useState } from "react";

import ConfidenceBadge from "./ConfidenceBadge";

export type EvidenceRow = {
  id: number;
  source: string;
  claim: string;
  confidence: number;
  independence_score: number;
  corroborating_sources: number[];
  contradictions: number[];
  links: string[];
};

const PAGE_SIZE = 10;

export default function EvidenceTable({ rows }: { rows: EvidenceRow[] }) {
  const [visible, setVisible] = useState(PAGE_SIZE);
  const shown = rows.slice(0, visible);

  if (rows.length === 0) {
    return <p className="text-sm text-gray-600">No evidence was stored.</p>;
  }

  return (
    <div>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="py-1 pr-3">Source</th>
            <th className="py-1 pr-3">Claim</th>
            <th className="py-1 pr-3">Confidence</th>
            <th className="py-1 pr-3">Independence</th>
            <th className="py-1">Links</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((row) => (
            <tr key={row.id} className="border-b align-top">
              <td className="py-2 pr-3 font-medium">{row.source}</td>
              <td className="py-2 pr-3">
                {row.claim}
                {row.corroborating_sources.length > 0 && (
                  <div className="text-xs text-green-700">
                    corroborated by evidence {row.corroborating_sources.join(", ")}
                  </div>
                )}
                {row.contradictions.length > 0 && (
                  <div className="text-xs text-red-700">
                    contradicted by evidence {row.contradictions.join(", ")}
                  </div>
                )}
              </td>
              <td className="py-2 pr-3">
                <ConfidenceBadge score={row.confidence} />
              </td>
              <td className="py-2 pr-3">{row.independence_score.toFixed(2)}</td>
              <td className="py-2 text-xs">
                {row.links.length === 0 && <span className="text-gray-400">none</span>}
                {row.links.map((link) => (
                  <a
                    key={link}
                    href={link}
                    target="_blank"
                    rel="noreferrer"
                    className="block text-blue-600 underline"
                  >
                    {link.length > 40 ? `${link.slice(0, 40)}…` : link}
                  </a>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-2 flex items-center justify-between text-xs text-gray-600">
        <span>
          showing {shown.length} of {rows.length}
        </span>
        {visible < rows.length && (
          <button
            type="button"
            className="rounded border px-3 py-1 text-blue-700"
            onClick={() => setVisible((current) => current + PAGE_SIZE)}
          >
            Show more
          </button>
        )}
      </div>
    </div>
  );
}

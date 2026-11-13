import Timeline, { TimelineEvent } from "../../components/Timeline";
import Graph, { GraphEdge, GraphNode } from "../../components/Graph";

type Dossier = {
  investigation: {
    id: number;
    target_name: string;
    claim_under_investigation: string;
    status: string;
    net_confidence_score: number | null;
  };
  summary: {
    evidence_count: number;
    result_count: number;
    mean_confidence: number;
  };
  evidence: Array<{
    id: number;
    source: string;
    claim: string;
    confidence: number;
    links: string[];
  }>;
};

type TimelinePayload = {
  events: TimelineEvent[];
  contradictions: Array<{ subject: string; years: number[]; events: string[] }>;
};

type GraphPayload = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

async function getJson<T>(path: string): Promise<T | null> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${base}${path}`, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export default async function DossierPage({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  const dossier = await getJson<Dossier>(`/api/dossiers/${id}`);
  const timeline = await getJson<TimelinePayload>(`/api/timeline/${id}`);
  const graph = await getJson<GraphPayload>(`/api/graph/${id}`);

  if (!dossier) {
    return (
      <main className="mx-auto max-w-5xl p-6">
        <h1 className="text-xl font-semibold">Dossier {params.id}</h1>
        <p className="mt-2 text-gray-600">
          Could not load this dossier. Check that the API is running at{" "}
          {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl p-6">
      <header className="border-b pb-4">
        <h1 className="text-2xl font-semibold">{dossier.investigation.target_name}</h1>
        <p className="text-gray-700">{dossier.investigation.claim_under_investigation}</p>
        <p className="mt-1 text-sm text-gray-500">
          {dossier.investigation.status} · evidence {dossier.summary.evidence_count} ·
          results {dossier.summary.result_count} · mean confidence{" "}
          {dossier.summary.mean_confidence.toFixed(2)}
        </p>
      </header>

      <section className="mt-6">
        <h2 className="text-lg font-semibold">Timeline</h2>
        <Timeline events={timeline?.events ?? []} />
      </section>

      {timeline && timeline.contradictions.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-semibold">Temporal contradictions</h2>
          <ul className="mt-2 list-disc pl-5 text-sm">
            {timeline.contradictions.map((item, index) => (
              <li key={`${item.subject}-${index}`}>
                <span className="font-medium">{item.subject}</span>: {item.years.join(" vs ")} —{" "}
                {item.events.join(" | ")}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-6">
        <h2 className="text-lg font-semibold">Entity network</h2>
        <Graph nodes={graph?.nodes ?? []} edges={graph?.edges ?? []} />
      </section>

      <section className="mt-6">
        <h2 className="text-lg font-semibold">Evidence</h2>
        <table className="mt-2 w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-1">Source</th>
              <th className="py-1">Claim</th>
              <th className="py-1">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {dossier.evidence.map((row) => (
              <tr key={row.id} className="border-b">
                <td className="py-1 pr-3">{row.source}</td>
                <td className="py-1 pr-3">{row.claim}</td>
                <td className="py-1">{row.confidence.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}

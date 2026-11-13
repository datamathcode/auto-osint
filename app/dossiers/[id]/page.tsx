import ConfidenceBadge from "../../components/ConfidenceBadge";
import EvidenceTable, { EvidenceRow } from "../../components/EvidenceTable";
import Graph, { GraphEdge, GraphNode } from "../../components/Graph";
import PrintButton from "../../components/PrintButton";
import Timeline, { TimelineEvent } from "../../components/Timeline";

type Dossier = {
  investigation: {
    id: number;
    target_name: string;
    target_id: string | null;
    claim_under_investigation: string;
    status: string;
    net_confidence_score: number | null;
    playbook_update: string | null;
  };
  verdict: string;
  summary: {
    evidence_count: number;
    result_count: number;
    mean_confidence: number;
    high_confidence_count: number;
    medium_confidence_count: number;
    low_confidence_count: number;
    counter_evidence_count: number;
  };
  evidence: EvidenceRow[];
  counter_evidence: EvidenceRow[];
};

type TimelinePayload = {
  events: TimelineEvent[];
  contradictions: Array<{ subject: string; years: number[]; events: string[] }>;
};

type GraphPayload = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

type GapsPayload = {
  claim_type: string;
  gaps: string[];
  unanswered_questions: string[];
  weight: { net_confidence: number; low_confidence: boolean };
  bias: { dominated_by: string[]; secondary_heavy: boolean };
};

type PlaybookPayload = {
  claim_type: string;
  reference: string | null;
  latest_lessons: Array<{
    label: string;
    recorded_at: string;
    gaps: string[];
    patterns: string[];
    successful_tools: string[];
  }>;
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

const VERDICT_STYLES: Record<string, string> = {
  supported: "bg-green-100 text-green-900 border-green-300",
  inconclusive: "bg-yellow-100 text-yellow-900 border-yellow-300",
  unsupported: "bg-red-100 text-red-900 border-red-300",
};

export default async function DossierPage({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  const dossier = await getJson<Dossier>(`/api/dossiers/${id}`);
  const timeline = await getJson<TimelinePayload>(`/api/dossiers/${id}/timeline`);
  const graph = await getJson<GraphPayload>(`/api/dossiers/${id}/graph`);
  const gaps = await getJson<GapsPayload>(`/api/dossiers/${id}/gaps`);
  const playbook = await getJson<PlaybookPayload>(`/api/dossiers/${id}/playbook-update`);

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

  const confidence =
    dossier.investigation.net_confidence_score ?? dossier.summary.mean_confidence;

  return (
    <main className="mx-auto max-w-5xl p-6">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-2xl font-semibold">{dossier.investigation.target_name}</h1>
          <p className="text-gray-700">{dossier.investigation.claim_under_investigation}</p>
          <p className="mt-1 text-sm text-gray-500">
            {dossier.investigation.status} · evidence {dossier.summary.evidence_count} · results{" "}
            {dossier.summary.result_count}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`rounded border px-3 py-1 text-sm font-semibold ${
              VERDICT_STYLES[dossier.verdict] ?? "bg-gray-100"
            }`}
          >
            {dossier.verdict}
          </span>
          <ConfidenceBadge score={confidence} />
          <PrintButton />
        </div>
      </header>

      <section className="mt-4 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
        <div className="rounded border p-3">
          <div className="text-xs text-gray-500">High confidence</div>
          <div className="text-lg font-semibold">{dossier.summary.high_confidence_count}</div>
        </div>
        <div className="rounded border p-3">
          <div className="text-xs text-gray-500">Medium</div>
          <div className="text-lg font-semibold">{dossier.summary.medium_confidence_count}</div>
        </div>
        <div className="rounded border p-3">
          <div className="text-xs text-gray-500">Low</div>
          <div className="text-lg font-semibold">{dossier.summary.low_confidence_count}</div>
        </div>
        <div className="rounded border p-3">
          <div className="text-xs text-gray-500">Counter-evidence</div>
          <div className="text-lg font-semibold">{dossier.summary.counter_evidence_count}</div>
        </div>
      </section>

      {gaps && gaps.gaps.length > 0 && (
        <section className="mt-6 rounded border-l-4 border-red-500 bg-red-50 p-4">
          <h2 className="text-lg font-semibold text-red-800">Gaps ({gaps.gaps.length})</h2>
          <ul className="mt-2 list-disc pl-5 text-sm text-red-900">
            {gaps.gaps.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-red-800">
            claim type: {gaps.claim_type} · net confidence {gaps.weight.net_confidence.toFixed(2)}
            {gaps.bias.dominated_by.length > 0
              ? ` · dominated by ${gaps.bias.dominated_by.join(", ")}`
              : ""}
          </p>
        </section>
      )}

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
        <div className="mt-2">
          <EvidenceTable rows={dossier.evidence} />
        </div>
      </section>

      {dossier.counter_evidence.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-semibold">Counter-evidence</h2>
          <ul className="mt-2 space-y-2 text-sm">
            {dossier.counter_evidence.map((row) => (
              <li key={row.id} className="rounded border border-red-200 bg-red-50 p-2">
                <span className="font-medium">{row.source}</span>: {row.claim}{" "}
                <ConfidenceBadge score={row.confidence} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-6">
        <h2 className="text-lg font-semibold">Improvement log</h2>
        {playbook?.latest_lessons?.length ? (
          <ul className="mt-2 space-y-2 text-sm">
            {playbook.latest_lessons.map((lesson) => (
              <li key={lesson.label} className="rounded border p-2">
                <div className="flex justify-between text-xs text-gray-500">
                  <span className="font-medium text-gray-700">{lesson.label}</span>
                  <time>{lesson.recorded_at}</time>
                </div>
                {lesson.successful_tools.length > 0 && (
                  <p className="mt-1">tools that worked: {lesson.successful_tools.join(", ")}</p>
                )}
                {lesson.gaps.length > 0 && (
                  <p className="text-red-700">gaps: {lesson.gaps.join("; ")}</p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-gray-600">
            No learning record yet{playbook?.reference ? ` (${playbook.reference})` : ""}.
          </p>
        )}
      </section>
    </main>
  );
}

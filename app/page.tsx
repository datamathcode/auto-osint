import Link from "next/link";

type Investigation = {
  id: number;
  target_name: string;
  target_id: string | null;
  claim_under_investigation: string | null;
  status: string;
  net_confidence_score: number | null;
};

const STATUS_STYLES: Record<string, string> = {
  complete: "bg-green-100 text-green-900 border-green-300",
  in_progress: "bg-blue-100 text-blue-900 border-blue-300",
  failed: "bg-red-100 text-red-900 border-red-300",
};

async function recentInvestigations(): Promise<Investigation[]> {
  const base = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const clientId = process.env.CF_ACCESS_CLIENT_ID;
  const clientSecret = process.env.CF_ACCESS_CLIENT_SECRET;
  const headers: Record<string, string> =
    clientId && clientSecret
      ? { "CF-Access-Client-Id": clientId, "CF-Access-Client-Secret": clientSecret }
      : {};

  try {
    const response = await fetch(`${base}/api/investigations`, { cache: "no-store", headers });
    if (!response.ok) return [];
    const rows = (await response.json()) as Investigation[];
    return rows.slice(0, 6);
  } catch {
    return [];
  }
}

export default async function Home() {
  const investigations = await recentInvestigations();

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-4xl font-bold text-gray-900">auto-osint</h1>
        <p className="mt-3 text-lg text-gray-600">
          Agentic recursive OSINT research with data journalism rigor.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/investigate"
            className="rounded-lg bg-gray-900 px-5 py-3 text-sm font-medium text-white hover:bg-gray-800"
          >
            Start an investigation
          </Link>
          {investigations[0] && (
            <Link
              href={`/dossiers/${investigations[0].id}`}
              className="rounded-lg border border-gray-300 bg-white px-5 py-3 text-sm font-medium text-gray-900 hover:bg-gray-100"
            >
              Latest dossier
            </Link>
          )}
        </div>

        <section className="mt-12">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
            Recent investigations
          </h2>

          {investigations.length === 0 ? (
            <p className="mt-4 rounded-lg border border-gray-200 bg-white p-5 text-gray-600">
              No investigations yet, or the API is unreachable. Start one to see it
              here.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {investigations.map((row) => (
                <li
                  key={row.id}
                  className="rounded-lg border border-gray-200 bg-white p-5 hover:border-gray-300"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <Link
                        href={`/dossiers/${row.id}`}
                        className="text-lg font-semibold text-gray-900 hover:underline"
                      >
                        {row.target_name}
                      </Link>
                      <p className="mt-1 text-sm text-gray-600">
                        {row.claim_under_investigation ?? "No claim recorded"}
                      </p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full border px-3 py-1 text-xs font-medium ${
                        STATUS_STYLES[row.status] ?? "bg-gray-100 text-gray-900 border-gray-300"
                      }`}
                    >
                      {row.status.replace("_", " ")}
                    </span>
                  </div>
                  <div className="mt-3 flex gap-4 text-sm text-gray-500">
                    <span>confidence {row.net_confidence_score ?? "n/a"}</span>
                    <Link href={`/investigations/${row.id}/progress`} className="hover:underline">
                      progress
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}

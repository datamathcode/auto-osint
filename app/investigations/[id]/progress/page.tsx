"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

type ProgressEvent = {
  type: string;
  step?: string | null;
  message: string;
  data?: Record<string, unknown>;
  progress?: number | null;
  timestamp: string;
};

const MAX_ATTEMPTS = 6;

function streamUrl(investigationId: string): string {
  return `/api/proxy/sse/investigation/${investigationId}`;
}

export default function ProgressPage({ params }: { params: { id: string } }) {
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<"connecting" | "live" | "reconnecting" | "done" | "error">(
    "connecting",
  );
  const [reconnects, setReconnects] = useState(0);
  const socketRef = useRef<EventSource | null>(null);
  const closedByUs = useRef(false);

  const connect = useCallback(() => {
    if (closedByUs.current) return;

    // SSE, not WebSocket: a Worker cannot upgrade a socket without a Durable
    // Object, and the backend already exposes /sse/investigation/{id}.
    const source = new EventSource(streamUrl(params.id));
    socketRef.current = source;

    source.onopen = () => {
      setStatus("live");
      setReconnects(0);
    };

    source.onmessage = (message) => {
      const event = JSON.parse(message.data) as ProgressEvent;
      if (event.type === "heartbeat") return;

      setEvents((current) => [...current, event]);
      if (typeof event.progress === "number") setProgress(event.progress);

      if (event.type === "investigation_complete") {
        closedByUs.current = true;
        setStatus("done");
        source.close();
      }
    };

    source.onerror = () => {
      source.close();
      if (closedByUs.current) return;
      setReconnects((attempt) => {
        if (attempt + 1 > MAX_ATTEMPTS) {
          setStatus("error");
          return attempt;
        }
        setStatus("reconnecting");
        const delay = Math.min(500 * 2 ** attempt, 8000);
        window.setTimeout(connect, delay);
        return attempt + 1;
      });
    };
  }, [params.id]);

  useEffect(() => {
    closedByUs.current = false;
    connect();
    return () => {
      closedByUs.current = true;
      socketRef.current?.close();
    };
  }, [connect]);

  const failures = events.filter(
    (event) => event.type === "step_finished" && event.data?.status === "failed",
  );

  return (
    <main className="mx-auto max-w-3xl p-6">
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Investigation #{params.id}</h1>
          <p className="text-sm text-gray-600">
            status: {status}
            {status === "reconnecting" ? ` (attempt ${reconnects}/${MAX_ATTEMPTS})` : ""}
          </p>
        </div>
        <Link className="text-sm text-blue-600 underline" href={`/dossiers/${params.id}`}>
          Open dossier
        </Link>
      </header>

      <div className="mt-6">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>Progress</span>
          <span>{progress}%</span>
        </div>
        <div className="mt-1 h-2 w-full rounded bg-gray-200">
          <div
            className="h-2 rounded bg-blue-600 transition-all"
            style={{ width: `${Math.min(progress, 100)}%` }}
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>

      {failures.length > 0 && (
        <p className="mt-4 rounded border-l-4 border-red-500 bg-red-50 p-3 text-sm text-red-800">
          {failures.length} step(s) failed. See the log below.
        </p>
      )}

      <section className="mt-6">
        <h2 className="text-lg font-semibold">Status log</h2>
        {events.length === 0 && <p className="mt-2 text-sm text-gray-600">Waiting for events…</p>}

        <ol className="mt-2 space-y-2">
          {events.map((event, index) => {
            const failed = event.type === "step_finished" && event.data?.status === "failed";
            return (
              <li
                key={`${event.timestamp}-${index}`}
                className={`rounded border p-3 text-sm ${
                  failed ? "border-red-300 bg-red-50" : "border-gray-200"
                }`}
              >
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span className="font-medium text-gray-700">{event.type}</span>
                  <time>{new Date(event.timestamp).toLocaleTimeString()}</time>
                </div>
                <p className="mt-1">{event.message}</p>
                {event.step && <p className="text-xs text-gray-500">step: {event.step}</p>}
                {typeof event.progress === "number" && (
                  <p className="text-xs text-gray-500">progress: {event.progress}%</p>
                )}
              </li>
            );
          })}
        </ol>
      </section>
    </main>
  );
}

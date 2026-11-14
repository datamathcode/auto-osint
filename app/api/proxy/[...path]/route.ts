import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

/**
 * Same-origin bridge to the FastAPI backend.
 *
 * Browser pages call `/api/proxy/...`; this handler attaches the Cloudflare
 * Access service token server-side so the credential never reaches the client.
 * Streaming responses (SSE) pass through because the body is forwarded as a
 * stream rather than buffered.
 */

const API_BASE =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function accessHeaders(): Record<string, string> {
  const id = process.env.CF_ACCESS_CLIENT_ID;
  const secret = process.env.CF_ACCESS_CLIENT_SECRET;
  return id && secret ? { "CF-Access-Client-Id": id, "CF-Access-Client-Secret": secret } : {};
}

async function forward(request: NextRequest, context: { params: { path: string[] } }) {
  const path = (context.params.path ?? []).join("/");
  const search = new URL(request.url).search;

  const headers: Record<string, string> = {
    ...accessHeaders(),
    Accept: request.headers.get("accept") ?? "*/*",
    "User-Agent": "auto-osint-worker/0.1",
  };
  const contentType = request.headers.get("content-type");
  if (contentType) headers["Content-Type"] = contentType;

  const init: RequestInit = { method: request.method, headers, cache: "no-store" };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${API_BASE}/${path}${search}`, init);
  } catch {
    return Response.json({ detail: "upstream unreachable" }, { status: 502 });
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
      "Cache-Control": "no-store",
      "X-Accel-Buffering": "no",
    },
  });
}

export {
  forward as GET,
  forward as POST,
  forward as PUT,
  forward as PATCH,
  forward as DELETE,
  forward as HEAD,
};

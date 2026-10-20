// app/api/[...path]/route.ts — server-side proxy to the SecureFlow AI backend.
// Forwards method, query parameters, body and headers to BACKEND_URL while injecting
// the X-API-Key secret from the server environment. The key is never exposed to the browser.

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8080";
const BACKEND_API_KEY = process.env.BACKEND_API_KEY || "";

async function handleProxy(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const subpath = (params.path || []).join("/");
  // Construct the target URL under /api/ on the backend
  const targetUrl = new URL(`/api/${subpath}`, BACKEND_URL);
  targetUrl.search = req.nextUrl.search;

  const headers: Record<string, string> = {
    "X-API-Key": BACKEND_API_KEY,
  };

  const contentType = req.headers.get("content-type");
  if (contentType) {
    headers["content-type"] = contentType;
  }

  const init: RequestInit = {
    method: req.method,
    headers,
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }

  try {
    const upstreamRes = await fetch(targetUrl.toString(), init);
    const body = await upstreamRes.arrayBuffer();

    const responseHeaders = new Headers();
    const upstreamContentType = upstreamRes.headers.get("content-type");
    if (upstreamContentType) {
      responseHeaders.set("content-type", upstreamContentType);
    }

    return new NextResponse(body, {
      status: upstreamRes.status,
      statusText: upstreamRes.statusText,
      headers: responseHeaders,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { error: "Failed to connect to backend", details: message },
      { status: 502 }
    );
  }
}

export const GET = handleProxy;
export const POST = handleProxy;
export const PUT = handleProxy;
export const PATCH = handleProxy;
export const DELETE = handleProxy;

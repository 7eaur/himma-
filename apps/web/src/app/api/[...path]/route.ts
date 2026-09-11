import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REQUEST_ID_PATTERN = /^[A-Za-z0-9._-]{8,128}$/;

function correlationId(req: NextRequest): string {
  const incoming = req.headers.get("x-request-id")?.trim() ?? "";
  return REQUEST_ID_PATTERN.test(incoming) ? incoming : crypto.randomUUID();
}

async function proxy(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const upstream_path = path.join("/");
  const search = req.nextUrl.search;
  const url = `${API_URL}/${upstream_path}${search}`;

  const cookieHeader = req.headers.get("cookie") ?? "";
  const contentType = req.headers.get("content-type") ?? "";
  const idempotencyKey = req.headers.get("idempotency-key");
  const requestId = correlationId(req);

  const headers: Record<string, string> = {
    "content-type": contentType,
    cookie: cookieHeader,
    "x-request-id": requestId,
  };
  if (idempotencyKey) {
    headers["idempotency-key"] = idempotencyKey;
  }

  const init: RequestInit = {
    method: req.method,
    cache: "no-store",
    headers,
  };

  if (!["GET", "HEAD"].includes(req.method)) {
    init.body = await req.blob();
  }

  const upstream = await fetch(url, init);
  const body = await upstream.arrayBuffer();
  const upstreamRequestId = upstream.headers.get("x-request-id") ?? requestId;

  const res = new NextResponse(body, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
      "cache-control": "private, no-store",
      "x-request-id": upstreamRequestId,
    },
  });

  // Forward Set-Cookie (critical for auth)
  const setCookie = upstream.headers.get("set-cookie");
  if (setCookie) {
    res.headers.set("set-cookie", setCookie);
  }

  return res;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;

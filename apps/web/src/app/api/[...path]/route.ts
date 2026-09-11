import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REQUEST_ID_PATTERN = /^[A-Za-z0-9._-]{8,128}$/;
const PRIVATE_NO_STORE = "private, no-store";
const APPROVED_MEDIA_PREFIX = "media/";

function correlationId(req: NextRequest): string {
  const incoming = req.headers.get("x-request-id")?.trim() ?? "";
  return REQUEST_ID_PATTERN.test(incoming) ? incoming : crypto.randomUUID();
}

/**
 * Only the read-only approved media surface may be shared-cacheable.
 * Everything else remains private/no-store because the BFF carries session
 * cookies and serves student/supervisor data.
 *
 * A Set-Cookie header always forces a private response even on a media-looking
 * path, preventing authentication state from ever entering a shared cache.
 */
export function responseCacheControl({
  upstreamPath,
  method,
  ok,
  upstreamCacheControl,
  hasSetCookie,
}: {
  upstreamPath: string;
  method: string;
  ok: boolean;
  upstreamCacheControl: string | null;
  hasSetCookie: boolean;
}): string {
  const mediaRead = upstreamPath.startsWith(APPROVED_MEDIA_PREFIX) && ["GET", "HEAD"].includes(method);
  if (!mediaRead || !ok || hasSetCookie) return PRIVATE_NO_STORE;

  const upstreamPolicy = upstreamCacheControl?.trim();
  if (upstreamPolicy && /(^|,)\s*public\b/i.test(upstreamPolicy) && !/\b(no-store|private)\b/i.test(upstreamPolicy)) {
    return upstreamPolicy;
  }

  // The backend approved-media registry is ID allow-listed and static. Keep a
  // conservative one-day browser policy if an upstream cache header is absent.
  return "public, max-age=86400";
}

async function proxy(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const upstreamPath = path.join("/");
  const search = req.nextUrl.search;
  const url = `${API_URL}/${upstreamPath}${search}`;

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
  const setCookie = upstream.headers.get("set-cookie");
  const cacheControl = responseCacheControl({
    upstreamPath,
    method: req.method,
    ok: upstream.ok,
    upstreamCacheControl: upstream.headers.get("cache-control"),
    hasSetCookie: Boolean(setCookie),
  });

  const res = new NextResponse(body, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
      "cache-control": cacheControl,
      "x-request-id": upstreamRequestId,
    },
  });

  // Forward Set-Cookie (critical for auth). Responses carrying it are forced
  // private by responseCacheControl above.
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

import { NextRequest, NextResponse } from "next/server";
import { responseCacheControl } from "./cachePolicy";
import { boundedRequestBody, proxyError, rejectUnsafeMutation, upstreamSignal } from "../proxySecurity";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REQUEST_ID_PATTERN = /^[A-Za-z0-9._-]{8,128}$/;

function correlationId(req: NextRequest): string {
  const incoming = req.headers.get("x-request-id")?.trim() ?? "";
  return REQUEST_ID_PATTERN.test(incoming) ? incoming : crypto.randomUUID();
}

async function proxy(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const rejected = rejectUnsafeMutation(req);
  if (rejected) return rejected;
  const { path } = await params;
  const upstreamPath = path.join("/");
  const search = req.nextUrl.search;
  const url = `${API_URL}/${upstreamPath}${search}`;

  const cookieHeader = req.headers.get("cookie") ?? "";
  const contentType = req.headers.get("content-type") ?? "";
  const idempotencyKey = req.headers.get("idempotency-key");
  const rangeHeader = req.headers.get("range");
  const requestId = correlationId(req);

  const headers: Record<string, string> = {
    "content-type": contentType,
    cookie: cookieHeader,
    "x-request-id": requestId,
  };
  if (idempotencyKey) headers["idempotency-key"] = idempotencyKey;
  if (rangeHeader) headers.range = rangeHeader;
  // Restore partial transfers and conditional requests only for approved media.
  if (/^v2\/content\/media\/[A-Z0-9-]+$/.test(upstreamPath) && req.method === "GET") {
    for (const name of ["if-range", "if-none-match", "if-modified-since"]) {
      const value = req.headers.get(name);
      if (value) headers[name] = value;
    }
  }

  let upstream: Response;
  try {
    const body = await boundedRequestBody(req);
    upstream = await fetch(url, { method: req.method, cache: "no-store", headers, body, signal: upstreamSignal() });
  } catch (error) {
    return proxyError(error, requestId);
  }
  const upstreamRequestId = upstream.headers.get("x-request-id") ?? requestId;
  const setCookie = upstream.headers.get("set-cookie");
  const cacheControl = responseCacheControl({
    upstreamPath,
    method: req.method,
    ok: upstream.ok,
    upstreamCacheControl: upstream.headers.get("cache-control"),
    hasSetCookie: Boolean(setCookie),
  });

  const responseHeaders: Record<string, string> = {
    "content-type": upstream.headers.get("content-type") ?? "application/json",
    "cache-control": cacheControl,
    "x-request-id": upstreamRequestId,
  };
  for (const name of ["accept-ranges", "content-range", "content-length", "content-disposition", "retry-after", "vary", "etag", "last-modified"]) {
    const value = upstream.headers.get(name);
    if (value) responseHeaders[name] = value;
  }

  const res = new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });

  if (setCookie) res.headers.set("set-cookie", setCookie);
  return res;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;

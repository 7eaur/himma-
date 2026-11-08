import { NextRequest, NextResponse } from "next/server";

export const MAX_PROXY_BODY_BYTES = 12 * 1024 * 1024;
export const UPSTREAM_TIMEOUT_MS = 30_000;

export class ProxyBodyTooLarge extends Error {}

export function rejectUnsafeMutation(req: NextRequest): NextResponse | null {
  if (["GET", "HEAD", "OPTIONS"].includes(req.method)) return null;
  const origin = req.headers.get("origin");
  const fetchSite = req.headers.get("sec-fetch-site")?.toLowerCase();
  // Railway terminates HTTPS before Next.js. Trust only deployment-configured
  // origins; request Host and forwarded headers cannot add trusted domains.
  const trustedOrigins = new Set<string>();
  const publicDomain = process.env.RAILWAY_PUBLIC_DOMAIN?.trim().toLowerCase();
  if (publicDomain && /^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$/.test(publicDomain)) {
    trustedOrigins.add(`https://${publicDomain}`);
  }
  for (const value of (process.env.APP_ALLOWED_ORIGINS ?? "").split(",")) {
    const configured = value.trim();
    if (!configured) continue;
    try {
      const url = new URL(configured);
      if (url.protocol === "https:" && url.username === "" && url.password === ""
          && url.pathname === "/" && url.search === "" && url.hash === "") {
        trustedOrigins.add(url.origin);
      }
    } catch {
      // Invalid configuration never widens the allowlist.
    }
  }
  if (trustedOrigins.size === 0) trustedOrigins.add(req.nextUrl.origin);
  if (origin === "null" || (origin && !trustedOrigins.has(origin)) || fetchSite === "cross-site") {
    return NextResponse.json({ detail: "مصدر الطلب غير مسموح" }, { status: 403 });
  }
  return null;
}

export async function boundedRequestBody(req: NextRequest): Promise<ArrayBuffer | undefined> {
  if (["GET", "HEAD"].includes(req.method)) return undefined;
  const declared = Number(req.headers.get("content-length") ?? "0");
  if (Number.isFinite(declared) && declared > MAX_PROXY_BODY_BYTES) throw new ProxyBodyTooLarge();
  const body = await req.arrayBuffer();
  if (body.byteLength > MAX_PROXY_BODY_BYTES) throw new ProxyBodyTooLarge();
  return body;
}

export function upstreamSignal(): AbortSignal {
  return AbortSignal.timeout(UPSTREAM_TIMEOUT_MS);
}

export function proxyError(error: unknown, requestId: string): NextResponse {
  if (error instanceof ProxyBodyTooLarge) {
    return NextResponse.json({ detail: "حجم الطلب أكبر من الحد المسموح", request_id: requestId }, { status: 413, headers: { "x-request-id": requestId } });
  }
  return NextResponse.json({ detail: "الخدمة غير متاحة مؤقتًا", request_id: requestId }, { status: 503, headers: { "cache-control": "private, no-store", "x-request-id": requestId, "retry-after": "3" } });
}

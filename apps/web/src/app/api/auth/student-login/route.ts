import { NextRequest, NextResponse } from "next/server";
import { boundedRequestBody, proxyError, rejectUnsafeMutation, upstreamSignal } from "../../proxySecurity";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  const rejected = rejectUnsafeMutation(req);
  if (rejected) return rejected;
  const requestId = crypto.randomUUID();
  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/auth/student-login`, { method: "POST", headers: { "Content-Type": "application/json", "x-request-id": requestId }, body: await boundedRequestBody(req), signal: upstreamSignal() });
  } catch (error) {
    return proxyError(error, requestId);
  }

  const res = new NextResponse(upstream.body, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
      "cache-control": "private, no-store",
      "x-request-id": upstream.headers.get("x-request-id") ?? requestId,
    },
  });
  const setCookie = upstream.headers.get("set-cookie");
  if (setCookie) {
    res.headers.set("set-cookie", setCookie);
  }

  return res;
}

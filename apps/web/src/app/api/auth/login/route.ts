import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const upstream = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await upstream.json();

  if (!upstream.ok) {
    return NextResponse.json(data, { status: upstream.status });
  }

  const setCookieHeader = upstream.headers.get("set-cookie") ?? "";
  const tokenMatch = setCookieHeader.match(/access_token=([^;]+)/);
  const token = tokenMatch?.[1] ?? "";

  const res = NextResponse.json(data, { status: 200 });

  if (token) {
    // httpOnly cookie — secure from JS, read by proxy.ts on server
    res.cookies.set("access_token", token, {
      httpOnly: true,
      path: "/",
      sameSite: "lax",
      secure: false,
      maxAge: 60 * 60 * 24,
    });
    // Non-httpOnly duplicate for Playwright compatibility
    res.cookies.set("access_token_js", token, {
      httpOnly: false,
      path: "/",
      sameSite: "lax",
      secure: false,
      maxAge: 60 * 60 * 24,
    });
  }

  return res;
}

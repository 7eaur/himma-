import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  // Forward the browser cookie to FastAPI
  const cookieHeader = req.headers.get("cookie") ?? "";

  const upstream = await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    headers: { "Content-Type": "application/json", cookie: cookieHeader },
  });

  const res = NextResponse.json({ message: "logged out" }, { status: 200 });

  res.cookies.set("access_token", "", { httpOnly: true, path: "/", maxAge: 0, sameSite: "lax" });
  res.cookies.set("access_token_js", "", { httpOnly: false, path: "/", maxAge: 0, sameSite: "lax" });

  return res;
}

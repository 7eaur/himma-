import { NextRequest, NextResponse } from "next/server";

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/admin/login" || pathname === "/student/login") {
    return NextResponse.next();
  }

  const studentRoute = pathname === "/student" || pathname.startsWith("/student/");
  const loginPath = studentRoute ? "/student/login" : "/admin/login";
  const login = () => {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = loginPath;
    loginUrl.search = "";
    loginUrl.searchParams.set("next", pathname + request.nextUrl.search);
    return NextResponse.redirect(loginUrl);
  };
  if (!request.cookies.get("access_token")?.value) return login();

  // The API validates the signature, expiry, current role and active account.
  // Cookie presence alone must never grant access to the protected page shell.
  try {
    const upstream = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/me`, {
      headers: { cookie: request.headers.get("cookie") ?? "" },
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (upstream.status === 401 || upstream.status === 403) return login();
    if (!upstream.ok) throw new Error("Session verification unavailable");
    const account = await upstream.json();
    if (account.role !== (studentRoute ? "student" : "researcher")) return login();
  } catch {
    return new NextResponse("تعذر التحقق من الجلسة. حاول مرة أخرى.", { status: 503 });
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*", "/student/:path*"],
};

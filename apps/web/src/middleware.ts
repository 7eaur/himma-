import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('access_token')?.value;

  // Protect Admin routes
  if (pathname.startsWith('/admin') && !pathname.startsWith('/admin/login')) {
    if (!token) {
      const url = request.nextUrl.clone();
      url.pathname = '/admin/login';
      return NextResponse.redirect(url);
    }
    // We cannot verify JWT role on Edge without jsonwebtoken package or subtlecrypto,
    // so we rely on backend rejecting API calls if the role is wrong, 
    // but at least we redirect unauthenticated users cleanly.
  }

  // Protect Student routes
  if (pathname.startsWith('/student') && !pathname.startsWith('/student/login')) {
    if (!token) {
      const url = request.nextUrl.clone();
      url.pathname = '/student/login';
      return NextResponse.redirect(url);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/admin/:path*',
    '/student/:path*',
  ],
};

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Route protection is handled by the pages themselves via /api/me check.
// This proxy file exists only to satisfy Next.js 16 requirement.
export function proxy(request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: [],
};

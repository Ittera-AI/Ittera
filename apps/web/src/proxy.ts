import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  // Auth is handled via Supabase session on the client. Avoid cookie-based
  // edge redirects here because OAuth logins (e.g. Google) can be valid while
  // a custom app cookie is absent, causing false redirects to /login.
  if (pathname === "/login") return NextResponse.next();

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
  ],
};

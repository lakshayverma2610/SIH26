import { NextRequest, NextResponse } from "next/server";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public routes
  if (pathname === "/" || pathname === "/login") {
    return NextResponse.next();
  }

  // For now, allow everything else.
  // We'll add authentication + role checks later.
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/complaints/:path*",
    "/predictions/:path*",
    "/alerts/:path*",
    "/profile/:path*",
    "/admin/:path*",
    "/super-admin/:path*",
  ],
};
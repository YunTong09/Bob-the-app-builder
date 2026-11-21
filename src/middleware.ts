import { NextResponse, type NextRequest } from "next/server";

// Hosted invite-code mode only: send visitors without a session cookie to
// /login before the workspace loads. This is a convenience redirect, not an
// access check. FastAPI verifies the signed cookie on every API request.
const INVITE_AUTH = process.env.NEXT_PUBLIC_R2R_MOCK === "false" && process.env.NEXT_PUBLIC_R2R_AUTH === "invite";
const SESSION_COOKIE = "__Host-r2r_session";
// Hosted mode serves the site and API from one public origin. Behind the
// gateway, request.url and nextUrl report the internal host (localhost:3000),
// so the redirect is built from the configured public origin instead.
const PUBLIC_ORIGIN = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

export function middleware(request: NextRequest) {
  if (!INVITE_AUTH || request.cookies.has(SESSION_COOKIE)) return NextResponse.next();
  return NextResponse.redirect(new URL("/login", PUBLIC_ORIGIN || request.url), 307);
}

export const config = {
  // Pages only: skip /login, API routes, Next.js assets and files with extensions.
  matcher: ["/((?!login|api|_next|.*\\..*).*)"],
};

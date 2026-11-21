"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, getSession, isInviteAuth, signIn } from "@/frontend/api/replyApi";

function messageFor(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return "That invite code isn't valid. Check it and try again.";
    if (error.status === 429) return "Too many attempts. Wait a few minutes, then try again.";
    if (error.status === 422) return "Enter your invite code.";
  }
  return "Couldn't reach the sign-in service. Try again.";
}

export default function LoginPage() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const started = useRef(false);

  async function attempt(inviteCode: string) {
    setBusy(true);
    setError(null);
    try {
      await signIn(inviteCode);
      router.replace("/");
    } catch (err) {
      setError(messageFor(err));
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!isInviteAuth || started.current) return;
    started.current = true;
    // Personal sign-in links put the code in the fragment (/login#R2R-...).
    // Fragments are never sent to the server, so the code stays out of request
    // logs and Referer headers. Clear it from the address bar right away.
    let linkCode = window.location.hash.slice(1);
    try {
      linkCode = decodeURIComponent(linkCode);
    } catch {
      // Malformed escapes: use the raw text; the server rejects bad codes.
    }
    linkCode = linkCode.trim().slice(0, 64);
    if (linkCode) {
      window.history.replaceState(null, "", window.location.pathname);
      setCode(linkCode);
      void attempt(linkCode);
      return;
    }
    getSession()
      .then(() => router.replace("/"))
      .catch(() => undefined);
    // attempt is stable for this one-time check.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    await attempt(code);
  }

  return (
    <main className="page-shell">
      <header className="page-header">
        <h1>Sign in</h1>
        <p>Enter the invite code you received to open your Rage-to-Reply workspace.</p>
      </header>
      <section className="panel workspace-panel" aria-labelledby="login-heading">
        <h2 id="login-heading" className="sr-only">
          Invite code
        </h2>
        {isInviteAuth ? (
          <form onSubmit={onSubmit} className="form-field">
            <label htmlFor="invite-code">Invite code</label>
            <input
              id="invite-code"
              name="inviteCode"
              autoComplete="off"
              autoCapitalize="characters"
              spellCheck={false}
              maxLength={64}
              placeholder="R2R-XXXX-XXXX-XXXX-XXXX"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            {error && (
              <p className="error-message" role="alert">
                <span className="status-label status-label-error">Error</span> {error}
              </p>
            )}
            <div>
              <button type="submit" className="primary-button" disabled={busy || !code.trim()}>
                {busy ? "Signing in…" : "Sign in"}
              </button>
            </div>
            <p className="small-text">Your history is private to your invite code. Use synthetic data for the demo.</p>
          </form>
        ) : (
          <p className="small-text">Sign-in is only used on the hosted site. This workspace runs without it.</p>
        )}
      </section>
    </main>
  );
}

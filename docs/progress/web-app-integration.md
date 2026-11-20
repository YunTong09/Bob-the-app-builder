# Rage-to-Reply Web App Integration Tracker

## TASK 1 — Frontend / Backend API Integration

**Status** — DONE for the local single-user demo  
**Updated** — 2026-11-21 (Australia/Brisbane)

Both browser pages now share the existing API client. Browser mock mode remains the default. In HTTP mode, requests go directly to the configured loopback FastAPI origin. FastAPI permits the exact local browser origin via CORS and retains the existing loopback and proxy-header restrictions. The Next.js configuration and legacy routes are intact. See the [local instructions](../../README.md#run-the-current-browser-prototype) and [API Contract](../API_CONTRACT.md).

| Files | Change |
| --- | --- |
| `src/app/page.tsx`, `src/frontend/features/memory/HistoryPanel.tsx` | Route generation and history through the existing shared client. |
| `src/frontend/api/replyApi.ts`, `src/frontend/api/web-api.ts` | Configure the backend origin, keep browser mock mode, and reuse the contract types. |
| `backend/api/main.py` | Add opt-in CORS and local host checks at the composition root. |
| `backend/tests/test_identity_and_wiring.py` | Cover allowed and denied preflight, actual responses, proxy rejection and host validation. |
| `.env.example`, `README.md`, `docs/ARCHITECTURE.md` | Document opt-in local integration and hosted boundaries. |
| Progress trackers | Record Web App verification and link the historical Slack tracker. |

### Verification

- Frontend TypeScript check, lint and production build passed in a temporary copy of the current working tree.
- Backend suite passed on the current frontend branch with 182 tests, including local-origin coverage. The later Slack-preview implementation on `origin/main` was outside this test snapshot.
- Chrome with a real local Next.js server and FastAPI in `R2R_AI_MODE=mock` rendered a generated reply and completed JSON import, review and confirmed delete. Verified `POST /api/reply/generate`, `POST /api/memory/import`, `GET /api/memory/search` and `DELETE /api/memory` returned 200.
- Verified that invalid generation returns the contract's 422 error and that a blocked request displays a network error while preserving the prior reply. Confirmed `/assistant` opens in HTTP mode and the optional preferences request still returns 501.
- A separate client check generated a reply and managed history with browser mock mode and a network call guard.
- Live Claude generation, live Slack credentials, Slack import UI, and hosted multi-user access remain unverified.

**Blockers** — None for the local HTTP flow with FastAPI mock AI. Live provider verification requires test credentials. The next integration should use the Slack-preview backend from the team branch.

**Next recommended task** — Add Slack import preview, message selection and confirmation after integrating the team backend changes. Continue using the existing [Slack tracker](slack-integration-tracker.md) as prototype history.

## Change Log

| Date | Task | Change | Verification | Commit |
| --- | --- | --- | --- | --- |
| 2026-11-21 | TASK 1 | Unified the browser API client and enabled explicit local FastAPI access. | Frontend checks, 182 backend tests, browser mock isolation and Chrome HTTP flow passed. | Uncommitted |

# Rage-to-Reply Web App Integration Tracker

## Handoff Guide

**Start with [WEB-01](#web-01--frontend--backend-integration).** Bring the latest Workspace and Tutorial changes into the reviewed frontend/backend integration branch, then rerun the core browser flow with FastAPI Mock AI. The product goal is a hosted HTTPS rewrite workflow for invited users.

### Before you start

1. Read the [development rules](../../AGENTS.md), [product spec](../PRODUCT_SPEC.md), [architecture](../ARCHITECTURE.md), [API contract](../API_CONTRACT.md), and [frontend contract](../FRONTEND_CONTRACT.md). See the [README](../../README.md) for setup and run commands.
2. Run `git status --short --branch` and `git log -1 --oneline`. Check your working tree and compare the latest available team refs with the recorded baseline below.
3. Confirm which changes are available to you. If the local integration branch or unpublished frontend changes are missing, ask the owner for a shareable branch or patch and record the missing input. Use a separate integration branch and preserve existing team work.

| Baseline recorded on 2026-11-21 | What is available |
| --- | --- |
| `irene/frontend` · `1ec3771` | Shared API client and Slack import UI were committed. Settings and History dialogs, sample inputs, history search, and the Tutorial were still in the local working tree. |
| `origin/main` · `c91bcce` | Team backend reference with FastAPI, updated validation, and Slack preview. Check for newer commits before integration. |
| Local `integration/web-01` · `4136ed5` | Merge commit `ff6ad6f` passed 435 backend tests and Chrome-to-FastAPI checks with Mock AI. `cfd2484` contains the centered layout. The branch had not been pushed or updated with the later Workspace and Tutorial changes at the time of recording. |

### First acceptance run for WEB-01

- Reuse `src/frontend/api/replyApi.ts` and `backend/api/main.py`. Preserve Slack service wiring and local CORS, and verify the actual routes against the API contract.
- Use synthetic data. Set `NEXT_PUBLIC_R2R_MOCK=false` and `NEXT_PUBLIC_API_BASE_URL` on the frontend. Set `R2R_AI_MODE=mock` and the matching `R2R_WEB_ORIGIN` on the backend. Confirm in Chrome Network that generation, history import, search, and deletion reach FastAPI.
- Run TypeScript, lint, production build, the full backend suite, and browser E2E on one commit. Verify that setup can be skipped and reopened, replies can be generated, regenerated, and edited, receipts and warnings display, history can be imported, searched, and deleted after confirmation, network errors are shown, and the Tutorial links back to the Workspace.
- **Quick Tone Rewrite** still needs a draft-only endpoint. **Live Slack import** still needs a test workspace. Track them separately. WEB-02 covers live Claude verification.

### After verification

Update both the roadmap table and the task status. Check off verified acceptance criteria. Record the branch and commit, commands, environment, provider, passed/failed/skipped counts, and blockers in Test Results and the Change Log. Keep past results tied to the version and scope tested. WEB-02 and WEB-03 can run in parallel after WEB-01 passes.

## P0 Development Roadmap

Rage-to-Reply is an **end-to-end AI web application**. Invited users should be able to complete the rewrite workflow at an HTTPS URL without installing software or running a backend locally.

| Task ID | Task | Priority | Status | Dependencies | Objective |
| --- | --- | --- | --- | --- | --- |
| WEB-01 | Frontend & Backend Integration | P0 | DONE | None | Build a testable version with the latest frontend and backend |
| WEB-02 | Real Claude API Integration | P0 | TODO | WEB-01 | Verify live rewriting, receipts, and error handling |
| WEB-03 | Web Deployment & Hosting | P0 | IN PROGRESS | WEB-01, parallel with WEB-02 | Provide HTTPS access for invited teammates |
| WEB-04 | End-to-End Testing & Demo Validation | P0 | TODO | WEB-02, WEB-03 | Verify on another computer and rehearse the two-minute demo |

**Status values** — `TODO` Pending, `IN PROGRESS` Underway, `BLOCKED` Waiting on a specific blocker, `DONE` Acceptance criteria verified. Roadmap statuses apply to the latest combined version. Earlier Mock AI results are in the [WEB-01 local baseline](#web-01--local-integration-baseline).

**Dependency order** — WEB-01 → WEB-02 and WEB-03 (in parallel) → WEB-04.

### WEB-01 — Frontend & Backend Integration

**Status** — DONE. **Dependencies** — None.

**Objective** — Integrate the latest `irene/frontend` and `origin/main` code into one testable version.

**Checklist**

- [x] Integrate the Next.js frontend and FastAPI backend.
- [x] Verify compatibility between the API contract, shared API client, and backend routes.
- [x] Preserve reply generation, Memory, Receipts, and existing Slack import. (Receipts display and live Slack import not exercised: Mock AI returns no evidence and no Slack token is configured.)
- [x] Resolve Git conflicts while preserving team changes.
- [x] Run the frontend build, lint, TypeScript, backend tests, and browser E2E on the same version.

**Acceptance Criteria**

- [x] Frontend and backend work together on the integrated version.
- [x] The core web workflow passes browser E2E.
- [x] No known critical regressions remain.

**Test Results** — 2026-11-21, branch `feature/bob` at merge `6b522ce` (includes `origin/main` `e35e563`), Windows, FastAPI with `R2R_AI_MODE=mock`, frontend with `NEXT_PUBLIC_R2R_MOCK=false`.
- Passed: 435 backend tests, `tsc --noEmit`, `npm run lint`, `npm run build`.
- Passed (API smoke): import, search, delete, three-tone generate, empty-input 422, preferences 501, CORS preflight.
- Passed (browser, manual): history JSON import (3 imported), Review history, three-tone generate, regenerate, reply editing, search (`blocked`), delete history, empty-input error display.
- Note: search matches whole words only, per the API contract (`block` does not match `blocked`). Prefix matching is a possible follow-up for the backend owner.
- Mock AI returns no evidence, so evidence display is deferred to WEB-02.

**Blockers** — None confirmed. First verify the latest commits and changes on both branches.

### WEB-02 — Real Claude API Integration

**Status** — TODO. **Dependencies** — WEB-01.

**Objective** — Verify that the website uses the live Claude API through FastAPI to rewrite drafts.

**Checklist**

- [ ] Configure server-side Claude API credentials and the model.
- [ ] Verify Diplomatic, Neutral, and Assertive tones.
- [ ] Verify reply regeneration and editing.
- [ ] Check that replies preserve the user's intent and important facts.
- [ ] Verify how live Memory, Receipts, and Warnings are returned and displayed.
- [ ] Test timeouts, rate limits, API failures, and retries.

**Acceptance Criteria**

- [ ] The browser → FastAPI → Claude API → frontend flow succeeds.
- [ ] Users can generate and regenerate with live Claude and edit the reply in the browser.
- [ ] API failures show a clear error and keep the configured provider.

**Test Results** — Live Claude verification is pending.

**Blockers** — Requires WEB-01 acceptance and confirmed server-side credentials and model configuration.

### WEB-03 — Web Deployment & Hosting

**Status** — IN PROGRESS. **Dependencies** — WEB-01. Can run in parallel with WEB-02.

**Objective** — Provide invited teammates with HTTPS access to the web app.

**Checklist**

- [x] Deploy the Next.js frontend and FastAPI backend.
- [x] Configure HTTPS, API routing, and environment variables.
- [x] Store the Claude API key in server-side secret management.
- [x] Configure CORS, allowed hosts, and access controls for invited users.
- [ ] Add basic rate limiting, API cost controls, and health checks. (Rate limits and cost controls are done. No dedicated health-check endpoint exists; systemd restarts failed services.)
- [x] Verify deployed API connectivity and backend availability.

**Acceptance Criteria**

- [x] Invited teammates can open the site without installing Python or Node.js or starting a local server.
- [x] The deployed frontend and backend communicate successfully.
- [x] API credentials are absent from the browser bundle and repository.
- [ ] Invited-user access controls pass verification. The local single-user identity mechanism remains limited to the local demo. (Sign-in, rejection of an invalid code and redirect checks passed on the deployed site. Isolation between two codes is verified in automated tests but not yet on the deployed site.)

**Test Results** — 2026-11-21, branch `feature/invite-auth`, deployed at `https://ragetoreply.tech` (Porkbun DNS → reserved IP `r2r-ip`, Compute Engine VM `r2r-vm` in `australia-southeast1-b`, Caddy with a Let's Encrypt certificate). See the [deployment guide](../../deploy/gce/README.md).
- Secret Manager holds `anthropic-api-key`, `r2r-invites` and `r2r-session-secret`. Only the VM service account has read access, and the key returned HTTP 200 from the Anthropic models endpoint.
- External checks from another network all passed. Without a session, `/` redirected (307) to `https://ragetoreply.tech/login`. `/login` returned 200 and `/api/session` returned 401. An invalid code returned 401 without setting a cookie. HTTP redirected (308) to HTTPS, and the HSTS, `X-Frame-Options` and `nosniff` headers were present.
- Teammates opened the site and signed in from their own computers. Live generation succeeded.
- Passed locally: 505 backend tests, including 57 invite-session tests (cookie attributes, tampering, expiry, revocation, isolation with in-memory and SQLite stores, throttling, validation, configuration and the invite CLI). Also passed: `tsc --noEmit`, `npm run lint` and the hosted-mode `npm run build`. HTTP smoke tests covered the per-address lockout, the per-invite generation limit and unknown-host rejection.
- Personal sign-in links (`/login#<code>`) were verified with headless Edge through a same-origin gateway. The link opened the workspace and the session persisted. A bad link showed an error, and a fresh browser without a link stayed on `/login`.
- Pending: isolation between two invite codes on the deployed site, and redeploying from `main` after this branch merges.

**Blockers** — Team agreement on the invite-code session change in [API_CONTRACT.md](../API_CONTRACT.md#hosted-invite-code-sessions) before merging.

### WEB-04 — End-to-End Testing & Demo Validation

**Status** — TODO. **Dependencies** — WEB-02 and WEB-03.

**Objective** — Verify that another user can complete the full rewrite workflow over HTTPS on a different computer.

**Checklist**

- [ ] Have a teammate open the deployed site on their own computer.
- [ ] Enter a work message and emotional draft, and generate a reply with live Claude.
- [ ] Verify switching tones, regenerating, editing, and confirming the final reply.
- [ ] Verify Memory, Receipts, Warnings, and history management.
- [ ] Test API failures, network failures, and empty states.
- [ ] Rehearse the two-minute hackathon demo.

**Acceptance Criteria**

- [ ] The core workflow succeeds from another computer using the hosted URL and live Claude without a local mock.
- [ ] No blocking issues remain in the core workflow.
- [ ] The two-minute demo has been rehearsed successfully.
- [ ] The environment, commit, results, and remaining limitations are recorded.

**Test Results** — Cross-device testing and the demo rehearsal are pending.

**Blockers** — Requires WEB-02 and WEB-03 acceptance.

### Optional Integrations and Public Release Requirements

- Slack Import remains an optional data source. Keep the Slack Modal and Desktop Companion research and history. All three are outside the core web P0 roadmap.
- **Public multi-user registration requires** authentication, per-user data isolation, and security acceptance. Verify rejection of unauthorized API access, isolation for Memory imports, searches, deletions, and receipts, and safe handling of sensitive data.

## WEB-05 — Voice-to-Text Input

**Status** — IN PROGRESS. Implementation and Chrome mock acceptance passed. Live microphone acceptance is pending.

**Changes**

- `src/frontend/features/reply/DictationControls.tsx` extracts the earlier prototype into one typed component. It handles language selection, listening and stop states, final results, cleanup, and privacy guidance.
- `VentInput.tsx` adds the controls beside the editable draft. `src/app/page.tsx` appends final transcripts to the current mode's draft, preserves typed text, and keeps the existing Generate flow. Mode changes cancel an active session.
- `ReplyPanel.tsx` reuses the shared controls and preserves the legacy panel. `src/frontend/styles/pixel-workspace.css` styles the controls and active state. `docs/FRONTEND_CONTRACT.md` records dictation's optional permissions and data handling.

**Verification**

- [x] TypeScript (`tsc --noEmit --incremental false`), `npm run lint`, and `npm run build` passed in an isolated workspace. The build emitted dependency-path cache warnings and exited successfully.
- [x] Headless Chrome with a mocked `webkitSpeechRecognition` verified keyboard start, listening status, `en-US` and `zh-TW`, multiple Start/Stop cycles, append to existing text, duplicate final and interim handling, and editable results.
- [x] Chrome mock verified denied permission, no speech, unavailable microphone, interruption, service and generic failures, unsupported browsers, and cancellation on mode and route changes. Existing text and typed fallback worked.
- [x] A local HTTP fixture captured the existing reply-generation request. It received the complete edited text after Generate, with zero requests caused by dictation alone.
- [x] Chrome confirmed the monochrome microphone sits inside the draft field at 1280px and 375px widths. Keyboard and mocked dictation flows passed after the layout change.
- [x] Chrome mock verified automatic stop after 1.5 seconds following the speech-end event, cancellation when speaking resumes, continued availability of manual stop, and no automatic Generate request.
- [ ] Verify real English and Traditional Chinese speech, permissions and stop behavior with a physical microphone on the target Chrome setup.

**Browser compatibility and limitations** — Uses `SpeechRecognition` or `webkitSpeechRecognition` where available. Browser and OS support, language availability, permissions, and network requirements may vary. A browser provider may process audio remotely. The app does not capture or store raw audio. The mock verifies the browser integration and request body; it does not measure transcription accuracy or exercise a live provider. Quick Tone Rewrite retains its existing generation availability.

## WEB-06 — Interactive Emotion Eating Animation

**Status** — DONE for frontend acceptance with a local HTTP fixture. A live Claude run was outside this task.

**States** — Generate starts at `interactive`. Each click or focused Enter/Space sends one decorative word into the angry face during `eating`. The face grows after each word. Manual taps add a brief pixel impact and squash; automatic feeding omits the hit effect. After the last word, the face swells during `inflating`, bursts into a pixel ring and flying fragments during `releasing`, and returns as a smile in `completed`. API failure exits to the workspace with Retry, preserving the draft and previous reply.

**Interaction and wait meter** — The face can feed itself after the interaction window. Skip and reduced motion bypass the animation. The restored 24-block pixel bar is tied only to the API. It displays elapsed time on the first request and estimates remaining time from up to three previous successful requests in the current workspace. Late responses switch back to elapsed time. The bar is full only after success.

**API synchronization** — The existing generation request starts immediately and is sent once per submission. A fast response is held until animation completion. A slow response keeps the processing status visible after the animation completes. Retry and Regenerate start a fresh animation. No backend, Claude, Slack, or speech recognition changes.

**Changed files** — `src/app/page.tsx`, `src/frontend/features/reply/ReplyProcessing.tsx`, `src/frontend/features/reply/RageLoadingMeter.tsx`, `src/frontend/features/reply/ReplyWaitMeter.tsx`, `src/frontend/styles/pixel-workspace.css`, and `docs/FRONTEND_CONTRACT.md`. Restored the missing `appendDictation` import on the branch so the existing voice callback builds.

**Verification** — TypeScript, lint, and production build passed in an isolated workspace. Headless Chrome verified click, Enter and Space, input focus isolation, one-word feeding, the final burst, elapsed and estimated wait behavior, one request per submission, fast and slow HTTP responses, failure and Retry, skip, automatic completion, reduced motion, regeneration, editing, switching tone, opening Memory and displaying Receipts.

**Known limitations** — Remaining time is an estimate, not server progress. Chrome tests use a local HTTP fixture. Timing, visual feel and accessibility behavior on other browsers were not evaluated.

## History

<details>
<summary>View TASK 1, TASK 2, the local integration baseline, and frontend follow-up</summary>

## TASK 1 — Frontend / Backend API Integration

**Status** — DONE for the local single-user demo\
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

## TASK 2 — Slack Preview & Import UI

**Status** — BLOCKED for live acceptance. The frontend implementation and mock acceptance are complete.

### Backend readiness

The checked-out `irene/frontend` branch lacks `POST /api/slack/preview`. The fetched `origin/main` at `c91bcce` includes the route, the Slack history service, and API and adapter tests. The frontend uses that revision's documented request and response shapes. Live use requires a configured channel ID, a server-side bot token, bot channel membership, and `channels:history` for a public channel or `groups:history` for a private channel. No branch changes or backend modifications were made.

### Checklist

- [x] Add channel selection and read-only preview with an explicit mock label.
- [x] Display sender, content, available time and source, warnings and empty pages.
- [x] Provide checkboxes, page-wide selection, deselection, and a selected count across pages.
- [x] Require confirmation before sending the selected subset to the existing memory import API.
- [x] Guard repeated submissions, retain selections on failure, and report imported versus skipped messages.
- [x] Reuse the existing history view to review imported memory.
- [ ] Integrate and verify the team FastAPI endpoint against a real Slack test channel.

### Files and verification

- `src/frontend/features/memory/SlackImportPanel.tsx` and `HistoryPanel.tsx` provide the workflow in the existing history section. Manual JSON import remains available.
- `src/frontend/api/contract.ts` and `replyApi.ts` extend the TASK 1 client with the preview contract and synthetic fixture.
- TypeScript, lint and Next.js production build passed.
- Chrome browser mock verified preview, selection and deselection, no history change before confirmation, selected-only import, history review and existing reply generation.
- Chrome with a synthetic HTTP fixture verified POST payloads, cursor pagination, an empty page with skipped records, omitted metadata, 409 conflict handling, blocked duplicate confirmation, preserved selection, successful retry and history review. The fixture is not the team's FastAPI service.
- The import contract is atomic. On success, duplicate records are shown in the skipped count. A conflicting batch fails as a whole and remains available for retry.

**Blockers** — The real Slack Preview route has not been integrated into this branch. The real Slack credentials, allowlisted channel and permissions have yet to be verified with the browser.

**Next recommended task** — Coordinate integration of the team backend and complete live TASK 2 acceptance in a test Slack channel. Keep later tasks pending.

## WEB-01 — Local Integration Baseline

**Status** — DONE on the local `integration/web-01` branch for the FastAPI Mock AI baseline. Merge commit `ff6ad6f` combines the frontend and team backend. The tested layout commit is `cfd2484`; the detailed verification record is in tracker commit `4136ed5` on that branch.

TypeScript, lint and production build passed. The backend suite passed 435 tests, including the 171-test integration subset. Chrome verified localhost generation, tone regeneration, editing, history import/search/confirmed deletion and error handling. These results belong to the integration branch, before the Workspace and Tutorial changes below. Live Claude, Slack and hosted access remain unverified.

## Workspace and Tutorial — Frontend Follow-up

**Status** — Implemented on `irene/frontend`. Build and local page checks passed. Browser interaction checks and verification against the combined backend remain pending.

- The centered Workspace keeps the draft and generated reply stacked at equal widths. The reply appears after generation.
- First-time visitors can set communication preferences or skip setup. The Settings button reopens the dialog. The History button opens a separate dialog in Rewrite with Evidence mode.
- The Workspace offers sample draft inputs. History supports explicit sample and JSON imports, Slack preview and selected import, keyword search, and confirmed deletion.
- The reply view labels AI interpretation and shows receipts, unverified claims and warnings. The former Assistant page at `/assistant` now serves as the Tutorial and links back to the Workspace.
- Files include `src/app/page.tsx`, `src/app/assistant/page.tsx`, `src/frontend/shared/SiteNav.tsx`, `src/frontend/styles/globals.css`, `src/frontend/features/memory/HistoryPanel.tsx`, and `src/frontend/features/preferences/PreferencesPanel.tsx`.

**Verification** — TypeScript (`tsc --noEmit --incremental false`), `npm run lint` and `npm run build` passed in a temporary copy. Local HTTP checks at port 3000 confirmed the Workspace sample-input control and the Tutorial page. These checks did not exercise the new controls in a browser or call external providers.

**Remaining work** — Quick Tone Rewrite still requires a draft-only endpoint that excludes Memory. Shared preferences are pending on the backend; the Workspace retains its browser fallback. Bring the frontend follow-up into the reviewed integration branch and recheck the Workspace using FastAPI Mock AI. Continue with WEB-02 for live Claude once that baseline is confirmed.

</details>

## Change Log

| Date | Task | Change | Verification | Commit |
| --- | --- | --- | --- | --- |
| 2026-11-21 | TASK 1 | Unified the browser API client and enabled explicit local FastAPI access. | Frontend checks, 182 backend tests, browser mock isolation and Chrome HTTP flow passed. | Uncommitted |
| 2026-11-21 | TASK 2 | Added Slack preview, selective confirmation and history review to the web workspace. | TypeScript, lint, production build and both Chrome fixture paths passed. Live Slack API remains blocked. | Uncommitted |
| 2026-11-21 | WEB-01 | Established the local frontend and team backend integration baseline. | 435 backend tests and local Chrome HTTP passed with FastAPI Mock AI. | `ff6ad6f`, `cfd2484`; tracker `4136ed5` |
| 2026-11-21 | Frontend follow-up | Centered the Workspace, moved Settings and History into dialogs, added sample inputs and history search, and replaced Assistant with Tutorial. | TypeScript, lint, build and local page checks passed. Browser interaction and combined backend verification pending. | Uncommitted |
| 2026-11-21 | P0 Roadmap | Added WEB-01 through WEB-04, dependencies, and public release requirements. | Documentation update. Product testing was outside the scope. | Uncommitted |
| 2026-11-21 | WEB-01 | Verified the combined `feature/bob` version (main `e35e563` merged) with FastAPI Mock AI. | 435 backend tests, tsc, lint and build passed; core browser workflow passed manually. | `6b522ce` |
| 2026-11-21 | Tracker organization | Moved previous tasks and verification into expandable history and retained the roadmap and Change Log. | Markdown formatting checked. | Uncommitted |
| 2026-11-21 | Handoff guide | Added branch baselines, the next task, acceptance steps, and progress update instructions. | Markdown formatting checked. | Uncommitted |
| 2026-11-21 | WEB-05 | Added shared browser dictation to the workspace draft. | TypeScript, lint, production build and Chrome mock acceptance passed. Physical microphone pending. | Uncommitted |
| 2026-11-21 | WEB-03 | Added invite-code sessions, personal sign-in links, per-invite generation limits, the `/login` page and Compute Engine + Caddy deployment files. Deployed at `https://ragetoreply.tech`. | 505 backend tests, tsc, lint, hosted build, HTTP smoke tests and external HTTPS checks passed. Teammates signed in from their own computers. Deployed isolation check pending. | `feature/invite-auth` |
| 2026-11-21 | WEB-06 | Reused the processing mascot for interactive emotion release and synchronized it with generation. | TypeScript, lint, build and Chrome HTTP fixture acceptance passed. | Uncommitted |

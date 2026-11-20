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
| WEB-01 | Frontend & Backend Integration | P0 | TODO | None | Build a testable version with the latest frontend and backend |
| WEB-02 | Real Claude API Integration | P0 | TODO | WEB-01 | Verify live rewriting, receipts, and error handling |
| WEB-03 | Web Deployment & Hosting | P0 | TODO | WEB-01, parallel with WEB-02 | Provide HTTPS access for invited teammates |
| WEB-04 | End-to-End Testing & Demo Validation | P0 | TODO | WEB-02, WEB-03 | Verify on another computer and rehearse the two-minute demo |

**Status values** — `TODO` Pending, `IN PROGRESS` Underway, `BLOCKED` Waiting on a specific blocker, `DONE` Acceptance criteria verified. Roadmap statuses apply to the latest combined version. Earlier Mock AI results are in the [WEB-01 local baseline](#web-01--local-integration-baseline).

**Dependency order** — WEB-01 → WEB-02 and WEB-03 (in parallel) → WEB-04.

### WEB-01 — Frontend & Backend Integration

**Status** — TODO. **Dependencies** — None.

**Objective** — Integrate the latest `irene/frontend` and `origin/main` code into one testable version.

**Checklist**

- [ ] Integrate the Next.js frontend and FastAPI backend.
- [ ] Verify compatibility between the API contract, shared API client, and backend routes.
- [ ] Preserve reply generation, Memory, Receipts, and existing Slack import.
- [ ] Resolve Git conflicts while preserving team changes.
- [ ] Run the frontend build, lint, TypeScript, backend tests, and browser E2E on the same version.

**Acceptance Criteria**

- [ ] Frontend and backend work together on the integrated version.
- [ ] The core web workflow passes browser E2E.
- [ ] No known critical regressions remain.

**Test Results** — The latest combined version is pending. The 435 backend tests and Mock AI browser E2E apply to the earlier local baseline.

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

**Status** — TODO. **Dependencies** — WEB-01. Can run in parallel with WEB-02.

**Objective** — Provide invited teammates with HTTPS access to the web app.

**Checklist**

- [ ] Deploy the Next.js frontend and FastAPI backend.
- [ ] Configure HTTPS, API routing, and environment variables.
- [ ] Store the Claude API key in server-side secret management.
- [ ] Configure CORS, allowed hosts, and access controls for invited users.
- [ ] Add basic rate limiting, API cost controls, and health checks.
- [ ] Verify deployed API connectivity and backend availability.

**Acceptance Criteria**

- [ ] Invited teammates can open the site without installing Python or Node.js or starting a local server.
- [ ] The deployed frontend and backend communicate successfully.
- [ ] API credentials are absent from the browser bundle and repository.
- [ ] Invited-user access controls pass verification. The local single-user identity mechanism remains limited to the local demo.

**Test Results** — HTTPS deployment, access control, and network checks are pending.

**Blockers** — Requires WEB-01 acceptance and a confirmed hosting and invite-access setup.

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

## History

<details>
<summary>View TASK 1, TASK 2, the local integration baseline, and frontend follow-up</summary>

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
| 2026-11-21 | Tracker organization | Moved previous tasks and verification into expandable history and retained the roadmap and Change Log. | Markdown formatting checked. | Uncommitted |
| 2026-11-21 | Handoff guide | Added branch baselines, the next task, acceptance steps, and progress update instructions. | Markdown formatting checked. | Uncommitted |

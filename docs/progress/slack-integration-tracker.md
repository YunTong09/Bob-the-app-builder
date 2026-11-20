# Rage-to-Reply Slack Integration Tracker

## Progress Dashboard

| Metric | Value |
| --- | --- |
| Overall Progress | **14.3%** (1 / 7) |
| Completed Tasks | 1 · TASK-04 |
| In Progress Tasks | 1 · TASK-03 |
| Blocked Tasks | 1 · TASK-01 |
| Current Priority | Unblock the TASK-01 connection test |
| Next Recommended Task | Develop TASK-02 (shortcut that opens the TASK-03 modal) and wire the TASK-03 submission handler. Verify the combined flow in Slack after TASK-01. |
| Last Updated | 2026-11-21 (Australia/Brisbane) |

`Progress = DONE Tasks / 7 × 100%`. Count tasks once they are implemented and have passed acceptance.

## Goal and Current State

This phase delivers a **mock demo in a native Slack modal** using Slack Bolt for JavaScript with TypeScript, Socket Mode, a Message Shortcut, and Block Kit. The flow is **Slack Message → Message Shortcut → Input Modal → Mock Rewrite → Result Modal**. The demo shows its result in the modal and runs without a live Claude API, a memory database, or automatic Slack posting. Rewriting directly in Slack's composer is a later integration.

- At the initial review, local `main` was at `4fc1fcd` with a clean working tree, one commit behind the fetched `origin/main`. Both refs later reached `4ac176e`. The repo contains a Next.js prototype and `src/lib/mock.ts`. TASK-01 added the Slack Bolt entry point. Modal handlers are tracked in later tasks.
- Commit `4ac176e` added a Python/FastAPI backend. `backend/api/app.py` defines `POST /api/reply/generate`, and the backend includes a mock model and API fixtures. The source was reviewed in Git and the backend files were confirmed in the working tree. The API has yet to be run or connected to Slack. The web mock and Python fixtures provide reference material for this phase. Slack uses the mock adapter, with the Python API planned for later.
- See the [API Contract](../API_CONTRACT.md), [Architecture](../ARCHITECTURE.md), [Product Spec](../PRODUCT_SPEC.md), and [Frontend Contract](../FRONTEND_CONTRACT.md). The tracker covers the Slack mock demo. The linked documents own their respective requirements.

## Dependency Order and Current Progress

| Order | Task | Needed to Start | Needed for Full Acceptance | Status |
| --- | --- | --- | --- | --- |
| 1a | TASK-01 · Project Setup & Slack Connection | Existing project | Test app, valid tokens, and Socket Mode | BLOCKED |
| 1b | TASK-04 · Mock AI Rewrite Service | API Contract and synthetic fixtures | Offline checks of the fixed reply, tone, and evidence | DONE |
| 2a | TASK-02 · Slack Message Shortcut | Existing Bolt entry point from TASK-01 and a minimal modal | Verified live connection from TASK-01 | TODO |
| 2b | TASK-03 · Input Modal | Start now with a synthetic manager message | Connect TASK-02 for the live Slack flow | IN PROGRESS |
| 4 | TASK-05 · Processing & Result Modal | Use fixtures to build the result view | TASK-03 form submission and TASK-04 mock | TODO |
| 5 | TASK-06 · Error Handling & Retry | Prepare failure cases | Working form, mock, and result flow from TASK-03, TASK-04, and TASK-05 | TODO |
| 6 | TASK-07 · Team Testing & Demo Validation | Test workspace and teammate account | TASK-01 through TASK-06 | TODO |

TASK-02 and TASK-03 can be developed and tested offline in parallel. The live integration acceptance order is **TASK-01 → TASK-02 → TASK-03 → TASK-05 → TASK-06 → TASK-07**. TASK-04 can be developed and accepted independently ahead of TASK-05 integration. TASK-02 and TASK-04 have no dependency on each other. The TASK-02 handler can be tested with a synthetic payload now. The live shortcut and modal test requires a verified Slack connection.

**Work completed so far**

- TASK-01 added `slack/app.mts` and the Socket Mode start and type-check commands. Git ignores the local credentials file. The Slack type check and offline checks for missing and malformed credentials passed. Live connection verification is pending.
- TASK-04 reuses a synthetic Python API response fixture and passed offline acceptance.
- TASK-03 added `slack/input-modal.mts` (modal view, validation, and submission handler). Offline payload checks passed. Live Slack verification and registration in `slack/app.mts` are pending.

### TASK-01 · Project Setup & Slack Connection

**Status:** BLOCKED

**Objective:** Establish a TypeScript Slack Bolt entry point that can connect to a test workspace.

**Implementation Checklist:**

- [x] Review the existing project, dependencies, and Git baseline.
- [x] Add the Bolt TypeScript entry point and commands for startup and type checking.
- [x] Enable Socket Mode in the app, define the environment variables, and confirm Git ignores local credentials.
- [ ] Confirm the test app is installed, Socket Mode is enabled in Slack, and valid credentials are available.
- [ ] Verify a live test workspace connection and record the result with credentials redacted.

**Acceptance Criteria:**

- Starting the test app establishes a Socket Mode connection.
- Missing environment variables cause startup to fail promptly, with token values excluded from output.

**Files:** Added `slack/app.mts` and updated `package.json`, `package-lock.json`, `.env.example`, and this tracker.

**Dependencies:** Live acceptance requires a Slack app installed in a test workspace.

**Verification:**

- `npm run slack:typecheck` and `node --check slack/app.mts` passed on Node.js 24. `npm ls @slack/bolt --depth=0` reported Bolt 5.1.0.
- With empty or malformed test values, `npm run slack:start` loaded Bolt, printed the required variable names, and exited with code 1.
- `git check-ignore -v .env.slack.local` confirmed the local credentials file is ignored.
- The root-project `tsc --noEmit --incremental false` check was stopped before it returned a result. The Slack-specific check completed.
- The live Socket Mode test is pending.

**Blockers:** `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` were unavailable in the environment and local env file at verification time. Installation and Socket Mode settings in Slack remain unconfirmed.

**Notes:** Node.js 24 runs the TypeScript entry point using the root npm dependencies. The process runs independently of the web UI and Python. Set the test app's bot token and app-level token with `connections:write` in the environment or the Git-ignored `.env.slack.local`, then run `npm run slack:start` from the project root. The entry point waits for bot token verification before starting Socket Mode. [Slack Socket Mode setup](https://docs.slack.dev/tools/bolt-js/concepts/socket-mode/)

### TASK-02 · Slack Message Shortcut

**Status:** TODO

**Objective:** Open the Rage-to-Reply modal from a specific Slack message.

**Implementation Checklist:**

- [ ] Configure a Message Shortcut with a stable callback ID.
- [ ] Read the selected message and the necessary workspace, user, conversation, and message identifiers.
- [ ] Acknowledge the interaction promptly and open the modal with the trigger ID.

**Acceptance Criteria:**

- Starting the shortcut from a message menu opens the modal with the exact selected message.
- Acknowledge within Slack's three-second window. The selected message stays in the interaction and is excluded from automatic posting and memory storage.

**Files:** Slack handler and manifest paths are pending. See `docs/FRONTEND_CONTRACT.md` for the original flow.

**Dependencies:** Development can use the TASK-01 Bolt entry point and a synthetic payload. Live acceptance requires TASK-01's verified connection. A minimal modal is enough for the shortcut test. TASK-03 adds the full form.

**Verification:** An `rg` search found no shortcut handler in the files reviewed. Slack interaction testing is pending.

**Blockers:** Live acceptance awaits TASK-01.

**Notes:** Use only the explicitly selected message as context.

### TASK-03 · Input Modal

**Status:** IN PROGRESS

**Objective:** Collect the draft and tone in a native Slack modal.

**Implementation Checklist:**

- [x] Show the selected manager message and a multiline draft field using Block Kit.
- [x] Provide Diplomatic, Neutral, and Assertive options plus a Rewrite action.
- [x] Validate blank input, length, and allowed tone values.
- [ ] Register `INPUT_MODAL_CALLBACK_ID` with `handleInputSubmission` in the Bolt app and verify it live (needs TASK-01 and TASK-02).

**Acceptance Criteria:**

- A valid submission yields the original manager message, draft, and selected tone.
- Invalid or blank input shows an inline error and preserves the user's input.

**Files:** Added `slack/input-modal.mts` (`buildInputModal`, `parseInputSubmission`, `handleInputSubmission`). Its submission handler continues into `showRewriteInModal` from `slack/rewrite-modal.mts`. See `docs/API_CONTRACT.md` for fields and tones.

**Dependencies:** The input view has no prerequisite for offline development or testing. Live acceptance from message selection through form submission requires TASK-02 to call `buildInputModal({ managerMessage })` with the trigger ID, and the handler registration in `slack/app.mts`.

**Verification:**

- `tsc --noEmit --strict ... slack/app.mts slack/rewrite.mts slack/rewrite-modal.mts slack/input-modal.mts` passed. `npm run slack:typecheck` cannot expand `slack/*.mts` on Windows cmd, so the files were listed explicitly.
- An offline Node.js script with synthetic payloads confirmed: a valid submission returns `{ managerMessage, employeeDraft, tone }` for each tone. Blank and whitespace-only drafts, drafts over 3,000 characters, unknown or missing tones, and a missing manager message return inline errors. The draft is not written to `private_metadata`. The initial draft and tone are restored when the view is rebuilt. Invalid input skips the rewrite service and acks `response_action: "errors"`. Valid input acks the processing view and calls `views.update` once.
- Not tested: a live Slack modal submission, and whether Slack preserves typed input on an `errors` response.

**Blockers:** None for offline development. Live Slack acceptance depends on TASK-01 and TASK-02.

**Notes:** Slack caps `plain_text_input` `max_length`, section text, and `private_metadata` at 3,000 characters, which is below the API Contract's 10,000. The modal enforces 3,000, and `buildInputModal` throws a `RangeError` for a longer selected message. TASK-02 must handle that case. The selected manager message travels in `private_metadata`; the draft stays in the interaction only.

### TASK-04 · Mock AI Rewrite Service

**Status:** DONE

**Objective:** Provide a deterministic standalone mock with an interface that can later use the Python API.

**Implementation Checklist:**

- [x] Define a replaceable rewrite service interface for Slack callers.
- [x] Reuse a synthetic case that returns a fixed rewrite and one evidence item that supports its associated claim.
- [x] Support offline testing and a controllable failure for TASK-06.

**Acceptance Criteria:**

- The same test input returns a fixed result. The selected tone remains available to the UI.
- The mock works without a Claude key, Python server, or memory database.

**Files:** Added `slack/rewrite.mts`, updated `package.json` and this tracker, and reused `backend/fixtures/generate_response.json`.

**Dependencies:** The API Contract and synthetic fixtures are sufficient for independent development and offline acceptance. TASK-05 integrates the service.

**Verification:** `npm run slack:typecheck` passed. Offline assertions using `env -i PATH="$PATH" node --input-type=module` confirmed that all three tone requests produce the fixed result, the input retains the tone, each call returns independent data, the response includes one synthetic evidence item for the shared-document claim, and forced failure works.

**Blockers:** None identified.

**Notes:** The mock reply text is fixed. TASK-05 retains the selected tone from the request. The response follows the API Contract. Slack modal integration and live API acceptance remain pending.

### TASK-05 · Processing & Result Modal

**Status:** TODO

**Objective:** Show processing and the rewrite result in sequence in the same modal.

**Implementation Checklist:**

- [ ] Acknowledge the submission and switch the modal to a processing state.
- [ ] Update the same modal with the professional reply, selected tone, and one synthetic evidence item.
- [ ] Connect the service to the view states and keep the reply and evidence in distinct sections.

**Acceptance Criteria:**

- A deliberately delayed mock displays the processing state, followed by the reply, correct tone, and evidence in the same modal.
- The interaction stays in the modal without posting to Slack or writing to the original composer.

**Files:** Slack view and handler paths are pending. See `src/app/page.tsx` and `src/components/ComparePanel.tsx` for the web prototype.

**Dependencies:** Build the result view with a fixture. Full acceptance requires the TASK-03 submission flow and the TASK-04 mock adapter.

**Verification:** Reviewed the web result entry point and Slack-related file list. Slack modal update testing is pending.

**Blockers:** Full acceptance awaits the input modal and mock integration.

**Notes:** The web prototype's Copy reply button is outside this demo flow.

### TASK-06 · Error Handling & Retry

**Status:** TODO

**Objective:** Recover from rewrite failures and handle repeated or cancelled interactions.

**Implementation Checklist:**

- [ ] Handle blank input and mock service failures.
- [ ] Provide Retry and preserve the draft and tone.
- [ ] Prevent repeated submissions from launching duplicate rewrites.
- [ ] Handle closure and cancellation, and ignore late results for cancelled interactions.

**Acceptance Criteria:**

- Blank input skips the service. After a simulated failure, the user can retry with the original draft and tone.
- Repeated submission triggers one rewrite. A result arriving after cancellation leaves the modal untouched.

**Files:** Slack handler, view, and test file paths are pending. See `src/app/page.tsx` for the web prototype's error state.

**Dependencies:** TASK-03, TASK-04, and TASK-05.

**Verification:** Reviewed the web error state and found no Slack retry or cancellation flow in the files reviewed. Failure and duplicate-submission tests are pending.

**Blockers:** Full acceptance awaits the Slack result flow.

**Notes:** Keep retry state within the interaction. On cancellation, clean up or expire short-lived state. Keep raw drafts out of logs.

### TASK-07 · Team Testing & Demo Validation

**Status:** TODO

**Objective:** Have a teammate complete the Slack demo in a test workspace within two minutes.

**Implementation Checklist:**

- [ ] Prepare the installed app, synthetic manager message, and scenarios in the test workspace.
- [ ] Ask at least one teammate to complete the full flow using their own Slack account.
- [ ] Time the demo, test at least one retry, and record the outcome and known limitations.

**Acceptance Criteria:**

- A teammate opens the shortcut from the specified message and sees the private mock result, tone, and evidence within two minutes.
- The test record identifies the mock scope, pending live API verification, and which installation was tested.

**Files:** This tracker. Test script and other test record paths are pending.

**Dependencies:** TASK-01 through TASK-06.

**Verification:** Team testing and timing in Slack are pending.

**Blockers:** The test workspace and teammate participation remain unconfirmed.

**Notes:** Acceptance in one test workspace covers that installation only.

## AI Update Rules

1. Read this tracker before starting Slack integration work. Review the dashboard, task status, and dependencies.
2. Reuse work that has passed acceptance. Preserve teammate changes.
3. After making changes, run the relevant tests and update status, checklists, files, and the actual commands and results. Identify any pending verification.
4. Use only `TODO`, `IN PROGRESS`, `BLOCKED`, and `DONE`. Mark a task `DONE` only after its acceptance criteria pass. Record concrete blockers under **Blockers** and ordinary prerequisites under **Dependencies**.
5. Update the dashboard counts, date, and next recommended task, then add a Change Log entry.
6. Record a test as passed only if it ran successfully. Track mock acceptance and live API integration separately.
7. Keep changes within the task scope and keep API keys, Slack tokens, and other secrets out of documentation and logs.

## Change Log

| Date | Task ID | Summary | Verification | Git Commit |
| --- | --- | --- | --- | --- |
| 2026-11-21 | TASK-01 through TASK-07 | Created the baseline and seven tasks. Reviewed the repo and confirmed FastAPI source on `origin/main`. | Read-only review using `git status --short --branch`, `git ls-files`, `git diff --name-status HEAD..origin/main`, `git show origin/main:backend/api/app.py`, and source searches. Functional testing was pending. | Tracker was uncommitted at the time. Reviewed `4fc1fcd` and `4ac176e`. |
| 2026-11-21 | TASK-01 | Added the TypeScript Slack Bolt entry point, Socket Mode startup command, and env examples. | Type and missing-credential checks passed. Git ignores local credentials. The live test was pending for lack of credentials. | Uncommitted at the time. |
| 2026-11-21 | TASK-01 through TASK-07 | Reordered the overview by integration dependencies, identified work that can run in parallel, and recorded completed work. | Compared the tracker with local commit `84a0fd0`. Documentation update based on existing verification records. | Uncommitted at the time. |
| 2026-11-21 | TASK-04 | Added the standalone rewrite interface, fixture-based mock, and controllable failure mode. | Slack type check and offline assertions passed. Modal and live API integration remained pending. | Uncommitted at the time. |
| 2026-11-21 | TASK-03 | Added the Block Kit input modal, validation, and submission handler that continues into the TASK-05 modal. | Type check passed and offline payload assertions passed. Live Slack modal test and app registration pending. | Uncommitted at the time. |

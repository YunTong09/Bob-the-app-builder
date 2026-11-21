# Rage-to-Reply

Rage-to-Reply is a Web App that turns an employee's private draft into an editable professional reply and grounds claims in imported conversation history. The repository contains a Next.js browser prototype and a FastAPI backend. The prototype runs with synthetic data by default. The browser can use a local FastAPI instance or the built-in mock. Authenticated hosting is a later milestone.

## Documentation

| File | Purpose |
| --- | --- |
| [PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md) | Defines product behaviour, feature priorities, MVP scope and acceptance criteria. |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Explains the technology stack, component responsibilities, data flow and security boundaries. |
| [API_CONTRACT.md](docs/API_CONTRACT.md) | Defines endpoint behaviour, request and response schemas, validation rules and errors. |
| [FRONTEND_CONTRACT.md](docs/FRONTEND_CONTRACT.md) | Defines the browser workspace, input and result states, privacy handling and visual design. |
| [Hosted deployment guide](deploy/gce/README.md) | Puts the Web App on a Compute Engine VM at an HTTPS domain with invite-code sign-in. |
| [Slack prototype tracker](docs/progress/slack-integration-tracker.md) | Historical record of the Slack modal prototype. |

## Feature priorities

| Priority | Feature | Purpose |
| --- | --- | --- |
| P0 | Rage-to-Professional | Preserve intent while rewriting in Diplomatic, Neutral or Assertive tone; regenerate from the same input without accepting blame or inventing facts. |
| P0 | Manager Message Interpreter | Identify requests, possible actions, missing information and misunderstandings, with interpretations clearly labelled. |
| P0 | Replies with Receipts | Find supporting evidence in imported conversations and show it separately with available source references. |
| P0 | Communication Memory | Import, review and delete history; leave missing metadata blank and do not save emotional drafts by default. |
| P1 | Enhanced Tone Adjustment | Adjust tone beside a generated reply while preserving facts. |
| P1 | Communication Preferences | Save user-controlled tone, response length, formality and directness preferences. |

The [product specification](docs/PRODUCT_SPEC.md#3-core-application-features) owns the full requirements and acceptance criteria. Complete the P0 workflow before adding the two P1 features.

## Run the current browser prototype

```bash
npm install
copy .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

Both browser pages use the same frontend API client. The default browser mock works without FastAPI. To test the HTTP integration with FastAPI's mock AI on macOS or Linux, start these in separate terminals after installing the backend dependencies:

```bash
R2R_WEB_ORIGIN=http://127.0.0.1:3000 R2R_AI_MODE=mock python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
NEXT_PUBLIC_R2R_MOCK=false NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1
```

Open `http://127.0.0.1:3000`. Set the same variables in PowerShell with `$env:NAME="value"` before starting the corresponding command. The browser address, including its port, must exactly match `R2R_WEB_ORIGIN` on the backend. Rebuild or restart Next.js after changing its public variables. Both servers are loopback-only for this demo.

Useful commands:

```bash
npm run lint
npm run build
```

The browser's root `.env.local` is for public frontend settings such as `NEXT_PUBLIC_R2R_MOCK` and `NEXT_PUBLIC_API_BASE_URL`. Configure Claude separately in `backend/.env` as described below. Never put API keys or Slack tokens in a `NEXT_PUBLIC_` variable.

## FastAPI backend (P0 API, in progress)

`backend/` implements the P0 routes in [API_CONTRACT.md](docs/API_CONTRACT.md) with FastAPI and Pydantic, a SQLite + FTS5 memory store and Claude-based analysis, evidence assessment and drafting. Both browser pages can use the local routes through the shared frontend API client.

Windows setup, from the project root:

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
if (-not (Test-Path -LiteralPath backend/.env)) { Copy-Item -LiteralPath backend/.env.example -Destination backend/.env }
```

Create the virtual environment, install dependencies and copy the template once. Fill in `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` in the local, Git-ignored `backend/.env`, and keep `R2R_AI_MODE=claude` for real replies. The [backend environment template](backend/.env.example) sets `R2R_WEB_ORIGIN=http://127.0.0.1:3000` for the local browser demo.

FastAPI automatically loads **only `backend/.env`**. Values already set in the process environment take precedence. Restart the backend after changing configuration. The root `.env.local` and Socket Mode's `.env.slack.local` are separate files.

Start the loopback-only backend:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

For explicit mock replies, set `R2R_AI_MODE=mock` in `backend/.env` or set `$env:R2R_AI_MODE="mock"` before starting the backend. This still uses SQLite and the validator and makes no Claude calls. Tests mock Claude:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend
```

On macOS/Linux, use `backend/.venv/bin/python` for the Python commands.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ANTHROPIC_MODEL` | none (required for Claude) | Model ID supported by your Anthropic account |
| `ANTHROPIC_API_KEY` | none | Claude credentials; server-side only |
| `R2R_AI_MODE` | `claude` | `mock` for the explicit local mock; never used as a fallback |
| `R2R_WEB_ORIGIN` | unset; local template uses `http://127.0.0.1:3000` | Exact browser origin permitted for the local HTTP demo |
| `R2R_DB_PATH` | `backend/data/rage_to_reply.sqlite3` | SQLite file |
| `R2R_MODEL_TIMEOUT_SECONDS` | `30` | Per-request Claude timeout (`504 MODEL_TIMEOUT`) |
| `R2R_MODEL_EFFORT` | `medium` | Claude effort level |
| `R2R_REFUSAL_FALLBACK` | `default` | Server-side refusal fallback; `off` to disable |
| `R2R_SERVICES` | `real` | `stub` uses the in-memory development doubles |
| `R2R_IDENTITY_MODE` | `demo_local` | `invite_code` for the hosted site (variables below) |
| `R2R_PUBLIC_ORIGIN` | none (required for `invite_code`) | Public `https://` origin of the hosted site |
| `R2R_INVITES` | none (required for `invite_code`) | `label:sha256` entries, one per invited person |
| `R2R_SESSION_SECRET` | none (required for `invite_code`) | At least 32 characters; signs session cookies |
| `R2R_SESSION_TTL_HOURS` | `168` | Session lifetime in invite mode |
| `R2R_GENERATE_LIMIT_PER_HOUR` | `30` | Generations per invite per hour in invite mode |
| `R2R_LOGIN_FAILURES_PER_15_MIN` | `10` | Failed sign-ins per address before a lockout in invite mode |

- The default identity is a single-user demo owner. It accepts direct loopback connections only and rejects proxied requests. Do not bind it to `0.0.0.0` or put it behind a shared proxy.
- `invite_code` mode is for the hosted site behind the HTTPS gateway. Each invited person signs in with their own code and gets separate history. Create codes with `backend/.venv/bin/python -m backend.api.invite_auth <label>`; this prints the code to share and its `R2R_INVITES` entry. Follow the [deployment guide](deploy/gce/README.md). Other `R2R_IDENTITY_MODE` values refuse to start.
- Startup fails if `ANTHROPIC_MODEL` is missing in Claude mode; it never falls back to mock replies. The service interfaces are in `backend/application/ports.py`.
- To run the API tests against SQLite instead of the in-memory double, set `R2R_TEST_MEMORY_FACTORY=backend.tests.sqlite_factory:make`.
- Synthetic request and response fixtures are in `backend/fixtures/`.

### Preview and import a Slack test channel

1. Create a Slack app in a test workspace. Add the bot scope `channels:history` for a public channel or `groups:history` for a private channel, then install the app. Reinstall it after changing scopes.
2. Invite the bot to one test channel containing synthetic messages. Copy its channel ID and use the installed app's `xoxb-` bot token. This history reader does not require an `xapp-` Socket Mode token.
3. From the project root, set the FastAPI process environment and start the single-user demo in PowerShell:

```powershell
$slackTokenInput = Read-Host 'Slack bot token' -AsSecureString
$env:SLACK_BOT_TOKEN = [System.Net.NetworkCredential]::new('', $slackTokenInput).Password
$env:R2R_SLACK_CHANNEL_ID = 'C0123456789' # Replace with the one allowed test channel
$env:R2R_AI_MODE = 'mock'
.\backend\.venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

These process environment values override `backend/.env`. You may instead save the optional `SLACK_BOT_TOKEN` and `R2R_SLACK_CHANNEL_ID` in `backend/.env` and restart FastAPI. Socket Mode's `npm run slack:start` continues to use `.env.slack.local` separately. The `mock` setting avoids needing Claude credentials for this import workflow; the Slack history request still uses the real Slack API.

Keep the server running and open a second PowerShell terminal. Replace the channel ID below with the same allowed channel configured in the server terminal, then request a preview:

```powershell
$slackPreviewBody = @{ channelId = 'C0123456789'; limit = 20 } | ConvertTo-Json
$slackPreview = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/slack/preview' -ContentType 'application/json' -Body $slackPreviewBody
$slackPreview | ConvertTo-Json -Depth 10
```

Previewing does not save messages. Review the returned messages and submit only the ones you choose through the existing memory-import operation. The [Slack preview contract](docs/API_CONTRACT.md#slack-channel-preview-single-user-demo-extension) documents request fields, pagination, errors and how selected messages use the existing import operation. Missing metadata stays missing, and messages become searchable only after import.

This backend reader fetches parent channel messages; it does not fetch thread replies or import files, and it cannot read ordinary direct messages between other people using the bot token. It retains the existing direct-loopback demo identity and does not add a login, shared deployment or frontend integration.

## Browser environment variables

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_R2R_MOCK` | Browser mock is enabled unless set to `false`. |
| `NEXT_PUBLIC_API_BASE_URL` | Required in HTTP mode; use `http://127.0.0.1:8000` for the local backend, or the site's `https://` origin when hosted. |
| `NEXT_PUBLIC_R2R_AUTH` | Set to `invite` only for the hosted build. Visitors without a session are sent to `/login`. |

For real backend replies, set `NEXT_PUBLIC_R2R_MOCK=false` and `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000` in the project-root `.env.local`, then restart or rebuild Next.js. Open the browser at `http://127.0.0.1:3000` to match the backend template's allowed origin. Keep backend credentials in `backend/.env`; frontend public variables are visible to browser users.

## API contract

See [API_CONTRACT.md](docs/API_CONTRACT.md) for the target endpoints, request and response schemas, validation rules, errors and synthetic examples. FastAPI serves the contracted routes. The Web App client calls them directly in HTTP mode. The legacy Next.js routes remain available to older callers.

## Who owns what

The following paths describe the current prototype. [AGENTS.md](AGENTS.md#3-team-ownership) defines development ownership and handoffs for the target implementation.

- **A — Frontend:** browser routes in `src/app/` and feature modules, styles and API clients in `src/frontend/`
- **B — Backend/AI:** `src/lib/claude.ts`, `src/lib/prompts.ts`, `src/lib/schema.ts`
- **C — Cloud/integration:** `src/lib/memoryStore.ts`, deployment, seed data, and API route wiring

## Privacy and safety notes

The employee's raw text is only passed through the current analysis request. It is not added to the memory store, written to a file, or logged. The Claude system prompt also requires polished replies to use only facts present in the raw text or supplied memory records.

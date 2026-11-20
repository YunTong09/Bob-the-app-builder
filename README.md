# Rage-to-Reply

Rage-to-Reply is a Web App that turns an employee's private draft into an editable professional reply and grounds claims in imported conversation history. The repository contains a Next.js browser prototype and a FastAPI backend. The prototype runs with synthetic data by default. Connecting the browser to FastAPI and deploying authenticated access are the next integration milestones.

## Documentation

| File | Purpose |
| --- | --- |
| [PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md) | Defines product behaviour, feature priorities, MVP scope and acceptance criteria. |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Explains the technology stack, component responsibilities, data flow and security boundaries. |
| [API_CONTRACT.md](docs/API_CONTRACT.md) | Defines endpoint behaviour, request and response schemas, validation rules and errors. |
| [FRONTEND_CONTRACT.md](docs/FRONTEND_CONTRACT.md) | Defines the browser workspace, input and result states, privacy handling and visual design. |
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

Useful commands:

```bash
npm run lint
npm run build
```

Set `USE_MOCK=false` and provide `ANTHROPIC_API_KEY` to use Claude. `ANTHROPIC_MODEL` is required for the real API path and is never hardcoded in application code.

## FastAPI backend (P0 API, in progress)

`backend/` implements the P0 routes in [API_CONTRACT.md](docs/API_CONTRACT.md) with FastAPI and Pydantic, a SQLite + FTS5 memory store and Claude-based analysis, evidence assessment and drafting. The Next.js prototype above is unchanged.

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements-dev.txt   # Windows
# backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt     # macOS/Linux

# Tests (Claude mocked)
backend/.venv/Scripts/python -m pytest backend

# Local demo server with Claude, loopback only
ANTHROPIC_API_KEY=... ANTHROPIC_MODEL=claude-opus-5-5 backend/.venv/Scripts/python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000

# Explicit mock mode: real SQLite and validator, canned "[Mock reply]" output, no API calls
R2R_AI_MODE=mock backend/.venv/Scripts/python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `ANTHROPIC_MODEL` | none (required for Claude) | Model ID, e.g. `claude-opus-5-5` |
| `ANTHROPIC_API_KEY` | none | Claude credentials; server-side only |
| `R2R_AI_MODE` | `claude` | `mock` for the explicit local mock; never used as a fallback |
| `R2R_DB_PATH` | `backend/data/rage_to_reply.sqlite3` | SQLite file |
| `R2R_MODEL_TIMEOUT_SECONDS` | `30` | Per-request Claude timeout (`504 MODEL_TIMEOUT`) |
| `R2R_MODEL_EFFORT` | `medium` | Claude effort level |
| `R2R_REFUSAL_FALLBACK` | `default` | Server-side refusal fallback; `off` to disable |
| `R2R_SERVICES` | `real` | `stub` uses the in-memory development doubles |

- The only identity mode is a single-user demo owner. It accepts direct loopback connections only and rejects proxied requests. Do not bind it to `0.0.0.0` or put it behind a shared proxy. Any other `R2R_IDENTITY_MODE` refuses to start until authentication is agreed.
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

FastAPI reads these environment variables; it does not automatically load `.env.local` or `.env.slack.local`. The `mock` setting avoids needing Claude credentials for this import workflow; the Slack history request still uses the real Slack API.

Keep the server running and open a second PowerShell terminal. Replace the channel ID below with the same allowed channel configured in the server terminal, then request a preview:

```powershell
$slackPreviewBody = @{ channelId = 'C0123456789'; limit = 20 } | ConvertTo-Json
$slackPreview = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/slack/preview' -ContentType 'application/json' -Body $slackPreviewBody
$slackPreview | ConvertTo-Json -Depth 10
```

Previewing does not save messages. Review the returned messages and submit only the ones you choose through the existing memory-import operation. The [Slack preview contract](docs/API_CONTRACT.md#slack-channel-preview-single-user-demo-extension) documents request fields, pagination, errors and how selected messages use the existing import operation. Missing metadata stays missing, and messages become searchable only after import.

This backend reader fetches parent channel messages; it does not fetch thread replies or import files, and it cannot read ordinary direct messages between other people using the bot token. It retains the existing direct-loopback demo identity and does not add a login, shared deployment or frontend integration.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | Claude API key. If absent, the mock path is used. |
| `ANTHROPIC_MODEL` | Model name passed to Anthropic. |
| `USE_MOCK` | Set to `true` for local canned responses. |

## API contract

See [API_CONTRACT.md](docs/API_CONTRACT.md) for the target endpoints, request and response schemas, validation rules, errors and synthetic examples. FastAPI serves the contracted routes. The Next.js prototype still uses its legacy endpoints until Web App integration is complete.

## Who owns what

The following paths describe the current prototype. [AGENTS.md](AGENTS.md#3-team-ownership) defines development ownership and handoffs for the target implementation.

- **A — Frontend:** `src/components` and `src/app/page.tsx`
- **B — Backend/AI:** `src/lib/claude.ts`, `src/lib/prompts.ts`, `src/lib/schema.ts`
- **C — Cloud/integration:** `src/lib/memoryStore.ts`, deployment, seed data, and API route wiring

## Privacy and safety notes

The employee's raw text is only passed through the current analysis request. It is not added to the memory store, written to a file, or logged. The Claude system prompt also requires polished replies to use only facts present in the raw text or supplied memory records.

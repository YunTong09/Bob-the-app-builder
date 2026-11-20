# Rage-to-Reply

Rage-to-Reply is a Web App that turns an employee's private draft into an editable professional reply and grounds claims in imported conversation history. The repository contains a Next.js browser prototype and a FastAPI backend. The prototype runs with synthetic data by default. The browser can use a local FastAPI instance or the built-in mock. Authenticated hosting is a later milestone.

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

Set `USE_MOCK=false` and provide `ANTHROPIC_API_KEY` to use Claude. `ANTHROPIC_MODEL` is required for the real API path and is never hardcoded in application code.

## FastAPI backend (P0 API, in progress)

`backend/` implements the P0 routes in [API_CONTRACT.md](docs/API_CONTRACT.md) with FastAPI and Pydantic, a SQLite + FTS5 memory store and Claude-based analysis, evidence assessment and drafting. Both browser pages can use the local routes through the shared frontend API client.

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

## Environment variables

| Variable | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | Claude API key. If absent, the mock path is used. |
| `ANTHROPIC_MODEL` | Model name passed to Anthropic. |
| `USE_MOCK` | Set to `true` for local canned responses. |

## API contract

See [API_CONTRACT.md](docs/API_CONTRACT.md) for the target endpoints, request and response schemas, validation rules, errors and synthetic examples. FastAPI serves the contracted routes. The Web App client calls them directly in HTTP mode. The legacy Next.js routes remain available to older callers.

## Who owns what

The following paths describe the current prototype. [AGENTS.md](AGENTS.md#3-team-ownership) defines development ownership and handoffs for the target implementation.

- **A — Frontend:** browser routes in `src/app/` and feature modules, styles and API clients in `src/frontend/`
- **B — Backend/AI:** `src/lib/claude.ts`, `src/lib/prompts.ts`, `src/lib/schema.ts`
- **C — Cloud/integration:** `src/lib/memoryStore.ts`, deployment, seed data, and API route wiring

## Privacy and safety notes

The employee's raw text is only passed through the current analysis request. It is not added to the memory store, written to a file, or logged. The Claude system prompt also requires polished replies to use only facts present in the raw text or supplied memory records.

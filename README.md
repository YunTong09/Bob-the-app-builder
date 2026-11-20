# Rage-to-Reply

Rage-to-Reply turns an employee's private vent into a professional reply while preserving their intent and grounding claims in imported conversation history. The repository currently contains a Next.js prototype with seeded in-memory history and canned analysis by default, so the prototype can run without an API key. The feature list below describes the target scope, not completed implementation.

## Documentation

| File | Purpose |
| --- | --- |
| [PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md) | Defines product behaviour, feature priorities, MVP scope and acceptance criteria. |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Explains the technology stack, component responsibilities, data flow and security boundaries. |
| [API_CONTRACT.md](docs/API_CONTRACT.md) | Defines endpoint behaviour, request and response schemas, validation rules and errors. |
| [FRONTEND_CONTRACT.md](docs/FRONTEND_CONTRACT.md) | Describes the desktop reply assistant workflow, permissions, typed or spoken input, draft insertion and data handling. |

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

## Install and run

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

## Environment variables

| Variable | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | Claude API key. If absent, the mock path is used. |
| `ANTHROPIC_MODEL` | Model name passed to Anthropic. |
| `USE_MOCK` | Set to `true` for local canned responses. |

## API contract

See [API_CONTRACT.md](docs/API_CONTRACT.md) for the target endpoints, request and response schemas, validation rules, errors and synthetic examples. The current prototype routes and schemas do not yet implement that contract; integration must follow the owning document.

## Who owns what

The following paths describe the current prototype. [AGENTS.md](AGENTS.md#3-team-ownership) defines development ownership and handoffs for the target implementation.

- **A — Frontend:** `src/components` and `src/app/page.tsx`
- **B — Backend/AI:** `src/lib/claude.ts`, `src/lib/prompts.ts`, `src/lib/schema.ts`
- **C — Cloud/integration:** `src/lib/memoryStore.ts`, deployment, seed data, and API route wiring

## Privacy and safety notes

The employee's raw text is only passed through the current analysis request. It is not added to the memory store, written to a file, or logged. The Claude system prompt also requires polished replies to use only facts present in the raw text or supplied memory records.

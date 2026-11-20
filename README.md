# Rage-to-Reply

Rage-to-Reply is a small Next.js foundation for turning an employee's private vent into a short, professional reply. The current skeleton uses seeded in-memory memory records and canned analysis by default, so the full flow works without an API key.

## Documentation

| File | Purpose |
| --- | --- |
| [PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md) | Defines product behaviour, feature priorities, MVP scope and acceptance criteria. |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Explains the technology stack, component responsibilities, data flow and security boundaries. |
| [API_CONTRACT.md](docs/API_CONTRACT.md) | Defines endpoint behaviour, request and response schemas, validation rules and errors. |
| [FRONTEND_CONTRACT.md](docs/FRONTEND_CONTRACT.md) | Describes the desktop reply assistant workflow, permissions, typed or spoken input, draft insertion and data handling. |

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

`POST /api/analyze`

```json
{
  "managerId": "dave",
  "managerMessage": "I already gave you the company docs, why don't you know where the key is?",
  "employeeRawText": "The key is locked behind a password, am I supposed to guess it psychically?"
}
```

Returns:

```json
{
  "managerIntent": "Confirm whether the employee can access the key and identify what is blocking them.",
  "rageLevel": 72,
  "extractedFacts": ["The key is behind a password.", "The employee does not have the password."],
  "relatedMemories": [{ "id": "...", "text": "...", "date": "2026-11-12" }],
  "polishedReply": "Hi Dave, I don't currently have the password for the key..."
}
```

`GET /api/memory?managerId=dave` returns `MemoryEvent[]`.

`POST /api/memory` accepts `{ "managerId": "dave", "text": "...", "date": "YYYY-MM-DD" }` and returns the saved event.

`POST /api/reset` reloads `src/data/seed.json` into the in-memory store.

`MemoryEvent = { id: string, managerId: string, text: string, date: string }`

## Who owns what

- **A — Frontend:** `src/components` and `src/app/page.tsx`
- **B — Backend/AI:** `src/lib/claude.ts`, `src/lib/prompts.ts`, `src/lib/schema.ts`
- **C — Cloud/integration:** `src/lib/memoryStore.ts`, deployment, seed data, and API route wiring

## TODO

- Voice input
- Shredder animation
- Manager personality memory
- Tone selector
- Slack integration

## Privacy and safety notes

The employee's raw text is only passed through the current analysis request. It is not added to the memory store, written to a file, or logged. The Claude system prompt also requires polished replies to use only facts present in the raw text or supplied memory records.

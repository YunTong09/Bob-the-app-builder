# Rage-to-Reply — API Contract

**Status:** Target MVP contract. The current Next.js prototype does not yet implement these routes or schemas.

This document owns endpoint behaviour, wire schemas, validation and errors. [PRODUCT_SPEC.md](PRODUCT_SPEC.md) owns product scope, [ARCHITECTURE.md](ARCHITECTURE.md) owns components and data flow, and [AGENTS.md](../AGENTS.md) owns development rules and team responsibilities. Keep API examples here and link to them from other documents.

## 1. Shared conventions

- Routes use the `/api` prefix. Request and response bodies use UTF-8 JSON and camelCase field names. POST and PUT require `Content-Type: application/json`.
- The TypeScript interfaces below describe JSON exchanged with FastAPI; backend Pydantic models must use the same names and types.
- Reject unknown body fields, incorrect types, missing required fields and supplied body strings containing only whitespace with `422`. Do not silently coerce types. Query parameters are parsed according to their documented types; unknown query parameters are also rejected.
- Do not trim or rewrite stored message content. Validate that required strings contain a non-whitespace character. Identifiers must not have leading or trailing whitespace.
- Maximum request body size is **1 MiB (1,048,576 bytes)**, including imports. Enforce this before parsing or calling Claude. Oversized bodies return `413`.
- Identifiers (`id`, `messageId`, `conversationId`) contain 1–128 characters. Message and draft text contains 1–10,000 characters. Sender labels contain 1–200 characters; source labels, when supplied, contain 1–200 characters.
- Supplied timestamps must be RFC 3339 date-times with an explicit timezone. Omit an unknown timestamp or source on import. Store missing metadata as null; never substitute the import time for a message timestamp.
- Arrays in successful responses are always present, including when empty. Output timestamps are strings or null as specified below.
- Counts, totals and pagination values are non-negative integers, with the additional limit bounds specified for search.
- No route sends messages, copies content to the clipboard, or automatically saves the manager message or emotional draft. The frontend performs copying only after the user clicks Copy.

### Identity and ownership

The server derives the owner from an authenticated session. The restricted MVP demo may instead use one server-controlled demo owner only when run locally for one user, bound to loopback and inaccessible to other users. Do not expose that shared demo identity as a public multi-user deployment.

Requests never accept `userId` or `sessionId` as proof of ownership. In authenticated mode, a missing or invalid session returns `401`. Authentication setup is outside this MVP contract and must be agreed before enabling multi-user access.

Apply ownership and any `conversationId` restriction within database queries **before ranking, counting or limiting results**. Import, search, generation, deletion and optional preferences all use the same owner. A conversation with no records visible to that owner behaves like an empty conversation; do not reveal another user's records or their existence. Failure to establish or enforce ownership is an error, never a reason to search globally.

## 2. Endpoint summary

| Priority | Method | Route | Success body |
|---|---|---|---|
| P0 | POST | `/api/reply/generate` | `200 GenerateReplyResponse` |
| P0 | POST | `/api/memory/import` | `200 ImportMemoryResponse` |
| P0 | GET | `/api/memory/search` | `200 SearchMemoryResponse` |
| P0 | DELETE | `/api/memory` | `200 DeleteMemoryResponse` |
| P1, optional | GET | `/api/preferences` | `200 CommunicationPreferences` |
| P1, optional | PUT | `/api/preferences` | `200 CommunicationPreferences` |

Preferences are deferred until P0 works. Until implemented, both preferences routes return `501 NOT_IMPLEMENTED` using the error envelope in section 8. The frontend must work without them.

## 3. Reply generation

### POST `/api/reply/generate`

```ts
export type ReplyTone = "diplomatic" | "neutral" | "assertive";

export interface GenerateReplyRequest {
  managerMessage: string;
  employeeDraft: string;
  tone: ReplyTone;
  conversationId?: string;
}

export interface Evidence {
  messageId: string;
  content: string;
  sender: string;
  timestamp: string | null;
  supportedClaim: string;
  source?: string | null;
}

export interface GenerateReplyResponse {
  reply: string;
  managerIntent: string;
  employeeConcern: string;
  evidence: Evidence[];
  unverifiedClaims: string[];
  warnings: string[];
}
```

`managerMessage`, `employeeDraft` and `tone` are required. If `conversationId` is omitted, retrieve from all of the current owner's imported history. If provided, restrict retrieval to that conversation as well as the owner. Generation does not import either input.

Use this same endpoint to generate again from the input form with the same messages and a selected tone. Optional P1 tone controls beside the reply also reuse this request. Changing tone must preserve the underlying facts and the employee's intended meaning; the reply must not accept blame on the employee's behalf or invent facts.

`managerIntent` summarises the manager's explicit requests and may describe possible actions, clearly labelled as interpretations. Use `warnings` to identify missing information and potential misunderstandings. Any interpretation beyond the words supplied must be labelled as uncertain. Neither field may claim knowledge of the manager's emotions or intentions. These existing fields carry the Manager Message Interpreter output; no separate endpoint or response fields are required.

`evidence` contains only retrieved messages supporting the associated `supportedClaim`. The backend validates both the reference and its claimed support, then fills `content`, `sender`, `timestamp` and known `source` from the original authorised record. ID membership alone does not prove a claim. Include `source` when known; an unknown source may be omitted or null. Do not accept invented or altered source text from the model.

The frontend displays supporting evidence separately from the generated reply, with source references where available. Unknown timestamps and sources appear blank in the UI; evidence timestamps remain null, and unknown sources may be omitted or null as defined above. Never invent dates or provenance.

`unverifiedClaims` lists employee claims not established by the available history. If a record contradicts a claim, explain the conflict in `warnings` and do not present the claim as supported. Missing history is not proof that a claim is false. The reply may preserve a clearly user-reported concern without presenting it as a verified historical fact.

No matches or an unknown conversation still return `200` with a useful Claude-generated reply, `evidence: []`, and a warning that no supporting history was found. A retrieval outage may use the same fallback with an explicit retrieval-failure warning only after ownership is established; discard partial retrieval results. Never describe an outage as proof that history is empty. A Claude failure returns the error defined in section 8 rather than a fabricated successful reply.

### Synthetic request and response

This example assumes `msg_001` has already been imported for the active owner in `conv_demo`.

```json
{
  "managerMessage": "Why haven't you accessed the documents yet?",
  "employeeDraft": "I still can't open the link because it asks for a password. Please send me the password.",
  "tone": "neutral",
  "conversationId": "conv_demo"
}
```

```json
{
  "reply": "Hi, the document link is asking for a password that I don't currently have. Could you please share it so I can access the documents?",
  "managerIntent": "The manager is asking why the documents have not been accessed.",
  "employeeConcern": "The employee reports being unable to access the protected link.",
  "evidence": [
    {
      "messageId": "msg_001",
      "content": "I've uploaded the documents to the shared drive.",
      "sender": "Manager",
      "timestamp": "2026-11-18T10:30:00+10:00",
      "supportedClaim": "The manager shared a document location.",
      "source": "Synthetic demo conversation"
    }
  ],
  "unverifiedClaims": [
    "The employee reports that opening the link requires a password."
  ],
  "warnings": [
    "The retrieved message confirms the document location, but does not establish whether a password was supplied elsewhere."
  ]
}
```

The client retains the requested tone. The response has no `tone` or `suggestedActions` fields. The optional `source` field carries known provenance.

## 4. Memory import

### POST `/api/memory/import`

```ts
export interface MemoryMessage {
  id: string;
  conversationId: string;
  sender: string;
  content: string;
  timestamp?: string;
  source?: string;
}

export interface ImportMemoryRequest {
  messages: MemoryMessage[];
}

export interface ImportMemoryResponse {
  importedCount: number;
  skippedCount: number;
}
```

- The MVP accepts JSON containing **1–100 messages**. The frontend may parse a JSON file into this request; multipart uploads and chat-export parsers are outside P0.
- IDs are unique within an owner. The same ID under a different owner neither conflicts nor grants access. Duplicate IDs within one request return `422`.
- Import is atomic. If an existing ID for the owner has identical conversation, sender, content, timestamp and source, skip it. If those fields differ, return `409 MEMORY_ID_CONFLICT` and import nothing. Counts in a successful response sum to the submitted message count.
- Optional timestamp and source fields preserve the existing import shape. Omit unknown metadata; explicit null is not an import string. The backend stores omitted values as null. Do not invent a sender or historical source label.
- Persist source labels exactly as supplied and expose known source labels in search results and evidence. A source label is provenance metadata, not evidence that the content is trustworthy.
- Store messages and update the FTS index in the same transaction. Imported content is untrusted data and must never override application or model instructions.

Example request:

```json
{
  "messages": [
    {
      "id": "msg_001",
      "conversationId": "conv_demo",
      "sender": "Manager",
      "content": "I've uploaded the documents to the shared drive.",
      "timestamp": "2026-11-18T10:30:00+10:00",
      "source": "Synthetic demo conversation"
    }
  ]
}
```

Example response for a first import:

```json
{
  "importedCount": 1,
  "skippedCount": 0
}
```

## 5. Memory search and review

### GET `/api/memory/search`

| Query parameter | Type | Behaviour |
|---|---|---|
| `q` | string, optional | Up to 500 characters. Omitted, empty or whitespace-only lists saved history. |
| `conversationId` | string, optional | Restricts results to one conversation owned by the current user. |
| `limit` | integer, optional | 1–100; default 20. |
| `offset` | integer, optional | Zero or greater; default 0. |

```ts
export interface StoredMemoryMessage {
  id: string;
  conversationId: string;
  sender: string;
  content: string;
  timestamp: string | null;
  source: string | null;
}

export interface SearchMemoryResponse {
  messages: StoredMemoryMessage[];
  total: number;
  limit: number;
  offset: number;
}
```

`total` counts all matching records for the owner and optional conversation before pagination. No matches return `200` with `messages: []` and `total: 0`. An offset past the last match returns an empty page with the actual total.

History review displays unknown timestamps and sources as blank. Keep the corresponding response values null rather than substituting an import date or a fabricated source.

Treat non-empty `q` as literal search terms joined with AND, not executable SQL or raw FTS operators. Return content matches ordered by relevance, then `id` ascending for ties. A non-empty query with no searchable terms returns no matches. For history review without a query, order by `id` ascending. Use parameterised queries and construct safe FTS expressions.

## 6. Memory deletion

### DELETE `/api/memory`

No request body or query parameters. Delete all imported messages and associated FTS entries belonging to the active owner in one transaction. Do not delete another owner's data or the active owner's communication preferences. The frontend provides a clear user-initiated delete action.

```ts
export interface DeleteMemoryResponse {
  deletedCount: number;
}
```

Return `200` even if history is already empty (`deletedCount: 0`). Deleted history must no longer appear in subsequent search or generation requests.

## 7. Optional communication preferences (P1)

### GET and PUT `/api/preferences`

```ts
export interface CommunicationPreferences {
  tone: ReplyTone;
  responseLength: "short" | "medium" | "long";
  formality: "casual" | "professional" | "formal";
  directness: "gentle" | "balanced" | "direct";
}
```

When implemented, GET returns the owner's saved preferences or defaults: `neutral`, `short`, `professional`, and `balanced`, respectively. PUT requires all four fields, replaces the owner's preferences, and returns the saved object. Invalid enum values or missing fields return `422` without changing stored preferences.

The frontend may preselect the saved tone, but `GenerateReplyRequest.tone` remains required and overrides the saved tone for that request. The other saved preferences guide generation only after P1 is implemented. They must never override factual accuracy or the user's expressed intent. Preferences belong to the user and do not create a profile of a manager.

## 8. Errors

All non-success API responses, including framework validation errors, use this envelope:

```ts
export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: {
      field: string;
      message: string;
    }[];
  };
}
```

| HTTP status | `error.code` | Meaning |
|---|---|---|
| 400 | `INVALID_JSON` | Body cannot be parsed as JSON. |
| 401 | `UNAUTHENTICATED` | Authentication is required and the session is missing or invalid. |
| 404 | `NOT_FOUND` | No API route exists at the requested path; an empty conversation is not a 404. |
| 405 | `METHOD_NOT_ALLOWED` | The route exists but does not support the requested method. |
| 409 | `MEMORY_ID_CONFLICT` | An imported ID conflicts with an existing record for this owner. |
| 413 | `REQUEST_TOO_LARGE` | Body exceeds 1 MiB. |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | POST or PUT body is not JSON. |
| 422 | `VALIDATION_ERROR` | Body fields or query parameters violate this contract. |
| 500 | `INTERNAL_ERROR` | Unexpected server error. |
| 501 | `NOT_IMPLEMENTED` | Optional preferences feature has not been implemented. |
| 502 | `MODEL_ERROR` | Claude fails or returns unusable output that cannot pass schema/evidence validation. |
| 503 | `SERVICE_UNAVAILABLE` | Required storage or another backend dependency is unavailable. |
| 504 | `MODEL_TIMEOUT` | Claude exceeds the backend's configured timeout. |

Return field paths such as `messages[0].content` in validation details. Messages must be safe for users and must not echo emotional drafts, API keys, provider responses, stack traces, or other users' identifiers. Normalise FastAPI/Pydantic errors into this envelope instead of returning raw framework errors.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Check the required fields.",
    "details": [
      {
        "field": "employeeDraft",
        "message": "Must contain a non-whitespace character."
      }
    ]
  }
}
```

## 9. Integration agreement

Follow the ownership and service handoffs in [AGENTS.md](../AGENTS.md). Coordinate wire changes before implementation and update this contract, its examples and affected frontend/backend consumers together. Use these examples as synthetic fixtures for integration checks; mock Claude in unit tests.

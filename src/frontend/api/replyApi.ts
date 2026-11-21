import {
  ApiErrorResponse,
  CommunicationPreferences,
  CreateSessionRequest,
  DeleteMemoryResponse,
  GenerateReplyRequest,
  GenerateReplyResponse,
  ImportMemoryResponse,
  MemoryMessage,
  SearchMemoryResponse,
  SessionResponse,
  SlackPreviewRequest,
  SlackPreviewResponse,
  StoredMemoryMessage,
} from "./contract";
import { parseSlackImport } from "@/frontend/features/memory/slackImport";
import { SYNTHETIC_SLACK_EXPORT_FILES, SYNTHETIC_SLACK_CHANNEL_ID } from "@/frontend/features/memory/sampleSlackExport";

// Frontend API client for docs/API_CONTRACT.md.
// Mock mode (default) serves the contract's synthetic fixtures so the UI works without the backend.
// Set NEXT_PUBLIC_R2R_MOCK=false and NEXT_PUBLIC_API_BASE_URL to use FastAPI.
// Hosted deployments also set NEXT_PUBLIC_R2R_AUTH=invite: an expired or
// missing session then sends the browser to /login.

const USE_MOCK = process.env.NEXT_PUBLIC_R2R_MOCK !== "false";
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/+$/, "");
export const isInviteAuth = !USE_MOCK && process.env.NEXT_PUBLIC_R2R_AUTH === "invite";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

export const isMockMode = USE_MOCK;

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  if (!BASE_URL) {
    throw new ApiError(0, "API_NOT_CONFIGURED", "The reply service URL is not configured.");
  }
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      cache: "no-store",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Could not reach the reply service.");
  }
  if (!response.ok) {
    let envelope: Partial<ApiErrorResponse> = {};
    try {
      envelope = await response.json();
    } catch {
      // non-JSON error body
    }
    if (response.status === 401 && isInviteAuth && !path.startsWith("/api/session") && typeof window !== "undefined") {
      window.location.assign("/login");
    }
    throw new ApiError(response.status, envelope.error?.code ?? "INTERNAL_ERROR", envelope.error?.message ?? "Request failed.");
  }
  return (await response.json()) as T;
}

// ---------- Mock backend (synthetic data only) ----------

let mockMemory: StoredMemoryMessage[] = [];
let mockPreferences: CommunicationPreferences = { tone: "neutral", responseLength: "short", formality: "professional", directness: "balanced" };
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export { SYNTHETIC_SLACK_CHANNEL_ID };
export const SYNTHETIC_IMPORT: { messages: MemoryMessage[] } = {
  messages: parseSlackImport(SYNTHETIC_SLACK_EXPORT_FILES).messages,
};

function mockGenerate(req: GenerateReplyRequest): GenerateReplyResponse {
  const hit = mockMemory.find((m) =>
    (!req.conversationId || m.conversationId === req.conversationId) &&
    /uploaded.*documents.*shared drive/i.test(m.content),
  );
  const hasManagerMessage = Boolean(req.managerMessage?.trim());
  return {
    reply: "Hi, the document link is asking for a password that I don't currently have. Could you please share it so I can access the documents?",
    managerIntent: hasManagerMessage
      ? `Supplied manager message (synthetic demo): ${req.managerMessage}`
      : "No manager message was provided, so its request cannot be interpreted.",
    employeeConcern: "The employee reports being unable to access the protected link.",
    evidence: hit
      ? [{ messageId: hit.id, content: hit.content, sender: hit.sender, timestamp: hit.timestamp, source: hit.source, supportedClaim: "A document location was shared." }]
      : [],
    unverifiedClaims: ["The employee reports that opening the link requires a password."],
    warnings: [
      ...(!hasManagerMessage ? ["No manager message was provided; the reply uses your draft and available history."] : []),
      hit
        ? "The retrieved message confirms the document location, but does not establish whether a password was supplied elsewhere."
        : "No supporting history was found. Import conversation history to add receipts.",
    ],
  };
}

// ---------- Public client ----------

// Invite-code sessions exist only in hosted mode; mock and local demo modes
// never call them.
export async function signIn(inviteCode: string): Promise<SessionResponse> {
  const body: CreateSessionRequest = { inviteCode };
  return request("POST", "/api/session", body);
}

export async function getSession(): Promise<SessionResponse> {
  return request("GET", "/api/session");
}

export async function signOut(): Promise<SessionResponse> {
  return request("DELETE", "/api/session");
}

export async function generateReply(req: GenerateReplyRequest): Promise<GenerateReplyResponse> {
  if (!USE_MOCK) return request("POST", "/api/reply/generate", req);
  // Synthetic demo pacing lets users see the full loading experience.
  // Real backend requests above return as soon as the service responds.
  await delay(8_000);
  if (/\bFAIL\b/.test(req.employeeDraft)) throw new ApiError(502, "MODEL_ERROR", "The reply module failed.");
  return mockGenerate(req);
}

export async function previewSlack(req: SlackPreviewRequest): Promise<SlackPreviewResponse> {
  if (!USE_MOCK) return request("POST", "/api/slack/preview", req);
  if (req.channelId !== SYNTHETIC_SLACK_CHANNEL_ID) {
    throw new ApiError(403, "SLACK_CHANNEL_NOT_ALLOWED", `Use ${SYNTHETIC_SLACK_CHANNEL_ID} to preview synthetic Slack messages.`);
  }
  const messages = SYNTHETIC_IMPORT.messages
    .filter((message) => message.conversationId === `slack-export:${req.channelId}`)
    .map((message) => ({ ...message }));
  const limit = req.limit ?? 100;
  const cursor = req.cursor?.match(/^sample:(\d+)$/);
  if (!Number.isInteger(limit) || limit < 1 || limit > 100 || (req.cursor !== undefined && !cursor)) {
    throw new ApiError(422, "VALIDATION_ERROR", "Use a valid sample page cursor and a limit from 1 to 100.");
  }
  const offset = cursor ? Number(cursor[1]) : 0;
  if (!Number.isSafeInteger(offset) || offset > messages.length) {
    throw new ApiError(422, "VALIDATION_ERROR", "The sample page cursor is not valid.");
  }
  const page = messages.slice(offset, offset + limit);
  const nextOffset = offset + page.length;
  return { messages: page, nextCursor: nextOffset < messages.length ? `sample:${nextOffset}` : null, skippedCount: 0, warnings: [] };
}

export async function importMemory(messages: MemoryMessage[]): Promise<ImportMemoryResponse> {
  if (!USE_MOCK) return request("POST", "/api/memory/import", { messages });
  let imported = 0;
  let skipped = 0;
  for (const m of messages) {
    if (mockMemory.some((x) => x.id === m.id)) {
      skipped += 1;
    } else {
      mockMemory.push({ ...m, timestamp: m.timestamp ?? null, source: m.source ?? null });
      imported += 1;
    }
  }
  return { importedCount: imported, skippedCount: skipped };
}

export async function searchMemory(q: string, limit = 20, offset = 0): Promise<SearchMemoryResponse> {
  if (!USE_MOCK) {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (q.trim()) params.set("q", q.trim());
    return request("GET", `/api/memory/search?${params}`);
  }
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  const matches = mockMemory.filter((m) => terms.every((t) => m.content.toLowerCase().includes(t))).sort((a, b) => a.id.localeCompare(b.id));
  return { messages: matches.slice(offset, offset + limit), total: matches.length, limit, offset };
}

export async function deleteAllMemory(): Promise<DeleteMemoryResponse> {
  if (!USE_MOCK) return request("DELETE", "/api/memory");
  const deletedCount = mockMemory.length;
  mockMemory = [];
  return { deletedCount };
}

// Preferences are optional P1: the backend returns 501 NOT_IMPLEMENTED until built.
export async function getPreferences(): Promise<CommunicationPreferences> {
  if (!USE_MOCK) return request("GET", "/api/preferences");
  return { ...mockPreferences };
}

export async function savePreferences(prefs: CommunicationPreferences): Promise<CommunicationPreferences> {
  if (!USE_MOCK) return request("PUT", "/api/preferences", prefs);
  mockPreferences = { ...prefs };
  return { ...mockPreferences };
}

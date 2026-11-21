// Wire types mirrored from docs/API_CONTRACT.md. Keep in sync with that document.

export type ReplyTone = "diplomatic" | "neutral" | "assertive";

export interface GenerateReplyRequest {
  managerMessage?: string;
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

export interface MemoryMessage {
  id: string;
  conversationId: string;
  sender: string;
  content: string;
  timestamp?: string;
  source?: string;
}

export interface ImportMemoryResponse {
  importedCount: number;
  skippedCount: number;
}

// Slack preview contract from origin/main, pending backend integration on this branch.
export interface SlackPreviewRequest {
  channelId: string;
  oldest?: string;
  latest?: string;
  cursor?: string;
  limit?: number;
}

export interface SlackPreviewResponse {
  messages: MemoryMessage[];
  nextCursor: string | null;
  skippedCount: number;
  warnings: string[];
}

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

export interface DeleteMemoryResponse {
  deletedCount: number;
}

export interface CommunicationPreferences {
  tone: ReplyTone;
  responseLength: "short" | "medium" | "long";
  formality: "casual" | "professional" | "formal";
  directness: "gentle" | "balanced" | "direct";
}

export interface ApiErrorResponse {
  error: { code: string; message: string; details?: { field: string; message: string }[] };
}

// Hosted invite-code sessions (R2R_IDENTITY_MODE=invite_code). The session
// itself travels only as an HttpOnly cookie set by the server.
export interface CreateSessionRequest {
  inviteCode: string;
}

export interface SessionResponse {
  authenticated: boolean;
}

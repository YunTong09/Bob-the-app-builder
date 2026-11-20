
export type ReplyTone =
  | "diplomatic"
  | "neutral"
  | "assertive";

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
}

export interface ImportMemoryRequest {
  messages: MemoryMessage[];
}

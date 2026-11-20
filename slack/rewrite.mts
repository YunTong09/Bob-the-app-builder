import demoResponse from "../backend/fixtures/generate_response.json" with { type: "json" };

export type ReplyTone = "diplomatic" | "neutral" | "assertive";

export interface RewriteRequest {
  managerMessage: string;
  employeeDraft: string;
  tone: ReplyTone;
  conversationId?: string;
}

export interface RewriteResponse {
  reply: string;
  managerIntent: string;
  employeeConcern: string;
  evidence: Array<{
    messageId: string;
    content: string;
    sender: string;
    timestamp: string | null;
    supportedClaim: string;
    source?: string | null;
  }>;
  unverifiedClaims: string[];
  warnings: string[];
}

export type RewriteService = (request: RewriteRequest) => Promise<RewriteResponse>;

export function createMockRewriteService({ fail = false } = {}): RewriteService {
  return async () => {
    if (fail) {
      throw new Error("Mock rewrite failed.");
    }

    return structuredClone(demoResponse);
  };
}

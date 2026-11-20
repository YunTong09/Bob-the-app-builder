export type Tone = "diplomatic" | "neutral" | "assertive";

export const toneLabels: Record<Tone, string> = {
  diplomatic: "Diplomatic",
  neutral: "Neutral",
  assertive: "Assertive",
};

export interface ReplyResult {
  reply: string;
  managerIntent: string;
  employeeConcern: string;
  evidence: {
    messageId: string;
    content: string;
    sender: string;
    timestamp: string | null;
    supportedClaim: string;
    source?: string | null;
  }[];
  unverifiedClaims: string[];
  warnings: string[];
}

export interface HistoryPage {
  messages: {
    id: string;
    conversationId: string;
    sender: string;
    content: string;
    timestamp: string | null;
    source: string | null;
  }[];
  total: number;
  limit: number;
  offset: number;
}

export async function webApi<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, cache: "no-store" }).catch(() => {
    throw new Error("Could not reach the server. Try again.");
  });
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = data?.error?.message;
    throw new Error(typeof message === "string" ? message : "The request failed. Try again.");
  }

  if (!data || typeof data !== "object") {
    throw new Error("The server returned an unexpected response. Try again.");
  }
  return data as T;
}

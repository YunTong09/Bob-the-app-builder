import type { ReplyTone } from "./contract";

export type Tone = ReplyTone;

export const toneLabels: Record<Tone, string> = {
  diplomatic: "Diplomatic",
  neutral: "Neutral",
  assertive: "Assertive",
};

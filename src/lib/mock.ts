import { AnalyzeInput, AnalyzeOutput, MemoryEvent } from "./schema";

export function getMockAnalysis(
  input: AnalyzeInput,
  memories: MemoryEvent[],
): AnalyzeOutput {
  const relatedMemories = memories.filter((memory) =>
    /key|vault|password|docs|documentation/i.test(memory.text),
  );

  return {
    managerIntent: "Confirm whether the employee can access the key and identify what is blocking them.",
    rageLevel: Math.min(100, Math.max(0, input.employeeRawText.length > 90 ? 78 : 64)),
    extractedFacts: [
      "The manager expects the company documentation to contain the key information.",
      "The employee cannot access the key because the required password has not been provided.",
    ],
    relatedMemories,
    polishedReply:
      "Hi Dave, I can see the company docs, but I still do not have the password for the key or vault access. Could you please share it so I can access the key? Thanks!",
  };
}

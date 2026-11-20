import Anthropic from "@anthropic-ai/sdk";
import { getMockAnalysis } from "./mock";
import { ANALYSIS_SYSTEM_PROMPT, buildAnalysisPrompt } from "./prompts";
import { AnalyzeInput, AnalyzeOutput, analyzeOutputSchema, MemoryEvent } from "./schema";

function shouldUseMock(): boolean {
  return process.env.USE_MOCK === "true" || !process.env.ANTHROPIC_API_KEY;
}

function parseClaudeJson(text: string): AnalyzeOutput {
  const parsed = JSON.parse(text);
  return analyzeOutputSchema.parse(parsed);
}

export async function analyzeWithClaude(
  input: AnalyzeInput,
  memories: MemoryEvent[],
): Promise<AnalyzeOutput> {
  if (shouldUseMock()) {
    return getMockAnalysis(input, memories);
  }

  const model = process.env.ANTHROPIC_MODEL;
  if (!model) {
    throw new Error("ANTHROPIC_MODEL must be set when mock mode is disabled.");
  }

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  const prompt = buildAnalysisPrompt(
    input.managerMessage,
    input.employeeRawText,
    memories,
  );

  let lastError: unknown;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await client.messages.create({
        model,
        max_tokens: 900,
        system: ANALYSIS_SYSTEM_PROMPT,
        messages: [
          {
            role: "user",
            content:
              attempt === 0
                ? prompt
                : `${prompt}\n\nYour previous output was invalid. Return only a valid JSON object matching the required schema.`,
          },
        ],
      });
      const text = response.content.find((block) => block.type === "text");
      if (!text || text.type !== "text") {
        throw new Error("Claude returned no text content.");
      }
      return parseClaudeJson(text.text);
    } catch (error) {
      lastError = error;
    }
  }

  throw new Error(
    `Analysis response was invalid after one retry: ${lastError instanceof Error ? lastError.message : "unknown error"}`,
  );
}

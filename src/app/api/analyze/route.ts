import { NextResponse } from "next/server";
import { analyzeWithClaude } from "@/lib/claude";
import { memoryStore } from "@/lib/memoryStore";
import { analyzeInputSchema } from "@/lib/schema";

export async function POST(request: Request) {
  try {
    const input = analyzeInputSchema.parse(await request.json());
    const memories = memoryStore.list(input.managerId);

    // Privacy rule: employeeRawText is used only for this real-time request; it is never stored or logged.
    const result = await analyzeWithClaude(input, memories);
    return NextResponse.json(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to analyze the message.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

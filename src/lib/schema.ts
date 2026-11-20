import { z } from "zod";

export const memoryEventSchema = z.object({
  id: z.string(),
  managerId: z.string(),
  text: z.string(),
  date: z.string(),
});

export const analyzeInputSchema = z.object({
  managerId: z.string().min(1),
  managerMessage: z.string().min(1),
  employeeRawText: z.string().min(1),
});

export const analyzeOutputSchema = z.object({
  managerIntent: z.string(),
  rageLevel: z.number().min(0).max(100),
  extractedFacts: z.array(z.string()),
  relatedMemories: z.array(memoryEventSchema),
  polishedReply: z.string(),
});

export type MemoryEvent = z.infer<typeof memoryEventSchema>;
export type AnalyzeInput = z.infer<typeof analyzeInputSchema>;
export type AnalyzeOutput = z.infer<typeof analyzeOutputSchema>;

import { NextResponse } from "next/server";
import { memoryStore } from "@/lib/memoryStore";
import { z } from "zod";

const addMemorySchema = z.object({
  managerId: z.string().min(1),
  text: z.string().min(1),
  date: z.string().min(1),
});

export async function GET(request: Request) {
  const managerId = new URL(request.url).searchParams.get("managerId");
  if (!managerId) {
    return NextResponse.json({ error: "managerId is required." }, { status: 400 });
  }
  return NextResponse.json(memoryStore.list(managerId));
}

export async function POST(request: Request) {
  try {
    const input = addMemorySchema.parse(await request.json());
    return NextResponse.json(memoryStore.add(input), { status: 201 });
  } catch {
    return NextResponse.json({ error: "Invalid memory event." }, { status: 400 });
  }
}

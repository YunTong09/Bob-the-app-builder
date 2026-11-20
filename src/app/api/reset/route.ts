import { NextResponse } from "next/server";
import { memoryStore } from "@/lib/memoryStore";

export async function POST() {
  return NextResponse.json({ memories: memoryStore.reset() });
}

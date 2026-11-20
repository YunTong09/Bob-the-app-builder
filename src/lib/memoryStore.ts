import seed from "@/data/seed.json";
import { MemoryEvent } from "./schema";

export interface MemoryStore {
  list(managerId: string): MemoryEvent[];
  add(input: Omit<MemoryEvent, "id">): MemoryEvent;
  reset(): MemoryEvent[];
}

const seedEvents = (): MemoryEvent[] =>
  seed.memoryEvents.map((event) => ({ ...event }));

class InMemoryMemoryStore implements MemoryStore {
  private events: MemoryEvent[] = seedEvents();

  list(managerId: string): MemoryEvent[] {
    return this.events.filter((event) => event.managerId === managerId);
  }

  add(input: Omit<MemoryEvent, "id">): MemoryEvent {
    const saved = { ...input, id: `memory-${Date.now()}` };
    this.events = [...this.events, saved];
    return saved;
  }

  reset(): MemoryEvent[] {
    this.events = seedEvents();
    return this.events;
  }
}

export const memoryStore: MemoryStore = new InMemoryMemoryStore();

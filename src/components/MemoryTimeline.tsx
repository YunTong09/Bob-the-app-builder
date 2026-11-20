import { MemoryEvent } from "@/lib/schema";

type MemoryTimelineProps = {
  memories: MemoryEvent[];
  citedMemoryIds: string[];
};

export default function MemoryTimeline({ memories, citedMemoryIds }: MemoryTimelineProps) {
  return (
    <section className="panel">
      <div className="section-label">Memory timeline</div>
      <div className="timeline">
        {memories.map((memory) => {
          const cited = citedMemoryIds.includes(memory.id);
          return (
            <div className={`timeline-item ${cited ? "cited" : ""}`} key={memory.id}>
              <div className="timeline-date">{memory.date}</div>
              <p>{memory.text}</p>
              {cited && <span className="cited-badge">Used in reply</span>}
            </div>
          );
        })}
      </div>
    </section>
  );
}

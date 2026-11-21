"use client";

import { useEffect, useState } from "react";

export default function ReplyWaitMeter({
  startedAt, estimateMs, replyReady,
}: {
  startedAt: number;
  estimateMs: number | null;
  replyReady: boolean;
}) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (replyReady) return;
    const tick = () => setElapsed(performance.now() - startedAt);
    tick();
    const timer = window.setInterval(tick, 400);
    return () => window.clearInterval(timer);
  }, [startedAt, replyReady]);

  const hasEstimate = estimateMs !== null && elapsed < estimateMs;
  const filled = replyReady ? 24 : hasEstimate ? Math.min(23, Math.floor(elapsed / estimateMs * 24)) : 0;
  const elapsedSeconds = Math.floor(elapsed / 1000);
  const label = replyReady ? "Reply ready"
    : hasEstimate ? `About ${Math.ceil((estimateMs - elapsed) / 1000)}s remaining (estimate)`
    : estimateMs !== null ? `Taking longer than estimated · ${elapsedSeconds}s elapsed`
    : `Generating reply · ${elapsedSeconds}s elapsed`;

  return (
    <div className="reply-wait-meter">
      <div className="reply-wait-blocks" aria-hidden="true" data-indeterminate={!replyReady && !hasEstimate}>
        {Array.from({ length: 24 }, (_, i) => <span key={i} className={i < filled ? "active" : undefined} />)}
      </div>
      <p className="small-text">{label}</p>
    </div>
  );
}

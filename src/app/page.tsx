"use client";

import { useEffect, useState } from "react";
import ChatWindow from "@/components/ChatWindow";
import ComparePanel from "@/components/ComparePanel";
import IntentCard from "@/components/IntentCard";
import MemoryTimeline from "@/components/MemoryTimeline";
import RageMeter from "@/components/RageMeter";
import VentInput from "@/components/VentInput";
import { AnalyzeOutput, MemoryEvent } from "@/lib/schema";

const defaultManagerMessage = "I already gave you the company docs, why don't you know where the key is?";

export default function HomePage() {
  const [managerMessage, setManagerMessage] = useState(defaultManagerMessage);
  const [rawText, setRawText] = useState("");
  const [memories, setMemories] = useState<MemoryEvent[]>([]);
  const [result, setResult] = useState<AnalyzeOutput | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/memory?managerId=dave")
      .then((response) => response.json())
      .then(setMemories)
      .catch(() => setError("Could not load memory timeline."));
  }, []);

  async function handleAnalyze() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ managerId: "dave", managerMessage, employeeRawText: rawText }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Analysis failed.");
      setResult(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Private message translator</p>
          <h1>Rage-to-Reply</h1>
          <p className="subtitle">Get it out. Send something better.</p>
        </div>
        <div className="status-pill"><span /> mock mode</div>
      </header>

      <div className="workspace-grid">
        <div className="main-column">
          <ChatWindow managerMessage={managerMessage} onChange={setManagerMessage} />
          <VentInput value={rawText} onChange={setRawText} onSubmit={handleAnalyze} loading={loading} />
          {error && <p className="error-message">{error}</p>}
          {result && (
            <div className="results-stack">
              <div className="result-grid">
                <RageMeter rageLevel={result.rageLevel} />
                <IntentCard managerIntent={result.managerIntent} />
              </div>
              <ComparePanel rawText={rawText} polishedReply={result.polishedReply} />
            </div>
          )}
        </div>
        <aside>
          <MemoryTimeline memories={memories} citedMemoryIds={result?.relatedMemories.map((memory) => memory.id) || []} />
        </aside>
      </div>
    </main>
  );
}

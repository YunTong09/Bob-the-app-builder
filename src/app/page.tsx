"use client";

import { useRef, useState, type FormEvent } from "react";
import ChatWindow from "@/components/ChatWindow";
import ComparePanel from "@/components/ComparePanel";
import HistoryPanel from "@/components/HistoryPanel";
import VentInput from "@/components/VentInput";
import { webApi, type ReplyResult, type Tone } from "@/lib/web-api";

export default function HomePage() {
  const [managerMessage, setManagerMessage] = useState("");
  const [draft, setDraft] = useState("");
  const [tone, setTone] = useState<Tone>("neutral");
  const [result, setResult] = useState<{ data: ReplyResult; tone: Tone } | null>(null);
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);
  const canSubmit = Boolean(managerMessage.trim() && draft.trim());

  async function handleGenerate(event: FormEvent) {
    event.preventDefault();
    if (inFlight.current || !canSubmit) return;
    inFlight.current = true;
    setLoading(true);
    setError("");

    try {
      const data = await webApi<ReplyResult>("/api/reply/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ managerMessage, employeeDraft: draft, tone }),
      });
      setResult({ data, tone });
      setReply(data.reply);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not generate a reply. Try again.");
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="page-header">
        <h1>Rage-to-Reply</h1>
        <p>Turn a difficult workplace message into a reply you can stand behind.</p>
      </header>
      <div className="workspace-grid">
        <form className="panel workspace-panel" onSubmit={handleGenerate}>
          <h2>Write a draft</h2>
          <ChatWindow managerMessage={managerMessage} onChange={setManagerMessage} />
          <VentInput
            value={draft} onChange={setDraft} tone={tone} onToneChange={setTone}
            loading={loading} canSubmit={canSubmit} hasReply={Boolean(result)}
          />
          {error && <p className="error-message" role="alert">{error}</p>}
        </form>
        <section className="panel workspace-panel" aria-labelledby="review-heading">
          <h2 id="review-heading">Review your reply</h2>
          <div className="small-text" role="status">
            {loading ? "Generating your reply…" : result && !error ? "Suggested reply ready." : null}
          </div>
          {result ? (
            <>
              <ComparePanel polishedReply={reply} tone={result.tone} onChange={setReply} />
              <div className="review-section">
                <h3>Manager’s request and interpretation</h3>
                <p>{result.data.managerIntent}</p>
                <h3>Your concern</h3>
                <p>{result.data.employeeConcern}</p>
              </div>
              <div className="review-section">
                <h3>Supporting evidence</h3>
                {result.data.evidence.length ? (
                  <ul className="record-list">
                    {result.data.evidence.map((item, index) => (
                      <li key={`${item.messageId}-${index}`}>
                        <strong>{item.sender}</strong>
                        <blockquote>{item.content}</blockquote>
                        <p>Supports: {item.supportedClaim}</p>
                        {(item.timestamp || item.source) && <p className="small-text">{[item.timestamp, item.source].filter(Boolean).join(" · ")}</p>}
                      </li>
                    ))}
                  </ul>
                ) : <p className="small-text">No supporting evidence was found.</p>}
              </div>
              {result.data.unverifiedClaims.length > 0 && (
                <div className="review-section">
                  <h3>Unverified claims</h3>
                  <ul className="text-list">{result.data.unverifiedClaims.map((claim, index) => <li key={index}>{claim}</li>)}</ul>
                </div>
              )}
              {result.data.warnings.length > 0 && (
                <div className="review-section">
                  <h3>Warnings</h3>
                  <ul className="text-list">{result.data.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
                </div>
              )}
            </>
          ) : <p className="small-text">Generate a reply to review and edit it here.</p>}
        </section>
      </div>
      <HistoryPanel />
    </main>
  );
}

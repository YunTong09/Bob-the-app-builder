"use client";

import { useState } from "react";
import { Evidence, GenerateReplyResponse, ReplyTone } from "@/frontend/api/contract";
import { ApiError, generateReply } from "@/frontend/api/replyApi";
import DictationControls, { appendDictation } from "./DictationControls";
import { formatTimestamp } from "@/frontend/shared/formatTimestamp";

export const TONES: { value: ReplyTone; label: string }[] = [
  { value: "diplomatic", label: "Diplomatic" },
  { value: "neutral", label: "Neutral" },
  { value: "assertive", label: "Assertive" },
];

function ToneRadios({ name, value, onChange, disabled }: { name: string; value: ReplyTone; onChange: (tone: ReplyTone) => void; disabled?: boolean }) {
  return (
    <div className="tone-group" role="radiogroup" aria-label="Tone">
      {TONES.map((tone) => (
        <label key={tone.value} className="tone-option">
          <span>{tone.label}</span>
          <input type="radio" name={name} checked={value === tone.value} disabled={disabled} onChange={() => onChange(tone.value)} />
        </label>
      ))}
    </div>
  );
}

function ReceiptCard({ item, onApply, applied }: { item: Evidence; onApply: () => void; applied: boolean }) {
  const when = formatTimestamp(item.timestamp);
  return (
    <section className="card receipt" aria-label="Receipt">
      <h3 className="card-title"><span className="status-label status-label-supported">Supported</span></h3>
      <blockquote className="receipt-quote">{item.content}</blockquote>
      <p>Supports: {item.supportedClaim}</p>
      <p className="meta">
        Sender: {item.sender}
        {when && ` · ${when}`}
      </p>
      <p className="meta">Source: {item.source ?? ""}</p>
      <div className="row-end">
        <button type="button" className="btn btn-secondary" onClick={onApply} disabled={applied}>
          {applied ? "Applied" : "Apply"}
        </button>
      </div>
    </section>
  );
}

export default function ReplyPanel({ initialManagerMessage }: { initialManagerMessage: string }) {
  const [managerMessage, setManagerMessage] = useState(initialManagerMessage);
  const [draft, setDraft] = useState("");
  const [tone, setTone] = useState<ReplyTone>("neutral");
  const [result, setResult] = useState<GenerateReplyResponse | null>(null);
  const [reply, setReply] = useState("");
  const [appliedIds, setAppliedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [listening, setListening] = useState(false);
  const [copyNote, setCopyNote] = useState("");

  const canGenerate = draft.trim() !== "" && !loading;

  async function run(nextTone: ReplyTone) {
    setTone(nextTone);
    setLoading(true);
    setError(null);
    setCopied(false);
    try {
      // The draft is sent only to generate a reply; it is never stored by the frontend.
      const data = await generateReply({ managerMessage: managerMessage.trim() ? managerMessage : undefined, employeeDraft: draft, tone: nextTone });
      setResult(data);
      setReply(data.reply);
      setAppliedIds([]);
    } catch (caught) {
      setResult(null);
      const detail = caught instanceof ApiError ? ` (${caught.code})` : "";
      setError(`No response${detail}`);
    } finally {
      setLoading(false);
    }
  }

  function applyReceipt(item: Evidence) {
    const when = formatTimestamp(item.timestamp);
    const ref = `\n\n(Ref: "${item.content}" — ${item.sender}${when ? `, ${when}` : ""})`;
    setReply((current) => current + ref);
    setAppliedIds((ids) => [...ids, item.messageId]);
  }

  async function copyReply() {
    try {
      await navigator.clipboard.writeText(reply);
      setCopied(true);
    } catch {
      setCopyNote("Could not copy automatically. Select the text and copy it manually.");
    }
  }

  const notices = [...(result?.unverifiedClaims ?? []).map((text) => ({ kind: "unverified" as const, text })), ...(result?.warnings ?? []).map((text) => ({ kind: "warning" as const, text }))];

  return (
    <div className="stack">
      <section className="card">
        <label className="field-label" htmlFor="manager-message">Manager&apos;s message (optional)</label>
        <textarea id="manager-message" className="textarea textarea-sm" value={managerMessage} onChange={(e) => setManagerMessage(e.target.value)} maxLength={10000} placeholder="Optional: add their message for more context" />
        <label className="field-label" htmlFor="your-words">Your words</label>
        <DictationControls onTranscript={(text) => setDraft((current) => appendDictation(current, text))} disabled={loading}>
          <textarea id="your-words" className="textarea" value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={10000} placeholder="Say what you really think. This stays private and isn't saved." />
        </DictationControls>
        {copyNote && <p className="meta" role="status">{copyNote}</p>}
        <div className="row tone-row">
          <span className="field-label inline">Tone</span>
          <ToneRadios name="tone-input" value={tone} onChange={setTone} disabled={loading} />
        </div>
        <div className="row-end">
          <button type="button" className="btn btn-primary" onClick={() => run(tone)} disabled={!canGenerate}>
            {loading ? "Generating…" : "Generate Reply"}
          </button>
        </div>
      </section>

      <div role="status" aria-live="polite">
        {loading && <p className="meta">Reading the chat and checking your receipts…</p>}
      </div>

      {error && (
        <section className="card status-card status-error" role="alert">
          <span className="status-icon" aria-hidden="true">✕</span>
          <div>
            <strong>{error}</strong>
            <p className="meta">Something went wrong generating a reply. Your words are still here — try again.</p>
          </div>
        </section>
      )}

      {result && (
        <>
          <section className="card" aria-label="Suggested response">
            <h3 className="card-title">Suggested response</h3>
            <label className="field-label sr-only" htmlFor="reply">Suggested response (editable)</label>
            <textarea id="reply" className="textarea" value={reply} onChange={(e) => setReply(e.target.value)} />
            <div className="row tone-row">
              <span className="field-label inline">Regenerate</span>
              <ToneRadios name="tone-regen" value={tone} onChange={(next) => run(next)} disabled={loading} />
            </div>
            <div className="row-end">
              <button type="button" className="btn btn-secondary" onClick={copyReply}>{copied ? "Copied" : "Copy"}</button>
            </div>
            <p className="meta">This is a suggestion. Nothing is sent automatically — paste it into the chat yourself.</p>
          </section>

          <details className="card">
            <summary className="card-title">How I read the message</summary>
            <p className="meta"><strong>Manager request (interpretation):</strong> {result.managerIntent}</p>
            <p className="meta"><strong>Your concern:</strong> {result.employeeConcern}</p>
          </details>

          {result.evidence.length === 0 ? (
            <section className="card receipt" aria-label="Receipt">
              <h3 className="card-title">Receipt</h3>
              <p className="meta">No supporting messages found in imported history.</p>
            </section>
          ) : (
            result.evidence.map((item) => <ReceiptCard key={item.messageId} item={item} applied={appliedIds.includes(item.messageId)} onApply={() => applyReceipt(item)} />)
          )}

          {notices.map((notice, index) => (
            <section key={index} className={`card status-card ${notice.kind === "unverified" ? "status-unverified" : "status-warning"}`}>
              <span className="status-icon" aria-hidden="true">{notice.kind === "unverified" ? "?" : "⚠"}</span>
              <p>
                <strong>{notice.kind === "unverified" ? "Not verified: " : "Reminder: "}</strong>
                {notice.text}
              </p>
            </section>
          ))}
        </>
      )}
    </div>
  );
}

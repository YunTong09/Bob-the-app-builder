"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import ChatWindow from "@/frontend/features/reply/ChatWindow";
import ComparePanel from "@/frontend/features/reply/ComparePanel";
import HistoryPanel from "@/frontend/features/memory/HistoryPanel";
import PreferencesPanel, { readLocalPreferences } from "@/frontend/features/preferences/PreferencesPanel";
import VentInput from "@/frontend/features/reply/VentInput";
import type { GenerateReplyResponse, ReplyTone } from "@/frontend/api/contract";
import { generateReply } from "@/frontend/api/replyApi";

const setupKey = "rage-to-reply.workspace-setup";

export default function HomePage() {
  const [mode, setMode] = useState<"evidence" | "quick">("evidence");
  const [managerMessage, setManagerMessage] = useState("");
  const [draft, setDraft] = useState("");
  const [tone, setTone] = useState<ReplyTone>("neutral");
  const [quickDraft, setQuickDraft] = useState("");
  const [quickTone, setQuickTone] = useState<ReplyTone>("neutral");
  const [dialog, setDialog] = useState<"settings" | "history" | null>(null);
  const [historyOpened, setHistoryOpened] = useState(false);
  const [firstVisit, setFirstVisit] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [result, setResult] = useState<{ data: GenerateReplyResponse; tone: ReplyTone } | null>(null);
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);
  const canSubmit = Boolean(managerMessage.trim() && draft.trim());
  const withEvidence = mode === "evidence";
  const showReview = withEvidence && Boolean(result);

  useEffect(() => {
    const preferredTone = readLocalPreferences().tone;
    setTone(preferredTone);
    setQuickTone(preferredTone);
    try {
      if (localStorage.getItem(setupKey)) return;
    } catch {
      // The setup can still be dismissed if browser storage is unavailable.
    }
    setFirstVisit(true);
    setDialog("settings");
  }, []);

  useEffect(() => {
    const element = dialogRef.current;
    if (dialog && element && !element.open) element.showModal();
    if (!dialog && element?.open) element.close();
  }, [dialog]);

  function dismissDialog() {
    if (firstVisit) {
      try {
        localStorage.setItem(setupKey, "complete");
      } catch {
        // Dismissal still works for this visit.
      }
      setFirstVisit(false);
    }
    setDialog(null);
  }

  async function handleGenerate(event: FormEvent) {
    event.preventDefault();
    if (!withEvidence || inFlight.current || !canSubmit) return;
    inFlight.current = true;
    setLoading(true);
    setError("");

    try {
      const data = await generateReply({ managerMessage, employeeDraft: draft, tone });
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
      <fieldset className="mode-switch">
        <legend>Rewrite mode</legend>
        <div className="mode-options">
          <label><input type="radio" name="rewrite-mode" checked={withEvidence} onChange={() => setMode("evidence")} /> Rewrite with Evidence</label>
          <label><input type="radio" name="rewrite-mode" checked={!withEvidence} onChange={() => setMode("quick")} /> Quick Tone Rewrite</label>
        </div>
      </fieldset>
      <div className="workspace-actions">
        <button type="button" className="secondary-button" aria-haspopup="dialog" onClick={() => setDialog("settings")}>Settings</button>
        {withEvidence && <button type="button" className="secondary-button" aria-haspopup="dialog" onClick={() => { setHistoryOpened(true); setDialog("history"); }}>History</button>}
      </div>
      <dialog
        ref={dialogRef}
        className="workspace-dialog"
        aria-labelledby="workspace-dialog-title"
        onCancel={(event) => { event.preventDefault(); dismissDialog(); }}
      >
        <header>
          <h2 id="workspace-dialog-title">{dialog === "history" ? "Conversation history" : firstVisit ? "Set up your workspace" : "Settings"}</h2>
          <button type="button" className="secondary-button" onClick={dismissDialog}>{firstVisit ? "Skip for now" : "Close"}</button>
        </header>
        {dialog === "settings" && <PreferencesPanel allowBrowserStorage onSaved={(preferences) => {
          setTone(preferences.tone);
          setQuickTone(preferences.tone);
          dismissDialog();
        }} />}
        {historyOpened && <div hidden={dialog !== "history"}><HistoryPanel /></div>}
      </dialog>
      <div className="workspace-grid">
        <form className="panel workspace-panel" onSubmit={handleGenerate}>
          <h2>Write a draft</h2>
          {withEvidence && (
            <div>
              <button type="button" className="secondary-button" disabled={loading || Boolean(managerMessage || draft)} onClick={() => {
                setManagerMessage("Can you confirm why the shared document hasn't been reviewed yet?");
                setDraft("I can't open the shared document without the password. Please send it so I can review the document.");
              }}>Use sample inputs</button>
            </div>
          )}
          {withEvidence && <ChatWindow managerMessage={managerMessage} onChange={setManagerMessage} />}
          {!withEvidence && <p className="small-text">Quick rewrite is waiting for the draft-only API. Your text stays on this page.</p>}
          <VentInput
            value={withEvidence ? draft : quickDraft} onChange={withEvidence ? setDraft : setQuickDraft}
            tone={withEvidence ? tone : quickTone} onToneChange={withEvidence ? setTone : setQuickTone}
            loading={withEvidence && loading} canSubmit={withEvidence && canSubmit} hasReply={showReview}
          />
          <div className="small-text" role="status">
            {withEvidence && (loading ? "Generating your reply…" : result && !error ? "Suggested reply ready." : null)}
          </div>
          {withEvidence && error && <p className="error-message" role="alert"><span className="status-label status-label-error">Error</span>{error}</p>}
        </form>
        {withEvidence && result && <section className="panel workspace-panel" aria-labelledby="review-heading">
          <h2 id="review-heading">Review your reply</h2>
          <ComparePanel polishedReply={reply} tone={result.tone} onChange={setReply} />
          <div className="review-section">
            <h3>Manager’s request · AI interpretation</h3>
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
                    <span className="status-label status-label-supported">Supported</span>
                    <p className="small-text">{item.sender}</p>
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
              <h3><span className="status-label status-label-warning">Unverified claims</span></h3>
              <ul className="text-list">{result.data.unverifiedClaims.map((claim, index) => <li key={index}>{claim}</li>)}</ul>
            </div>
          )}
          {result.data.warnings.length > 0 && (
            <div className="review-section">
              <h3><span className="status-label status-label-warning">Warnings</span></h3>
              <ul className="text-list">{result.data.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
            </div>
          )}
        </section>}
      </div>
    </main>
  );
}

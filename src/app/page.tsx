"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import ChatWindow from "@/frontend/features/reply/ChatWindow";
import ComparePanel from "@/frontend/features/reply/ComparePanel";
import HistoryPanel from "@/frontend/features/memory/HistoryPanel";
import PreferencesPanel, {
  readLocalPreferences,
} from "@/frontend/features/preferences/PreferencesPanel";
import VentInput from "@/frontend/features/reply/VentInput";
import type { GenerateReplyResponse, ReplyTone } from "@/frontend/api/contract";
import PixelAnimation from "@/frontend/shared/PixelAnimation";
import { isMockMode, generateReply } from "@/frontend/api/replyApi";

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
  const [result, setResult] = useState<{
    data: GenerateReplyResponse;
    tone: ReplyTone;
  } | null>(null);
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
    // Preferences are optional; keep the writing workspace visible on first visit.
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
      const data = await generateReply({
        managerMessage,
        employeeDraft: draft,
        tone,
      });
      setResult({ data, tone });
      setReply(data.reply);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not generate a reply. Try again.",
      );
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <div className="workspace-topbar">
        <span>
          Workspace <span className="breadcrumb-divider">/</span> New reply
        </span>
        <span className="connection-badge">
          {isMockMode ? "Synthetic demo" : "Connected to reply service"}
        </span>
      </div>
      <header className="page-header">
        <div>
          <p className="eyebrow">FROM FRUSTRATION TO CLARITY</p>
          <h1>
            Say what you feel.
            <br />
            <span>Reply with intention.</span>
          </h1>
          <p>A calm reply. A clear point. The receipts to back it up.</p>
        </div>
        <div className="header-note">
          <span aria-hidden="true">✦</span>
          <p>
            Your voice, preserved.
            <br />
            Your facts, grounded.
          </p>
        </div>
      </header>
      <fieldset className="mode-switch">
        <legend className="sr-only">Rewrite mode</legend>
        <div className="mode-options">
          <label>
            <input
              type="radio"
              name="rewrite-mode"
              checked={withEvidence}
              onChange={() => setMode("evidence")}
            />{" "}
            Rewrite with Evidence{" "}
            <span className="mode-tag">WITH RECEIPTS</span>
          </label>
          <label>
            <input
              type="radio"
              name="rewrite-mode"
              checked={!withEvidence}
              onChange={() => setMode("quick")}
            />{" "}
            Quick Tone Rewrite <span className="mode-tag">COMING SOON</span>
          </label>
        </div>
      </fieldset>
      <div className="workspace-actions">
        <button
          type="button"
          className="secondary-button"
          aria-haspopup="dialog"
          onClick={() => setDialog("settings")}
        >
          Settings
        </button>
        {withEvidence && (
          <button
            type="button"
            className="secondary-button"
            aria-haspopup="dialog"
            onClick={() => {
              setHistoryOpened(true);
              setDialog("history");
            }}
          >
            Conversation history
          </button>
        )}
      </div>
      <dialog
        ref={dialogRef}
        className="workspace-dialog"
        aria-labelledby="workspace-dialog-title"
        onCancel={(event) => {
          event.preventDefault();
          dismissDialog();
        }}
      >
        <header>
          <h2 id="workspace-dialog-title">
            {dialog === "history"
              ? "Conversation history"
              : firstVisit
                ? "Set up your workspace"
                : "Settings"}
          </h2>
          <button
            type="button"
            className="secondary-button"
            onClick={dismissDialog}
          >
            {firstVisit ? "Skip for now" : "Close"}
          </button>
        </header>
        {dialog === "settings" && (
          <PreferencesPanel
            allowBrowserStorage
            onSaved={(preferences) => {
              setTone(preferences.tone);
              setQuickTone(preferences.tone);
              dismissDialog();
            }}
          />
        )}
        {historyOpened && (
          <div hidden={dialog !== "history"}>
            <HistoryPanel />
          </div>
        )}
      </dialog>
      <div className="workflow-strip">
        <span>
          <b>01</b> Get it off your chest
        </span>
        <i />
        <span>
          <b>02</b> Find the context
        </span>
        <i />
        <span>
          <b>03</b> Make it professional
        </span>
      </div>
      <div className="workspace-grid">
        <form
          className="panel workspace-panel workspace-draft"
          onSubmit={handleGenerate}
        >
          <div className="panel-heading">
            <div>
              <p className="eyebrow">THE STARTING POINT</p>
              <h2>A little room to vent</h2>
            </div>
            <span className="panel-icon" aria-hidden="true">
              ▤
            </span>
          </div>
          <p className="small-text">
            Start with the message. Then tell us your side.
          </p>
          {withEvidence && (
            <div>
              <button
                type="button"
                className="secondary-button"
                disabled={loading || Boolean(managerMessage || draft)}
                onClick={() => {
                  setManagerMessage(
                    "Can you confirm why the shared document hasn't been reviewed yet?",
                  );
                  setDraft(
                    "I can't open the shared document without the password. Please send it so I can review the document.",
                  );
                }}
              >
                Use sample inputs
              </button>
            </div>
          )}
          {withEvidence && (
            <ChatWindow
              managerMessage={managerMessage}
              onChange={setManagerMessage}
            />
          )}
          {!withEvidence && (
            <p className="feature-notice" role="status">
              Quick Tone Rewrite is coming soon. You can draft here, or switch
              to Rewrite with Evidence to generate a reply.
            </p>
          )}
          <VentInput
            value={withEvidence ? draft : quickDraft}
            onChange={withEvidence ? setDraft : setQuickDraft}
            tone={withEvidence ? tone : quickTone}
            onToneChange={withEvidence ? setTone : setQuickTone}
            loading={withEvidence && loading}
            canSubmit={withEvidence && canSubmit}
            hasReply={showReview}
          />
          <div className="small-text" role="status">
            {withEvidence &&
              (loading
                ? "Generating your reply…"
                : result && !error
                  ? "Suggested reply ready."
                  : null)}
          </div>
          {withEvidence && error && (
            <p className="error-message" role="alert">
              <span className="status-label status-label-error">Error</span>
              {error}
            </p>
          )}
        </form>
        {withEvidence && result && (
          <section
            className="panel workspace-panel workspace-review"
            aria-labelledby="review-heading"
          >
            <div className="panel-heading">
              <div>
                <p className="eyebrow">A COOLER HEAD</p>
                <h2 id="review-heading">Your words, reworked</h2>
              </div>
              <span className="ready-badge">Ready to review</span>
            </div>
            {loading && (
              <p className="small-text" role="status">
                Generating a fresh reply. Your previous version stays below.
              </p>
            )}
            <ComparePanel
              polishedReply={reply}
              tone={result.tone}
              onChange={setReply}
            />
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
                      <span className="status-label status-label-supported">
                        Supported
                      </span>
                      <p className="small-text">{item.sender}</p>
                      <blockquote>{item.content}</blockquote>
                      <p>Supports: {item.supportedClaim}</p>
                      {(item.timestamp || item.source) && (
                        <p className="small-text">
                          {[item.timestamp, item.source]
                            .filter(Boolean)
                            .join(" · ")}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="small-text">No supporting evidence was found.</p>
              )}
            </div>
            {result.data.unverifiedClaims.length > 0 && (
              <div className="review-section">
                <h3>
                  <span className="status-label status-label-warning">
                    Unverified claims
                  </span>
                </h3>
                <ul className="text-list">
                  {result.data.unverifiedClaims.map((claim, index) => (
                    <li key={index}>{claim}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.data.warnings.length > 0 && (
              <div className="review-section">
                <h3>
                  <span className="status-label status-label-warning">
                    Warnings
                  </span>
                </h3>
                <ul className="text-list">
                  {result.data.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}
        {(!withEvidence || !result) && (
          <section
            className="panel workspace-panel workspace-review review-empty"
            aria-labelledby="empty-review-heading"
          >
            <div className="panel-heading">
              <div>
                <p className="eyebrow">THE OTHER SIDE</p>
                <h2 id="empty-review-heading">Clarity is on the way</h2>
              </div>
              <span className="panel-icon" aria-hidden="true">
                ✦
              </span>
            </div>
            <PixelAnimation
              kind={loading ? "rage" : "investigate"}
              label={
                loading
                  ? "Turning the heat down. Finding your words."
                  : "A closer look. A clearer reply."
              }
            />
            <h3>
              {loading
                ? "A little less heat. A lot more clarity."
                : "A reply you can stand behind."}
            </h3>
            <p className="small-text">
              {loading
                ? "Checking the context and preparing your suggested reply. This animation is decorative, not a measured rage score."
                : "Your suggested reply will appear here, with supporting evidence and anything that needs a second look."}
            </p>
            <div className="empty-features">
              <span>✓ Your intent, preserved</span>
              <span>✓ Evidence shown separately</span>
              <span>✓ Always yours to edit</span>
            </div>
          </section>
        )}
      </div>
      {withEvidence && (
        <button
          type="button"
          className="history-banner"
          aria-haspopup="dialog"
          onClick={() => {
            setHistoryOpened(true);
            setDialog("history");
          }}
        >
          <PixelAnimation kind="folder" label="Conversation memory" />
          <span>
            <strong>Good replies have a little history.</strong>
            <span>
              Import conversations to find the facts behind your reply.
            </span>
          </span>
          <span className="history-banner-action">Open history</span>
        </button>
      )}
      <footer className="workspace-footer">
        <span>
          Draft freely. Review carefully. You decide what happens next.
        </span>
        <span>MADE FOR A COOLER HEAD.</span>
      </footer>
    </main>
  );
}

"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import ChatWindow from "@/frontend/features/reply/ChatWindow";
import ComparePanel from "@/frontend/features/reply/ComparePanel";
import HistoryPanel from "@/frontend/features/memory/HistoryPanel";
import PreferencesPanel, {
  readLocalPreferences,
} from "@/frontend/features/preferences/PreferencesPanel";
import DisplaySettings from "@/frontend/features/preferences/DisplaySettings";
import { appendDictation } from "@/frontend/features/reply/DictationControls";
import VentInput from "@/frontend/features/reply/VentInput";
import type { GenerateReplyResponse, ReplyTone } from "@/frontend/api/contract";
import PixelAnimation from "@/frontend/shared/PixelAnimation";
import ReplyInsights from "@/frontend/features/reply/ReplyInsights";
import ReplyProcessing from "@/frontend/features/reply/ReplyProcessing";
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
  const [pendingReply, setPendingReply] = useState<typeof result>(null);
  const [animationDone, setAnimationDone] = useState(false);
  const finishAnimation = useCallback(() => setAnimationDone(true), []);

  const regeneratingRequest = useRef(false);
  const inFlight = useRef(false);
  const requestTiming = useRef<{ startedAt: number; estimateMs: number | null }>({ startedAt: 0, estimateMs: null });
  const successfulDurations = useRef<number[]>([]);
  const canSubmit = Boolean(managerMessage.trim() && draft.trim());
  const withEvidence = mode === "evidence";
  const showReview = withEvidence && Boolean(result);

  useEffect(() => {
    if (!animationDone || !pendingReply) return;
    setResult(pendingReply);
    setReply(pendingReply.data.reply);
    setPendingReply(null);
    inFlight.current = false;
    setLoading(false);
  }, [animationDone, pendingReply]);

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
    regeneratingRequest.current = Boolean(result);
    setAnimationDone(false);
    setPendingReply(null);
    setLoading(true);
    setError("");
    const samples = successfulDurations.current;
    const startedAt = performance.now();
    requestTiming.current = {
      startedAt,
      estimateMs: samples.length ? samples.reduce((total, ms) => total + ms, 0) / samples.length : null,
    };

    try {
      const data = await generateReply({
        managerMessage,
        employeeDraft: draft,
        tone,
      });
      successfulDurations.current = [...samples, performance.now() - startedAt].slice(-3);
      setPendingReply({ data, tone });
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not generate a reply. Try again.",
      );
      inFlight.current = false;
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <ReplyProcessing
        regenerating={regeneratingRequest.current}
        synthetic={isMockMode}
        replyReady={Boolean(pendingReply)}
        {...requestTiming.current}
        onAnimationComplete={finishAnimation}
      />
    );
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
      {withEvidence && (
        <button
          type="button"
          className="history-banner history-banner-top"
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
          className="secondary-button settings-icon-button"
          aria-label="Settings"
          title="Settings"
          aria-haspopup="dialog"
          onClick={() => setDialog("settings")}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
            <path d="M9 2h6v3h3v3h3v8h-3v3h-3v3H9v-3H6v-3H3V8h3V5h3V2Z" />
            <circle cx="12" cy="12" r="3.5" />
          </svg>
        </button>
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
        {dialog === "settings" && <DisplaySettings />}
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
                    "Can you confirm why the shared document hasn't been reviewed yet? I uploaded the document link to the shared drive and expected you to be able to start reviewing it. Before we discuss the next steps, please let me know whether you have been able to open the link, what is preventing you from accessing the material, and what you need from me to move forward. I would appreciate a clear update rather than another general acknowledgement. If there is an access problem, please explain the issue so that we can resolve it and agree on a realistic time for the review.",
                  );
                  setDraft(
                    "I am frustrated that this is being treated as though I just ignored the document. I want to review it, but I cannot open the shared link because it asks for a password that I do not currently have. Having a link to the shared drive is not the same as having access to the protected document. I do not want my reply to sound defensive, but I also do not want to accept blame for a review I cannot start. Please make it clear that I need the password before I can read the material and provide useful feedback. Once I can access it, we can agree on an appropriate review time. Keep the reply professional and focused on resolving the access issue. Do not invent a date when I asked for the password, claim that I already completed any part of the review, or promise a deadline I have not agreed to. If the imported conversation only confirms that a document location was shared, distinguish that from proof that a password was supplied.",
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
            key={withEvidence ? "evidence" : "quick"}
            value={withEvidence ? draft : quickDraft}
            onChange={withEvidence ? setDraft : setQuickDraft}
            onDictated={(text) => (withEvidence ? setDraft : setQuickDraft)((current) => appendDictation(current, text))}
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
              <button type="submit" className="secondary-button" disabled={!canSubmit}>Retry</button>
            </p>
          )}
        </form>
        {withEvidence && result && (
          <section
            className="panel workspace-panel workspace-review"
            aria-labelledby="review-heading"
            aria-busy={false}
          >
            <div className="panel-heading">
              <div>
                <p className="eyebrow">A COOLER HEAD</p>
                <h2 id="review-heading">Your words, reworked</h2>
              </div>
              <span className="ready-badge">Ready to review</span>
            </div>
            <ComparePanel
              polishedReply={reply}
              tone={result.tone}
              onChange={setReply}
            />
            <ReplyInsights {...result.data} />
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
                <h2 id="empty-review-heading">{withEvidence && error ? "No reply generated" : "Clarity is on the way"}</h2>
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
                : withEvidence && error
                  ? "Your draft is still here. Check the error above and try again when ready."
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
      <footer className="workspace-footer">
        <span>
          Draft freely. Review carefully. You decide what happens next.
        </span>
        <span>MADE FOR A COOLER HEAD.</span>
      </footer>
    </main>
  );
}

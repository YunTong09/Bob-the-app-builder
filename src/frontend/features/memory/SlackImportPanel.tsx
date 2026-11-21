import { useId, useRef, useState, type FormEvent } from "react";
import type {
  ImportMemoryResponse,
  MemoryMessage,
  SlackPreviewResponse,
} from "@/frontend/api/contract";
import {
  importMemory,
  isMockMode,
  previewSlack,
} from "@/frontend/api/replyApi";

const pageSize = 20;
const maxMessages = 100;
const maxImportBytes = 1_048_576;
const channelPattern = /^[CG][A-Z0-9]{1,127}$/;

export default function SlackImportPanel({
  onReviewHistory,
}: {
  onReviewHistory: () => void;
}) {
  const id = useId();
  const [channel, setChannel] = useState(isMockMode ? "CDEMO123" : "");
  const [preview, setPreview] = useState<SlackPreviewResponse | null>(null);
  const [selected, setSelected] = useState(new Map<string, MemoryMessage>());
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState<"preview" | "import" | null>(null);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ImportMemoryResponse | null>(null);
  const inFlight = useRef(false);

  async function run(
    action: NonNullable<typeof busy>,
    work: () => Promise<void>,
  ) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(action);
    setError("");
    try {
      await work();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The Slack import request failed. Try again.",
      );
    } finally {
      inFlight.current = false;
      setBusy(null);
    }
  }

  function changeChannel(value: string) {
    setChannel(value);
    setPreview(null);
    setSelected(new Map());
    setConfirming(false);
    setResult(null);
    setError("");
  }

  function loadPreview(cursor?: string) {
    return run("preview", async () => {
      const channelId = channel.trim();
      if (!channelPattern.test(channelId))
        throw new Error("Enter a Slack channel ID starting with C or G.");
      const page = await previewSlack({
        channelId,
        limit: pageSize,
        ...(cursor ? { cursor } : {}),
      });
      setPreview(page);
    });
  }

  function selectMessages(messages: MemoryMessage[], checked: boolean) {
    const next = new Map(selected);
    for (const message of messages) {
      if (checked) next.set(message.id, message);
      else next.delete(message.id);
    }
    if (next.size > maxMessages) {
      setError(`Select up to ${maxMessages} messages per import.`);
      return;
    }
    setSelected(next);
    setError("");
  }

  function confirmImport() {
    if (!confirming || !selected.size) return;
    void run("import", async () => {
      const messages = Array.from(selected.values());
      if (
        new TextEncoder().encode(JSON.stringify({ messages })).byteLength >
        maxImportBytes
      ) {
        throw new Error(
          "The selection exceeds 1 MiB. Deselect some messages and try again.",
        );
      }
      setResult(null);
      const imported = await importMemory(messages);
      setResult(imported);
      setSelected(new Map());
      setConfirming(false);
    });
  }

  function submitPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!confirming) void loadPreview();
  }

  const selectionDisabled = busy !== null || confirming;

  return (
    <section
      className="history-source-card history-slack-card"
      aria-labelledby={`${id}-heading`}
    >
      <div className="history-card-title">
        <span
          className="history-source-icon slack-source-icon"
          aria-hidden="true"
        >
          #
        </span>
        <div>
          <p className="eyebrow">FROM YOUR WORKSPACE</p>
          <h3 id={`${id}-heading`}>Import from Slack</h3>
        </div>
      </div>
      <p className="small-text" id={`${id}-hint`}>
        {isMockMode
          ? "Mock preview · Synthetic messages only."
          : "Enter the channel ID configured by your Slack app administrator."}
      </p>
      <form className="history-slack-form" onSubmit={submitPreview}>
        <div className="form-field">
          <label htmlFor={`${id}-channel`}>Slack channel ID</label>
          <input
            id={`${id}-channel`}
            className="plain-textarea"
            value={channel}
            required
            maxLength={128}
            autoComplete="off"
            spellCheck={false}
            disabled={busy !== null}
            aria-describedby={`${id}-hint`}
            onChange={(event) => changeChannel(event.target.value)}
          />
        </div>
        <button
          className="secondary-button"
          type="submit"
          disabled={selectionDisabled || !channel.trim()}
        >
          Preview messages
        </button>
      </form>
      <div role="status" className="small-text">
        {busy === "preview"
          ? "Loading Slack preview…"
          : busy === "import"
            ? "Importing selected messages…"
            : null}
        {busy === null && result && (
          <p>
            Imported {result.importedCount}{" "}
            {result.importedCount === 1 ? "message" : "messages"}. Skipped{" "}
            {result.skippedCount} already in history.
          </p>
        )}
      </div>
      {error && (
        <p className="error-message" role="alert">
          <span className="status-label status-label-error">Error</span>
          {error}
        </p>
      )}
      {result && (
        <div>
          <button
            type="button"
            className="secondary-button"
            disabled={busy !== null}
            onClick={onReviewHistory}
          >
            View imported memory
          </button>
        </div>
      )}
      {preview && (
        <div className="form-field">
          {preview.skippedCount > 0 && (
            <p className="small-text">
              {preview.skippedCount} messages on this page could not be
              previewed.
            </p>
          )}
          {preview.warnings.map((warning, index) => (
            <p key={index} className="small-text">
              {warning}
            </p>
          ))}
          {(preview.messages.length > 0 || selected.size > 0) && (
            <div className="history-controls">
              {preview.messages.length > 0 && (
                <button
                  type="button"
                  className="secondary-button"
                  disabled={selectionDisabled}
                  onClick={() => selectMessages(preview.messages, true)}
                >
                  Select all on this page
                </button>
              )}
              <button
                type="button"
                className="secondary-button"
                disabled={selectionDisabled || !selected.size}
                onClick={() =>
                  selectMessages(Array.from(selected.values()), false)
                }
              >
                Deselect all
              </button>
            </div>
          )}
          {preview.messages.length ? (
            <ul className="record-list">
              {preview.messages.map((message, index) => (
                <li key={message.id}>
                  <label>
                    <input
                      type="checkbox"
                      checked={selected.has(message.id)}
                      disabled={selectionDisabled}
                      aria-describedby={`${id}-message-${index}`}
                      onChange={(event) =>
                        selectMessages([message], event.target.checked)
                      }
                    />{" "}
                    {message.sender}
                  </label>
                  <p id={`${id}-message-${index}`}>{message.content}</p>
                  {(message.timestamp || message.source) && (
                    <p className="small-text">
                      {[message.timestamp, message.source]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="small-text">No messages to preview on this page.</p>
          )}
          <div className="history-controls">
            <p role="status" className="small-text">
              {selected.size} selected
            </p>
            {preview.nextCursor && (
              <button
                type="button"
                className="secondary-button"
                disabled={selectionDisabled}
                onClick={() =>
                  void loadPreview(preview.nextCursor ?? undefined)
                }
              >
                Next Slack page
              </button>
            )}
            {!confirming && (
              <button
                type="button"
                className="primary-button"
                disabled={busy !== null || !selected.size}
                onClick={() => {
                  setError("");
                  setConfirming(true);
                }}
              >
                Review selection
              </button>
            )}
          </div>
          {confirming && (
            <div
              className="history-confirm"
              role="group"
              aria-label="Confirm Slack import"
            >
              <p>
                Save {selected.size} selected{" "}
                {selected.size === 1 ? "message" : "messages"} to history?
              </p>
              <button
                type="button"
                className="secondary-button"
                disabled={busy !== null}
                onClick={() => {
                  setConfirming(false);
                  setError("");
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="primary-button"
                disabled={busy !== null}
                onClick={confirmImport}
              >
                {busy === "import" ? "Importing…" : "Confirm Slack import"}
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

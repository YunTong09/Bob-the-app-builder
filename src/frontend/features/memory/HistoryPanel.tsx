import PixelAnimation from "@/frontend/shared/PixelAnimation";
import SlackImportPanel from "./SlackImportPanel";
import { useRef, useState } from "react";
import type { SearchMemoryResponse } from "@/frontend/api/contract";
import {
  deleteAllMemory,
  importMemory,
  searchMemory,
  SYNTHETIC_IMPORT,
} from "@/frontend/api/replyApi";

const pageSize = 20;
const maxImportBytes = 1_048_576;

export default function HistoryPanel() {
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [page, setPage] = useState<SearchMemoryResponse | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const inFlight = useRef(false);

  async function run(action: () => Promise<void>) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not update history. Try again.",
      );
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  async function load(offset = 0, search = appliedQuery) {
    setPage(await searchMemory(search, pageSize, offset));
    setAppliedQuery(search);
  }

  async function importSample() {
    const result = await importMemory(SYNTHETIC_IMPORT.messages);
    setNotice(
      `Imported ${result.importedCount}. Skipped ${result.skippedCount} existing messages.`,
    );
    setQuery("");
    await load(0, "");
  }

  async function importHistory() {
    if (!file) return;
    if (file.size > maxImportBytes)
      throw new Error("Choose a JSON file of 1 MiB or less.");
    const contents = await file.text();
    let data: unknown;
    try {
      data = JSON.parse(contents);
    } catch {
      throw new Error("The file is not valid JSON.");
    }
    if (
      !data ||
      typeof data !== "object" ||
      !("messages" in data) ||
      Object.keys(data).length !== 1 ||
      !Array.isArray(data.messages)
    ) {
      throw new Error('Use a JSON object with a "messages" array.');
    }
    const result = await importMemory(data.messages);
    setFile(null);
    if (fileInput.current) fileInput.current.value = "";
    setNotice(
      `Imported ${result.importedCount}. Skipped ${result.skippedCount} existing messages.`,
    );
    setQuery("");
    await load(0, "");
  }

  function reviewHistory() {
    setQuery("");
    void run(() => load(0, ""));
  }

  async function deleteHistory() {
    const result = await deleteAllMemory();
    setPage({ messages: [], total: 0, limit: pageSize, offset: 0 });
    setConfirmDelete(false);
    setNotice(`Deleted ${result.deletedCount} saved messages.`);
  }

  return (
    <section className="history-panel" aria-labelledby="history-heading">
      <div className="history-intro">
        <div>
          <p className="eyebrow">THE CONTEXT BEHIND YOUR REPLY</p>
          <h2 id="history-heading">Good replies have a little history.</h2>
          <p>
            Bring in the conversations that matter. Find the facts, keep the
            receipts.
          </p>
          <span className="history-privacy">
            Only messages you choose to import are saved.
          </span>
        </div>
        <PixelAnimation
          kind="folder"
          label="The context behind your conversations"
          className="history-animation"
        />
      </div>

      <div className="history-import-grid">
        <section
          className="history-source-card"
          aria-labelledby="file-import-heading"
        >
          <div className="history-card-title">
            <span className="history-source-icon" aria-hidden="true">
              ▤
            </span>
            <div>
              <p className="eyebrow">FROM A FILE</p>
              <h3 id="file-import-heading">Import conversation JSON</h3>
            </div>
          </div>
          <p className="small-text">
            Upload an exported conversation in the supported message format.
          </p>
          <div className="history-file-field form-field">
            <label htmlFor="history-file">Conversation file</label>
            <input
              id="history-file"
              type="file"
              accept=".json,application/json"
              ref={fileInput}
              disabled={busy}
              aria-describedby="history-file-hint"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <p id="history-file-hint" className="small-text">
              JSON only · Up to 1 MiB and 100 messages per import.
            </p>
          </div>
          <button
            type="button"
            className="primary-button history-import-button"
            disabled={!file || busy}
            onClick={() => void run(importHistory)}
          >
            Import history <span aria-hidden="true">✦</span>
          </button>
          <div className="history-sample">
            <p>Just exploring? Start with synthetic conversations.</p>
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={() => void run(importSample)}
            >
              Import sample history
            </button>
          </div>
        </section>
        <SlackImportPanel onReviewHistory={reviewHistory} />
      </div>

      <section
        className="history-library"
        aria-labelledby="history-library-heading"
      >
        <div className="history-library-heading">
          <div>
            <p className="eyebrow">YOUR COMMUNICATION MEMORY</p>
            <h3 id="history-library-heading">
              Saved conversations{" "}
              {page && (
                <span className="history-count">{page.total} messages</span>
              )}
            </h3>
          </div>
          <button
            type="button"
            className="secondary-button"
            disabled={busy}
            onClick={reviewHistory}
          >
            Review history
          </button>
        </div>
        <form
          className="history-search-form"
          onSubmit={(event) => {
            event.preventDefault();
            void run(() => load(0, query.trim()));
          }}
        >
          <div className="form-field">
            <label htmlFor="history-search">Search saved messages</label>
            <input
              id="history-search"
              type="search"
              placeholder="Find a message, topic, or detail…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              disabled={busy}
            />
          </div>
          <button type="submit" className="secondary-button" disabled={busy}>
            Search
          </button>
        </form>
        <p className="history-notice small-text" role="status">
          {busy ? "Updating history…" : notice}
        </p>
        {error && (
          <p className="error-message" role="alert">
            <span className="status-label status-label-error">Error</span>
            {error}
          </p>
        )}
        {!page && (
          <div className="history-empty">
            <span aria-hidden="true">▧</span>
            <strong>A place for the facts behind your reply.</strong>
            <p>
              Import a conversation, or select Review history to see your saved
              messages.
            </p>
          </div>
        )}
        {page &&
          (page.messages.length === 0 ? (
            <div className="history-empty">
              <span aria-hidden="true">▧</span>
              <strong>
                {appliedQuery ? "No matching messages." : "A fresh start."}
              </strong>
              <p>
                {appliedQuery
                  ? "Try a different search or review all saved history."
                  : "No saved messages on this page. Import a conversation to add context."}
              </p>
            </div>
          ) : (
            <ul className="record-list history-records">
              {page.messages.map((message) => (
                <li key={message.id}>
                  <div className="history-record-author">
                    <span aria-hidden="true">▤</span>
                    <strong>{message.sender}</strong>
                  </div>
                  <p>{message.content}</p>
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
          ))}
        {page && page.total > pageSize && (
          <div className="history-pagination">
            <span className="small-text">
              Showing {page.offset + 1}–
              {Math.min(page.offset + page.limit, page.total)} of {page.total}
            </span>
            <div className="history-controls">
              <button
                type="button"
                className="secondary-button"
                disabled={busy || page.offset === 0}
                onClick={() =>
                  void run(() => load(Math.max(0, page.offset - pageSize)))
                }
              >
                Previous
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={busy || page.offset + page.limit >= page.total}
                onClick={() => void run(() => load(page.offset + page.limit))}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </section>

      <div className="history-management">
        <p>Your draft stays private. Imported history stays in your control.</p>
        <button
          type="button"
          className="history-delete-button"
          disabled={busy || !page?.total}
          onClick={() => setConfirmDelete(true)}
        >
          Delete history
        </button>
      </div>
      {confirmDelete && (
        <div
          className="history-confirm history-delete-confirm"
          role="group"
          aria-label="Confirm history deletion"
        >
          <div>
            <span className="status-label status-label-warning">
              Delete imported history?
            </span>
            <p>
              This removes all imported messages. Your current draft stays on
              this page.
            </p>
          </div>
          <button
            type="button"
            className="secondary-button"
            disabled={busy}
            onClick={() => setConfirmDelete(false)}
          >
            Cancel
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={busy}
            onClick={() => void run(deleteHistory)}
          >
            Confirm deletion
          </button>
        </div>
      )}
    </section>
  );
}

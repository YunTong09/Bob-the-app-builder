import SlackImportPanel from "./SlackImportPanel";
import { useRef, useState } from "react";
import type { SearchMemoryResponse } from "@/frontend/api/contract";
import { deleteAllMemory, importMemory, searchMemory, SYNTHETIC_IMPORT } from "@/frontend/api/replyApi";

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
      setError(caught instanceof Error ? caught.message : "Could not update history. Try again.");
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
    setNotice(`Imported ${result.importedCount}. Skipped ${result.skippedCount} existing messages.`);
    setQuery("");
    await load(0, "");
  }

  async function importHistory() {
    if (!file) return;
    if (file.size > maxImportBytes) throw new Error("Choose a JSON file of 1 MiB or less.");
    const contents = await file.text();
    let data: unknown;
    try {
      data = JSON.parse(contents);
    } catch {
      throw new Error("The file is not valid JSON.");
    }
    if (!data || typeof data !== "object" || !("messages" in data) || Object.keys(data).length !== 1 || !Array.isArray(data.messages)) {
      throw new Error('Use a JSON object with a "messages" array.');
    }
    const result = await importMemory(data.messages);
    setFile(null);
    if (fileInput.current) fileInput.current.value = "";
    setNotice(`Imported ${result.importedCount}. Skipped ${result.skippedCount} existing messages.`);
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
    <section className="panel history-panel" aria-labelledby="history-heading">
      <h2 id="history-heading">Conversation history</h2>
      <p className="small-text">Import past messages you’re allowed to use as supporting context.</p>
      <SlackImportPanel onReviewHistory={reviewHistory} />
      <div className="history-controls">
        <div className="form-field">
          <label htmlFor="history-file">Conversation history JSON</label>
          <input id="history-file" type="file" accept=".json,application/json" ref={fileInput}
            disabled={busy} onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </div>
        <button type="button" className="secondary-button" disabled={!file || busy} onClick={() => void run(importHistory)}>Import history</button>
        <button type="button" className="secondary-button" disabled={busy} onClick={reviewHistory}>Review history</button>
        <button type="button" className="secondary-button" disabled={busy || !page?.total} onClick={() => setConfirmDelete(true)}>Delete history</button>
      </div>
      <div>
        <button type="button" className="secondary-button" disabled={busy} onClick={() => void run(importSample)}>Import sample history</button>
      </div>
      <form className="history-controls" onSubmit={(event) => {
        event.preventDefault();
        void run(() => load(0, query.trim()));
      }}>
        <div className="form-field">
          <label htmlFor="history-search">Search saved messages</label>
          <input id="history-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} disabled={busy} />
        </div>
        <button type="submit" className="secondary-button" disabled={busy}>Search</button>
      </form>
      {confirmDelete && (
        <div className="history-confirm">
          <span className="status-label status-label-warning">Warning</span>
          <p>Delete all imported messages?</p>
          <button type="button" className="secondary-button" disabled={busy} onClick={() => setConfirmDelete(false)}>Cancel</button>
          <button type="button" className="secondary-button" disabled={busy} onClick={() => void run(deleteHistory)}>Confirm deletion</button>
        </div>
      )}
      <p className="small-text" role="status">{busy ? "Updating history…" : notice}</p>
      {error && <p className="error-message" role="alert"><span className="status-label status-label-error">Error</span>{error}</p>}
      {page && (
        <>
          {page.messages.length === 0 ? <p className="small-text">No saved messages on this page.</p> : (
            <ul className="record-list">
              {page.messages.map((message) => (
                <li key={message.id}>
                  <strong>{message.sender}</strong>
                  <p>{message.content}</p>
                  {(message.timestamp || message.source) && <p className="small-text">{[message.timestamp, message.source].filter(Boolean).join(" · ")}</p>}
                </li>
              ))}
            </ul>
          )}
          {page.total > pageSize && (
            <div className="history-controls">
              <button type="button" className="secondary-button" disabled={busy || page.offset === 0} onClick={() => void run(() => load(Math.max(0, page.offset - pageSize)))}>Previous</button>
              <button type="button" className="secondary-button" disabled={busy || page.offset + page.limit >= page.total} onClick={() => void run(() => load(page.offset + page.limit))}>Next</button>
            </div>
          )}
        </>
      )}
    </section>
  );
}

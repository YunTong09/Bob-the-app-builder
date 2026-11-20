import { useRef, useState } from "react";
import { webApi, type HistoryPage } from "@/lib/web-api";

const pageSize = 20;
const maxImportBytes = 1_048_576;

export default function HistoryPanel() {
  const [page, setPage] = useState<HistoryPage | null>(null);
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

  async function load(offset = 0) {
    setPage(await webApi<HistoryPage>(`/api/memory/search?limit=${pageSize}&offset=${offset}`));
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
    if (!data || typeof data !== "object" || !("messages" in data) || !Array.isArray(data.messages)) {
      throw new Error('Use a JSON object with a "messages" array.');
    }
    const result = await webApi<{ importedCount: number; skippedCount: number }>("/api/memory/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: contents,
    });
    setFile(null);
    if (fileInput.current) fileInput.current.value = "";
    setNotice(`Imported ${result.importedCount}. Skipped ${result.skippedCount} existing messages.`);
    await load();
  }

  async function deleteHistory() {
    const result = await webApi<{ deletedCount: number }>("/api/memory", { method: "DELETE" });
    setPage({ messages: [], total: 0, limit: pageSize, offset: 0 });
    setConfirmDelete(false);
    setNotice(`Deleted ${result.deletedCount} saved messages.`);
  }

  return (
    <section className="panel history-panel" aria-labelledby="history-heading">
      <h2 id="history-heading">Conversation history</h2>
      <p className="small-text">Import past messages you’re allowed to use as supporting context.</p>
      <div className="history-controls">
        <div className="form-field">
          <label htmlFor="history-file">Conversation history JSON</label>
          <input id="history-file" type="file" accept=".json,application/json" ref={fileInput}
            disabled={busy} onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </div>
        <button type="button" className="secondary-button" disabled={!file || busy} onClick={() => void run(importHistory)}>Import history</button>
        <button type="button" className="secondary-button" disabled={busy} onClick={() => void run(() => load())}>Review history</button>
        <button type="button" className="secondary-button" disabled={busy || !page?.total} onClick={() => setConfirmDelete(true)}>Delete history</button>
      </div>
      {confirmDelete && (
        <div className="history-confirm">
          <p>Delete all imported messages?</p>
          <button type="button" className="secondary-button" disabled={busy} onClick={() => setConfirmDelete(false)}>Cancel</button>
          <button type="button" className="secondary-button" disabled={busy} onClick={() => void run(deleteHistory)}>Confirm deletion</button>
        </div>
      )}
      <p className="small-text" role="status">{busy ? "Updating history…" : notice}</p>
      {error && <p className="error-message" role="alert">{error}</p>}
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

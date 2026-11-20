"use client";

import { useCallback, useEffect, useState } from "react";
import { MemoryMessage, StoredMemoryMessage } from "@/frontend/api/contract";
import { ApiError, deleteAllMemory, importMemory, isMockMode, SYNTHETIC_IMPORT, searchMemory } from "@/frontend/api/replyApi";
import { formatTimestamp } from "@/frontend/shared/formatTimestamp";

export default function MemoryPanel() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<StoredMemoryMessage[]>([]);
  const [total, setTotal] = useState(0);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [confirming, setConfirming] = useState(false);

  const refresh = useCallback(async (q: string) => {
    try {
      const data = await searchMemory(q);
      setMessages(data.messages);
      setTotal(data.total);
      setError("");
    } catch (caught) {
      setError(caught instanceof ApiError ? `Could not load history (${caught.code}).` : "Could not load history.");
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => refresh(query), 200);
    return () => clearTimeout(timer);
  }, [query, refresh]);

  async function runImport(list: MemoryMessage[]) {
    try {
      const result = await importMemory(list);
      setNote(`Imported ${result.importedCount}, skipped ${result.skippedCount} duplicate(s).`);
      setError("");
      await refresh(query);
    } catch (caught) {
      setNote("");
      setError(caught instanceof ApiError ? `Import failed (${caught.code}): ${caught.message}` : "Import failed.");
    }
  }

  async function onFile(file: File | undefined) {
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text());
      const list: unknown = Array.isArray(parsed) ? parsed : parsed?.messages;
      if (!Array.isArray(list) || list.length < 1 || list.length > 100) throw new Error("range");
      await runImport(list as MemoryMessage[]);
    } catch {
      setNote("");
      setError('Use a JSON file with 1–100 messages: { "messages": [ ... ] }.');
    }
  }

  async function onDeleteAll() {
    try {
      const result = await deleteAllMemory();
      setNote(`Deleted ${result.deletedCount} message(s).`);
      setConfirming(false);
      await refresh(query);
    } catch {
      setError("Could not delete history. Nothing was changed.");
    }
  }

  return (
    <div className="stack">
      <section className="card">
        <div className="row-between">
          <h3 className="card-title">Conversation JSON</h3>
          <span className="badge" role="status">{total} message{total === 1 ? "" : "s"}</span>
        </div>
        <div className="row">
          <label className="btn btn-secondary file-btn">
            Import JSON
            <input type="file" accept="application/json,.json" onChange={(e) => { onFile(e.target.files?.[0]); e.target.value = ""; }} />
          </label>
          {isMockMode && <button type="button" className="btn btn-secondary" onClick={() => runImport(SYNTHETIC_IMPORT.messages)}>Load sample</button>}
        </div>
        <label className="field-label" htmlFor="memory-search">Search</label>
        <input id="memory-search" className="input" value={query} maxLength={500} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. password" />
        <p className="meta" role="status">{note}</p>
        {error && <p className="meta text-error" role="alert">{error}</p>}
      </section>

      <section className="stack" aria-label="Saved messages">
        {messages.length === 0 && <p className="meta">No messages saved yet.</p>}
        {messages.map((m) => (
          <article key={m.id} className="card">
            <p className="meta">
              {m.sender}
              {m.timestamp && ` · ${formatTimestamp(m.timestamp)}`}
              {` · ${m.conversationId}`}
            </p>
            <p className="memory-text">{m.content}</p>
            <p className="meta">Source: {m.source ?? ""}</p>
          </article>
        ))}
      </section>

      {confirming ? (
        <section className="card status-card status-warning" role="alertdialog" aria-label="Confirm delete">
          <div>
            <strong>Delete all saved messages?</strong>
            <p className="meta">This removes your imported history. It can&apos;t be undone.</p>
            <div className="row">
              <button type="button" className="btn btn-danger" onClick={onDeleteAll}>Yes, delete all</button>
              <button type="button" className="btn btn-secondary" onClick={() => setConfirming(false)}>Cancel</button>
            </div>
          </div>
        </section>
      ) : (
        <button type="button" className="btn btn-danger-outline" onClick={() => setConfirming(true)} disabled={total === 0}>
          🗑 Delete all JSON
        </button>
      )}
    </div>
  );
}

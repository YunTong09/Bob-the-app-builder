import PixelAnimation from "@/frontend/shared/PixelAnimation";
import SlackImportPanel from "./SlackImportPanel";
import { useRef, useState } from "react";
import type { SearchMemoryResponse } from "@/frontend/api/contract";
import { SYNTHETIC_SLACK_EXPORT_FILES } from "./sampleSlackExport";
import { isSlackExportJsonPath, parseSlackImport } from "./slackImport";
import {
  deleteAllMemory,
  importMemory,
  searchMemory,
} from "@/frontend/api/replyApi";

const pageSize = 20;
const maxImportBytes = 1_048_576;

type HistoryPanelProps = {
  onHistoryChanged?: (change?: "import" | "delete") => void;
  onParticipants?: (names: Record<string, string>) => void;
  onConversationNames?: (names: Record<string, string>) => void;
};

export default function HistoryPanel({ onHistoryChanged, onParticipants, onConversationNames }: HistoryPanelProps) {
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [page, setPage] = useState<SearchMemoryResponse | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [preview, setPreview] = useState<ReturnType<typeof parseSlackImport> | null>(null);
  const [participantNames, setParticipantNames] = useState<Record<string, string>>({});
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

  async function previewSample() {
    showPreview(parseSlackImport(SYNTHETIC_SLACK_EXPORT_FILES));
    setNotice("Synthetic Slack export ready to review. Nothing has been saved yet.");
  }

  function showPreview(parsed: ReturnType<typeof parseSlackImport>) {
    setPreview(parsed);
    // Resolve saved sender IDs from this export's user registry without
    // requiring another memory import just to display participant names.
    setParticipantNames((current) => ({ ...current, ...parsed.participants }));
    onParticipants?.(parsed.participants);
    onConversationNames?.(parsed.conversationNames ?? {});
  }

  async function previewFolder() {
    if (!files.length) return;
    setPreview(null);
    if (files.some((file) => !file.webkitRelativePath))
      throw new Error("Your browser did not provide folder paths. Use a browser that supports folder selection.");
    const relevantFiles = files.filter((file) => isSlackExportJsonPath(file.webkitRelativePath));
    if (!relevantFiles.length)
      throw new Error("Choose an extracted Slack export folder containing users.json, channels.json and channel folders with dated message JSON files.");
    if (relevantFiles.reduce((size, file) => size + file.size, 0) > maxImportBytes)
      throw new Error("The export's user, channel and message JSON exceeds 1 MiB. Choose a smaller export.");
    const parsedFiles = await Promise.all(relevantFiles.map(async (file) => {
      let data: unknown;
      try {
        data = JSON.parse(await file.text());
      } catch {
        throw new Error("A user, channel or message file in the selected folder is not valid JSON.");
      }
      return { name: file.name, data, relativePath: file.webkitRelativePath };
    }));
    showPreview(parseSlackImport(parsedFiles));
    setNotice("Review the messages below before importing. Nothing has been saved yet.");
  }

  async function importPreview() {
    if (!preview?.messages.length) return;
    const result = await importMemory(preview.messages);
    setParticipantNames((current) => ({ ...current, ...preview.participants }));
    onParticipants?.(preview.participants);
    onConversationNames?.(preview.conversationNames ?? {});
    onHistoryChanged?.("import");
    setPreview(null);
    setFiles([]);
    if (fileInput.current) fileInput.current.value = "";
    setNotice(
      `Imported ${result.importedCount}. Skipped ${result.skippedCount} existing messages.`,
    );
    setQuery("");
    await load(0, "");
  }

  function participantLabel(sender: string, names = participantNames) {
    const name = Object.prototype.hasOwnProperty.call(names, sender) ? names[sender] : undefined;
    return name ? `${name} (${sender})` : sender;
  }

  function reviewHistory() {
    setQuery("");
    void run(() => load(0, ""));
  }

  async function deleteHistory() {
    const result = await deleteAllMemory();
    setPage({ messages: [], total: 0, limit: pageSize, offset: 0 });
    setConfirmDelete(false);
    setParticipantNames({});
    onParticipants?.({});
    onConversationNames?.({});
    onHistoryChanged?.("delete");
    setNotice(`Deleted ${result.deletedCount} saved messages.`);
  }

  const folderName = files[0]?.webkitRelativePath.split("/")[0] ?? "";
  const relevantFileCount = files.filter((file) => isSlackExportJsonPath(file.webkitRelativePath)).length;

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
              <p className="eyebrow">FROM AN EXPORT FOLDER</p>
              <h3 id="file-import-heading">Import Slack export</h3>
            </div>
          </div>
          <p className="small-text">
            Select the extracted Slack export folder. Participant names and channels
            are read from users.json and channels.json, with dated messages grouped
            by channel automatically.
          </p>
          <div className="history-file-field form-field">
            <label htmlFor="history-folder">Slack export folder</label>
            <input
              id="history-folder"
              type="file"
              className="sr-only"
              tabIndex={-1}
              {...{ webkitdirectory: "" }}
              multiple
              ref={fileInput}
              disabled={busy}
              aria-describedby="history-folder-hint"
              onChange={(event) => {
                setFiles(Array.from(event.target.files ?? []));
                setPreview(null);
                setError("");
                setNotice("");
              }}
            />
            <button type="button" className="secondary-button" disabled={busy} onClick={() => fileInput.current?.click()}>
              Choose export folder
            </button>
            <p id="history-folder-hint" className="small-text">
              Choose the folder after extracting its ZIP. Up to 1 MiB of relevant JSON
              and 100 messages per import. Attachments and unrelated export metadata are ignored.
            </p>
            {files.length > 0 && (
              <p className="small-text" role="status">
                {folderName ? `Selected folder: ${folderName}. ` : "Folder paths unavailable. "}
                {relevantFileCount} relevant JSON files; {files.length - relevantFileCount} other files ignored.
              </p>
            )}
          </div>
          <button
            type="button"
            className="primary-button history-import-button"
            disabled={!files.length || busy}
            onClick={() => void run(previewFolder)}
          >
            Preview folder import <span aria-hidden="true">✦</span>
          </button>
          <div className="history-sample">
            <p>Try a synthetic week of Slack conversations with varied workplace situations. Choose a manager message and write your own draft.</p>
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={() => void run(previewSample)}
            >
              Preview sample Slack export
            </button>
          </div>
          {preview && (
            <section aria-labelledby="file-preview-heading">
              <h4 id="file-preview-heading">Review {preview.messages.length} messages</h4>
              <p className="small-text">No participant is assumed to be your manager. You choose who is who in the reply workspace after importing.</p>
              {preview.skippedCount > 0 && <p className="small-text">Skipped {preview.skippedCount} unsupported messages.</p>}
              {preview.warnings.map((warning, index) => <p className="small-text" key={index}>{warning}</p>)}
              <ul className="record-list">
                {preview.messages.map((message) => (
                  <li key={message.id}>
                    <strong>{participantLabel(message.sender, preview.participants)}</strong>
                    <p>{message.content}</p>
                    {(message.timestamp || message.source) && <p className="small-text">{[message.timestamp, message.source].filter(Boolean).join(" · ")}</p>}
                  </li>
                ))}
              </ul>
              <div className="history-controls">
                <button type="button" className="secondary-button" disabled={busy} onClick={() => setPreview(null)}>Cancel import</button>
                <button type="button" className="primary-button" disabled={busy || !preview.messages.length} onClick={() => void run(importPreview)}>
                  Import {preview.messages.length} messages
                </button>
              </div>
            </section>
          )}
        </section>
        <SlackImportPanel onReviewHistory={reviewHistory} onImported={() => onHistoryChanged?.("import")} />
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
                    <strong>{participantLabel(message.sender)}</strong>
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

"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { StoredMemoryMessage } from "@/frontend/api/contract";
import { searchMemory } from "@/frontend/api/replyApi";
import { formatTimestamp } from "@/frontend/shared/formatTimestamp";
import { sharedConversations, validSelection, type ImportedMessageSelection } from "./importedMessageSelection";

export type { ImportedMessageSelection } from "./importedMessageSelection";

type Props = {
  revision: number;
  participantNames?: Record<string, string>;
  conversationNames?: Record<string, string>;
  selection: ImportedMessageSelection;
  onSelectionChange: (selection: ImportedMessageSelection) => void;
  onUseMessage: (message: StoredMemoryMessage | null) => void;
};

const pageSize = 100;
const maxPages = 100;

function unchanged(a: ImportedMessageSelection, b: ImportedMessageSelection) {
  return a.selfId === b.selfId && a.managerId === b.managerId && a.conversationId === b.conversationId && a.messageId === b.messageId;
}

export default function ImportedMessagePicker({
  revision,
  participantNames,
  conversationNames,
  selection,
  onSelectionChange,
  onUseMessage,
}: Props) {
  const id = useId();
  const [messages, setMessages] = useState<StoredMemoryMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const current = useRef({ selection, onSelectionChange, onUseMessage });

  useEffect(() => {
    current.current = { selection, onSelectionChange, onUseMessage };
  }, [selection, onSelectionChange, onUseMessage]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");

    async function load() {
      try {
        const collected: StoredMemoryMessage[] = [];
        let total: number | undefined;
        for (let pageIndex = 0; pageIndex < maxPages; pageIndex += 1) {
          const page = await searchMemory("", pageSize, collected.length);
          if (cancelled) return;
          if (page.total > maxPages * pageSize) {
            throw new Error("This message picker supports up to 10,000 saved messages. You can still add a manager message manually.");
          }
          if (total !== undefined && total !== page.total) {
            throw new Error("Your saved history changed while loading. Refresh the messages and try again.");
          }
          total = page.total;
          collected.push(...page.messages);
          if (collected.length >= total) break;
          if (!page.messages.length || pageIndex === maxPages - 1) {
            throw new Error("Could not load all saved messages. Refresh the messages and try again.");
          }
        }
        if (new Set(collected.map((message) => message.id)).size !== collected.length) {
          throw new Error("Your saved history changed while loading. Refresh the messages and try again.");
        }
        setMessages(collected);
        const latest = current.current;
        const checked = validSelection(latest.selection, collected);
        if (!unchanged(latest.selection, checked)) {
          latest.onSelectionChange(checked);
          latest.onUseMessage(null);
        }
      } catch (caught) {
        if (cancelled) return;
        setMessages([]);
        setError(caught instanceof Error ? caught.message : "Could not load saved messages. Try again.");
        const latest = current.current;
        if (latest.selection.messageId) {
          latest.onSelectionChange({ ...latest.selection, messageId: "" });
          latest.onUseMessage(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [revision, retry]);

  const senders = useMemo(() => Array.from(new Set(messages.map((message) => message.sender))).sort(), [messages]);
  const conversations = useMemo(() => sharedConversations(messages, selection.selfId, selection.managerId), [messages, selection.selfId, selection.managerId]);
  const managerMessages = useMemo(() => messages
    .filter((message) => message.sender === selection.managerId && message.conversationId === selection.conversationId)
    .sort((a, b) => (Date.parse(b.timestamp ?? "") || 0) - (Date.parse(a.timestamp ?? "") || 0) || b.id.localeCompare(a.id)), [messages, selection.managerId, selection.conversationId]);
  const chosenMessage = managerMessages.find((message) => message.id === selection.messageId);
  const rolesChosen = Boolean(selection.selfId && selection.managerId && selection.selfId !== selection.managerId);

  function participantName(sender: string) {
    const name = participantNames && Object.prototype.hasOwnProperty.call(participantNames, sender) ? participantNames[sender] : undefined;
    return name || sender;
  }

  function participantLabel(sender: string) {
    const label = participantName(sender);
    const duplicates = senders.filter((other) => participantName(other) === label);
    return duplicates.length > 1 ? `${label} (${duplicates.indexOf(sender) + 1})` : label;
  }

  function conversationLabel(conversation: string) {
    const name = conversationNames && Object.prototype.hasOwnProperty.call(conversationNames, conversation) ? conversationNames[conversation] : undefined;
    if (!name) return `Imported conversation ${conversations.indexOf(conversation) + 1}`;
    const duplicates = conversations.filter((other) => conversationNames?.[other] === name);
    return duplicates.length > 1 ? `${name} (${duplicates.indexOf(conversation) + 1})` : name;
  }

  function update(next: ImportedMessageSelection) {
    onSelectionChange(next);
    onUseMessage(null);
  }

  return (
    <section className="imported-message-picker" aria-labelledby={`${id}-heading`} aria-busy={loading}>
      <div className="imported-message-heading">
        <h3 id={`${id}-heading`}>Reply to an imported message</h3>
        <button type="button" className="secondary-button" disabled={loading} onClick={() => setRetry((value) => value + 1)}>
          Refresh messages
        </button>
      </div>
      <p className="small-text">Choose who is who, then select the message you want to answer. Roles are your choice and stay in this workspace for this visit.</p>
      {loading && <p className="small-text" role="status">Loading saved messages...</p>}
      {error && <p className="error-message" role="alert">{error}</p>}
      {!loading && !error && !messages.length && (
        <p className="small-text">Import conversation history to choose a message. You can also write a draft without importing history.</p>
      )}
      {!loading && !error && messages.length > 0 && (
        <>
          <div className="imported-message-roles">
            <div className="form-field">
              <label htmlFor={`${id}-self`}>You</label>
              <select id={`${id}-self`} value={selection.selfId} onChange={(event) => update({ selfId: event.target.value, managerId: event.target.value === selection.managerId ? "" : selection.managerId, conversationId: "", messageId: "" })}>
                <option value="">Select your participant</option>
                {senders.map((sender) => <option key={sender} value={sender}>{participantLabel(sender)}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label htmlFor={`${id}-manager`}>Your manager</label>
              <select id={`${id}-manager`} value={selection.managerId} onChange={(event) => update({ ...selection, managerId: event.target.value, conversationId: "", messageId: "" })}>
                <option value="">Select your manager</option>
                {senders.filter((sender) => sender !== selection.selfId).map((sender) => <option key={sender} value={sender}>{participantLabel(sender)}</option>)}
              </select>
            </div>
          </div>
          {rolesChosen && !conversations.length && <p className="small-text" role="status">No imported conversation contains messages from both selected participants. Import their conversation or choose different participants.</p>}
          {rolesChosen && conversations.length > 0 && (
            <>
              <div className="form-field">
                <label htmlFor={`${id}-conversation`}>Conversation</label>
                <select id={`${id}-conversation`} value={selection.conversationId} onChange={(event) => update({ ...selection, conversationId: event.target.value, messageId: "" })}>
                  <option value="">Select a conversation</option>
                  {conversations.map((conversation) => <option key={conversation} value={conversation}>{conversationLabel(conversation)}</option>)}
                </select>
              </div>
              {selection.conversationId && (
                <div className="form-field">
                  <label htmlFor={`${id}-message`}>Manager message to reply to</label>
                  <select id={`${id}-message`} value={selection.messageId} onChange={(event) => update({ ...selection, messageId: event.target.value })}>
                    <option value="">Select a manager message</option>
                    {managerMessages.map((message) => <option key={message.id} value={message.id}>{[formatTimestamp(message.timestamp), message.content.slice(0, 120)].filter(Boolean).join(" - ")}</option>)}
                  </select>
                </div>
              )}
              {chosenMessage && (
                <div className="imported-message-preview">
                  <blockquote>{chosenMessage.content}</blockquote>
                  {(chosenMessage.timestamp || chosenMessage.source) && <p className="small-text">{[chosenMessage.timestamp, chosenMessage.source].filter(Boolean).join(" - ")}</p>}
                  <button type="button" className="secondary-button" onClick={() => onUseMessage(chosenMessage)}>Use selected message</button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}

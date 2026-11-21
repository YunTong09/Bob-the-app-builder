import type { StoredMemoryMessage } from "@/frontend/api/contract";

export interface ImportedMessageSelection {
  selfId: string;
  managerId: string;
  conversationId: string;
  messageId: string;
}

export function sharedConversations(messages: StoredMemoryMessage[], selfId: string, managerId: string) {
  if (!selfId || !managerId || selfId === managerId) return [];
  const mine = new Set(messages.filter((message) => message.sender === selfId).map((message) => message.conversationId));
  return Array.from(new Set(messages
    .filter((message) => message.sender === managerId && mine.has(message.conversationId))
    .map((message) => message.conversationId))).sort();
}

/** Remove context that no longer belongs to the explicitly chosen people/conversation. */
export function validSelection(selection: ImportedMessageSelection, messages: StoredMemoryMessage[]): ImportedMessageSelection {
  const senders = new Set(messages.map((message) => message.sender));
  const selfId = senders.has(selection.selfId) ? selection.selfId : "";
  const managerId = senders.has(selection.managerId) && selection.managerId !== selfId ? selection.managerId : "";
  const conversations = sharedConversations(messages, selfId, managerId);
  const conversationId = conversations.includes(selection.conversationId) ? selection.conversationId : "";
  const messageId = messages.some((message) => message.id === selection.messageId && message.sender === managerId && message.conversationId === conversationId)
    ? selection.messageId : "";
  return { selfId, managerId, conversationId, messageId };
}

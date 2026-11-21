import assert from "node:assert/strict";
import test from "node:test";
import { loadTsModule } from "./load-ts-test-module.mjs";

const { sharedConversations, validSelection } = await loadTsModule("src/frontend/features/reply/importedMessageSelection.ts");

const record = (id, sender, conversationId) => ({ id, sender, conversationId, content: `Original ${id}\n  preserved.`, timestamp: null, source: null });
const messages = [
  record("my-message", "UEMPLOYEE", "shared"),
  record("manager-message", "UMANAGER", "shared"),
  record("teammate-message", "UTEAMMATE", "shared"),
  record("manager-other-channel", "UMANAGER", "other"),
  record("my-other-channel", "UEMPLOYEE", "mine-only"),
];
const selected = { selfId: "UEMPLOYEE", managerId: "UMANAGER", conversationId: "shared", messageId: "manager-message" };

test("a group conversation is eligible only when it contains both chosen participants", () => {
  assert.deepEqual(sharedConversations(messages, "UEMPLOYEE", "UMANAGER"), ["shared"]);
  assert.deepEqual(sharedConversations(messages, "", "UMANAGER"), []);
  assert.deepEqual(sharedConversations(messages, "UEMPLOYEE", ""), []);
  assert.deepEqual(sharedConversations(messages, "UMANAGER", "UMANAGER"), []);
});

test("valid selection keeps exact IDs and does not change original message data", () => {
  const original = structuredClone(messages);
  assert.deepEqual(validSelection(selected, messages), selected);
  assert.deepEqual(messages, original);
});

test("a teammate message cannot become the selected manager message", () => {
  assert.deepEqual(validSelection({ ...selected, messageId: "teammate-message" }, messages), { ...selected, messageId: "" });
});

test("a real manager message from a different conversation cannot be selected", () => {
  assert.deepEqual(validSelection({ ...selected, messageId: "manager-other-channel" }, messages), { ...selected, messageId: "" });
  assert.deepEqual(validSelection({ ...selected, conversationId: "other", messageId: "manager-other-channel" }, messages), { ...selected, conversationId: "", messageId: "" });
});

test("removing the selected message clears it while retaining valid chosen people", () => {
  assert.deepEqual(validSelection(selected, messages.filter((message) => message.id !== "manager-message")), { ...selected, conversationId: "", messageId: "" });
});

test("removing history clears stale roles and context rather than inventing replacements", () => {
  assert.deepEqual(validSelection(selected, []), { selfId: "", managerId: "", conversationId: "", messageId: "" });
});

test("the same participant cannot be both the employee and manager", () => {
  assert.deepEqual(validSelection({ ...selected, managerId: "UEMPLOYEE" }, messages), { selfId: "UEMPLOYEE", managerId: "", conversationId: "", messageId: "" });
});

test("changing a role invalidates the previous author's message", () => {
  assert.deepEqual(validSelection({ ...selected, managerId: "UTEAMMATE" }, messages), { ...selected, managerId: "UTEAMMATE", messageId: "" });
});

test("loading history never chooses roles, a conversation, or a message automatically", () => {
  assert.deepEqual(validSelection({ selfId: "", managerId: "", conversationId: "", messageId: "" }, messages), { selfId: "", managerId: "", conversationId: "", messageId: "" });
  assert.deepEqual(validSelection({ ...selected, messageId: "" }, messages), { ...selected, messageId: "" });
});

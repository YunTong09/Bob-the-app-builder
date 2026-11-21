import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { join, relative } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { loadTsModule } from "./load-ts-test-module.mjs";

const { parseSlackImport, isSlackExportJsonPath } = await loadTsModule("src/frontend/features/memory/slackImport.ts");
const root = new URL("../src/data/slack-export/", import.meta.url);
const manifest = JSON.parse(await readFile(new URL("../src/data/slack-week-scenarios.json", import.meta.url), "utf8"));
const entries = await readdir(root, { recursive: true, withFileTypes: true });
const files = [];
for (const entry of entries) {
  if (!entry.isFile()) continue;
  const fixturePath = relative(fileURLToPath(root), join(entry.parentPath, entry.name)).replaceAll("\\", "/");
  files.push({
    name: entry.name,
    relativePath: `slack-export/${fixturePath}`,
    data: isSlackExportJsonPath(`slack-export/${fixturePath}`)
      ? JSON.parse(await readFile(join(entry.parentPath, entry.name), "utf8")) : null,
  });
}
const parsed = parseSlackImport(files);
const messages = new Map(parsed.messages.map((message) => [message.id, message]));
const users = JSON.parse(await readFile(new URL("users.json", root), "utf8"));
const channels = JSON.parse(await readFile(new URL("channels.json", root), "utf8"));
const humanIds = new Set(users.filter((user) => !user.is_bot && !user.is_app_user).map((user) => user.id));
const channelByFolder = new Map(channels.map((channel) => [channel.name, channel.id]));
const dateFormatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: manifest.timeZone, year: "numeric", month: "2-digit", day: "2-digit",
});
const dayOf = (timestamp) => dateFormatter.format(new Date(timestamp));
const rawMessages = files.filter((file) => /\/\d{4}-\d{2}-\d{2}\.json$/.test(file.relativePath)).flatMap((file) =>
  file.data.map((message) => ({ message, file })),
);

test("the complete work week fits one supported import and includes all seven local dates", () => {
  assert.equal(manifest.weekStart, "2026-11-16");
  assert.equal(manifest.weekEnd, "2026-11-22");
  assert.equal(manifest.timeZone, "Australia/Brisbane");
  assert.ok(parsed.messages.length >= manifest.scenarios.length * 4, "Each situation needs actual conversation context, not a lone prompt.");
  assert.ok(parsed.messages.length <= 100);
  assert.ok(Buffer.byteLength(JSON.stringify({ messages: parsed.messages })) <= 1_048_576);
  assert.deepEqual([...new Set(parsed.messages.map((message) => dayOf(message.timestamp)))].sort(), [
    "2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-21", "2026-11-22",
  ]);
  assert.ok(parsed.skippedCount >= 2, "The realistic export retains excluded bot/system records.");
  assert.equal(new Set(parsed.messages.map((message) => message.conversationId)).size, 3);
});

test("dated channel files preserve registered authors and the stated local day", () => {
  for (const { message, file } of rawMessages) {
    if (message.type !== "message" || message.subtype || !humanIds.has(message.user)) continue;
    const [, channelFolder, dateFile] = file.relativePath.split("/");
    const channelId = channelByFolder.get(channelFolder);
    assert.ok(channelId, `Unregistered channel folder ${channelFolder}`);
    const id = `slack-export:${channelId}:${message.ts}`;
    const imported = messages.get(id);
    assert.ok(imported, `Human record missing from import: ${id}`);
    assert.equal(imported.sender, message.user);
    assert.equal(imported.content, message.text);
    assert.equal(dayOf(imported.timestamp), dateFile.slice(0, -5), `Timestamp and dated file disagree for ${id}`);
  }
  assert.equal(messages.get("slack-export:C08PROJECT1:1795047300.000001").timestamp, "2026-11-19T00:15:00.000001Z");
  assert.ok(humanIds.has(manifest.employeeId));
  assert.ok(humanIds.has(manifest.managerId));
  assert.notEqual(manifest.employeeId, manifest.managerId);
});

test("channel metadata predates its conversation rather than describing a workspace created midweek", () => {
  for (const channel of channels) {
    const records = rawMessages.filter(({ file }) => file.relativePath.split("/")[1] === channel.name);
    assert.ok(records.length > 0, `Empty exported channel ${channel.name}`);
    const earliestSeconds = Math.min(...records.map(({ message }) => Number(message.ts.split(".")[0])));
    assert.ok(Number.isInteger(channel.created) && channel.created <= earliestSeconds, channel.name);
  }
});

test("at least ten distinct situations have a real manager message and earlier conversation context", () => {
  assert.ok(manifest.scenarios.length >= 10);
  assert.equal(new Set(manifest.scenarios.map((scenario) => scenario.id)).size, manifest.scenarios.length);
  assert.equal(new Set(manifest.scenarios.map((scenario) => scenario.title)).size, manifest.scenarios.length);
  assert.equal(new Set(manifest.scenarios.map((scenario) => scenario.managerMessageId)).size, manifest.scenarios.length);
  for (const scenario of manifest.scenarios) {
    const managerMessage = messages.get(scenario.managerMessageId);
    assert.ok(managerMessage, `Missing manager prompt for ${scenario.id}`);
    assert.equal(managerMessage.sender, manifest.managerId, scenario.id);
    assert.equal(managerMessage.conversationId, `slack-export:${scenario.channelId}`, scenario.id);
    assert.ok(scenario.contextMessageIds.length > 0, `No earlier context for ${scenario.id}`);
    for (const contextId of scenario.contextMessageIds) {
      const context = messages.get(contextId);
      assert.ok(context, `Missing context ${contextId} for ${scenario.id}`);
      assert.equal(context.conversationId, managerMessage.conversationId, scenario.id);
      assert.ok(context.timestamp < managerMessage.timestamp, `Context must precede ${scenario.id}'s manager prompt`);
    }
    assert.ok(typeof scenario.writingPrompt === "string" && scenario.writingPrompt.trim(), scenario.id);
    assert.ok(typeof scenario.evidenceExpectation === "string" && scenario.evidenceExpectation.trim(), scenario.id);
    for (const solutionField of ["employeeDraft", "reply", "suggestedReply", "professionalReply"]) {
      assert.equal(solutionField in scenario, false, `${scenario.id} must leave users free to write their own draft`);
    }
  }
});

test("practice includes supported evidence, contradictory history and unverified claims", () => {
  assert.deepEqual([...new Set(manifest.scenarios.map((scenario) => scenario.evidenceStatus))].sort(), [
    "contradicted", "supported", "unverified",
  ]);
  for (const scenario of manifest.scenarios.filter((scenario) => scenario.evidenceStatus !== "supported")) {
    assert.ok(scenario.evidenceExpectation.length > 30, `${scenario.id} needs an explanation of uncertainty or conflict`);
  }
});

test("Slack threads reference earlier messages in the same channel", () => {
  const rawByChannelAndTimestamp = new Map(rawMessages.map(({ message, file }) => [
    `${file.relativePath.split("/")[1]}:${message.ts}`, message,
  ]));
  let threads = 0;
  for (const { message, file } of rawMessages) {
    if (!message.thread_ts || message.thread_ts === message.ts) continue;
    const parent = rawByChannelAndTimestamp.get(`${file.relativePath.split("/")[1]}:${message.thread_ts}`);
    assert.ok(parent, `Missing parent for thread reply ${message.ts}`);
    assert.ok(parent.ts < message.ts, `Thread reply ${message.ts} predates its parent`);
    if (message.parent_user_id !== undefined) {
      assert.equal(message.parent_user_id, parent.user, `Thread reply ${message.ts} identifies the wrong root author`);
    }
    threads += 1;
  }
  assert.ok(threads >= 10, "Varied work conversations should include actual threaded exchanges.");
});

test("the bundled sample includes every JSON file in the selectable export folder", async () => {
  const source = await readFile(new URL("../src/frontend/features/memory/sampleSlackExport.ts", import.meta.url), "utf8");
  const importedPaths = [...source.matchAll(/from "@\/data\/slack-export\/([^"]+\.json)"/g)].map((match) => `slack-export/${match[1]}`);
  const bundledPaths = [...source.matchAll(/relativePath: "(slack-export\/[^"]+\.json)"/g)].map((match) => match[1]);
  const expectedPaths = files.map((file) => file.relativePath).sort();
  assert.deepEqual(importedPaths.sort(), expectedPaths);
  assert.deepEqual(bundledPaths.sort(), expectedPaths);
});

test("the practice guide points to every real situation without requiring a prepared employee reply", async () => {
  const guide = await readFile(new URL("../TEST_SITUATION.md", import.meta.url), "utf8");
  for (const scenario of manifest.scenarios) {
    assert.ok(guide.includes(scenario.title), `Guide is missing ${scenario.id}'s title`);
    assert.ok(guide.includes(scenario.managerMessageId), `Guide is missing ${scenario.id}'s manager message reference`);
  }
});

import type { MemoryMessage } from "@/frontend/api/contract";

export type ImportJsonFile = { name: string; data: unknown; relativePath?: string };
export type ParsedSlackImport = {
  messages: MemoryMessage[];
  participants: Record<string, string>;
  conversationNames?: Record<string, string>;
  skippedCount: number;
  warnings: string[];
};

const maxBytes = 1_048_576;
const maxMessages = 100;
const userIdPattern = /^[UW][A-Z0-9]{1,127}$/;
const channelIdPattern = /^[CGD][A-Z0-9]{1,100}$/;
const messageKeys = new Set(["id", "conversationId", "sender", "content", "timestamp", "source"]);
const userRegistryPattern = /^users?\.json$/i;
const registryPattern = /^(?:users?|channels)\.json$/i;
const dayFilePattern = /^\d{4}-\d{2}-\d{2}\.json$/i;

function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function pathParts(relativePath: string): string[] | null {
  if (typeof relativePath !== "string" || !relativePath || /^(?:[\\/]|[a-z]:)/i.test(relativePath) || relativePath.includes("\0")) return null;
  const parts = relativePath.replace(/\\/g, "/").split("/");
  return parts.some((part) => part === "" || part === "." || part === "..") ? null : parts;
}

function isDayFile(name: string): boolean {
  return dayFilePattern.test(name) && validTimestamp(`${name.slice(0, 10)}T00:00:00Z`);
}

/** Check folder relevance before reading JSON; attachments and root logs need no parsing. */
export function isSlackExportJsonPath(relativePath: string): boolean {
  const parts = pathParts(relativePath);
  if (!parts) return false;
  if (parts.length === 1) return registryPattern.test(parts[0]);
  if (parts.length === 2) return registryPattern.test(parts[1]) || isDayFile(parts[1]);
  return parts.length === 3 && isDayFile(parts[2]);
}

function folderMessageFiles(files: ImportJsonFile[]): { files: ImportJsonFile[]; ignoredFiles: number; conversationNames: Record<string, string> } {
  const paths = files.map((file) => {
    const parts = file.relativePath === undefined ? null : pathParts(file.relativePath);
    if (!parts) throw new Error("Choose one extracted Slack export folder with valid relative file paths.");
    return { file, parts };
  });
  const roots = new Map<string, { users: ImportJsonFile[]; channels: ImportJsonFile[] }>();
  for (const { file, parts } of paths) {
    if (parts.length > 2 || !registryPattern.test(parts[parts.length - 1])) continue;
    const root = parts.slice(0, -1).join("/");
    const registries = roots.get(root) ?? { users: [], channels: [] };
    if (userRegistryPattern.test(parts[parts.length - 1])) registries.users.push(file);
    else registries.channels.push(file);
    roots.set(root, registries);
  }
  const complete = Array.from(roots.entries()).filter(([, registries]) => registries.users.length > 0 && registries.channels.length > 0);
  if (complete.length > 1) throw new Error("Choose one Slack export folder at a time; more than one export root was found.");
  if (complete.length === 0) {
    if (!Array.from(roots.values()).some((registries) => registries.users.length > 0)) {
      throw new Error("The export folder needs users.json (or user.json) at its root. Select the full extracted folder.");
    }
    if (!Array.from(roots.values()).some((registries) => registries.channels.length > 0)) {
      throw new Error("The export folder needs channels.json at its root to identify conversations.");
    }
    throw new Error("The users and channels registries must be in the same export root folder.");
  }
  const [root, registries] = complete[0];
  if (registries.users.length !== 1 || registries.channels.length !== 1) {
    throw new Error("The export folder has ambiguous user or channel registries. Keep one users.json (or user.json) and one channels.json.");
  }
  if (root && paths.some(({ parts }) => parts[0] !== root)) {
    throw new Error("Files from different export roots cannot be combined. Choose one extracted Slack export folder.");
  }
  const channels = registries.channels[0].data;
  if (!Array.isArray(channels)) throw new Error("Slack channels.json must contain an array of channel records.");
  const channelNames = new Map<string, string>();
  for (const entry of channels) {
    if (!object(entry) || typeof entry.id !== "string" || !channelIdPattern.test(entry.id)
      || !text(entry.name, 200) || entry.name !== entry.name.trim() || /[\\/]/.test(entry.name) || [".", ".."].includes(entry.name)) {
      throw new Error("Slack channels.json contains a channel without a valid ID and name.");
    }
    const existing = channelNames.get(entry.name);
    if (existing !== undefined && existing !== entry.id) {
      throw new Error("Slack channels.json maps the same channel name to multiple IDs. Resolve the ambiguous channel before importing.");
    }
    channelNames.set(entry.name, entry.id);
  }
  const result: ImportJsonFile[] = [{ name: "users.json", data: registries.users[0].data }];
  let ignoredFiles = 0;
  for (const { file, parts } of paths) {
    if (file === registries.users[0] || file === registries.channels[0]) continue;
    const relativeParts = root ? (parts[0] === root ? parts.slice(1) : []) : parts;
    if (relativeParts.length !== 2 || !isDayFile(relativeParts[1])) {
      ignoredFiles += 1;
      continue;
    }
    const conversation = channelNames.get(relativeParts[0]);
    if (!conversation) throw new Error("A channel folder has no matching ID in channels.json. Include the registry for the selected export.");
    if (!Array.isArray(file.data)) throw new Error("Each channel-day JSON file must contain a Slack message array.");
    result.push({ name: file.name, data: { channel: { id: conversation }, messages: file.data } });
  }
  return {
    files: result,
    ignoredFiles,
    conversationNames: Object.fromEntries(Array.from(channelNames, ([name, id]) => [`slack-export:${id}`, name])),
  };
}

function validUnicode(value: string): boolean {
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return false;
      index += 1;
    } else if (code >= 0xdc00 && code <= 0xdfff) {
      return false;
    }
  }
  return true;
}

function text(value: unknown, max: number): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= max && Boolean(value.trim()) && validUnicode(value);
}

function identifier(value: unknown): value is string {
  return text(value, 128) && value === value.trim();
}

function validTimestamp(value: unknown): value is string {
  if (typeof value !== "string") return false;
  const match = /^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:[Zz]|([+-])(\d{2}):(\d{2}))$/.exec(value);
  if (!match) return false;
  const [, yearText, monthText, dayText, hourText, minuteText, secondText, , offsetHour, offsetMinute] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const monthDays = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return year >= 1 && month >= 1 && month <= 12 && Number(dayText) >= 1 && Number(dayText) <= monthDays[month - 1]
    && Number(hourText) <= 23 && Number(minuteText) <= 59 && Number(secondText) <= 59
    && (offsetHour === undefined || (Number(offsetHour) <= 23 && Number(offsetMinute) <= 59));
}

/** Slack timestamps are decimal strings. Never round their microseconds through a float. */
function slackTimestamp(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const match = /^(\d{1,12})\.(\d{6})$/.exec(value);
  if (!match) return null;
  const seconds = Number(match[1]);
  if (seconds > 253_402_300_799) return null;
  return new Date(seconds * 1000).toISOString().replace(".000Z", `.${match[2]}Z`);
}

function canonicalMessage(value: unknown): MemoryMessage {
  if (!object(value) || Object.keys(value).some((key) => !messageKeys.has(key))
    || !identifier(value.id) || !identifier(value.conversationId)
    || !text(value.sender, 200) || !text(value.content, 10_000)
    || ("timestamp" in value && !validTimestamp(value.timestamp))
    || ("source" in value && !text(value.source, 200))) {
    throw new Error("A saved-format message has invalid fields. Check its IDs, sender, content and optional metadata.");
  }
  return {
    id: value.id,
    conversationId: value.conversationId,
    sender: value.sender,
    content: value.content,
    ...(typeof value.timestamp === "string" ? { timestamp: value.timestamp } : {}),
    ...(typeof value.source === "string" ? { source: value.source } : {}),
  };
}

/**
 * Convert explicitly selected JSON files to the existing memory-import contract.
 * Sender IDs remain IDs; display names never determine who the manager is.
 */
export function parseSlackImport(files: ImportJsonFile[], channelId?: string): ParsedSlackImport {
  if (!Array.isArray(files) || files.length === 0) throw new Error("Choose at least one conversation JSON file.");
  if (files.some((file) => !file || typeof file.name !== "string")) throw new Error("Choose valid conversation JSON files.");
  const folderImport = files.some((file) => typeof file.relativePath === "string" && file.relativePath.length > 0);
  const explicitChannelId = folderImport ? undefined : channelId;
  if (explicitChannelId !== undefined && explicitChannelId !== "" && !channelIdPattern.test(explicitChannelId)) {
    throw new Error("Enter the Slack channel or conversation ID starting with C, G or D.");
  }
  let inputBytes = 0;
  for (const file of files) {
    if (folderImport && !isSlackExportJsonPath(file.relativePath ?? "")) continue;
    let serialized: string | undefined;
    try { serialized = JSON.stringify(file.data); } catch { /* JSON files cannot contain cycles. */ }
    if (serialized === undefined) throw new Error("The selected file does not contain valid JSON data.");
    inputBytes += new TextEncoder().encode(serialized).byteLength;
    if (inputBytes > maxBytes) throw new Error("Choose relevant JSON files totalling 1 MiB or less.");
  }
  const prepared = folderImport ? folderMessageFiles(files) : { files, ignoredFiles: 0, conversationNames: {} };

  const names = new Map<string, string>();
  const conversationNames = new Map<string, string>(Object.entries(prepared.conversationNames));
  const botIds = new Set<string>();
  const participants = new Map<string, string>();
  const messages = new Map<string, MemoryMessage>();
  let skippedCount = 0;

  function readUsers(users: unknown) {
    if (!Array.isArray(users)) throw new Error("Slack users metadata must be a users.json array.");
    for (const user of users) {
      if (!object(user) || typeof user.id !== "string" || !userIdPattern.test(user.id)) continue;
      if (user.is_bot === true || user.is_app_user === true) {
        botIds.add(user.id);
        continue;
      }
      const profile = object(user.profile) ? user.profile : {};
      const name = [profile.display_name, profile.real_name, user.real_name, user.name].find((value) => text(value, 200));
      if (typeof name === "string") names.set(user.id, name.trim());
    }
  }

  for (const file of prepared.files) {
    if (userRegistryPattern.test(file.name)) readUsers(file.data);
    else if (object(file.data) && "users" in file.data) readUsers(file.data.users);
  }

  // Keep the registry's complete ID-to-name lookup, including people whose
  // names are needed for history imported earlier in this workspace.
  names.forEach((name, id) => participants.set(id, name));

  function addMessage(message: MemoryMessage) {
    const existing = messages.get(message.id);
    if (existing) {
      if (JSON.stringify(existing) !== JSON.stringify(message)) {
        throw new Error("Two imported messages have the same ID but different content or metadata. Choose one version before importing.");
      }
      skippedCount += 1;
      return;
    }
    messages.set(message.id, message);
    participants.set(message.sender, names.get(message.sender) ?? message.sender);
    if (messages.size > maxMessages) throw new Error("Import up to 100 messages at a time. Choose fewer conversation files.");
  }

  for (const file of prepared.files) {
    if (userRegistryPattern.test(file.name)) continue;
    const data = file.data;
    if (!Array.isArray(data) && (!object(data) || !Array.isArray(data.messages))) {
      throw new Error("Use a Slack channel message array, a Slack test bundle, or an object with a messages array.");
    }
    const entries: unknown[] = Array.isArray(data) ? data : (data as Record<string, unknown>).messages as unknown[];
    const bundle = object(data) ? data : null;
    const canonical = bundle !== null && !("channel" in bundle) && !("users" in bundle)
      && entries.some((entry) => object(entry) && ("conversationId" in entry || "sender" in entry || "content" in entry));
    if (canonical) {
      if (Object.keys(bundle).some((key) => key !== "messages")) throw new Error("Saved-format conversation JSON must contain only a messages array.");
      for (const entry of entries) addMessage(canonicalMessage(entry));
      continue;
    }

    const bundleChannel = bundle && object(bundle.channel) ? bundle.channel.id : undefined;
    if (bundleChannel !== undefined && (typeof bundleChannel !== "string" || !channelIdPattern.test(bundleChannel))) {
      throw new Error("The Slack bundle must have a valid channel.id.");
    }
    if (explicitChannelId && bundleChannel && explicitChannelId !== bundleChannel) {
      throw new Error("The entered channel ID does not match the channel in the Slack file.");
    }
    const conversation = bundleChannel || explicitChannelId;
    if (typeof conversation !== "string" || !channelIdPattern.test(conversation)) {
      throw new Error("Enter the original Slack channel or conversation ID for channel message arrays.");
    }
    const bundleName = bundle && object(bundle.channel) ? bundle.channel.name : undefined;
    if (text(bundleName, 200)) conversationNames.set(`slack-export:${conversation}`, bundleName.trim());
    for (const entry of entries) {
      if (!object(entry) || entry.type !== "message" || (entry.subtype !== undefined && entry.subtype !== null)
        || (entry.hidden !== undefined && entry.hidden !== false) || entry.bot_id !== undefined
        || typeof entry.user !== "string" || !userIdPattern.test(entry.user) || botIds.has(entry.user)
        || (entry.channel !== undefined && entry.channel !== conversation) || !text(entry.text, 10_000)) {
        skippedCount += 1;
        continue;
      }
      const timestamp = slackTimestamp(entry.ts);
      const id = `slack-export:${conversation}:${entry.ts}`;
      if (!timestamp || !identifier(id)) {
        skippedCount += 1;
        continue;
      }
      addMessage({
        id,
        conversationId: `slack-export:${conversation}`,
        sender: entry.user,
        content: entry.text,
        timestamp,
        source: `Slack export ${conversation}/${entry.ts}`,
      });
    }
  }

  const result = Array.from(messages.values());
  if (result.length === 0) throw new Error("No importable regular human messages were found. Join events, bot posts and other system records are excluded; choose an export with ordinary conversation messages.");
  if (new TextEncoder().encode(JSON.stringify({ messages: result })).byteLength > maxBytes) {
    throw new Error("The converted messages exceed 1 MiB. Choose fewer messages.");
  }
  return {
    messages: result,
    participants: Object.fromEntries(participants),
    ...(conversationNames.size ? { conversationNames: Object.fromEntries(conversationNames) } : {}),
    skippedCount,
    warnings: [
      ...(skippedCount ? [`Skipped ${skippedCount} bot, system, duplicate or unsupported records. Only available human message text is imported.`] : []),
      ...(prepared.ignoredFiles ? [`Ignored ${prepared.ignoredFiles} ancillary export files or attachments. Only channel-day JSON and participant metadata are imported.`] : []),
    ],
  };
}

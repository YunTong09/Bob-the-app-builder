import manifest from "@/data/slack-export/.slack-manifest.json";
import users from "@/data/slack-export/users.json";
import channels from "@/data/slack-export/channels.json";
import canvases from "@/data/slack-export/canvases.json";
import fileConversations from "@/data/slack-export/file_conversations.json";
import huddleTranscripts from "@/data/slack-export/huddle_transcripts.json";
import integrationLogs from "@/data/slack-export/integration_logs.json";
import lists from "@/data/slack-export/lists.json";
import messages0 from "@/data/slack-export/all-new-workspace/2026-11-16.json";
import messages1 from "@/data/slack-export/all-new-workspace/2026-11-17.json";
import messages2 from "@/data/slack-export/all-new-workspace/2026-11-18.json";
import messages3 from "@/data/slack-export/all-new-workspace/2026-11-19.json";
import messages4 from "@/data/slack-export/all-new-workspace/2026-11-20.json";
import messages5 from "@/data/slack-export/new-channel/2026-11-16.json";
import messages6 from "@/data/slack-export/new-channel/2026-11-17.json";
import messages7 from "@/data/slack-export/new-channel/2026-11-18.json";
import messages8 from "@/data/slack-export/new-channel/2026-11-19.json";
import messages9 from "@/data/slack-export/new-channel/2026-11-20.json";
import messages10 from "@/data/slack-export/social/2026-11-16.json";
import messages11 from "@/data/slack-export/social/2026-11-17.json";
import messages12 from "@/data/slack-export/social/2026-11-18.json";
import messages13 from "@/data/slack-export/social/2026-11-19.json";
import messages14 from "@/data/slack-export/social/2026-11-20.json";
import messages15 from "@/data/slack-export/social/2026-11-21.json";
import messages16 from "@/data/slack-export/social/2026-11-22.json";
import type { ImportJsonFile } from "./slackImport";

export const SYNTHETIC_SLACK_CHANNEL_ID = "C08PROJECT1";
export const SYNTHETIC_SLACK_MANAGER_MESSAGE_ID = "slack-export:C08PROJECT1:1795047300.000001";

// The sample's public registries are available even when its messages were
// imported on an earlier visit. Keep option values as IDs and resolve labels
// from users.json rather than waiting for another import to populate state.
export const SYNTHETIC_PARTICIPANT_NAMES: Record<string, string> = Object.fromEntries(
  users.filter((user) => !user.is_bot).map((user) => [
    user.id,
    user.profile.display_name || user.name,
  ]),
);
export const SYNTHETIC_CONVERSATION_NAMES: Record<string, string> = Object.fromEntries(
  channels.map((channel) => [`slack-export:${channel.id}`, channel.name]),
);

// The bundled sample and selectable folder contain the same synthetic week.
// Names and message content are synthetic; workplace roles are chosen by the user.
export const SYNTHETIC_SLACK_EXPORT_FILES: ImportJsonFile[] = [
  { name: ".slack-manifest.json", relativePath: "slack-export/.slack-manifest.json", data: manifest },
  { name: "users.json", relativePath: "slack-export/users.json", data: users },
  { name: "channels.json", relativePath: "slack-export/channels.json", data: channels },
  { name: "canvases.json", relativePath: "slack-export/canvases.json", data: canvases },
  { name: "file_conversations.json", relativePath: "slack-export/file_conversations.json", data: fileConversations },
  { name: "huddle_transcripts.json", relativePath: "slack-export/huddle_transcripts.json", data: huddleTranscripts },
  { name: "integration_logs.json", relativePath: "slack-export/integration_logs.json", data: integrationLogs },
  { name: "lists.json", relativePath: "slack-export/lists.json", data: lists },
  { name: "2026-11-16.json", relativePath: "slack-export/all-new-workspace/2026-11-16.json", data: messages0 },
  { name: "2026-11-17.json", relativePath: "slack-export/all-new-workspace/2026-11-17.json", data: messages1 },
  { name: "2026-11-18.json", relativePath: "slack-export/all-new-workspace/2026-11-18.json", data: messages2 },
  { name: "2026-11-19.json", relativePath: "slack-export/all-new-workspace/2026-11-19.json", data: messages3 },
  { name: "2026-11-20.json", relativePath: "slack-export/all-new-workspace/2026-11-20.json", data: messages4 },
  { name: "2026-11-16.json", relativePath: "slack-export/new-channel/2026-11-16.json", data: messages5 },
  { name: "2026-11-17.json", relativePath: "slack-export/new-channel/2026-11-17.json", data: messages6 },
  { name: "2026-11-18.json", relativePath: "slack-export/new-channel/2026-11-18.json", data: messages7 },
  { name: "2026-11-19.json", relativePath: "slack-export/new-channel/2026-11-19.json", data: messages8 },
  { name: "2026-11-20.json", relativePath: "slack-export/new-channel/2026-11-20.json", data: messages9 },
  { name: "2026-11-16.json", relativePath: "slack-export/social/2026-11-16.json", data: messages10 },
  { name: "2026-11-17.json", relativePath: "slack-export/social/2026-11-17.json", data: messages11 },
  { name: "2026-11-18.json", relativePath: "slack-export/social/2026-11-18.json", data: messages12 },
  { name: "2026-11-19.json", relativePath: "slack-export/social/2026-11-19.json", data: messages13 },
  { name: "2026-11-20.json", relativePath: "slack-export/social/2026-11-20.json", data: messages14 },
  { name: "2026-11-21.json", relativePath: "slack-export/social/2026-11-21.json", data: messages15 },
  { name: "2026-11-22.json", relativePath: "slack-export/social/2026-11-22.json", data: messages16 },
];

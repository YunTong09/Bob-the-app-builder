import type { AckFn, ViewOutput, ViewResponseAction, ViewUpdateResponseAction, types, webApi } from "@slack/bolt";
import { showRewriteInModal } from "./rewrite-modal.mts";
import type { ReplyTone, RewriteRequest, RewriteService } from "./rewrite.mts";

export const INPUT_MODAL_CALLBACK_ID = "rage_to_reply_input";

// Limits from docs/API_CONTRACT.md (message and draft text: 1–10,000 characters).
export const MAX_TEXT_LENGTH = 10_000;
// Slack caps modal section text, plain_text_input max_length and private_metadata at 3,000 characters.
export const SLACK_FIELD_LIMIT = 3_000;

export const DRAFT_BLOCK_ID = "draft_block";
export const DRAFT_ACTION_ID = "draft";
export const TONE_BLOCK_ID = "tone_block";
export const TONE_ACTION_ID = "tone";

export const TONE_OPTIONS: ReadonlyArray<{ value: ReplyTone; label: string }> = [
  { value: "diplomatic", label: "Diplomatic" },
  { value: "neutral", label: "Neutral" },
  { value: "assertive", label: "Assertive" },
];

const DEFAULT_TONE: ReplyTone = "neutral";

export interface InputModalOptions {
  /** The selected Slack message. Also stored in private_metadata, so it must fit Slack's 3,000-character limit. */
  managerMessage: string;
  /** Previously typed draft, used to preserve input when the form is shown again. */
  draft?: string;
  tone?: ReplyTone;
}

function isReplyTone(value: unknown): value is ReplyTone {
  return TONE_OPTIONS.some((option) => option.value === value);
}

function toneOption({ value, label }: (typeof TONE_OPTIONS)[number]) {
  return { text: { type: "plain_text", text: label }, value } as const;
}

/**
 * Builds the input modal. The draft is never placed in private_metadata; only the selected manager message is.
 */
export function buildInputModal({ managerMessage, draft, tone }: InputModalOptions): types.ModalView {
  if (managerMessage.length > SLACK_FIELD_LIMIT) {
    throw new RangeError(`The selected message exceeds Slack's ${SLACK_FIELD_LIMIT}-character modal limit.`);
  }

  const initialTone = TONE_OPTIONS.find((option) => option.value === (tone ?? DEFAULT_TONE)) ?? TONE_OPTIONS[1];

  return {
    type: "modal",
    callback_id: INPUT_MODAL_CALLBACK_ID,
    private_metadata: managerMessage,
    title: { type: "plain_text", text: "Rage-to-Reply" },
    submit: { type: "plain_text", text: "Rewrite" },
    close: { type: "plain_text", text: "Cancel" },
    blocks: [
      { type: "header", text: { type: "plain_text", text: "Manager message" } },
      { type: "section", text: { type: "plain_text", text: managerMessage || " " } },
      { type: "divider" },
      {
        type: "input",
        block_id: DRAFT_BLOCK_ID,
        label: { type: "plain_text", text: "Your draft" },
        element: {
          type: "plain_text_input",
          action_id: DRAFT_ACTION_ID,
          multiline: true,
          max_length: SLACK_FIELD_LIMIT,
          placeholder: { type: "plain_text", text: "Write what you really want to say…" },
          ...(draft ? { initial_value: draft } : {}),
        },
      },
      {
        type: "input",
        block_id: TONE_BLOCK_ID,
        label: { type: "plain_text", text: "Tone" },
        element: {
          type: "radio_buttons",
          action_id: TONE_ACTION_ID,
          options: TONE_OPTIONS.map(toneOption),
          initial_option: toneOption(initialTone),
        },
      },
    ],
  };
}

type SubmittedView = Pick<ViewOutput, "state" | "private_metadata">;

export type InputValidation =
  | { ok: true; request: RewriteRequest }
  | { ok: false; errors: Record<string, string> };

/** Validates the submitted modal state and, when valid, returns the rewrite request. */
export function parseInputSubmission(view: SubmittedView): InputValidation {
  const values = view.state.values;
  const draft = values[DRAFT_BLOCK_ID]?.[DRAFT_ACTION_ID]?.value ?? "";
  const tone = values[TONE_BLOCK_ID]?.[TONE_ACTION_ID]?.selected_option?.value;
  const managerMessage = view.private_metadata ?? "";
  const errors: Record<string, string> = {};

  if (draft.trim().length === 0) {
    errors[DRAFT_BLOCK_ID] = "Enter a draft to rewrite.";
  } else if (draft.length > Math.min(MAX_TEXT_LENGTH, SLACK_FIELD_LIMIT)) {
    errors[DRAFT_BLOCK_ID] = `Keep the draft within ${SLACK_FIELD_LIMIT.toLocaleString("en-US")} characters.`;
  }

  if (!isReplyTone(tone)) {
    errors[TONE_BLOCK_ID] = "Choose Diplomatic, Neutral, or Assertive.";
  }

  if (managerMessage.trim().length === 0 || managerMessage.length > MAX_TEXT_LENGTH) {
    errors[DRAFT_BLOCK_ID] ??= "The selected message is missing. Close this window and start again.";
  }

  if (Object.keys(errors).length > 0 || !isReplyTone(tone)) {
    return { ok: false, errors };
  }

  return { ok: true, request: { managerMessage, employeeDraft: draft, tone } };
}

interface HandleInputSubmissionOptions {
  ack: AckFn<ViewResponseAction | ViewUpdateResponseAction>;
  view: ViewOutput;
  views: Pick<webApi.WebClient["views"], "update">;
  rewrite?: RewriteService;
}

/**
 * view_submission handler body for INPUT_MODAL_CALLBACK_ID.
 * Invalid input shows inline errors and Slack keeps what the user typed; valid input continues into TASK-05.
 */
export async function handleInputSubmission({ ack, view, views, rewrite }: HandleInputSubmissionOptions): Promise<void> {
  const result = parseInputSubmission(view);

  if (!result.ok) {
    await ack({ response_action: "errors", errors: result.errors });
    return;
  }

  await showRewriteInModal({
    ack: ack as AckFn<ViewUpdateResponseAction>,
    views,
    viewId: view.id,
    request: result.request,
    rewrite,
  });
}

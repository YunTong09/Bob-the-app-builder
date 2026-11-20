import type { AckFn, ViewUpdateResponseAction, types, webApi } from "@slack/bolt";
import { createMockRewriteService } from "./rewrite.mts";
import type { ReplyTone, RewriteRequest, RewriteResponse, RewriteService } from "./rewrite.mts";

const toneLabels: Record<ReplyTone, string> = {
  diplomatic: "Diplomatic",
  neutral: "Neutral",
  assertive: "Assertive",
};

const modalTitle = { type: "plain_text", text: "Rage-to-Reply" } as const;
const closeButton = { type: "plain_text", text: "Close" } as const;

function processingModal(): types.ModalView {
  return {
    type: "modal",
    title: modalTitle,
    close: closeButton,
    blocks: [
      { type: "section", text: { type: "plain_text", text: "Rewriting your draft…" } },
    ],
  };
}

function resultModal(response: RewriteResponse, tone: ReplyTone): types.ModalView {
  const blocks: types.ModalView["blocks"] = [
    { type: "header", text: { type: "plain_text", text: "Suggested reply" } },
    { type: "context", elements: [{ type: "plain_text", text: `Tone: ${toneLabels[tone]}` }] },
    { type: "section", text: { type: "plain_text", text: response.reply } },
  ];

  if (response.evidence.length > 0) {
    blocks.push(
      { type: "divider" },
      { type: "header", text: { type: "plain_text", text: "Supporting evidence" } },
      ...response.evidence.map(({ sender, content, supportedClaim, source }): types.SectionBlock => ({
        type: "section",
        text: {
          type: "plain_text",
          text: [`${sender}: ${content}`, `Supports: ${supportedClaim}`, source].filter(Boolean).join("\n"),
        },
      })),
    );
  }

  return { type: "modal", title: modalTitle, close: closeButton, blocks };
}

interface ShowRewriteInModalOptions {
  ack: AckFn<ViewUpdateResponseAction>;
  views: Pick<webApi.WebClient["views"], "update">;
  viewId: string;
  request: RewriteRequest;
  rewrite?: RewriteService;
}

export async function showRewriteInModal({
  ack,
  views,
  viewId,
  request,
  rewrite = createMockRewriteService(),
}: ShowRewriteInModalOptions): Promise<void> {
  await ack({ response_action: "update", view: processingModal() });
  const response = await rewrite(request);
  await views.update({ view_id: viewId, view: resultModal(response, request.tone) });
}

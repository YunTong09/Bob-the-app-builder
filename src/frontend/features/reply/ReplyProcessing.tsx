"use client";

import { useEffect, useRef } from "react";
import PixelAnimation from "@/frontend/shared/PixelAnimation";
import RageLoadingMeter from "./RageLoadingMeter";
import ReplyWaitMeter from "./ReplyWaitMeter";

type Props = {
  regenerating: boolean;
  synthetic: boolean;
  replyReady: boolean;
  startedAt: number;
  estimateMs: number | null;
  onAnimationComplete: () => void;
};

export default function ReplyProcessing({
  regenerating,
  synthetic,
  replyReady,
  startedAt,
  estimateMs,
  onAnimationComplete,
}: Props) {
  const titleRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  return (
    <main className="page-shell processing-page">
      <div className="workspace-topbar">
        <span>
          Workspace <span className="breadcrumb-divider">/</span>{" "}
          {regenerating ? "Regenerating reply" : "Preparing your reply"}
        </span>
        <span className="connection-badge">
          {synthetic ? "Synthetic demo" : replyReady ? "Reply ready" : "Reply in progress"}
        </span>
      </div>
      <header className="processing-header">
        <p className="eyebrow">FROM FRUSTRATION TO CLARITY</p>
        <h1 ref={titleRef} tabIndex={-1}>
          {regenerating
            ? "A fresh take. The same intent."
            : "A cooler head is on the way."}
        </h1>
        <p role="status">
          {replyReady
            ? "Your reply is ready. Finish or skip the animation to review it."
            : regenerating
              ? "Preparing a new version. Your previous reply and draft are kept until this finishes."
              : "Your draft stays here while we prepare your reply."}
        </p>
      </header>
      <section
        className="processing-overview panel"
        aria-labelledby="overall-process-heading"
      >
        <div className="processing-overview-copy">
          <p className="eyebrow">THE OVERALL PROCESS</p>
          <h2 id="overall-process-heading">Turning the heat into clarity</h2>
          <p>
            Understand your message. Check the context. Shape a professional
            reply that keeps your point intact.
          </p>
          <span className="processing-state" role="status">
            {replyReady ? "Reply ready" : "Processing your request"}
          </span>
          <ReplyWaitMeter startedAt={startedAt} estimateMs={estimateMs} replyReady={replyReady} />
        </div>
        <RageLoadingMeter onComplete={onAnimationComplete} />
      </section>
      <div className="processing-details">
        <section
          className="panel processing-evidence"
          aria-labelledby="evidence-process-heading"
        >
          <PixelAnimation
            kind="investigate"
            label="A closer look at the supporting context"
          />
          <div>
            <p className="eyebrow">EVIDENCE REVIEW</p>
            <h2 id="evidence-process-heading">Looking for the receipts</h2>
            <p>
              Imported conversations provide context for checking your claims.
              Supporting sources, missing evidence, and uncertainty will be
              shown separately with your reply.
            </p>
            <span className="processing-detail-label">
              Part of the reply workflow
            </span>
          </div>
        </section>
        <section
          className="panel processing-explainer"
          aria-labelledby="workflow-overview-heading"
        >
          <p className="eyebrow">WHAT GOES INTO YOUR REPLY</p>
          <h2 id="workflow-overview-heading">More than a tone change</h2>
          <ul>
            <li>
              <span aria-hidden="true">▤</span>
              <div>
                <strong>Understand your point</strong>
                <p>
                  Read the original message and your draft without changing your
                  meaning.
                </p>
              </div>
            </li>
            <li>
              <span aria-hidden="true">▧</span>
              <div>
                <strong>Review the context</strong>
                <p>
                  Look for support in imported history and distinguish uncertain
                  claims.
                </p>
              </div>
            </li>
            <li>
              <span aria-hidden="true">✦</span>
              <div>
                <strong>Prepare your reply</strong>
                <p>Use your selected tone, ready for you to review and edit.</p>
              </div>
            </li>
          </ul>
        </section>
      </div>
      <p className="processing-honesty">
        {synthetic
          ? "Synthetic demo: sample replies and evidence demonstrate this workflow."
          : "This is an overview of the workflow. Individual stages are not reported live."}
      </p>
      <footer className="workspace-footer">
        <span>Nothing is sent automatically. You review the final words.</span>
        <span>YOUR WORDS. YOUR DECISION.</span>
      </footer>
    </main>
  );
}

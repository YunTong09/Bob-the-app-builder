"use client";

import { useState, type KeyboardEvent } from "react";
import MemoryPanel from "@/frontend/features/memory/MemoryPanel";
import PreferencesPanel from "@/frontend/features/preferences/PreferencesPanel";
import ReplyPanel from "@/frontend/features/reply/ReplyPanel";
import { isMockMode } from "@/frontend/api/replyApi";
import "@/frontend/styles/assistant.css";

// Synthetic chat shown on the left to stand in for the desktop chat app (Slack) in the sketches.
const CHAT_MANAGER_MESSAGE = "Why haven't you accessed the document yet?";

type Tab = "reply" | "memory" | "preferences";
const TABS: { id: Tab; label: string }[] = [
  { id: "reply", label: "Reply" },
  { id: "memory", label: "Memory" },
  { id: "preferences", label: "Preferences" },
];

export default function AssistantPage() {
  const [tab, setTab] = useState<Tab>("reply");

  function navigateTabs(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const offsets: Record<string, number> = {
      ArrowLeft: (index + TABS.length - 1) % TABS.length,
      ArrowRight: (index + 1) % TABS.length,
      Home: 0,
      End: TABS.length - 1,
    };
    if (!Object.hasOwn(offsets, event.key)) return;
    event.preventDefault();
    const next = TABS[offsets[event.key]].id;
    setTab(next);
    document.getElementById(`tab-${next}`)?.focus();
  }

  return (
    <div className="r2r">
      <div className="r2r-layout">
        <section className="slack-mock" aria-label="Chat app preview (synthetic)">
          <aside className="slack-sidebar">
            <p className="slack-title">Slack</p>
            <p className="slack-user">Dave</p>
          </aside>
          <div className="slack-main">
            <p className="slack-message"><strong>Dave:</strong> {CHAT_MANAGER_MESSAGE}</p>
            <div className="slack-composer">
              <label htmlFor="slack-composer-input">Message</label>
              <textarea id="slack-composer-input" disabled placeholder="The assistant never sends for you — you stay in control." />
              <button type="button" className="btn btn-secondary" disabled>Send</button>
            </div>
          </div>
        </section>

        <main className="popup" aria-label="Rage-to-Reply assistant">
          <header className="popup-header">
            <h1>Rage-to-Reply</h1>
            {isMockMode && <span className="badge">mock data</span>}
          </header>
          <div role="tablist" aria-label="Sections" className="tabs">
            {TABS.map((t, index) => (
              <button
                key={t.id}
                role="tab"
                id={`tab-${t.id}`}
                aria-selected={tab === t.id}
                aria-controls={`panel-${t.id}`}
                tabIndex={tab === t.id ? 0 : -1}
                className="tab"
                onClick={() => setTab(t.id)}
                onKeyDown={(event) => navigateTabs(event, index)}
              >
                {t.label}
              </button>
            ))}
          </div>
          {/* All panels stay mounted so typed input survives tab switches. */}
          <div role="tabpanel" id="panel-reply" aria-labelledby="tab-reply" hidden={tab !== "reply"}>
            <ReplyPanel initialManagerMessage={CHAT_MANAGER_MESSAGE} />
          </div>
          <div role="tabpanel" id="panel-memory" aria-labelledby="tab-memory" hidden={tab !== "memory"}>
            <MemoryPanel />
          </div>
          <div role="tabpanel" id="panel-preferences" aria-labelledby="tab-preferences" hidden={tab !== "preferences"}>
            <PreferencesPanel />
          </div>
        </main>
      </div>
    </div>
  );
}

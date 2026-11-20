import Link from "next/link";

export default function TutorialPage() {
  return (
    <main className="page-shell">
      <header className="page-header">
        <h1>Tutorial</h1>
        <p>Write a professional reply and check what your history supports.</p>
      </header>
      <div className="workspace-grid">
        <section className="panel workspace-panel" aria-labelledby="tutorial-start">
          <h2 id="tutorial-start">Try it in the Workspace</h2>
          <ol className="text-list">
            <li>Choose <strong>Rewrite with Evidence</strong>. Enter the work message and your draft, or select <strong>Use sample inputs</strong> on a blank form.</li>
            <li>Optionally open <strong>History</strong> to import sample messages, upload a JSON file, or preview Slack messages and confirm which ones to import.</li>
            <li>Pick Diplomatic, Neutral, or Assertive and choose <strong>Generate reply</strong>.</li>
            <li>Review the AI interpretation, supporting evidence, unverified claims, and warnings. Edit the suggested reply, or change the tone and regenerate.</li>
          </ol>
          <div><Link href="/">Open Workspace</Link></div>
        </section>
        <section className="panel workspace-panel" aria-labelledby="tutorial-history">
          <h2 id="tutorial-history">Manage history and preferences</h2>
          <p>Use <strong>History</strong> to search saved messages or confirm deletion of all imported messages. Use <strong>Settings</strong> to change your default tone.</p>
          <p>Your draft stays out of conversation history. Review the final text in the Workspace before using it.</p>
        </section>
      </div>
    </main>
  );
}

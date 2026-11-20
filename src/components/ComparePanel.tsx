type ComparePanelProps = { rawText: string; polishedReply: string };

export default function ComparePanel({ rawText, polishedReply }: ComparePanelProps) {
  async function copyReply() {
    await navigator.clipboard.writeText(polishedReply);
  }

  return (
    <section className="panel compare-panel">
      <div className="compare-column raw-column">
        <div className="result-label">Your raw thoughts</div>
        <p>{rawText}</p>
      </div>
      <div className="compare-column polished-column">
        <div className="result-label">Ready to send</div>
        <p>{polishedReply}</p>
        <button className="secondary-button" type="button" onClick={copyReply}>Copy reply</button>
      </div>
    </section>
  );
}

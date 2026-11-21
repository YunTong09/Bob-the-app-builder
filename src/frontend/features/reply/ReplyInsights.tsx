import type { GenerateReplyResponse } from "@/frontend/api/contract";

function displayWarnings(warnings: string[]) {
  return warnings.map((text) => {
    if (text.startsWith("Missing information:")) {
      return { label: "To confirm", text: text.slice("Missing information:".length).trim(), conflict: false };
    }
    if (text.startsWith("Possible misunderstanding (interpretation):")) {
      return { label: "Possible misunderstanding", text: text.slice("Possible misunderstanding (interpretation):".length).trim(), conflict: false };
    }
    return { label: "", text, conflict: text.startsWith("Conflicting history:") };
  });
}

function insightPreview(text: string) {
  if (text.length <= 140 || typeof Intl.Segmenter !== "function") return text;
  const sentences = new Intl.Segmenter(undefined, { granularity: "sentence" }).segment(text);
  return Array.from(sentences)[0]?.segment.trim() || text;
}

export default function ReplyInsights({
  managerIntent, employeeConcern, warnings, unverifiedClaims,
}: Pick<GenerateReplyResponse, "managerIntent" | "employeeConcern" | "warnings" | "unverifiedClaims">) {
  const managerPoints = managerIntent.split(/(?=Explicit request:|Possible action \(interpretation\):)/)
    .map((text) => text.trim()).filter(Boolean);
  const concernPreview = insightPreview(employeeConcern);
  const concernHasMore = concernPreview !== employeeConcern;
  const showFullInsights = managerPoints.length > 0 || concernHasMore;
  const warningItems = displayWarnings(warnings);
  const orderedWarnings = [
    ...warningItems.filter((warning) => warning.conflict),
    ...warningItems.filter((warning) => !warning.conflict),
    ...unverifiedClaims.map((text) => ({ label: "Unverified claim", text, conflict: false })),
  ];
  const mainWarning = orderedWarnings[0];
  const hiddenWarnings = orderedWarnings.slice(1);
  const warningList = (items: typeof warningItems) => (
    <ul className="reply-insight-list">
      {items.map(({ label, text }, index) => (
        <li key={index}>{label && <strong>{label} · </strong>}{text}</li>
      ))}
    </ul>
  );

  return (
    <div className="reply-insight-grid">
      <section className="reply-insight-card" aria-labelledby="insights-heading">
        <h3 id="insights-heading">Insights</h3>
        <dl className="reply-insight-summary">
          {employeeConcern && <div><dt>Main concern</dt><dd>{concernPreview}</dd></div>}
        </dl>
        {showFullInsights && (
          <details>
            <summary>View full insights</summary>
            <ul className="reply-insight-list">
              {managerPoints.map((text, index) => <li key={index}>{text}</li>)}
            </ul>
            {concernHasMore && <p>{employeeConcern}</p>}
          </details>
        )}
      </section>
      {mainWarning && (
        <section className="reply-insight-card reply-warning-card" aria-labelledby="warnings-heading">
          <h3 id="warnings-heading"><span className="status-label status-label-warning">Warnings</span></h3>
          <p>{mainWarning.label && <strong>{mainWarning.label} · </strong>}{mainWarning.text}</p>
          {hiddenWarnings.length > 0 && (
            <details>
              <summary>View {hiddenWarnings.length} more</summary>
              {warningList(hiddenWarnings)}
            </details>
          )}
        </section>
      )}
    </div>
  );
}

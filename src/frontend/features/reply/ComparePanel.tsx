import { toneLabels, type Tone } from "@/frontend/api/web-api";

type ComparePanelProps = {
  polishedReply: string;
  tone: Tone;
  onChange: (reply: string) => void;
};

export default function ComparePanel({ polishedReply, tone, onChange }: ComparePanelProps) {
  return (
    <div className="form-field">
      <div className="reply-label">
        <label htmlFor="suggested-reply">Suggested reply</label>
        <span className="tone-badge">{toneLabels[tone]}</span>
      </div>
      <textarea
        id="suggested-reply"
        className="plain-textarea vent-textarea"
        value={polishedReply}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

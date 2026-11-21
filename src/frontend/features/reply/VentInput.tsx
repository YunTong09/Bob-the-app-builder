import DictationControls from "./DictationControls";
import { toneLabels, type Tone } from "@/frontend/api/web-api";
type Props = {
  value: string;
  onChange: (v: string) => void;
  onDictated: (text: string) => void;
  tone: Tone;
  onToneChange: (t: Tone) => void;
  loading: boolean;
  canSubmit: boolean;
  hasReply: boolean;
};
const descriptions = {
  diplomatic: "Keep it considerate",
  neutral: "Clear and balanced",
  assertive: "Firm, with respect",
};
export default function VentInput({
  value,
  onChange,
  onDictated,
  tone,
  onToneChange,
  loading,
  canSubmit,
  hasReply,
}: Props) {
  return (
    <>
      <div className="form-field">
        <div className="field-heading">
          <label htmlFor="employee-draft">Your unfiltered draft</label>
          <span className="private-label">Private draft</span>
        </div>
        <DictationControls onTranscript={onDictated} disabled={loading}>
          <textarea
            id="employee-draft"
            className="plain-textarea vent-textarea"
            placeholder="This is your space. Say what you actually want to say…"
            aria-describedby="draft-privacy"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            required
            maxLength={10000}
          />
        </DictationControls>
        <div className="field-heading">
          <p className="small-text" id="draft-privacy">
            Not saved to conversation history.
          </p>
          <span className="character-count">
            {value.length.toLocaleString()} / 10,000
          </span>
        </div>
      </div>
      <fieldset className="tone-field">
        <legend>How should it sound?</legend>
        <div className="tone-options">
          {Object.entries(toneLabels).map(([key, label]) => (
            <label key={key} className={tone === key ? "selected" : ""}>
              <input
                type="radio"
                name="reply-tone"
                checked={tone === key}
                onChange={() => onToneChange(key as Tone)}
              />
              <span>{label}</span>
              <small>{descriptions[key as Tone]}</small>
            </label>
          ))}
        </div>
      </fieldset>
      <button
        className="primary-button generate-button"
        type="submit"
        disabled={loading || !canSubmit}
      >
        {loading
          ? "Finding the right words…"
          : hasReply
            ? "Regenerate reply"
            : "Find the right words"}
        <span aria-hidden="true">✦</span>
      </button>
    </>
  );
}

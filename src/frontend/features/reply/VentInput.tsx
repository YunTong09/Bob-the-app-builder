import { toneLabels, type Tone } from "@/frontend/api/web-api";

type VentInputProps = {
  value: string;
  onChange: (value: string) => void;
  tone: Tone;
  onToneChange: (tone: Tone) => void;
  loading: boolean;
  canSubmit: boolean;
  hasReply: boolean;
};

export default function VentInput({
  value, onChange, tone, onToneChange, loading, canSubmit, hasReply,
}: VentInputProps) {
  return (
    <>
      <div className="form-field">
        <label htmlFor="employee-draft">What you want to say</label>
        <textarea
          id="employee-draft"
          className="plain-textarea vent-textarea"
          placeholder="Write what you really think"
          aria-describedby="draft-privacy"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          required
          maxLength={10_000}
        />
        <p className="small-text" id="draft-privacy">Your draft is processed for this request. It isn’t added to history.</p>
      </div>
      <div className="input-footer">
        <div className="form-field">
          <label htmlFor="reply-tone">Tone</label>
          <select id="reply-tone" value={tone} onChange={(event) => onToneChange(event.target.value as Tone)}>
            {Object.entries(toneLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </div>
        <button className="primary-button" type="submit" disabled={loading || !canSubmit}>
          {loading ? "Generating…" : hasReply ? "Regenerate reply" : "Generate reply"}
        </button>
      </div>
    </>
  );
}

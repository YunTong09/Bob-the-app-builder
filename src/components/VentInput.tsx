type VentInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
};

export default function VentInput({ value, onChange, onSubmit, loading }: VentInputProps) {
  return (
    <section className="panel">
      <div className="section-label">Say what you really mean</div>
      <textarea
        aria-label="Employee raw thoughts"
        className="plain-textarea vent-textarea"
        placeholder="The key is locked behind a password, am I supposed to guess it psychically?"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
      <div className="input-footer">
        <span className="privacy-note">Private for this conversion only</span>
        <button className="primary-button" type="button" onClick={onSubmit} disabled={loading || !value.trim()}>
          {loading ? "Converting…" : "Convert"}
        </button>
      </div>
    </section>
  );
}

type ChatWindowProps = {
  managerMessage: string;
  onChange: (value: string) => void;
};

export default function ChatWindow({ managerMessage, onChange }: ChatWindowProps) {
  return (
    <div className="form-field">
      <label htmlFor="manager-message">Manager’s message (optional)</label>
      <textarea
        id="manager-message"
        className="plain-textarea manager-textarea"
        placeholder="Optional: add their message for more context"
        value={managerMessage}
        onChange={(event) => onChange(event.target.value)}
        maxLength={10_000}
      />
    </div>
  );
}

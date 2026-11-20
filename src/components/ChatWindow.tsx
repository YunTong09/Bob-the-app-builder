type ChatWindowProps = {
  managerMessage: string;
  onChange: (value: string) => void;
};

export default function ChatWindow({ managerMessage, onChange }: ChatWindowProps) {
  return (
    <div className="form-field">
      <label htmlFor="manager-message">Manager’s message</label>
      <textarea
        id="manager-message"
        className="plain-textarea manager-textarea"
        placeholder="Paste the message you’re replying to"
        value={managerMessage}
        onChange={(event) => onChange(event.target.value)}
        required
        maxLength={10_000}
      />
    </div>
  );
}

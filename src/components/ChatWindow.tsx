type ChatWindowProps = {
  managerMessage: string;
  onChange: (value: string) => void;
};

export default function ChatWindow({ managerMessage, onChange }: ChatWindowProps) {
  return (
    <section className="panel">
      <div className="section-label">Manager message</div>
      <div className="chat-bubble">
        <div className="avatar">D</div>
        <div className="chat-content">
          <div className="chat-meta"><strong>Dave</strong><span>manager</span></div>
          <textarea
            aria-label="Manager message"
            className="plain-textarea manager-textarea"
            value={managerMessage}
            onChange={(event) => onChange(event.target.value)}
          />
        </div>
      </div>
    </section>
  );
}

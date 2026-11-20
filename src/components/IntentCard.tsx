export default function IntentCard({ managerIntent }: { managerIntent: string }) {
  return (
    <section className="result-card intent-card">
      <div className="result-label">What Dave actually wants</div>
      <p>{managerIntent}</p>
    </section>
  );
}

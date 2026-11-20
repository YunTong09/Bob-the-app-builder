export default function RageMeter({ rageLevel }: { rageLevel: number }) {
  return (
    <section className="result-card">
      <div className="result-label">Rage level</div>
      <div className="rage-value">{rageLevel}<span>/100</span></div>
      <div className="meter-track"><div className="meter-fill" style={{ width: `${rageLevel}%` }} /></div>
    </section>
  );
}

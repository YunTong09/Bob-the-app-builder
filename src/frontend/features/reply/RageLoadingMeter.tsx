"use client";

import { useEffect, useReducer, useRef } from "react";

type Phase = "interactive" | "eating" | "inflating" | "releasing" | "completed";
type State = { phase: Phase; eaten: number; skipped: boolean; tapped: boolean };
type Action = "advance" | "feed" | "tap" | "skip";

const heatWords = ["UGH", "STRESS", "FRUSTRATION", "ENOUGH", "PRESSURE"];
const initial: State = { phase: "interactive", eaten: 0, skipped: false, tapped: false };
const duration: Record<Exclude<Phase, "interactive">, number> = {
  eating: 460,
  inflating: 700,
  releasing: 620,
  completed: 500,
};

function advance(state: State, action: Action): State {
  if (action === "skip") return { phase: "completed", eaten: heatWords.length, skipped: true, tapped: false };
  if (action === "feed" || action === "tap") {
    return state.phase === "interactive"
      ? { ...state, phase: "eating", tapped: action === "tap" }
      : state;
  }
  switch (state.phase) {
    case "eating": {
      const eaten = state.eaten + 1;
      return { ...state, eaten, tapped: false, phase: eaten === heatWords.length ? "inflating" : "interactive" };
    }
    case "inflating": return { ...state, phase: "releasing" };
    case "releasing": return { ...state, phase: "completed" };
    default: return state;
  }
}

export default function RageLoadingMeter({ onComplete }: { onComplete: () => void }) {
  const [{ phase, eaten, skipped, tapped }, dispatch] = useReducer(advance, initial);
  const idleDeadline = useRef<number | null>(null);

  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const applyPreference = () => { if (preference.matches) dispatch("skip"); };
    applyPreference();
    preference.addEventListener("change", applyPreference);
    return () => preference.removeEventListener("change", applyPreference);
  }, []);

  useEffect(() => {
    if (phase === "completed" && skipped) {
      onComplete();
      return;
    }
    idleDeadline.current ??= performance.now() + 4200;
    const timer = window.setTimeout(() => {
      if (phase === "completed") onComplete();
      else dispatch(phase === "interactive" ? "feed" : "advance");
    }, phase === "interactive"
      ? Math.max(170, idleDeadline.current - performance.now())
      : duration[phase]);
    return () => window.clearTimeout(timer);
  }, [phase, skipped, onComplete]);

  const interactive = phase === "interactive";
  const stateLabel = {
    eating: "Eating the rage…",
    inflating: "Too much heat…",
    interactive: "Punch the face to feed it a word. Click it, or focus it and press Enter or Space.",
    releasing: "Pop! Letting the heat out…",
    completed: "Heat released.",
  }[phase];
  const puffed = phase === "inflating" || phase === "releasing";
  const words = phase === "releasing" ? heatWords : heatWords.slice(eaten, eaten + 1);
  const showWords = interactive || phase === "eating" || phase === "releasing";
  const smiling = phase === "completed";

  const size = smiling ? 1 : puffed ? 1.58 : 1 + eaten * .075;

  return (
    <div className="emotion-bao" data-phase={phase} data-eaten={eaten} data-skipped={skipped}>
      <div className="emotion-bao-stage">
        <button type="button" className="emotion-bao-button"
          aria-disabled={!interactive} aria-label={smiling ? "Calm smile" : "Punch the face to feed it one word"} onClick={() => dispatch("tap")}>
          <span className="emotion-bao-shape" style={{ transform: `scale(${size})` }}>
            <span className="emotion-bao-art">
              <svg className="emotion-bao-face" viewBox="112 269 164 164" aria-hidden="true" shapeRendering="crispEdges">
                <path d="M122 303H146V279H242V303H266V399H242V423H146V399H122Z" fill="#101525" />
                <path d="M130 311H154V287H234V311H258V391H234V415H154V391H130Z" fill={smiling ? "#8de3b6" : "#ee8b76"} />
                {!smiling ? (
                  <>
                    <path d="M154 331H166V339H178V347H154Z M214 339H226V331H238V347H214Z" fill="#151a2c" />
                    <path d={phase === "eating" ? "M180 365H212V387H180Z" : "M170 379V371H222V379"}
                      fill={phase === "eating" ? "#151a2c" : "none"} stroke="#151a2c" strokeWidth="6" />
                  </>
                ) : (
                  <>
                    <path d="M154 343H178 M214 343H238" stroke="#151a2c" strokeWidth="8" />
                    <path d="M178 371V379H214V371" fill="none" stroke="#151a2c" strokeWidth="8" />
                  </>
                )}
              </svg>
            </span>
          </span>
        </button>
        {phase === "releasing" && (
          <span className="emotion-bao-burst" aria-hidden="true">
            <i /><i /><i /><i /><i /><i /><i /><i />
          </span>
        )}
        {tapped && <span className="emotion-bao-impact" aria-hidden="true"><i /><i /><i /></span>}
        {showWords && (
          <span className="emotion-bao-words" aria-hidden="true">
            {words.map((word, index) => <span key={word} data-word={phase === "releasing" ? index : eaten}>{word}</span>)}
          </span>
        )}
      </div>
      <p role="status" className={interactive ? "emotion-bao-hint" : undefined}>{stateLabel}</p>
      {phase !== "completed" && <button type="button" className="secondary-button" onClick={() => dispatch("skip")}>Skip animation</button>}
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";

// A decorative countdown, not an estimate of server work remaining.
export const coolingRemaining = (elapsedMs: number) =>
  Math.max(1, Math.ceil(100 * Math.exp(-Math.max(0, elapsedMs) / 5000)));

export default function RageLoadingMeter({
  complete = false,
}: {
  complete?: boolean;
}) {
  const [percent, setPercent] = useState(100);
  const current = useRef(100);
  useEffect(() => {
    const preference = matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0;
    const start = performance.now();
    const from = current.current;
    function update(now: number) {
      const reduced = preference.matches;
      const next = complete
        ? reduced
          ? 0
          : Math.max(
              0,
              Math.round(from * (1 - Math.min(1, (now - start) / 400))),
            )
        : reduced
          ? 100
          : coolingRemaining(now - start);
      current.current = next;
      setPercent(next);
      if (!complete || next > 0) frame = requestAnimationFrame(update);
    }
    frame = requestAnimationFrame(update);
    return () => cancelAnimationFrame(frame);
  }, [complete]);
  const color = percent > 55 ? "#ee8b76" : percent > 22 ? "#efb957" : "#8de3b6";
  const blocks = Math.ceil((percent * 24) / 100);
  return (
    <figure
      className="pixel-animation live-rage-meter"
      aria-label="Decorative cooling meter"
    >
      <svg
        viewBox="100 250 1080 205"
        width="100%"
        role="img"
        aria-label={
          complete
            ? "Reply ready"
            : "Cooling animation while your reply is prepared"
        }
        shapeRendering="crispEdges"
      >
        <path
          d="M122 303H146V279H242V303H266V399H242V423H146V399H122Z"
          fill="#101525"
        />
        <path
          d="M130 311H154V287H234V311H258V391H234V415H154V391H130Z"
          fill={color}
        />
        {percent > 40 ? (
          <>
            <path
              d="M154 331H166V339H178V347H154Z M214 339H226V331H238V347H214Z"
              fill="#151a2c"
            />
            <path
              d="M170 379V371H222V379"
              fill="none"
              stroke="#151a2c"
              strokeWidth="8"
            />
          </>
        ) : (
          <>
            <path
              d="M154 343H178 M214 343H238"
              stroke="#151a2c"
              strokeWidth="8"
            />
            <path
              d="M178 371V379H214V371"
              fill="none"
              stroke="#151a2c"
              strokeWidth="8"
            />
          </>
        )}
        <path
          d="M308 295H1136V319H1152V399H1136V423H308V399H292V319H308Z"
          fill="#727992"
        />
        <path
          d="M308 303H1136V319H1144V399H1136V415H308V399H300V319H308Z"
          fill="#d9d9dd"
        />
        <rect x="308" y="319" width="828" height="80" fill="#171a28" />
        {Array.from({ length: 24 }, (_, i) => (
          <g key={i}>
            <rect
              x={318 + i * 34}
              y="329"
              width="26"
              height="60"
              fill={i < blocks ? color : "#292c3d"}
            />
            {i < blocks && (
              <>
                <rect
                  x={318 + i * 34}
                  y="329"
                  width="26"
                  height="8"
                  fill="#fff1d5"
                  opacity=".5"
                />
                <rect
                  x={318 + i * 34}
                  y="381"
                  width="26"
                  height="8"
                  fill="#080a12"
                  opacity=".3"
                />
              </>
            )}
          </g>
        ))}
        <text
          x="1136"
          y="275"
          textAnchor="end"
          fontFamily="monospace"
          fontWeight="bold"
          fontSize="28"
          fill={color}
          aria-hidden="true"
        >
          {percent}%
        </text>
      </svg>
      <figcaption>
        {complete
          ? "Reply ready. Time to review."
          : "From frustration to a thoughtful reply"}
      </figcaption>
    </figure>
  );
}

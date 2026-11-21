"use client";

import { useEffect, useId, useState } from "react";
import { FONT_SIZES, type FontSize, fontSizeStorageKey, isFontSize } from "./fontSize";

function applyFontSize(size: FontSize) {
  document.documentElement.dataset.fontSize = size;
}

export default function DisplaySettings() {
  const id = useId();
  const [fontSize, setFontSize] = useState<FontSize>("medium");

  useEffect(() => {
    const current = document.documentElement.dataset.fontSize;
    if (isFontSize(current)) setFontSize(current);
  }, []);

  function onChange(value: string) {
    if (!isFontSize(value)) return;
    setFontSize(value);
    applyFontSize(value);
    try {
      localStorage.setItem(fontSizeStorageKey, value);
    } catch {
      // The size still applies for this visit if storage is unavailable.
    }
  }

  return (
    <section className="panel display-settings">
      <h2>Display</h2>
      <div className="pref-item">
        <label htmlFor={`${id}-font-size`}>Text size</label>
        <select id={`${id}-font-size`} value={fontSize} onChange={(e) => onChange(e.target.value)}>
          {FONT_SIZES.map((size) => (
            <option key={size.value} value={size.value}>{size.label}</option>
          ))}
        </select>
      </div>
      <p className="small-text">Applies immediately and is saved in this browser.</p>
    </section>
  );
}

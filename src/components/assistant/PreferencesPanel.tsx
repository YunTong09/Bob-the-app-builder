"use client";

import { useEffect, useState } from "react";
import { CommunicationPreferences } from "@/lib/contract";
import { ApiError, getPreferences, savePreferences } from "@/lib/replyApi";

const DEFAULTS: CommunicationPreferences = { tone: "neutral", responseLength: "short", formality: "professional", directness: "balanced" };

const FIELDS: { key: keyof CommunicationPreferences; label: string; options: string[] }[] = [
  { key: "tone", label: "Tone", options: ["diplomatic", "neutral", "assertive"] },
  { key: "responseLength", label: "Length", options: ["short", "medium", "long"] },
  { key: "formality", label: "Formal", options: ["casual", "professional", "formal"] },
  { key: "directness", label: "Assertive", options: ["gentle", "balanced", "direct"] },
];

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export default function PreferencesPanel() {
  const [prefs, setPrefs] = useState<CommunicationPreferences>(DEFAULTS);
  const [available, setAvailable] = useState(true);
  const [status, setStatus] = useState("");

  useEffect(() => {
    getPreferences()
      .then(setPrefs)
      .catch((caught) => {
        // Preferences are optional P1; the rest of the app works without them.
        if (caught instanceof ApiError && caught.code === "NOT_IMPLEMENTED") setAvailable(false);
        else setStatus("Could not load saved preferences. Showing defaults.");
      });
  }, []);

  async function onSave() {
    try {
      setPrefs(await savePreferences(prefs));
      setStatus("Preferences saved.");
    } catch (caught) {
      if (caught instanceof ApiError && caught.code === "NOT_IMPLEMENTED") setAvailable(false);
      else setStatus("Could not save preferences. Nothing was changed.");
    }
  }

  return (
    <div className="stack">
      <section className="card">
        <h3 className="card-title">Preference setting</h3>
        {!available && <p className="meta" role="status">Saving preferences isn&apos;t available yet. Replies still work with the tone you pick each time.</p>}
        <div className="pref-grid">
          {FIELDS.map((field) => (
            <div key={field.key} className="pref-item">
              <label className="field-label" htmlFor={`pref-${field.key}`}>{field.label}</label>
              <select
                id={`pref-${field.key}`}
                className="input"
                disabled={!available}
                value={prefs[field.key]}
                onChange={(e) => setPrefs({ ...prefs, [field.key]: e.target.value } as CommunicationPreferences)}
              >
                {field.options.map((option) => (
                  <option key={option} value={option}>{cap(option)}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
        <div className="row-end">
          <button type="button" className="btn btn-primary" onClick={onSave} disabled={!available}>Save</button>
        </div>
        <p className="meta" role="status">{status}</p>
      </section>
    </div>
  );
}

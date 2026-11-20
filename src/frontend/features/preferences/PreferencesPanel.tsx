"use client";

import { useEffect, useId, useState } from "react";
import { CommunicationPreferences } from "@/frontend/api/contract";
import { ApiError, getPreferences, isMockMode, savePreferences } from "@/frontend/api/replyApi";

const DEFAULTS: CommunicationPreferences = { tone: "neutral", responseLength: "short", formality: "professional", directness: "balanced" };

const FIELDS: { key: keyof CommunicationPreferences; label: string; options: string[] }[] = [
  { key: "tone", label: "Tone", options: ["diplomatic", "neutral", "assertive"] },
  { key: "responseLength", label: "Length", options: ["short", "medium", "long"] },
  { key: "formality", label: "Formality", options: ["casual", "professional", "formal"] },
  { key: "directness", label: "Directness", options: ["gentle", "balanced", "direct"] },
];

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const storageKey = "rage-to-reply.preferences";

export function readLocalPreferences(): CommunicationPreferences {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) ?? "null");
    if (saved && FIELDS.every(({ key, options }) => options.includes(saved[key]))) return saved;
  } catch {
    // Keep defaults if the browser disallows storage or the value is invalid.
  }
  return DEFAULTS;
}

export default function PreferencesPanel({
  allowBrowserStorage = false,
  onSaved,
}: { allowBrowserStorage?: boolean; onSaved?: (prefs: CommunicationPreferences) => void }) {
  const fieldId = useId();
  const [prefs, setPrefs] = useState<CommunicationPreferences>(DEFAULTS);
  const [storage, setStorage] = useState<"loading" | "api" | "browser" | "unavailable">("loading");
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    let cancelled = false;
    function loadBrowserPreferences() {
      setPrefs(readLocalPreferences());
      setStorage("browser");
    }
    if (allowBrowserStorage && isMockMode) {
      loadBrowserPreferences();
      return;
    }
    getPreferences()
      .then((saved) => {
        if (cancelled) return;
        setPrefs(saved);
        setStorage("api");
      })
      .catch((caught) => {
        if (cancelled) return;
        if (caught instanceof ApiError && caught.status === 501 && allowBrowserStorage) {
          loadBrowserPreferences();
          return;
        }
        setStorage(caught instanceof ApiError && caught.status === 501 ? "unavailable" : "api");
        setStatus("Could not load saved preferences. Showing defaults.");
      });
    return () => { cancelled = true; };
  }, [allowBrowserStorage]);

  async function onSave() {
    setSaving(true);
    try {
      let saved = prefs;
      if (storage === "browser") {
        localStorage.setItem(storageKey, JSON.stringify(prefs));
      } else {
        saved = await savePreferences(prefs);
      }
      setPrefs(saved);
      onSaved?.(saved);
      setStatus(storage === "browser" ? "Preferences saved in this browser." : "Preferences saved.");
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 501) setStorage("unavailable");
      else setStatus("Could not save preferences. Nothing was changed.");
    } finally {
      setSaving(false);
    }
  }

  const disabled = storage === "loading" || storage === "unavailable" || saving;

  return (
    <section className="panel preferences-panel">
      <h2>Communication preferences</h2>
      {storage === "browser" && <p className="small-text">Settings are stored in this browser. The workspace applies your preferred tone.</p>}
      {storage === "unavailable" && <p className="small-text" role="status">Saving preferences isn&apos;t available yet. Replies still work with the tone you pick each time.</p>}
      <div className="pref-grid">
        {FIELDS.map((field) => (
          <div key={field.key} className="pref-item">
            <label htmlFor={`${fieldId}-${field.key}`}>{field.label}</label>
            <select
              id={`${fieldId}-${field.key}`}
              disabled={disabled}
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
      <div className="preferences-actions">
        <button type="button" className="primary-button" onClick={onSave} disabled={disabled}>{saving ? "Saving…" : "Save"}</button>
      </div>
      <p className="small-text" role="status">{status}</p>
    </section>
  );
}

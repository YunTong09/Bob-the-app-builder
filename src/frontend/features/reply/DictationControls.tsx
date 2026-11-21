"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";

type DictationLanguage = "en-US" | "zh-TW";
type RecognitionResult = { isFinal: boolean; 0?: { transcript: string } };
type Recognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onstart: (() => void) | null;
  onspeechstart: (() => void) | null;
  onspeechend: (() => void) | null;
  onresult: ((event: { resultIndex: number; results: ArrayLike<RecognitionResult> }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
};

function recognitionConstructor() {
  const browser = window as Window & {
    SpeechRecognition?: new () => Recognition;
    webkitSpeechRecognition?: new () => Recognition;
  };
  return browser.SpeechRecognition ?? browser.webkitSpeechRecognition;
}

const SILENCE_DELAY_MS = 1500;

const errorMessages: Record<string, string> = {
  "not-allowed": "Microphone permission was denied.",
  "service-not-allowed": "The browser blocked its speech recognition service.",
  "audio-capture": "No microphone is available.",
  "no-speech": "No speech was detected.",
  "network": "The browser could not reach its speech recognition service.",
  "aborted": "Dictation was interrupted.",
  "language-not-supported": "The browser does not support dictation in this language.",
};

export function appendDictation(draft: string, text: string) {
  const separator = draft && !/\s$/.test(draft) ? " " : "";
  const available = Math.max(0, 10000 - draft.length - separator.length);
  const addition = text.slice(0, available).replace(/[\uD800-\uDBFF]$/, "");
  return addition ? draft + separator + addition : draft;
}

export default function DictationControls({
  children,
  onTranscript,
  disabled = false,
}: {
  children: ReactNode;
  onTranscript: (text: string) => void;
  disabled?: boolean;
}) {
  const languageId = useId();
  const privacyId = useId();
  const active = useRef<Recognition | null>(null);
  const silenceTimer = useRef<number | undefined>(undefined);
  const stopRequested = useRef(false);
  const onTranscriptRef = useRef(onTranscript);
  const [supported, setSupported] = useState<boolean | null>(null);
  const [language, setLanguage] = useState<DictationLanguage>("en-US");
  const [phase, setPhase] = useState<"idle" | "starting" | "listening" | "stopping">("idle");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    onTranscriptRef.current = onTranscript;
  }, [onTranscript]);

  useEffect(() => {
    setSupported(Boolean(recognitionConstructor()));
    return () => {
      window.clearTimeout(silenceTimer.current);
      const session = active.current;
      active.current = null;
      if (!session) return;
      session.onspeechstart = session.onspeechend = null;
      session.onstart = session.onresult = session.onerror = session.onend = null;
      session.abort();
    };
  }, []);

  function stop(session: Recognition) {
    if (active.current !== session || stopRequested.current) return;
    stopRequested.current = true;
    window.clearTimeout(silenceTimer.current);
    setPhase("stopping");
    session.stop();
  }

  function toggle() {
    if (active.current) {
      stop(active.current);
      return;
    }
    const Constructor = recognitionConstructor();
    if (!Constructor) return;
    const finalResults = new Map<number, string>();
    let problem = "";
    let session: Recognition;
    try {
      session = new Constructor();
      session.lang = language;
      session.continuous = true;
      // Show listening status and keep any interim transcript out of the draft.
      session.interimResults = false;
      session.onstart = () => {
        if (active.current === session) {
          setPhase((current) => current === "starting" ? "listening" : current);
        }
      };
      session.onspeechstart = () => {
        if (active.current === session) window.clearTimeout(silenceTimer.current);
      };
      session.onspeechend = () => {
        if (active.current !== session || stopRequested.current) return;
        window.clearTimeout(silenceTimer.current);
        silenceTimer.current = window.setTimeout(() => stop(session), SILENCE_DELAY_MS);
      };
      session.onresult = ({ resultIndex, results }) => {
        if (active.current !== session) return;
        for (let index = resultIndex; index < results.length; index++) {
          const result = results[index];
          if (result.isFinal) finalResults.set(index, result[0]?.transcript.trim() ?? "");
        }
      };
      session.onerror = ({ error }) => {
        if (active.current !== session) return;
        window.clearTimeout(silenceTimer.current);
        problem = errorMessages[error] ?? "Speech recognition failed.";
        setNotice(`${problem} You can keep typing.`);
      };
      session.onend = () => {
        if (active.current !== session) return;
        window.clearTimeout(silenceTimer.current);
        active.current = null;
        setPhase("idle");
        const transcript = Array.from(finalResults.entries())
          .sort(([first], [second]) => first - second)
          .map(([, text]) => text)
          .filter(Boolean)
          .join(" ");
        if (transcript) onTranscriptRef.current(transcript);
        setNotice(problem
          ? `${problem} You can keep typing.`
          : transcript ? "Dictation finished. Review your draft." : "No speech was added. You can keep typing.");
      };
      stopRequested.current = false;
      active.current = session;
      setNotice("");
      setPhase("starting");
      session.start();
    } catch {
      active.current = null;
      setPhase("idle");
      setNotice("Could not start dictation. You can keep typing.");
    }
  }

  const recording = phase !== "idle";
  const action = recording ? "Stop dictation" : "Start dictation";
  return (
    <div className="dictation-controls">
      <div className={supported ? "dictation-input has-dictation" : "dictation-input"}>
        {children}
        {supported && (
          <button type="button" className="dictation-button" aria-label={action} title={action}
            aria-describedby={privacyId} aria-pressed={recording}
            disabled={phase === "starting" || phase === "stopping" || (disabled && !recording)} onClick={toggle}>
            <span className={recording ? "dictation-stop" : "dictation-mic"} aria-hidden="true" />
          </button>
        )}
      </div>
      {supported === false && <p className="small-text">Dictation is unavailable in this browser. You can keep typing.</p>}
      {supported && (
        <>
          <div className="dictation-language">
            <label htmlFor={languageId}>Dictation language</label>
            <select id={languageId} value={language} disabled={recording || disabled}
              onChange={(event) => setLanguage(event.target.value === "zh-TW" ? "zh-TW" : "en-US")}>
              <option value="en-US">English (US)</option>
              <option value="zh-TW" lang="zh-TW">繁體中文</option>
            </select>
          </div>
          <p className="small-text" id={privacyId}>Your browser may send audio to its speech service. This app does not store audio.</p>
          <p className="small-text" role="status">
            {notice || (phase === "starting" ? "Starting microphone…" : phase === "listening" ? "● Listening…" : phase === "stopping" ? "Finishing dictation…" : "")}
          </p>
        </>
      )}
    </div>
  );
}

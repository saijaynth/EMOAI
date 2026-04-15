"use client";

import { useRef, useState } from "react";

type Props = { onSubmit: () => void; language: string };

export function VoiceInput({ onSubmit, language }: Props) {
  const recognitionRef = useRef<any>(null);
  const [transcript, setTranscript] = useState("");
  const [listening, setListening] = useState(false);
  const [error, setError] = useState("");

  const startListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.lang = language.toLowerCase().startsWith("english") ? "en-US" : "en-US";

    recognition.onresult = (event: any) => {
      const text = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join(" ")
        .trim();
      setTranscript(text);
    };

    recognition.onerror = (event: any) => {
      setError(`Voice error: ${event.error ?? "unknown"}`);
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };

    setError("");
    setListening(true);
    recognition.start();
  };

  const stopListening = () => {
    recognitionRef.current?.stop?.();
    setListening(false);
  };

  const handleSubmit = () => {
    const clean = transcript.trim();
    sessionStorage.setItem("emoai_voice", clean);
    onSubmit();
  };

  return (
    <div className="mt-6 space-y-3">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={listening ? stopListening : startListening}
          className={`rounded-xl px-4 py-2 font-semibold transition ${
            listening ? "bg-coral text-white" : "bg-white/15 text-white hover:bg-white/25"
          }`}
        >
          {listening ? "Stop Listening" : "Start Listening"}
        </button>
      </div>

      <textarea
        value={transcript}
        onChange={(e) => setTranscript(e.target.value)}
        placeholder="Speak and transcribe, or type transcript manually..."
        className="h-36 w-full rounded-2xl border border-white/20 bg-white/10 p-4 outline-none placeholder:text-white/40 focus:ring-2 focus:ring-coral resize-none"
      />

      {error && <p className="rounded-xl bg-red-500/25 p-3 text-sm">{error}</p>}

      <div className="mt-2 flex items-center justify-between">
        <p className="text-xs text-white/40">{transcript.length} chars</p>
        <button
          type="button"
          disabled={transcript.trim().length === 0}
          onClick={handleSubmit}
          className="rounded-xl bg-coral px-6 py-3 font-bold text-white disabled:opacity-40 hover:bg-coral/80 transition"
        >
          Analyze Voice Mood →
        </button>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";

type Props = { onSubmit: () => void };

export function TextInput({ onSubmit }: Props) {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    sessionStorage.setItem("emoai_text", text.trim());
    onSubmit();
  };

  return (
    <div className="mt-8">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. I feel a bit tired but hopeful. Had a rough morning but things are looking up."
        className="glass h-48 w-full p-6 text-lg font-body text-ink outline-none transition-all duration-300 placeholder:text-ink/40 focus:border-primary focus:ring-4 focus:ring-primary/20 resize-none leading-relaxed"
      />
      <div className="mt-6 flex items-center justify-between">
        <p className="font-display text-sm uppercase tracking-widest text-ink/60">{text.length} <span className="opacity-50">/ 1200</span></p>
        <button
          type="button"
          disabled={text.trim().length === 0}
          onClick={handleSubmit}
          className="btn-vibrant px-8 py-4 text-base disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          Initialize Analysis
        </button>
      </div>
    </div>
  );
}

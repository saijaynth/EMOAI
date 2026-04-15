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
    <div className="mt-10">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. I feel a bit tired but hopeful. Had a rough morning but things are looking up."
        className="h-48 w-full rounded-[24px] border border-white/10 bg-white/5 p-6 font-light text-white outline-none transition-all duration-500 placeholder:text-white/20 focus:border-coral/50 focus:bg-white/10 focus:shadow-glow resize-none backdrop-blur-md leading-relaxed"
      />
      <div className="mt-6 flex items-center justify-between">
        <p className="text-xs uppercase tracking-widest text-white/30">{text.length} <span className="opacity-50">/ 1200</span></p>
        <button
          type="button"
          disabled={text.trim().length === 0}
          onClick={handleSubmit}
          className="rounded-full bg-coral/10 border border-coral text-coral px-8 py-4 font-display text-sm uppercase tracking-widest font-medium transition-all duration-300 disabled:opacity-30 disabled:border-white/10 disabled:text-white/30 disabled:bg-transparent hover:bg-coral hover:text-white hover:shadow-glow"
        >
          Initialize Analysis
        </button>
      </div>
    </div>
  );
}

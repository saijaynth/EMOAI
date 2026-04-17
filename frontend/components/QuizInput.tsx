"use client";

import { useState } from "react";
import type { MoodLabel } from "../lib/api";

const QUESTIONS: { q: string; options: { label: string; mood: MoodLabel }[] }[] = [
  {
    q: "How is your energy level right now?",
    options: [
      { label: "🔥 Very high", mood: "excited" },
      { label: "⚡ Moderate", mood: "focused" },
      { label: "😌 Low but okay", mood: "calm" },
      { label: "😔 Drained", mood: "sad" },
    ],
  },
  {
    q: "What best describes your thoughts?",
    options: [
      { label: "🌈 Positive and clear", mood: "happy" },
      { label: "🎯 Locked in on something", mood: "focused" },
      { label: "🌀 Racing and scattered", mood: "anxious" },
      { label: "😶 Blank, not much", mood: "neutral" },
    ],
  },
  {
    q: "How do you feel about people around you right now?",
    options: [
      { label: "🤗 Want to connect", mood: "happy" },
      { label: "😤 Irritated by them", mood: "angry" },
      { label: "😶 Indifferent", mood: "neutral" },
      { label: "🥺 Missing someone", mood: "sad" },
    ],
  },
  {
    q: "What kind of music sounds right?",
    options: [
      { label: "🎉 Upbeat and danceable", mood: "excited" },
      { label: "🎸 Intense and raw", mood: "angry" },
      { label: "🎹 Soft and slow", mood: "calm" },
      { label: "🎧 Deep focus beats", mood: "focused" },
    ],
  },
  {
    q: "If today were a weather, it would be:",
    options: [
      { label: "☀️ Sunny and bright", mood: "happy" },
      { label: "🌧️ Rainy and grey", mood: "sad" },
      { label: "⛈️ Stormy", mood: "angry" },
      { label: "🌫️ Foggy and uncertain", mood: "anxious" },
    ],
  },
];

type Props = { onSubmit: (mood: MoodLabel) => void };

export function QuizInput({ onSubmit }: Props) {
  const [index, setIndex] = useState(0);
  const [scores, setScores] = useState<Record<string, number>>({});

  const pick = (mood: MoodLabel) => {
    const updated = { ...scores, [mood]: (scores[mood] ?? 0) + 1 };
    if (index < QUESTIONS.length - 1) {
      setScores(updated);
      setIndex(index + 1);
    } else {
      const winner = Object.entries(updated).sort((a, b) => b[1] - a[1])[0][0] as MoodLabel;
      onSubmit(winner);
    }
  };

  const q = QUESTIONS[index];

  return (
    <div className="mt-8 glass p-8 bg-white max-w-2xl mx-auto">
      <div className="mb-6 flex gap-2">
        {QUESTIONS.map((_, i) => (
          <div key={i} className={`h-3 flex-1 border-2 border-border ${i <= index ? "bg-cta" : "bg-slate-200"}`} />
        ))}
      </div>
      <p className="text-sm font-bold uppercase tracking-widest text-ink/50 mb-3">Question {index + 1} of {QUESTIONS.length}</p>
      <h2 className="font-display text-4xl uppercase tracking-wide font-bold leading-tight title-glow text-primary">{q.q}</h2>
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {q.options.map((opt) => (
          <button
            key={opt.label}
            type="button"
            onClick={() => pick(opt.mood)}
            className="border-[3px] border-border bg-white p-5 text-left font-bold text-lg cursor-pointer hover:bg-secondary/10 hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_var(--border-color)] active:translate-y-1 active:shadow-none transition-all duration-200"
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

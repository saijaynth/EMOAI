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
    <div className="mt-6">
      <div className="mb-4 flex gap-1">
        {QUESTIONS.map((_, i) => (
          <div key={i} className={`h-1.5 flex-1 rounded-full ${i <= index ? "bg-coral" : "bg-white/20"}`} />
        ))}
      </div>
      <p className="text-xs text-white/50 mb-2">Question {index + 1} of {QUESTIONS.length}</p>
      <h2 className="font-display text-2xl font-bold">{q.q}</h2>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {q.options.map((opt) => (
          <button
            key={opt.label}
            type="button"
            onClick={() => pick(opt.mood)}
            className="glass card-hover rounded-2xl p-4 text-left ring-1 ring-white/15 hover:ring-coral transition font-semibold"
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

"use client";

import { motion } from "framer-motion";

const MESSAGES = [
  "Reading your emotional frequency...",
  "Scanning the universal song map...",
  "Filtering by your language...",
  "Ranking by mood resonance...",
];

export function LoadingScreen({ language }: { language: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <motion.div
        animate={{ scale: [1, 1.15, 1], rotate: [0, 10, -10, 0] }}
        transition={{ duration: 1.8, repeat: Infinity }}
        className="text-7xl mb-8 glass p-6 bg-white inline-block shadow-[6px_6px_0px_0px_var(--border-color)]"
      >
        ✨
      </motion.div>
      <h2 className="font-display text-4xl uppercase tracking-wide font-bold title-glow">Finding your sound...</h2>
      <p className="mt-4 text-ink/60 font-bold font-body">Matching mood to <span className="text-primary tracking-widest uppercase">{language}</span> songs</p>
      <div className="mt-8 flex flex-col gap-3">
        {MESSAGES.map((msg, i) => (
          <motion.p
            key={msg}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.5 }}
            className="text-sm font-bold text-ink/50 font-body uppercase tracking-wider"
          >
            {msg}
          </motion.p>
        ))}
      </div>
    </div>
  );
}

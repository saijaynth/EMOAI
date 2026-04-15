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
        animate={{ scale: [1, 1.15, 1], opacity: [0.7, 1, 0.7] }}
        transition={{ duration: 1.8, repeat: Infinity }}
        className="text-7xl mb-8"
      >
        🎵
      </motion.div>
      <h2 className="font-display text-3xl font-bold">Finding your sound...</h2>
      <p className="mt-2 text-white/60">Matching mood to <span className="text-mint font-semibold">{language}</span> songs</p>
      <div className="mt-8 flex flex-col gap-2">
        {MESSAGES.map((msg, i) => (
          <motion.p
            key={msg}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.5 }}
            className="text-sm text-white/50"
          >
            {msg}
          </motion.p>
        ))}
      </div>
    </div>
  );
}

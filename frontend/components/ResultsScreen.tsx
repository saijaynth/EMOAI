"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { SongCard } from "./SongCard";
import type { MoodResult, SongItem, UserIdentity } from "../app/page";

const MOOD_COLORS: Record<string, string> = {
  happy: "bg-yellow-300 text-yellow-900 border-yellow-400",
  excited: "bg-orange-400 text-orange-950 border-orange-500",
  calm: "bg-green-300 text-green-900 border-green-400",
  focused: "bg-blue-300 text-blue-900 border-blue-400",
  sad: "bg-indigo-300 text-indigo-900 border-indigo-400",
  angry: "bg-red-400 text-red-950 border-red-500",
  anxious: "bg-purple-300 text-purple-900 border-purple-400",
  neutral: "bg-gray-300 text-gray-900 border-gray-400",
  romantic: "bg-pink-300 text-pink-900 border-pink-400",
  nostalgic: "bg-amber-200 text-amber-900 border-amber-300",
  confident: "bg-emerald-300 text-emerald-900 border-emerald-400",
  dreamy: "bg-fuchsia-200 text-fuchsia-900 border-fuchsia-300",
  triumphant: "bg-amber-400 text-amber-950 border-amber-500",
  chill: "bg-cyan-200 text-cyan-900 border-cyan-300",
  hype: "bg-rose-400 text-rose-950 border-rose-500",
  melancholic: "bg-slate-400 text-slate-900 border-slate-500",
  hopeful: "bg-teal-300 text-teal-900 border-teal-400",
  frustrated: "bg-stone-400 text-stone-900 border-stone-500",
  bored: "bg-zinc-300 text-zinc-800 border-zinc-400",
};

type Props = {
  mood: MoodResult;
  language: string;
  context: string;
  songs: SongItem[];
  user: UserIdentity | null;
  apiBase: string;
  onReset: () => void;
};

export function ResultsScreen({ mood, language, context, songs, user, apiBase, onReset }: Props) {
  const [feedback, setFeedback] = useState<Record<string, string>>({});

  const sendFeedback = async (songId: string, action: "like" | "skip" | "save") => {
    setFeedback((prev) => ({ ...prev, [songId]: action }));
    await fetch(`${apiBase}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        song_id: songId,
        action,
        relevance_score: action === "like" ? 5 : action === "save" ? 4 : 2,
        mood: mood.mood,
        language,
      }),
    }).catch(() => null);
  };

  return (
    <div className="mt-8 animate-fade-in">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mb-12 glass p-8">
        <p className="mb-4 text-sm font-bold uppercase tracking-[0.2em] text-cta">Sonic Profile Generated</p>
        <div className="flex items-center justify-between flex-wrap gap-4 font-display">
          <div className="flex items-center gap-4">
            <span className={`border-[3px] shadow-[4px_4px_0px_0px_var(--border-color)] px-6 py-2 text-4xl font-bold uppercase tracking-wide ${MOOD_COLORS[mood.mood] ?? "bg-white text-ink border-border"}`}>
              {mood.mood}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="border-[3px] border-border bg-white text-ink font-bold px-4 py-2 text-sm tracking-widest uppercase shadow-[2px_2px_0px_0px_var(--border-color)]">{language}</span>
            <span className="border-[3px] border-border bg-white text-ink font-bold px-4 py-2 text-sm tracking-widest uppercase shadow-[2px_2px_0px_0px_var(--border-color)]">{context}</span>
          </div>
        </div>
      </motion.div>

      <div className="grid gap-6 sm:grid-cols-2 mb-12">
        {songs.map((song, i) => (
          <motion.div
            key={song.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <SongCard
              title={song.title}
              artist={song.artist}
              language={song.language}
              moods={song.mood_tags}
              energy={song.energy}
              feedbackState={feedback[song.id]}
              spotifySearchUrl={`https://open.spotify.com/search/${encodeURIComponent(`${song.title} ${song.artist}`)}`}
              onFeedback={(action) => sendFeedback(song.id, action)}
            />
          </motion.div>
        ))}
      </div>

      {songs.length === 0 && (
        <p className="mt-8 p-6 glass text-center font-bold text-ink/60 text-lg">No songs matched this profile</p>
      )}

      <div className="mt-16 text-center">
        <button
          onClick={onReset}
          className="btn-vibrant px-10 py-5 text-xl cursor-pointer"
        >
          <span className="mr-3 font-bold">←</span>
          Initiate New Sequence
        </button>
      </div>
    </div>
  );
}

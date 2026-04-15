"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { SongCard } from "./SongCard";
import type { MoodResult, SongItem, UserIdentity } from "../app/page";

const MOOD_COLORS: Record<string, string> = {
  happy: "bg-amber/30 text-amber",
  excited: "bg-coral/30 text-coral",
  calm: "bg-mint/30 text-mint",
  focused: "bg-blue-400/30 text-blue-300",
  sad: "bg-indigo-400/30 text-indigo-300",
  angry: "bg-red-500/30 text-red-300",
  anxious: "bg-yellow-500/30 text-yellow-300",
  neutral: "bg-white/20 text-white/70",
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

type UserProfile = {
  user_id: string;
  username: string;
  total_sessions: number;
  favorite_mood: string | null;
  favorite_language: string | null;
  last_mood: string | null;
};

type SessionRecord = {
  session_id: string;
  user_id: string;
  mood: string;
  language: string;
  context: string;
  method: string;
  song_ids: string[];
  created_at: string;
};

export function ResultsScreen({ mood, language, context, songs, user, apiBase, onReset }: Props) {
  const [energyFilter, setEnergyFilter] = useState(1.0);
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [sessions, setSessions] = useState<SessionRecord[]>([]);

  const filtered = songs.filter((s) => s.energy <= energyFilter);

  useEffect(() => {
    if (!user) {
      return;
    }

    const loadProfile = async () => {
      const profileRes = await fetch(`${apiBase}/users/${user.user_id}/profile`);
      if (profileRes.ok) {
        setProfile((await profileRes.json()) as UserProfile);
      }

      const sessionsRes = await fetch(`${apiBase}/users/${user.user_id}/sessions`);
      if (sessionsRes.ok) {
        const history = (await sessionsRes.json()) as SessionRecord[];
        setSessions(history.slice(0, 5));
      }
    };

    void loadProfile().catch(() => null);
  }, [apiBase, user]);

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
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="mb-12">
        <p className="mb-4 text-xs uppercase tracking-[0.2em] text-white/40 font-medium">Sonic Profile Generated</p>
        <div className="flex items-center gap-4 flex-wrap font-display">
          <span className={`rounded-full border border-white/10 px-6 py-2 text-3xl font-light tracking-wide capitalize shadow-glow ${MOOD_COLORS[mood.mood] ?? "text-white"}`}>
            {mood.mood}
          </span>
          <div className="h-px border-t border-white/10 w-8 mx-2" />
          <span className="text-lg font-light text-white/40 tracking-widest uppercase">{(mood.confidence * 100).toFixed(0)}% Confident</span>
          <span className="rounded-full border border-mint/20 text-mint px-4 py-1.5 text-xs tracking-widest uppercase">{language}</span>
          <span className="rounded-full border border-coral/20 text-coral px-4 py-1.5 text-xs tracking-widest uppercase capitalize">{context}</span>
        </div>
      </motion.div>

      {user && (
        <div className="glass rounded-[24px] p-8 mb-10 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 blur-3xl rounded-full -translate-y-1/2 translate-x-1/3 group-hover:bg-white/10 transition-colors duration-700" />
          <p className="mb-6 text-xs uppercase tracking-[0.2em] text-white/40 border-b border-white/5 pb-4">Identity Matrix</p>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 text-sm font-light text-white/70">
            <div className="flex flex-col"><span className="text-white/30 text-[10px] uppercase tracking-widest mb-1">Subject</span><span className="text-lg">{profile?.username ?? user.username}</span></div>
            <div className="flex flex-col"><span className="text-white/30 text-[10px] uppercase tracking-widest mb-1">Sessions</span><span className="text-lg">{profile?.total_sessions ?? 0}</span></div>
            <div className="flex flex-col"><span className="text-white/30 text-[10px] uppercase tracking-widest mb-1">Dominant State</span><span className="text-lg capitalize">{profile?.favorite_mood ?? "-"}</span></div>
            <div className="flex flex-col"><span className="text-white/30 text-[10px] uppercase tracking-widest mb-1">Core Lang</span><span className="text-lg">{profile?.favorite_language ?? language}</span></div>
          </div>
          
          {sessions.length > 0 && (
            <div className="mt-8 pt-6 border-t border-white/5 relative z-10">
              <p className="mb-4 text-xs uppercase tracking-widest text-white/30">Historical Trajectory</p>
              <div className="space-y-3">
                {sessions.map((session) => (
                  <div key={session.session_id} className="group/row flex items-center justify-between gap-4 py-2 px-4 rounded-xl hover:bg-white/[0.03] transition-colors border border-transparent hover:border-white/[0.05]">
                    <span className="font-light text-sm text-white/60 capitalize tracking-wide">{session.mood} <span className="opacity-30 mx-2">/</span> {session.context} <span className="opacity-30 mx-2">/</span> {session.method}</span>
                    <span className="text-xs text-white/30 font-mono">{new Date(session.created_at).toLocaleDateString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="flex items-center gap-6 mb-10 border-b border-white/10 pb-8">
        <span className="text-xs uppercase tracking-[0.2em] text-white/40 whitespace-nowrap">Energy Output</span>
        <div className="relative flex-1 h-1 bg-white/10 rounded-full mx-4">
          <input
            type="range"
            min={0.1}
            max={1.0}
            step={0.05}
            value={energyFilter}
            onChange={(e) => setEnergyFilter(parseFloat(e.target.value))}
            className="absolute inset-0 w-full opacity-0 cursor-pointer z-10"
          />
          <div className="absolute top-0 left-0 h-full bg-coral rounded-full shadow-glow pointer-events-none transition-all duration-300" style={{ width: `${energyFilter * 100}%` }} />
          <div className="absolute top-1/2 -ml-2 -mt-2 w-4 h-4 rounded-full bg-white shadow-glow pointer-events-none transition-all duration-300" style={{ left: `${energyFilter * 100}%` }} />
        </div>
        <span className="text-lg font-light text-coral tracking-widest w-12 text-right">{Math.round(energyFilter * 100)}%</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {filtered.map((song, i) => (
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

      {filtered.length === 0 && (
        <p className="mt-6 text-center text-white/50">No songs match this energy level. Try raising the slider.</p>
      )}

      <div className="mt-16 text-center">
        <button
          onClick={onReset}
          className="group relative inline-flex items-center gap-4 px-8 py-4 backdrop-blur-md transition-all duration-500"
        >
          <span className="absolute inset-0 rounded-full border border-white/20 group-hover:border-white/50 group-hover:scale-105 transition-all duration-500" />
          <span className="text-white/40 group-hover:-translate-x-1 transition-transform duration-500">←</span>
          <span className="font-display text-sm tracking-[0.2em] font-light text-white/60 uppercase group-hover:text-white transition-colors duration-500" style={{ letterSpacing: '0.3em' }}>Initiate New Sequence</span>
        </button>
      </div>
    </div>
  );
}

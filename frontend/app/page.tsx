"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

import { LanguagePicker } from "../components/LanguagePicker";
import { MoodMethodCard } from "../components/MoodMethodCard";
import { TextInput } from "../components/TextInput";
import { QuizInput } from "../components/QuizInput";
import { VoiceInput } from "../components/VoiceInput";
import { FaceInput } from "../components/FaceInput";
import { LoadingScreen } from "../components/LoadingScreen";
import { ResultsScreen } from "../components/ResultsScreen";

export type MoodLabel = "happy" | "sad" | "angry" | "calm" | "anxious" | "focused" | "excited" | "neutral";

export type SongItem = {
  id: string;
  title: string;
  artist: string;
  language: string;
  mood_tags: MoodLabel[];
  energy: number;
};

export type MoodResult = {
  mood: MoodLabel;
  confidence: number;
};

export type UserIdentity = {
  user_id: string;
  username: string;
};

const METHODS = [
  { key: "text" as const, title: "Text Journal", subtitle: "Describe how you feel in words.", icon: "✍️", ready: true },
  { key: "quiz" as const, title: "Quick Quiz", subtitle: "Answer 5 micro-questions.", icon: "🎯", ready: true },
  { key: "voice" as const, title: "Voice Tone", subtitle: "Speak for 10 seconds.", icon: "🎙️", ready: true },
  { key: "face" as const, title: "Face Scan", subtitle: "Camera expression analysis.", icon: "📷", ready: true },
] as const;

const CONTEXTS = ["general", "study", "workout", "relax", "sleep", "party"] as const;

type Method = (typeof METHODS)[number]["key"];

type FacePayload = {
  expression: "smile" | "frown" | "neutral" | "surprised" | "tense";
  intensity: number;
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -16 },
  transition: { duration: 0.35 },
};

export default function HomePage() {
  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [languages, setLanguages] = useState<string[]>([]);
  const [language, setLanguage] = useState("");
  const [context, setContext] = useState<(typeof CONTEXTS)[number]>("general");
  const [method, setMethod] = useState<Method>("text");
  const [moodResult, setMoodResult] = useState<MoodResult | null>(null);
  const [songs, setSongs] = useState<SongItem[]>([]);
  const [error, setError] = useState("");
  const [user, setUser] = useState<UserIdentity | null>(null);

  useEffect(() => {
    fetch(`${apiBase}/languages`)
      .then((r) => r.json())
      .then((d: { languages: string[] }) => {
        setLanguages(d.languages);
        setLanguage(d.languages[0] ?? "English");
      })
      .catch(() => setError("Could not load languages."));

    const existingUserId = localStorage.getItem("emoai_user_id");
    const existingUsername = localStorage.getItem("emoai_username");
    if (existingUserId && existingUsername) {
      setUser({ user_id: existingUserId, username: existingUsername });
      return;
    }

    const guestName = `guest_${Math.floor(1000 + Math.random() * 9000)}`;
    fetch(`${apiBase}/users/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: guestName }),
    })
      .then((r) => r.json())
      .then((u: UserIdentity) => {
        localStorage.setItem("emoai_user_id", u.user_id);
        localStorage.setItem("emoai_username", u.username);
        setUser(u);
      })
      .catch(() => null);
  }, []);

  const runAnalysis = async (quizMood?: MoodLabel) => {
    setStep(4);
    setError("");
    try {
      let detected: MoodResult;

      if (quizMood) {
        detected = { mood: quizMood, confidence: 0.82 };
      } else if (method === "text") {
        const text = sessionStorage.getItem("emoai_text") ?? "";
        const res = await fetch(`${apiBase}/mood/detect/text`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, language }),
        });
        if (!res.ok) throw new Error("Mood detection failed");
        detected = (await res.json()) as MoodResult;
      } else if (method === "voice") {
        const transcript = sessionStorage.getItem("emoai_voice") ?? "";
        const res = await fetch(`${apiBase}/mood/detect/voice`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript, language }),
        });
        if (!res.ok) throw new Error("Voice mood detection failed");
        detected = (await res.json()) as MoodResult;
      } else {
        const raw = sessionStorage.getItem("emoai_face") ?? "{}";
        const payload = JSON.parse(raw) as FacePayload;
        const res = await fetch(`${apiBase}/mood/detect/face`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ expression: payload.expression ?? "neutral", intensity: payload.intensity ?? 0.5, language }),
        });
        if (!res.ok) throw new Error("Face mood detection failed");
        detected = (await res.json()) as MoodResult;
      }

      const recRes = await fetch(
        `${apiBase}/recommendations?mood=${encodeURIComponent(detected.mood)}&language=${encodeURIComponent(language)}&context=${encodeURIComponent(context)}&confidence=${detected.confidence}`,
      );
      if (!recRes.ok) throw new Error("Recommendations failed");
      const recData = (await recRes.json()) as { recommendations: SongItem[] };

      setMoodResult(detected);
      setSongs(recData.recommendations);

      if (user) {
        await fetch(`${apiBase}/sessions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: user.user_id,
            mood: detected.mood,
            language,
            context,
            method,
            song_ids: recData.recommendations.map((song) => song.id),
          }),
        }).catch(() => null);
      }

      setStep(5);
    } catch (e) {
      setError((e as Error).message);
      setStep(3);
    }
  };

  const reset = () => {
    setStep(1);
    setMoodResult(null);
    setSongs([]);
    setError("");
    sessionStorage.removeItem("emoai_text");
    sessionStorage.removeItem("emoai_voice");
    sessionStorage.removeItem("emoai_face");
  };

  return (
    <main>
      <div className="mb-16 flex items-center justify-between">
        <button onClick={reset} className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/5 border border-white/10 group-hover:bg-coral/20 group-hover:border-coral/50 transition-all duration-500">
             <span className="text-lg">✧</span>
          </div>
          <span className="font-display text-2xl font-light tracking-wide group-hover:text-coral transition-colors">Emo AI</span>
        </button>
        {step > 1 && step < 5 && (
          <div className="flex gap-3">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-1 rounded-full transition-all duration-700 ${step >= s + 1 ? "bg-coral w-12 shadow-glow" : "bg-white/10 w-6"}`}
              />
            ))}
          </div>
        )}
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div key="step1" {...fadeUp}>
            <p className="mb-3 text-xs uppercase tracking-[0.2em] text-coral/80 font-medium">Step 1 of 3</p>
            <h1 className="font-display text-5xl font-light sm:text-7xl tracking-tight leading-tight title-glow">Language <br/><span className="text-white/40 italic">preference</span></h1>
            <p className="mt-6 text-lg text-white/50 max-w-xl font-light leading-relaxed">Establish the baseline for your sonic landscape. Every recommendation resonates in this tongue.</p>
            <LanguagePicker
              languages={languages}
              selected={language}
              onSelect={(lang) => {
                setLanguage(lang);
                setStep(2);
              }}
            />
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="step2" {...fadeUp}>
            <p className="mb-3 text-xs uppercase tracking-[0.2em] text-coral/80 font-medium">Step 2 of 3</p>
            <h1 className="font-display text-5xl font-light sm:text-7xl tracking-tight leading-tight title-glow">Signal <br/><span className="text-white/40 italic">method</span></h1>
            <p className="mt-6 text-lg text-white/50 max-w-xl font-light leading-relaxed">
              Vocalizing in <span className="font-medium text-mint/80">{language}</span>.
              <button onClick={() => setStep(1)} className="ml-3 text-sm underline underline-offset-4 opacity-40 hover:opacity-100 transition-opacity">recalibrate layer</button>
            </p>
            <div className="mt-10 max-w-md">
              <label className="text-xs uppercase tracking-widest text-white/40 mb-3 block">Environmental Context</label>
              <div className="relative">
                <select
                  value={context}
                  onChange={(e) => setContext(e.target.value as (typeof CONTEXTS)[number])}
                  className="w-full appearance-none rounded-xl border border-white/10 bg-white/5 px-6 py-4 text-lg font-light text-white outline-none transition-all hover:bg-white/10 focus:border-white/30 backdrop-blur-md"
                >
                  {CONTEXTS.map((ctx) => (
                    <option key={ctx} value={ctx} className="bg-canvas text-white">
                      {ctx}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute right-6 top-1/2 -translate-y-1/2 text-white/30">↓</div>
              </div>
            </div>
            <div className="mt-12 grid gap-6 sm:grid-cols-2">
              {METHODS.map((m) => (
                <MoodMethodCard
                  key={m.key}
                  title={m.title}
                  subtitle={m.subtitle}
                  icon={m.icon}
                  active={method === m.key}
                  ready={m.ready}
                  onClick={() => {
                    if (!m.ready) return;
                    setMethod(m.key);
                    setStep(3);
                  }}
                />
              ))}
            </div>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="step3" {...fadeUp}>
            <p className="mb-3 text-xs uppercase tracking-[0.2em] text-coral/80 font-medium">Step 3 of 3</p>
            <h1 className="font-display text-5xl font-light sm:text-7xl tracking-tight leading-tight title-glow">
              {method === "text" ? <>Express <br/><span className="text-white/40 italic">state.</span></> : method === "quiz" ? <>Micro <br/><span className="text-white/40 italic">diagnostics.</span></> : method === "voice" ? <>Vocal <br/><span className="text-white/40 italic">resonance.</span></> : <>Facial <br/><span className="text-white/40 italic">metrics.</span></>}
            </h1>
            <p className="mt-6 text-lg text-white/50 max-w-xl font-light leading-relaxed">
              Environment: <span className="font-medium text-mint/80 capitalize">{context}</span>
              <button onClick={() => setStep(2)} className="ml-3 text-sm underline underline-offset-4 opacity-40 hover:opacity-100 transition-opacity">← switch protocol</button>
            </p>
            {error && <p className="mt-3 rounded-xl bg-red-500/25 p-3 text-sm">{error}</p>}
            {method === "text" ? (
              <TextInput onSubmit={() => runAnalysis()} />
            ) : method === "quiz" ? (
              <QuizInput onSubmit={(mood) => runAnalysis(mood)} />
            ) : method === "voice" ? (
              <VoiceInput language={language} onSubmit={() => runAnalysis()} />
            ) : (
              <FaceInput onSubmit={() => runAnalysis()} />
            )}
          </motion.div>
        )}

        {step === 4 && (
          <motion.div key="step4" {...fadeUp}>
            <LoadingScreen language={language} />
          </motion.div>
        )}

        {step === 5 && moodResult && (
          <motion.div key="step5" {...fadeUp}>
            <ResultsScreen
              mood={moodResult}
              language={language}
              context={context}
              songs={songs}
              user={user}
              apiBase={apiBase}
              onReset={reset}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}

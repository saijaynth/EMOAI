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

export type MoodLabel = 
  | "happy" | "sad" | "angry" | "calm" | "anxious" | "focused" | "excited" | "neutral"
  | "romantic" | "nostalgic" | "confident" | "dreamy" | "triumphant" | "chill" | "hype"
  | "melancholic" | "hopeful" | "frustrated" | "bored";

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

type VoiceToneProfile = {
  duration_ms: number;
  speaking_rate_wpm: number;
  avg_volume: number;
  volume_variability: number;
  avg_pitch_hz: number | null;
  pitch_variability: number;
  pause_ratio: number;
  energy_label: string;
};

import { apiBase } from "../lib/api";

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
    // Default fallback languages - ensures app works even if API is down
    const defaultLanguages = [
      "English", "Hindi", "Spanish", "French", "Korean", 
      "Arabic", "Tamil", "Telugu", "Kannada", "Malayalam", "Punjabi"
    ];

    fetch(`${apiBase}/languages`)
      .then((r) => {
        if (!r.ok) throw new Error(`API returned ${r.status}`);
        return r.json();
      })
      .then((d: { languages: string[] }) => {
        if (d.languages && d.languages.length > 0) {
          setLanguages(d.languages);
          setLanguage(d.languages[0] ?? "English");
        } else {
          throw new Error("Empty languages array");
        }
      })
      .catch((err) => {
        console.warn("Failed to load languages from API, using fallback:", err);
        // Use fallback languages so app always works
        setLanguages(defaultLanguages);
        setLanguage("English");
      });

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
      .then((r) => {
        if (!r.ok) throw new Error(`Registration failed: ${r.status}`);
        return r.json();
      })
      .then((u: UserIdentity) => {
        localStorage.setItem("emoai_user_id", u.user_id);
        localStorage.setItem("emoai_username", u.username);
        setUser(u);
      })
      .catch((err) => {
        console.warn("User registration failed, continuing as guest:", err);
        // Continue without user - app still works
      });
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
        const toneRaw = sessionStorage.getItem("emoai_voice_tone");
        let tone_profile: VoiceToneProfile | undefined;
        if (toneRaw) {
          try {
            tone_profile = JSON.parse(toneRaw) as VoiceToneProfile;
          } catch {
            tone_profile = undefined;
          }
        }
        const res = await fetch(`${apiBase}/mood/detect/voice`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript, language, tone_profile }),
        });
        if (!res.ok) throw new Error("Voice mood detection failed");
        detected = (await res.json()) as MoodResult;
      } else {
        const image_data = sessionStorage.getItem("emoai_face") ?? "";
        if (!image_data) throw new Error("Face image data was empty or invalid.");
        const res = await fetch(`${apiBase}/mood/detect/face`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_data, language }),
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
    sessionStorage.removeItem("emoai_voice_tone");
    sessionStorage.removeItem("emoai_face");
  };

  return (
    <main>
      <div className="mb-16 flex items-center justify-between">
        <button onClick={reset} className="flex items-center gap-3 cursor-pointer group">
          <div className="flex h-12 w-12 items-center justify-center border-[3px] border-border bg-white group-hover:bg-primary group-hover:text-white transition-all shadow-[4px_4px_0px_0px_var(--border-color)] group-hover:translate-x-[-2px] group-hover:translate-y-[-2px] group-hover:shadow-[6px_6px_0px_0px_var(--border-color)] rounded-lg">
             <span className="text-xl font-bold">✧</span>
          </div>
          <span className="font-display text-3xl font-bold uppercase tracking-wide text-ink group-hover:title-glow transition-all">Emo AI</span>
        </button>
        {step > 1 && step < 5 && (
          <div className="flex gap-4">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-2 rounded-full border-2 border-border transition-all duration-300 ${step >= s + 1 ? "bg-cta w-16 shadow-[2px_2px_0px_0px_var(--border-color)]" : "bg-white w-8"}`}
              />
            ))}
          </div>

        )}
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div key="step1" {...fadeUp}>
            <p className="mb-4 text-sm font-bold uppercase tracking-[0.2em] text-cta">Step 1 of 3</p>
            <h1 className="font-display text-5xl sm:text-7xl tracking-tight leading-tight uppercase title-glow">Language <br/><span className="text-secondary">preference</span></h1>
            <p className="mt-6 text-lg text-ink/60 max-w-xl font-bold leading-relaxed">Establish the baseline for your sonic landscape. Every recommendation resonates in this tongue.</p>
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
            <p className="mb-4 text-sm font-bold uppercase tracking-[0.2em] text-cta">Step 2 of 3</p>
            <h1 className="font-display text-5xl sm:text-7xl tracking-tight leading-tight uppercase title-glow">Signal <br/><span className="text-secondary">method</span></h1>
            <p className="mt-6 text-lg text-ink/60 max-w-xl font-bold leading-relaxed">
              Vocalizing in <span className="font-display uppercase text-primary tracking-widest">{language}</span>.
              <button 
                onClick={() => {
                  setStep(1);
                  setError("");
                }} 
                className="ml-3 text-sm underline underline-offset-4 text-ink/40 hover:text-ink cursor-pointer transition-colors">Change Language</button>
            </p>
            <div className="mt-10 max-w-md">
              <label className="font-display text-sm font-bold uppercase tracking-widest text-ink mb-3 block">Environmental Context</label>
              <div className="relative">
                <select
                  value={context}
                  onChange={(e) => setContext(e.target.value as (typeof CONTEXTS)[number])}
                  className="glass w-full cursor-pointer appearance-none p-4 text-lg font-bold text-ink outline-none transition-all hover:bg-gray-50 focus:border-border font-body"
                >
                  {CONTEXTS.map((ctx) => (
                    <option key={ctx} value={ctx} className="bg-canvas text-ink font-bold">
                      {ctx.toUpperCase()}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute right-6 top-1/2 -translate-y-1/2 text-border font-bold">↓</div>
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
                    setError("");
                    setStep(3);
                  }}
                />
              ))}
            </div>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="step3" {...fadeUp}>
            <p className="mb-4 text-sm font-bold uppercase tracking-[0.2em] text-cta">Step 3 of 3</p>
            <h1 className="font-display text-5xl sm:text-7xl tracking-tight leading-tight uppercase title-glow">
              {method === "text" ? <>Express <br/><span className="text-secondary">state.</span></> : method === "quiz" ? <>Micro <br/><span className="text-secondary">diagnostics.</span></> : method === "voice" ? <>Vocal <br/><span className="text-secondary">resonance.</span></> : <>Facial <br/><span className="text-secondary">metrics.</span></>}
            </h1>
            <p className="mt-6 text-lg text-ink/60 max-w-xl font-bold leading-relaxed">
              Environment: <span className="font-display uppercase tracking-widest text-primary">{context}</span>
              <button 
                onClick={() => {
                  setStep(2);
                  setError("");
                }} 
                className="ml-3 text-sm underline underline-offset-4 text-ink/40 hover:text-ink cursor-pointer transition-colors">← Back</button>
            </p>
            {error && <p className="glass mt-3 bg-red-100 p-4 text-sm font-bold text-red-600 border-red-500">{error}</p>}
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

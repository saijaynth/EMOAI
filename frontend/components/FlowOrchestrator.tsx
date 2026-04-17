"use client";

import { motion, AnimatePresence } from "framer-motion";
import { LanguagePicker } from "./LanguagePicker";
import { MoodMethodCard } from "./MoodMethodCard";
import { TextInput } from "./TextInput";
import { QuizInput } from "./QuizInput";
import { VoiceInput } from "./VoiceInput";
import { FaceInput } from "./FaceInput";
import { LoadingScreen } from "./LoadingScreen";
import { ResultsScreen } from "./ResultsScreen";
import { useMoodAnalysis } from "../hooks/useMoodAnalysis";
import { apiBase } from "../lib/api";

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -16 },
  transition: { duration: 0.35 },
};

const METHODS = [
  { key: "text" as const, title: "Text Journal", subtitle: "Describe how you feel in words.", icon: "✍️", ready: true },
  { key: "quiz" as const, title: "Quick Quiz", subtitle: "Answer 5 micro-questions.", icon: "🎯", ready: true },
  { key: "voice" as const, title: "Voice Tone", subtitle: "Speak for 10 seconds.", icon: "🎙️", ready: true },
  { key: "face" as const, title: "Face Scan", subtitle: "Camera expression analysis.", icon: "📷", ready: true },
] as const;

export function FlowOrchestrator() {
  const { state, actions, CONTEXTS } = useMoodAnalysis();
  const { step, languages, language, context, method, moodResult, songs, error, user } = state;
  const { setStep, setLanguage, setContext, setMethod, runAnalysis, reset } = actions;

  return (
    <>
      <div className="mb-16 flex items-center justify-between">
        <button onClick={reset} className="flex items-center gap-3 group cursor-pointer focus-visible">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/5 border border-white/10 group-hover:bg-coral/20 group-hover:border-coral/50 transition-all duration-300">
             <span className="text-lg">✧</span>
          </div>
          <span className="font-display text-2xl font-light tracking-wide group-hover:text-coral transition-colors duration-300">Emo AI</span>
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
              <button 
                onClick={() => setStep(1)} 
                className="ml-3 text-sm underline md:min-w-[44px] min-h-[44px] inline-flex items-center underline-offset-4 opacity-40 hover:opacity-100 transition-opacity duration-300 cursor-pointer focus-visible">
                  recalibrate layer
              </button>
            </p>
            <div className="mt-10 max-w-md">
              <label htmlFor="context_selector" className="text-xs uppercase tracking-widest text-white/40 mb-3 block">Environmental Context</label>
              <div className="relative">
                <select
                  id="context_selector"
                  value={context}
                  onChange={(e) => setContext(e.target.value as typeof CONTEXTS[number])}
                  className="w-full cursor-pointer appearance-none rounded-xl border border-white/10 bg-white/5 px-6 py-4 text-lg font-light text-white outline-none transition-all duration-300 hover:bg-white/10 focus:ring-2 focus:ring-coral/50 backdrop-blur-md"
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
              <button 
                onClick={() => setStep(2)} 
                className="ml-3 text-sm underline md:min-w-[44px] min-h-[44px] inline-flex items-center underline-offset-4 opacity-40 hover:opacity-100 transition-opacity duration-300 cursor-pointer focus-visible">
                  ← switch protocol
              </button>
            </p>
            {error && <p className="mt-3 rounded-xl bg-red-500/25 p-3 text-sm" role="alert">{error}</p>}
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
          <motion.div key="step4" {...fadeUp} role="status" aria-label="Loading analysis">
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
    </>
  );
}

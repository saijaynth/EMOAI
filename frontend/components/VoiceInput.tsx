"use client";

import { useEffect, useRef, useState } from "react";
import { transcribeVoice } from "../lib/api";

type Props = { onSubmit: () => void; language: string };

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

type RecorderMetrics = {
  startTime: number;
  totalFrames: number;
  voicedFrames: number;
  rmsSum: number;
  rmsSquareSum: number;
  pitchValues: number[];
};

export function VoiceInput({ onSubmit, language }: Props) {
  const recorderRef = useRef<MediaRecorder | null>(null);
  const recognitionRef = useRef<any>(null);
  const chunksRef = useRef<Blob[]>([]);
  const transcriptRef = useRef("");
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const metricsRef = useRef<RecorderMetrics | null>(null);

  const [transcript, setTranscript] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState("");
  const [toneProfile, setToneProfile] = useState<VoiceToneProfile | null>(null);
  const [recordedSeconds, setRecordedSeconds] = useState(0);
  const [transcriptConfidence, setTranscriptConfidence] = useState<number | null>(null);
  const [transcriptionMessage, setTranscriptionMessage] = useState("Record and stop to generate voice-to-text.");

  const LANGUAGE_TO_SPEECH_CODE: Record<string, string> = {
    english: "en-US",
    hindi: "hi-IN",
    tamil: "ta-IN",
    telugu: "te-IN",
    spanish: "es-ES",
    french: "fr-FR",
    korean: "ko-KR",
    arabic: "ar-SA",
    kannada: "kn-IN",
    malayalam: "ml-IN",
    punjabi: "pa-IN",
  };

  const estimatePitchHz = (buffer: Float32Array, sampleRate: number): number | null => {
    const minHz = 70;
    const maxHz = 350;
    const minLag = Math.floor(sampleRate / maxHz);
    const maxLag = Math.floor(sampleRate / minHz);

    let bestCorrelation = 0;
    let bestLag = -1;
    for (let lag = minLag; lag <= maxLag; lag += 1) {
      let correlation = 0;
      for (let i = 0; i < buffer.length - lag; i += 1) {
        correlation += buffer[i] * buffer[i + lag];
      }
      if (correlation > bestCorrelation) {
        bestCorrelation = correlation;
        bestLag = lag;
      }
    }

    if (bestLag <= 0 || bestCorrelation < 0.01) {
      return null;
    }
    return sampleRate / bestLag;
  };

  const deriveEnergyLabel = (profile: Omit<VoiceToneProfile, "energy_label">): string => {
    if (profile.avg_volume >= 0.18 && profile.speaking_rate_wpm >= 145) {
      return "high-energy";
    }
    if (profile.pause_ratio >= 0.35 && profile.speaking_rate_wpm <= 95) {
      return "hesitant";
    }
    if ((profile.avg_pitch_hz ?? 0) >= 215 && profile.pitch_variability >= 60) {
      return "tense";
    }
    if (profile.avg_volume <= 0.08 && profile.speaking_rate_wpm <= 100) {
      return "low-energy";
    }
    if (profile.pitch_variability <= 28 && profile.volume_variability <= 0.03) {
      return "steady";
    }
    return "balanced";
  };

  const stopAudioCapture = () => {
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => null);
      audioContextRef.current = null;
    }
    analyserRef.current = null;
  };

  const finalizeToneProfile = (finalTranscript: string): VoiceToneProfile | null => {
    const metrics = metricsRef.current;
    if (!metrics || metrics.totalFrames <= 0) {
      return null;
    }

    const duration_ms = Math.max(200, Date.now() - metrics.startTime);
    // Use character-based CPM / 5 to normalize WPM across languages (agglutinative/logographic)
    const charCount = finalTranscript.trim().length;
    const equivalent_words = charCount / 5;
    const speaking_rate_wpm = charCount > 0 ? (equivalent_words / (duration_ms / 60000)) : 0;

    const avg_volume = metrics.rmsSum / metrics.totalFrames;
    const rmsVariance = Math.max(0, (metrics.rmsSquareSum / metrics.totalFrames) - (avg_volume * avg_volume));
    const volume_variability = Math.sqrt(rmsVariance);

    const pause_ratio = Math.min(1, Math.max(0, 1 - (metrics.voicedFrames / metrics.totalFrames)));

    const avg_pitch_hz = metrics.pitchValues.length > 0
      ? metrics.pitchValues.reduce((sum, p) => sum + p, 0) / metrics.pitchValues.length
      : null;

    let pitch_variability = 0;
    if (avg_pitch_hz !== null && metrics.pitchValues.length > 1) {
      const pitchVar = metrics.pitchValues.reduce((sum, p) => sum + ((p - avg_pitch_hz) ** 2), 0) / metrics.pitchValues.length;
      pitch_variability = Math.sqrt(Math.max(0, pitchVar));
    }

    const baseProfile = {
      duration_ms,
      speaking_rate_wpm: Number(speaking_rate_wpm.toFixed(2)),
      avg_volume: Number(avg_volume.toFixed(4)),
      volume_variability: Number(volume_variability.toFixed(4)),
      avg_pitch_hz: avg_pitch_hz === null ? null : Number(avg_pitch_hz.toFixed(2)),
      pitch_variability: Number(pitch_variability.toFixed(2)),
      pause_ratio: Number(pause_ratio.toFixed(4)),
    };

    return {
      ...baseProfile,
      energy_label: deriveEnergyLabel(baseProfile),
    };
  };

  const beginAudioCapture = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();

    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0.2;
    source.connect(analyser);

    streamRef.current = stream;
    audioContextRef.current = audioContext;
    analyserRef.current = analyser;
    metricsRef.current = {
      startTime: Date.now(),
      totalFrames: 0,
      voicedFrames: 0,
      rmsSum: 0,
      rmsSquareSum: 0,
      pitchValues: [],
    };

    const sampleBuffer = new Float32Array(analyser.fftSize);
    const loop = () => {
      const activeAnalyser = analyserRef.current;
      const activeMetrics = metricsRef.current;
      if (!activeAnalyser || !activeMetrics) {
        return;
      }

      activeAnalyser.getFloatTimeDomainData(sampleBuffer);

      let sumSquares = 0;
      for (let i = 0; i < sampleBuffer.length; i += 1) {
        sumSquares += sampleBuffer[i] * sampleBuffer[i];
      }
      const rms = Math.sqrt(sumSquares / sampleBuffer.length);
      const isVoiced = rms > 0.015;

      activeMetrics.totalFrames += 1;
      if (isVoiced) {
        activeMetrics.voicedFrames += 1;
      }
      activeMetrics.rmsSum += rms;
      activeMetrics.rmsSquareSum += rms * rms;

      if (isVoiced) {
        const pitch = estimatePitchHz(sampleBuffer, audioContext.sampleRate);
        if (pitch !== null && Number.isFinite(pitch)) {
          activeMetrics.pitchValues.push(pitch);
        }
      }

      // Draw waveform on canvas
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext("2d");
        if (ctx) {
          const width = canvas.width;
          const height = canvas.height;
          ctx.clearRect(0, 0, width, height);

          // Use a modern gradient color
          const gradient = ctx.createLinearGradient(0, 0, width, 0);
          gradient.addColorStop(0, "#4F46E5"); // Indigo-600
          gradient.addColorStop(1, "#EC4899"); // Indigo-500 -> Pink-500

          ctx.lineWidth = 3;
          ctx.strokeStyle = gradient;
          ctx.beginPath();

          const sliceWidth = width * 1.0 / sampleBuffer.length;
          let x = 0;

          for (let i = 0; i < sampleBuffer.length; i++) {
            const v = sampleBuffer[i] * 2.0; // amplify
            const y = (v * height / 2) + height / 2;

            if (i === 0) {
              ctx.moveTo(x, y);
            } else {
              ctx.lineTo(x, y);
            }
            x += sliceWidth;
          }

          ctx.lineTo(width, height / 2);
          ctx.stroke();
        }
      }

      animationFrameRef.current = requestAnimationFrame(loop);
    };

    animationFrameRef.current = requestAnimationFrame(loop);
  };

  const blobToBase64 = async (blob: Blob): Promise<string> => {
    const buffer = await blob.arrayBuffer();
    let binary = "";
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.length; i += 1) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  };

  const startRecording = async () => {
    if (!window.MediaRecorder) {
      setError("Audio recording is not supported in this browser. Try Chrome or Edge.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        recognition.interimResults = true;
        recognition.continuous = true;
        recognition.lang = LANGUAGE_TO_SPEECH_CODE[language.trim().toLowerCase()] ?? "en-US";
        
        let accumulatedFinalText = "";

        recognition.onresult = (event: any) => {
          let currentInterim = "";
          let finalInThisEvent = "";

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalInThisEvent += event.results[i][0].transcript + " ";
            } else {
              currentInterim += event.results[i][0].transcript + " ";
            }
          }

          if (finalInThisEvent) {
            accumulatedFinalText += finalInThisEvent;
          }

          const fullText = (accumulatedFinalText + currentInterim).trim();
          if (fullText) {
            setTranscript(fullText);
            transcriptRef.current = fullText;
          }
        };

        recognition.onerror = (e: any) => console.warn("Speech recognition error:", e.error);
        
        recognition.onend = () => {
          // Keep it running as long as the user hasn't pressed stop manually
          if (recorderRef.current && recorderRef.current.state === "recording") {
            try {
              recognition.start();
            } catch (e) {
              // Ignore failure to restart
            }
          }
        };

        try {
          recognition.start();
        } catch {
          // no-op, fallback is best effort
        }
      }

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType });
      recorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        stopAudioCapture();
        stream.getTracks().forEach((track) => track.stop());
        setIsRecording(false);

        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        if (blob.size === 0) {
          setError("No audio was captured. Please record again.");
          return;
        }

        try {
          setIsTranscribing(true);
          setTranscriptionMessage(`Transcribing ${language} voice input via AI...`);
          
          const audioBase64 = await blobToBase64(blob);

          // Force waiting briefly for native SpeechRecognition's final fallback to fire before pushing (just in case)
          await new Promise((resolve) => setTimeout(resolve, 300));
          const fallbackTranscript = transcriptRef.current.trim();
          
          // Send to backend which uses Deepgram AI as per skill instructions
          const result = await transcribeVoice(
             audioBase64,
             language,
             blob.type || "audio/webm",
             fallbackTranscript || undefined
          );

          setTranscript(result.transcript || "[No words recognized, assessing tone only]");
          setTranscriptConfidence(result.confidence);
          setTranscriptionMessage(`Voice-to-text ready in ${language}.`);
          
          const profile = finalizeToneProfile(result.transcript);
          if (profile) {
            setToneProfile(profile);
          }
        } catch (e) {
          setTranscriptionMessage(`Could not convert speech to text for ${language}.`);
          setError((e as Error).message || "Could not transcribe recording.");
        } finally {
          setIsTranscribing(false);
        }
      };

      await beginAudioCapture();
      setError("");
      setTranscript("");
      setToneProfile(null);
      setTranscriptConfidence(null);
      setTranscriptionMessage(`Listening for ${language} voice...`);
      setRecordedSeconds(0);
      transcriptRef.current = "";
      recorder.start();
      setIsRecording(true);
    } catch {
      setError("Could not access microphone. Please allow permission and retry.");
      stopAudioCapture();
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    recognitionRef.current?.stop?.();
    recorderRef.current?.stop();
    setIsRecording(false);
    stopAudioCapture();
  };

  const handleSubmit = () => {
    const clean = transcript.trim();
    const profile = toneProfile ?? finalizeToneProfile(clean);
    if (!clean && !profile) return;

    sessionStorage.setItem("emoai_voice", clean || " ");
    if (profile) {
      sessionStorage.setItem("emoai_voice_tone", JSON.stringify(profile));
    } else {
      sessionStorage.removeItem("emoai_voice_tone");
    }
    onSubmit();
  };

  useEffect(() => {
    if (!isRecording) {
      return;
    }
    const timer = window.setInterval(() => {
      setRecordedSeconds((prev) => prev + 1);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [isRecording]);

  const [isSupported, setIsSupported] = useState(true);
  useEffect(() => {
    setIsSupported(typeof window !== "undefined" && !!window.MediaRecorder && !!navigator.mediaDevices);
    return () => {
      recognitionRef.current?.stop?.();
      recorderRef.current?.stop();
      stopAudioCapture();
    };
  }, []);

  return (
    <div className="mt-8 space-y-6">
      {!isSupported && (
        <div className="glass bg-yellow-500/20 p-4 font-bold text-yellow-100 border-yellow-500/50">
          <p className="mb-2">Voice input is not supported in your browser.</p>
          <p className="text-sm">Please use Chrome, Edge, or Safari for voice features.</p>
        </div>
      )}
      {!isRecording && !isTranscribing && transcript === "" && !error && isSupported ? (
        <div className="flex justify-center py-10">
          <button
            type="button"
            onClick={startRecording}
            className="btn-vibrant w-32 h-32 rounded-full cursor-pointer flex flex-col items-center justify-center shadow-[0_0_40px_rgba(249,115,22,0.4)] animate-pulse hover:animate-none"
          >
            <span className="text-4xl mb-2">🎙️</span>
            <span className="text-sm font-bold uppercase tracking-wider">Tap to Record</span>
          </button>
        </div>
      ) : (
        <div className="glass p-8 relative overflow-hidden group">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {isRecording ? (
                <>
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                  </span>
                  <span className="text-red-500 font-bold uppercase tracking-widest text-sm">
                    Recording Voice + Tone... {String(Math.floor(recordedSeconds / 60)).padStart(2, "0")}:{String(recordedSeconds % 60).padStart(2, "0")}
                  </span>
                </>
              ) : isTranscribing ? (
                <span className="text-primary font-bold uppercase tracking-widest text-sm">Transcribing in {language}...</span>
              ) : transcript ? (
                <span className="text-primary font-bold uppercase tracking-widest text-sm">Transcript Ready</span>
              ) : (
                <span className="text-ink/50 font-bold uppercase tracking-widest text-sm">Tone Ready</span>
              )}
            </div>
            <div className="flex items-center gap-3">
              {!isRecording && (
                <button
                  type="button"
                  onClick={startRecording}
                  className="px-4 py-2 border-2 border-primary/50 text-primary text-xs font-bold uppercase tracking-widest hover:bg-primary hover:text-white transition-colors"
                >
                  Record Again
                </button>
              )}
              {isRecording && (
                <button
                  type="button"
                  onClick={stopRecording}
                  className="px-4 py-2 border-2 border-red-500/50 text-red-500 text-xs font-bold uppercase tracking-widest hover:bg-red-500 hover:text-white transition-colors"
                >
                  Stop
                </button>
              )}
            </div>
          </div>

          {isRecording && (
            <div className="mt-4 flex flex-col gap-2">
              <canvas
                ref={canvasRef}
                width={800}
                height={120}
                className="w-full h-24 rounded-lg bg-gray-900/10 border border-border"
              />
              <div className="rounded-lg border border-border bg-white/50 px-4 py-3">
                <p className="text-sm font-bold text-ink/70">Capturing vocal tone automatically: pace, pauses, energy, and pitch variation.</p>
              </div>
            </div>
          )}

          {!isRecording && toneProfile && (
            <div className="mt-5 rounded-lg border-2 border-border bg-white/60 p-4">
              <p className="font-bold uppercase tracking-widest text-xs text-ink/60 mb-2">Captured Voice Tone</p>
              <div className="grid grid-cols-2 gap-2 text-sm font-semibold text-ink/80">
                <p>Energy Label: {toneProfile.energy_label}</p>
                <p>Speaking Rate: {Math.round(toneProfile.speaking_rate_wpm)} wpm</p>
                <p>Avg Volume: {toneProfile.avg_volume.toFixed(3)}</p>
                <p>Pause Ratio: {(toneProfile.pause_ratio * 100).toFixed(0)}%</p>
                <p>Avg Pitch: {toneProfile.avg_pitch_hz ? `${Math.round(toneProfile.avg_pitch_hz)} Hz` : "N/A"}</p>
                <p>Pitch Variability: {toneProfile.pitch_variability.toFixed(1)}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {error && <p className="glass bg-red-500/20 p-4 font-bold text-red-100 border-red-500/50">{error}</p>}

      {/* Converted voice to text shown down here */}
      <div className="mt-6 flex flex-col gap-3">
        <label htmlFor="voice-transcript" className="font-display text-sm uppercase tracking-widest text-ink/60 ml-1">
          Voice To Text Output
        </label>
        <textarea
          id="voice-transcript"
          aria-label={`Voice transcript in ${language}`}
          readOnly
          value={transcript.trim() ? transcript : transcriptionMessage}
          placeholder="Recording will transcribe here automatically..."
          className="glass min-h-[140px] w-full p-6 text-lg font-body text-ink outline-none transition-all duration-300 placeholder:text-ink/40 focus:border-primary focus:ring-4 focus:ring-primary/20 resize-none leading-relaxed cursor-default"
        />
        {transcriptConfidence !== null && (
          <p className="text-xs font-bold uppercase tracking-wider text-ink/50 ml-1">
            Expected Accuracy: {Math.round(transcriptConfidence * 100)}%
          </p>
        )}
      </div>

      <div className="mt-6 flex items-center justify-end">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={(!transcript.trim() && !toneProfile) || isTranscribing}
          className="btn-vibrant px-8 py-4 text-base disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer w-full md:w-auto text-center"
        >
          Initialize Analysis
        </button>
      </div>
    </div>
  );
}

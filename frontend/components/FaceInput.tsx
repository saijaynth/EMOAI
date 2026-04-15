"use client";

import { useEffect, useRef, useState } from "react";

type Props = { onSubmit: () => void };

export function FaceInput({ onSubmit }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [expression, setExpression] = useState("neutral");
  const [intensity, setIntensity] = useState(0.6);
  const [error, setError] = useState("");

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (videoRef.current) {
        (videoRef.current as any).srcObject = stream;
      }
      setStreaming(true);
      setError("");
    } catch {
      setError("Unable to access webcam. Please allow camera permissions.");
    }
  };

  const stopCamera = () => {
    const stream = (videoRef.current as any)?.srcObject as MediaStream | undefined;
    stream?.getTracks().forEach((track) => track.stop());
    if (videoRef.current) {
      (videoRef.current as any).srcObject = null;
    }
    setStreaming(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const randomCapture = () => {
    const expressions = ["neutral", "smile", "frown", "surprised", "tense"];
    setExpression(expressions[Math.floor(Math.random() * expressions.length)]);
    setIntensity(Number((0.4 + Math.random() * 0.6).toFixed(2)));
  };

  const handleSubmit = () => {
    sessionStorage.setItem("emoai_face", JSON.stringify({ expression, intensity }));
    onSubmit();
  };

  return (
    <div className="mt-6 space-y-3">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={streaming ? stopCamera : startCamera}
          className="rounded-xl bg-white/15 px-4 py-2 font-semibold text-white hover:bg-white/25 transition"
        >
          {streaming ? "Stop Camera" : "Start Camera"}
        </button>
        <button
          type="button"
          onClick={randomCapture}
          className="rounded-xl bg-white/10 px-4 py-2 text-sm text-white/80 hover:bg-white/20 transition"
        >
          Capture (Simulated)
        </button>
      </div>

      <video ref={videoRef} autoPlay muted playsInline className="h-48 w-full rounded-2xl border border-white/20 bg-black/40 object-cover" />

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm text-white/70">
          Expression
          <select
            value={expression}
            onChange={(e) => setExpression(e.target.value)}
            className="mt-1 w-full rounded-xl border border-white/20 bg-white/10 p-2"
          >
            <option value="neutral">Neutral</option>
            <option value="smile">Smile</option>
            <option value="frown">Frown</option>
            <option value="surprised">Surprised</option>
            <option value="tense">Tense</option>
          </select>
        </label>

        <label className="text-sm text-white/70">
          Intensity: {intensity.toFixed(2)}
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={intensity}
            onChange={(e) => setIntensity(Number(e.target.value))}
            className="mt-2 w-full accent-coral"
          />
        </label>
      </div>

      {error && <p className="rounded-xl bg-red-500/25 p-3 text-sm">{error}</p>}

      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleSubmit}
          className="rounded-xl bg-coral px-6 py-3 font-bold text-white hover:bg-coral/80 transition"
        >
          Analyze Face Mood →
        </button>
      </div>
    </div>
  );
}

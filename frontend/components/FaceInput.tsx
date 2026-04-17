"use client";

import { useEffect, useRef, useState } from "react";

type Props = { onSubmit: () => void };

export function FaceInput({ onSubmit }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setStreaming(true);
      setError("");
    } catch {
      setError("Unable to access webcam. Please allow camera permissions.");
    }
  };

  const stopCamera = () => {
    const stream = videoRef.current?.srcObject as MediaStream | undefined;
    stream?.getTracks().forEach((track) => track.stop());
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setStreaming(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const handleCaptureAndAnalyze = () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    setAnalyzing(true);
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    // Downscale for faster processing and to avoid payload size limits (5MB limit)
    const MAX_DIMENSION = 640;
    let width = video.videoWidth;
    let height = video.videoHeight;
    
    if (width > height && width > MAX_DIMENSION) {
        height *= MAX_DIMENSION / width;
        width = MAX_DIMENSION;
    } else if (height > MAX_DIMENSION) {
        width *= MAX_DIMENSION / height;
        height = MAX_DIMENSION;
    }

    canvas.width = width;
    canvas.height = height;
    
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageData = canvas.toDataURL("image/jpeg", 0.7); // Compress slightly
      
      // Store actual image data instead of mock expression
      sessionStorage.setItem("emoai_face", imageData);
      
      stopCamera();
      onSubmit();
    } else {
      setError("Failed to capture image. Please try again.");
      setAnalyzing(false);
    }
  };

  return (
    <div className="mt-8 space-y-6">
      <div className="glass p-2 relative overflow-hidden group">
        <video 
          ref={videoRef} 
          autoPlay 
          muted 
          playsInline 
          className="aspect-video w-full rounded-lg bg-black object-cover" 
        />
        <canvas ref={canvasRef} className="hidden" />
        
        {!streaming && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm rounded-lg">
            <button
              type="button"
              onClick={startCamera}
              className="btn-vibrant px-8 py-4 text-lg cursor-pointer flex items-center gap-3"
            >
              <span>📷</span> Start Camera
            </button>
          </div>
        )}
      </div>

      {error && <p className="glass bg-red-500/20 p-4 font-bold text-red-100 border-red-500/50">{error}</p>}

      {streaming && (
        <div className="flex gap-4 items-center justify-between animate-fade-in">
          <button
            type="button"
            onClick={stopCamera}
            className="px-6 py-3 cursor-pointer text-white/70 hover:text-white transition-colors underline underline-offset-4"
          >
            Stop Camera
          </button>
          
          <button
            type="button"
            onClick={handleCaptureAndAnalyze}
            disabled={analyzing}
            className="btn-vibrant px-8 py-4 text-lg cursor-pointer flex items-center gap-3 disabled:opacity-50"
          >
            {analyzing ? "Processing Context..." : "Analyze Expression →"}
          </button>
        </div>
      )}
    </div>
  );
}

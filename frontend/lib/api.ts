const getApiBaseUrl = (): string => {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  
  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "https:" : "http:";
    return `${protocol}//${window.location.hostname}:8000`;
  }
  
  return "http://localhost:8000"; // Default to localhost:8000, easy to proxy in production
};

export const apiBase = getApiBaseUrl();

export type MoodLabel = 
  | "happy" | "sad" | "angry" | "calm" | "anxious" | "focused" | "excited" | "neutral"
  | "romantic" | "nostalgic" | "confident" | "dreamy" | "triumphant" | "chill" | "hype"
  | "melancholic" | "hopeful" | "frustrated" | "bored";
export type Method = "text" | "quiz" | "voice" | "face";

export type MethodScore = {
  method: Method;
  mood: MoodLabel;
  confidence: number;
};

export type MoodDetectionResponse = {
  mood: MoodLabel;
  confidence: number;
  method_scores: MethodScore[];
  tone_emotion?: string;
  text_emotion?: string;
};

export type VoiceToneProfile = {
  duration_ms: number;
  speaking_rate_wpm: number;
  avg_volume: number;
  volume_variability: number;
  avg_pitch_hz: number | null;
  pitch_variability: number;
  pause_ratio: number;
  energy_label: string;
};

export type VoiceTranscriptionResponse = {
  transcript: string;
  language: string;
  confidence: number;
};

export type SongItem = {
  id: string;
  title: string;
  artist: string;
  language: string;
  mood_tags: MoodLabel[];
  energy: number;
};

export type UserIdentity = {
  user_id: string;
  username: string;
};

export type SessionRecord = {
  session_id: string;
  user_id: string;
  mood: MoodLabel;
  language: string;
  context: string;
  method: Method;
  song_ids: string[];
  created_at: string;
};

export async function fetchLanguages(): Promise<string[]> {
  const res = await fetch(`${apiBase}/languages`);
  if (!res.ok) throw new Error("Failed to fetch languages");
  const data = await res.json();
  return data.languages;
}

export async function registerGuest(guestName: string): Promise<UserIdentity> {
  const res = await fetch(`${apiBase}/users/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: guestName }),
  });
  if (!res.ok) throw new Error("Failed to register guest user");
  return await res.json();
}

export async function detectTextMood(text: string, language: string): Promise<MoodDetectionResponse> {
  const res = await fetch(`${apiBase}/mood/detect/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  if (!res.ok) throw new Error("Mood detection failed");
  return await res.json();
}

export async function detectVoiceMood(
  transcript: string,
  language: string,
  toneProfile?: VoiceToneProfile,
): Promise<MoodDetectionResponse> {
  const res = await fetch(`${apiBase}/mood/detect/voice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript, language, tone_profile: toneProfile }),
  });
  if (!res.ok) throw new Error("Voice mood detection failed");
  return await res.json();
}

export async function transcribeVoice(
  audioBase64: string,
  language: string,
  mimeType: string,
  fallbackTranscript?: string
): Promise<VoiceTranscriptionResponse> {
  const res = await fetch(`${apiBase}/voice/transcribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      audio_base64: audioBase64,
      language,
      mime_type: mimeType,
      fallback_transcript: fallbackTranscript ?? null,
    }),
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    if (payload?.detail && Array.isArray(payload.detail)) {
      throw new Error(payload.detail.map((d: any) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join(", "));
    }
    throw new Error(
      payload?.detail?.message ?? 
      (typeof payload?.detail === "string" ? payload.detail : "Voice transcription failed. Please try again.")
    );
  }
  return await res.json();
}

export async function detectFaceMood(image_data: string, language: string): Promise<MoodDetectionResponse> {
  const res = await fetch(`${apiBase}/mood/detect/face`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_data, language }),
  });
  if (!res.ok) throw new Error("Face mood detection failed");
  return await res.json();
}

export async function getRecommendations(
  mood: string,
  language: string,
  context: string,
  confidence: number,
  toneEmotion?: string,
  textEmotion?: string
): Promise<SongItem[]> {
  const url = new URL(`${apiBase}/recommendations`);
  url.searchParams.append("mood", mood);
  url.searchParams.append("language", language);
  url.searchParams.append("context", context);
  url.searchParams.append("confidence", confidence.toString());
  if (toneEmotion) url.searchParams.append("tone_emotion", toneEmotion);
  if (textEmotion) url.searchParams.append("text_emotion", textEmotion);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Recommendations failed");
  const data = await res.json();
  return data.recommendations;
}

export async function saveSession(user_id: string, mood: string, language: string, context: string, method: string, song_ids: string[]): Promise<SessionRecord | null> {
  const res = await fetch(`${apiBase}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, mood, language, context, method, song_ids }),
  });
  if (!res.ok) return null;
  return await res.json();
}

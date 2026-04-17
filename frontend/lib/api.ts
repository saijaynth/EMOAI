export const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type MoodLabel = "happy" | "sad" | "angry" | "calm" | "anxious" | "focused" | "excited" | "neutral";
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

export async function detectVoiceMood(transcript: string, language: string): Promise<MoodDetectionResponse> {
  const res = await fetch(`${apiBase}/mood/detect/voice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript, language }),
  });
  if (!res.ok) throw new Error("Voice mood detection failed");
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

export async function getRecommendations(mood: string, language: string, context: string, confidence: number): Promise<SongItem[]> {
  const res = await fetch(
    `${apiBase}/recommendations?mood=${encodeURIComponent(mood)}&language=${encodeURIComponent(language)}&context=${encodeURIComponent(context)}&confidence=${confidence}`
  );
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

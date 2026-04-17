import { useState, useEffect } from "react";
import { 
  fetchLanguages, registerGuest, detectTextMood, 
  detectVoiceMood, detectFaceMood, getRecommendations, 
  saveSession, MoodLabel, MoodDetectionResponse, 
  SongItem, UserIdentity, Method 
} from "../lib/api";

const CONTEXTS = ["general", "study", "workout", "relax", "sleep", "party"] as const;

export function useMoodAnalysis() {
  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [languages, setLanguages] = useState<string[]>([]);
  const [language, setLanguage] = useState("");
  const [context, setContext] = useState<(typeof CONTEXTS)[number]>("general");
  const [method, setMethod] = useState<Method>("text");
  const [moodResult, setMoodResult] = useState<MoodDetectionResponse | null>(null);
  const [songs, setSongs] = useState<SongItem[]>([]);
  const [error, setError] = useState("");
  const [user, setUser] = useState<UserIdentity | null>(null);

  useEffect(() => {
    fetchLanguages()
      .then((langs) => {
        setLanguages(langs);
        setLanguage(langs[0] ?? "English");
      })
      .catch(() => setError("Could not load languages."));

    const existingUserId = localStorage.getItem("emoai_user_id");
    const existingUsername = localStorage.getItem("emoai_username");
    if (existingUserId && existingUsername) {
      setUser({ user_id: existingUserId, username: existingUsername });
      return;
    }

    const guestName = `guest_${Math.floor(1000 + Math.random() * 9000)}`;
    registerGuest(guestName)
      .then((u) => {
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
      let detected: MoodDetectionResponse;

      if (quizMood) {
        detected = { 
          mood: quizMood, 
          confidence: 0.82, 
          method_scores: [{ method: "quiz", mood: quizMood, confidence: 0.82 }] 
        };
      } else if (method === "text") {
        const text = sessionStorage.getItem("emoai_text") ?? "";
        if (!text) throw new Error("Text input was empty or invalid.");
        detected = await detectTextMood(text, language);
      } else if (method === "voice") {
        const transcript = sessionStorage.getItem("emoai_voice") ?? "";
        if (!transcript) throw new Error("Voice input was empty or invalid.");
        detected = await detectVoiceMood(transcript, language);
      } else {
        const image_data = sessionStorage.getItem("emoai_face") ?? "";
        if (!image_data) throw new Error("Face image data was empty or invalid.");
        detected = await detectFaceMood(image_data, language);
      }

      const recommendations = await getRecommendations(detected.mood, language, context, detected.confidence);

      setMoodResult(detected);
      setSongs(recommendations);

      if (user) {
        await saveSession(
          user.user_id,
          detected.mood,
          language,
          context,
          method,
          recommendations.map((song) => song.id)
        );
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

  return {
    state: { step, languages, language, context, method, moodResult, songs, error, user },
    actions: { setStep, setLanguage, setContext, setMethod, runAnalysis, reset },
    CONTEXTS,
  };
}

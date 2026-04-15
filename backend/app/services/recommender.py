import json
from pathlib import Path

from app.schemas.mood import MethodScore, MoodLabel, SongItem


class RecommenderService:
    mood_energy_targets: dict[MoodLabel, float] = {
        "happy": 0.78,
        "sad": 0.28,
        "angry": 0.85,
        "calm": 0.32,
        "anxious": 0.38,
        "focused": 0.62,
        "excited": 0.82,
        "neutral": 0.5,
    }

    context_energy_offsets: dict[str, float] = {
        "general": 0.0,
        "study": -0.15,
        "workout": 0.22,
        "relax": -0.2,
        "sleep": -0.3,
        "party": 0.28,
    }

    def __init__(self) -> None:
        self.catalog: list[SongItem] = []

    def load_catalog(self) -> None:
        data_path = Path(__file__).resolve().parents[1] / "data" / "universal_songs.json"
        with data_path.open("r", encoding="utf-8") as file:
            raw = json.load(file)
        self.catalog = [SongItem(**item) for item in raw]

    def detect_text_mood(self, text: str) -> tuple[MoodLabel, float]:
        lower = text.lower()
        keyword_map: dict[MoodLabel, list[str]] = {
            "happy": ["happy", "joy", "great", "awesome", "good"],
            "sad": ["sad", "down", "upset", "cry", "hurt"],
            "angry": ["angry", "mad", "frustrated", "rage"],
            "calm": ["calm", "peaceful", "relaxed", "soft"],
            "anxious": ["anxious", "worried", "stress", "nervous"],
            "focused": ["focus", "study", "work", "concentrate"],
            "excited": ["excited", "hyped", "energetic", "pumped"],
            "neutral": [],
        }

        best_mood: MoodLabel = "neutral"
        best_score = 0
        for mood, keywords in keyword_map.items():
            score = sum(1 for k in keywords if k in lower)
            if score > best_score:
                best_score = score
                best_mood = mood

        confidence = min(0.95, 0.55 + (best_score * 0.1)) if best_score > 0 else 0.51
        return best_mood, confidence

    def detect_voice_mood(self, transcript: str) -> tuple[MoodLabel, float]:
        mood, confidence = self.detect_text_mood(transcript)
        voice_adjustment = {
            "happy": 0.03,
            "sad": 0.02,
            "angry": 0.05,
            "calm": 0.04,
            "anxious": 0.05,
            "focused": 0.04,
            "excited": 0.05,
            "neutral": 0.0,
        }
        return mood, min(0.97, confidence + voice_adjustment.get(mood, 0.0))

    def detect_face_mood(self, expression: str, intensity: float) -> tuple[MoodLabel, float]:
        expression_map: dict[str, MoodLabel] = {
            "smile": "happy",
            "frown": "sad",
            "neutral": "neutral",
            "surprised": "excited",
            "tense": "anxious",
        }
        mood = expression_map.get(expression, "neutral")
        base_confidence = 0.56 + (intensity * 0.28)
        if mood == "neutral":
            base_confidence = 0.52 + (intensity * 0.08)
        return mood, min(0.96, base_confidence)

    def fuse_scores(self, scores: list[MethodScore]) -> tuple[MoodLabel, float]:
        if not scores:
            return "neutral", 0.5

        weighted: dict[MoodLabel, float] = {}
        for score in scores:
            weighted[score.mood] = weighted.get(score.mood, 0.0) + score.confidence

        final_mood = max(weighted, key=weighted.get)
        confidence = min(0.99, weighted[final_mood] / max(1.0, sum(s.confidence for s in scores)))
        return final_mood, confidence

    def recommend(self, mood: MoodLabel, language: str, context: str = "general", limit: int = 10) -> list[SongItem]:
        normalized_language = language.strip().lower()
        normalized_context = context.strip().lower()
        language_matches = [song for song in self.catalog if song.language.lower() == normalized_language]

        # If the selected language has no matches, fall back to the full catalog but keep the same ranking rules.
        working_set = language_matches if language_matches else self.catalog
        target_energy = self.mood_energy_targets.get(mood, 0.5)
        context_offset = self.context_energy_offsets.get(normalized_context, 0.0)
        target_energy = min(1.0, max(0.0, target_energy + context_offset))

        def score(song: SongItem) -> float:
            mood_match = 2.0 if mood in song.mood_tags else 0.35
            language_match = 0.6 if song.language.lower() == normalized_language else 0.0
            energy_fit = 1.0 - abs(song.energy - target_energy)
            neutral_boost = 0.2 if mood == "neutral" and "calm" in song.mood_tags else 0.0
            popularity = 0.15
            return mood_match + language_match + energy_fit + neutral_boost + popularity

        ranked = sorted(working_set, key=score, reverse=True)
        return ranked[:limit]


recommender_service = RecommenderService()

import sys
import re

with open("app/services/recommender.py", "r", encoding="utf-8") as f:
    text = f.read()

centroids_block = """VOICE_CENTROIDS: dict[MoodLabel, tuple[float, float, float, float]] = {
    "happy":       (0.15, 140, 45, 0.20),
    "sad":         (0.06, 90,  20, 0.40),
    "angry":       (0.22, 160, 60, 0.15),
    "calm":        (0.08, 110, 25, 0.30),
    "anxious":     (0.12, 165, 70, 0.25),
    "focused":     (0.10, 130, 30, 0.18),
    "excited":     (0.20, 170, 65, 0.15),
    "neutral":     (0.10, 120, 35, 0.25),
    "romantic":    (0.09, 105, 30, 0.35),
    "nostalgic":   (0.07, 95,  25, 0.38),
    "confident":   (0.16, 140, 40, 0.18),
    "dreamy":      (0.06, 85,  20, 0.45),
    "triumphant":  (0.24, 150, 55, 0.12),
    "chill":       (0.09, 110, 25, 0.30),
    "hype":        (0.25, 180, 70, 0.10),
    "melancholic": (0.05, 85,  15, 0.42),
    "hopeful":     (0.14, 135, 45, 0.22),
    "frustrated":  (0.18, 155, 55, 0.20),
    "bored":       (0.07, 100, 15, 0.35),
}
"""

if "VOICE_CENTROIDS" not in text:
    text = text.replace("CONTEXT_ENERGY_OFFSETS: dict[str, float] =", centroids_block + "\nCONTEXT_ENERGY_OFFSETS: dict[str, float] =")


pattern = r"def _voice_tone_fallback\(tone_profile: dict \| None, language: str = \"English\"\) -> tuple\[MoodLabel, float\] \| None:(.*?)return None"

new_func = """def _voice_tone_fallback(tone_profile: dict | None, language: str = "English") -> tuple[MoodLabel, float] | None:
    \"""
    Infer mood from acoustic features when available.
    Uses K-Nearest Neighbor Euclidean Centroid mapping across all metrics for full coverage against 19 emotions.
    \"""
    if not tone_profile:
        return None

    avg_volume = float(tone_profile.get("avg_volume", 0.0) or 0.0)
    pitch_var = float(tone_profile.get("pitch_variability", 0.0) or 0.0)
    speaking_rate = float(tone_profile.get("speaking_rate_wpm", 0.0) or 0.0)
    pause_ratio = float(tone_profile.get("pause_ratio", 0.0) or 0.0)

    lang_lower = language.lower()
    
    # ML Domain Adjustment for Spoken Languages
    rate_mult, pitch_mult, vol_mult = 1.0, 1.0, 1.0
    if lang_lower in ["telugu", "hindi", "tamil", "kannada", "malayalam"]:
        rate_mult = 0.85
        pitch_mult = 1.15
        vol_mult = 1.10
    elif lang_lower in ["spanish", "italian", "japanese"]:
        rate_mult = 0.75
    elif lang_lower in ["french", "german"]:
        pitch_mult = 1.10

    n_rate = speaking_rate * rate_mult
    n_pitch_var = pitch_var * pitch_mult
    n_vol = avg_volume * vol_mult

    best_mood = "neutral"
    min_dist = float('inf')

    # Continuous multidimensional space distance mapped to 19 clusters
    for cluster_mood, (c_vol, c_rate, c_pitch, c_pause) in VOICE_CENTROIDS.items():
        # Scale variables uniformly (Volume: ~0.3, Rate: ~200 WPM, Pitch Var: ~100 Hz, Pause: ~0.5)
        # to ensure Euclidean math treats each metric as a uniform ~[0-1] scale dimension
        norm_vol = min(1.0, n_vol / 0.3)
        norm_rate = min(1.0, n_rate / 200.0)
        norm_pitch_var = min(1.0, n_pitch_var / 100.0)
        norm_pause = min(1.0, pause_ratio / 0.5)
        
        nc_vol = min(1.0, c_vol / 0.3)
        nc_rate = min(1.0, c_rate / 200.0)
        nc_pitch = min(1.0, c_pitch / 100.0)
        nc_pause = min(1.0, c_pause / 0.5)
        
        dist = ((norm_vol - nc_vol)**2 + 
                (norm_rate - nc_rate)**2 + 
                (norm_pitch_var - nc_pitch)**2 + 
                (norm_pause - nc_pause)**2) ** 0.5
                
        if dist < min_dist:
            min_dist = dist
            best_mood = cluster_mood
            
    # Convert n-dimensional distance (max ~2.0) to a scaled confidence score
    confidence = max(0.40, min(0.99, 1.0 - (min_dist / 1.5)))
    return best_mood, round(confidence, 2)"""

text = re.sub(pattern, new_func, text, flags=re.DOTALL)

with open("app/services/recommender.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Done ML rewrite!")

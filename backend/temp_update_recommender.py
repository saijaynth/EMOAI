import sys

with open("app/services/recommender.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update MOOD_ENERGY_TARGETS
old_energy = """MOOD_ENERGY_TARGETS: dict[MoodLabel, float] = {
    "happy":   0.78,
    "sad":     0.28,
    "angry":   0.85,
    "calm":    0.32,
    "anxious": 0.38,
    "focused": 0.62,
    "excited": 0.82,
    "neutral": 0.50,
}"""

new_energy = """MOOD_ENERGY_TARGETS: dict[MoodLabel, float] = {
    "happy":   0.78,
    "sad":     0.28,
    "angry":   0.85,
    "calm":    0.32,
    "anxious": 0.38,
    "focused": 0.62,
    "excited": 0.82,
    "neutral": 0.50,
    "romantic": 0.40,
    "nostalgic": 0.35,
    "confident": 0.70,
    "dreamy": 0.25,
    "triumphant": 0.88,
    "chill": 0.45,
    "hype": 0.90,
    "melancholic": 0.30,
    "hopeful": 0.65,
    "frustrated": 0.75,
    "bored": 0.40,
}"""

# 2. Update KEYWORD_MAP
old_keyword_end = """    "neutral": [
        "fine", "okay", "ok", "whatever", "normal", "usual", "alright",
        "so-so", "meh", "nothing special", "just", "regular", "average",
    ],
}"""

new_keyword_end = """    "neutral": [
        "fine", "okay", "ok", "whatever", "normal", "usual", "alright",
        "so-so", "meh", "nothing special", "just", "regular", "average",
    ],
    "romantic": [
        "love", "romantic", "affection", "passion", "adore", "crush", "sweet", "darling", "heart", "intimate"
    ],
    "nostalgic": [
        "nostalgic", "memories", "past", "remember", "throwback", "miss", "old times", "childhood", "reminisce"
    ],
    "confident": [
        "confident", "sure", "strong", "unbeatable", "ready", "bold", "fearless", "unstoppable", "proud", "capable"
    ],
    "dreamy": [
        "dreamy", "floaty", "surreal", "sleepy", "wander", "space", "lost in thought", "ethereal", "cloud", "magic"
    ],
    "triumphant": [
        "triumph", "victory", "won", "succeed", "champion", "glory", "conquer", "hero", "overcome", "success"
    ],
    "chill": [
        "chill", "vibe", "laid back", "breezy", "smooth", "groove", "cruising", "lounging", "unwind", "kick back"
    ],
    "hype": [
        "hype", "lit", "fire", "crazy", "wild", "turnt", "banger", "rager", "energy", "pop off"
    ],
    "melancholic": [
        "melancholy", "somber", "pensive", "wistful", "reflective", "sigh", "mournful", "sorrowful", "bleak"
    ],
    "hopeful": [
        "hope", "optimistic", "looking forward", "bright", "promising", "believe", "faith", "wish", "dream"
    ],
    "frustrated": [
        "frustrated", "annoy", "bothered", "stuck", "fed up", "exasperated", "irritated", "impatient", "aghast"
    ],
    "bored": [
        "bored", "dull", "tedious", "yawn", "uninterested", "tiresome", "monotonous", "lame", "drag"
    ],
}"""

print(text.find(old_energy))
print(text.find(old_keyword_end))

text = text.replace(old_energy, new_energy)
text = text.replace(old_keyword_end, new_keyword_end)

with open("app/services/recommender.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Done updating python mappings in recommender.")

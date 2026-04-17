import os

path = "backend/app/services/recommender.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# I want to replace the `def score(song) -> float:` section inside `recommend()`.

old_score_block = """\
        # --- ML Ranked Scoring (YouTube Two-Tower Collaborative Style) ---
        def score(song) -> float:
            mood_match = 2.5 if mood in song.mood_tags else 0.3

            energy_fit = 1.0 - abs(song.energy - target_energy)
            lang_bonus = 0.5 if song.language.lower() == normalized_language else 0.0

            pop_score = 0.1
            if song.playcount > 0:
                pop_score = min(1.0, song.playcount / 5_000_000) * 0.8
            elif song.popularity is not None:
                pop_score = (song.popularity / 100.0) * 0.7

            # Direct Collaborative History Boost
            fb_boost = self._feedback_boosts.get(song.id, 0.0)

            # Collaborative Genre Drift: If we don't have direct feedback, check if they liked similar songs.
            collab_bonus = 0.0
            if fb_boost == 0.0 and len(liked_songs) > 0:
                # Check genre overlap
                for l_song in liked_songs:
                    if set(l_song.mood_tags).intersection(set(song.mood_tags)):
                        collab_bonus += 0.1

            context_bonus = 0.0
            if normalized_context == "study" and mood in ("focused", "calm"): context_bonus = 0.3
            elif normalized_context == "workout" and mood in ("angry", "excited"): context_bonus = 0.3
            elif normalized_context == "sleep" and mood in ("calm", "sad"): context_bonus = 0.3
            elif normalized_context == "party" and mood in ("happy", "excited"): context_bonus = 0.3

            neutral_bonus = 0.2 if mood == "neutral" and any(t in song.mood_tags for t in ("calm", "happy")) else 0.0

            return mood_match + energy_fit + lang_bonus + pop_score + fb_boost + collab_bonus + context_bonus + neutral_bonus
"""

new_score_block = """\
        # --- Jittered Multi-Tiered Ranking (Darwin Evolution Applied) ---
        import random
        # Opposing moods for strict penalization
        opposing_moods = {
            "happy": ["sad", "angry"],
            "sad": ["happy", "excited", "party"],
            "angry": ["calm", "focused", "relax", "happy"],
            "calm": ["angry", "excited"],
            "excited": ["sad", "calm", "sleep"],
            "focused": ["angry", "party"],
            "neutral": ["angry", "excited", "sad"]
        }

        def score(song) -> float:
            # 1. Buff Exact Mood Match heavily so wrong tags NEVER outrank correct ones
            mood_match = 5.0 if mood in song.mood_tags else 0.0
            
            # 2. Strict Penalization for entirely Opposite Moods
            penalty = 0.0
            song_tags_set = set(song.mood_tags)
            if any(opp in song_tags_set for opp in opposing_moods.get(mood, [])):
                penalty = -4.0  # Decimates any score advantages from popularity or energy

            # 3. Energy fit still matters for ranking among matching moods
            energy_fit = 1.2 - abs(song.energy - target_energy)
            
            lang_bonus = 1.0 if song.language.lower() == normalized_language else 0.0

            pop_score = 0.0
            if song.playcount > 0:
                pop_score = min(1.0, song.playcount / 5_000_000) * 0.8
            elif song.popularity is not None:
                pop_score = (song.popularity / 100.0) * 0.7

            fb_boost = self._feedback_boosts.get(song.id, 0.0)

            collab_bonus = 0.0
            if fb_boost == 0.0 and len(liked_songs) > 0:
                for l_song in liked_songs:
                    if set(l_song.mood_tags).intersection(song_tags_set):
                        collab_bonus += 0.2

            context_bonus = 0.0
            if normalized_context == "study" and mood in ("focused", "calm"): context_bonus = 0.5
            elif normalized_context == "workout" and mood in ("angry", "excited"): context_bonus = 0.5
            elif normalized_context == "sleep" and mood in ("calm", "sad"): context_bonus = 0.5
            elif normalized_context == "party" and mood in ("happy", "excited"): context_bonus = 0.5

            neutral_bonus = 0.5 if mood == "neutral" and any(t in song_tags_set for t in ("calm", "happy")) else 0.0
            
            # 4. Stochastic serendipity drift (Randomness)
            # Adds between 0.0 to 1.5 extra points, allowing rotation of equal-match songs on reload
            serendipity_drift = random.uniform(0.0, 1.5)

            # 5. Fallback tiny partial match if there is tag overlap
            partial_match = 0.0
            if mood_match == 0.0 and tone_emotion and tone_emotion in song_tags_set: partial_match += 1.5
            if mood_match == 0.0 and text_emotion and text_emotion in song_tags_set: partial_match += 1.0

            return mood_match + partial_match + energy_fit + lang_bonus + pop_score + fb_boost + collab_bonus + context_bonus + neutral_bonus + serendipity_drift + penalty
"""

if old_score_block in code:
    print("Found old score block. Replacing.")
    code = code.replace(old_score_block, new_score_block)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
else:
    print("WARNING: Could not find exact old score block. Looking for loose block...")
    # Let me use regex or something to just replace it
    import re
    match = re.search(r"        # --- ML Ranked Scoring.*?return mood_match \+ .*?\n", code, re.DOTALL)
    if match:
        print("Found with regex, replacing!")
        code = code[:match.start()] + new_score_block + code[match.end():]
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
    else:
        print("Regex failed. Needs manual fix.")
        

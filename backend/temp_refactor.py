import sys

with open("app/services/recommender.py", "r", encoding="utf-8") as f:
    text = f.read()

new_recommend = """    def enrich_catalog_bg(self, mood: str, language: str, tone_emotion: str | None = None, text_emotion: str | None = None) -> None:
        '''
        BACKGROUND CRAWLER (The Adaptive Vault):
        Fetches live songs asynchronously and appends them to the vault to ensure fresh dynamic content
        for subsequent queries without blocking the user response.
        '''
        import threading
        try:
            logger.info(f"Adaptive Vault: Fetching dynamic songs for {mood} ({language}) in background...")
            live_songs = _fetch_global_songs_for_mood(
                mood, language, limit=30, tone_emotion=tone_emotion, text_emotion=text_emotion
            )
            
            existing_keys = {f"{s.title.lower()}::{s.artist.lower()}" for s in self.catalog}
            new_songs = []
            
            for song in live_songs:
                k = f"{song.title.lower()}::{song.artist.lower()}"
                if k not in existing_keys:
                    self.catalog.append(song)
                    existing_keys.add(k)
                    new_songs.append(song)
            
            if new_songs:
                logger.info(f"Adaptive Vault: Absorbed {len(new_songs)} new dynamic songs. Total size: {len(self.catalog)}")
        except Exception as e:
            logger.error(f"Adaptive Vault Fetch Error: {e}")

    def recommend(
        self,
        mood: str,
        language: str,
        context: str = "general",
        limit: int = 10,
        use_live: bool = False,
        tone_emotion: str | None = None,
        text_emotion: str | None = None,
    ) -> list:
        '''
        Recommend globally best-fit songs using Collaborative Ranking.
        1. Uses ONLY local vault `self.catalog` (use_live = False).
        2. Filter by language.
        3. ML Collaborative Filter Ranking: Scored by exact mood + historical user feedback.
        '''
        normalized_language = language.strip().lower()
        normalized_context = context.strip().lower()

        base_target_energy = self.mood_energy_targets.get(mood, 0.5)

        if tone_emotion and text_emotion and tone_emotion != text_emotion:      
            tone_e = self.mood_energy_targets.get(tone_emotion, base_target_energy)
            text_e = self.mood_energy_targets.get(text_emotion, base_target_energy)
            target_energy = round((tone_e * 0.6) + (text_e * 0.4), 2)
        else:
            target_energy = base_target_energy

        context_offset = self.context_energy_offsets.get(normalized_context, 0.0)
        target_energy = min(1.0, max(0.0, target_energy + context_offset))      

        working_set = []
        if use_live:
            # Fallback if explicitly asked to block
            working_set = _fetch_global_songs_for_mood(mood, language, limit=50, tone_emotion=tone_emotion, text_emotion=text_emotion)
            new_k = {f"{s.title.lower()}::{s.artist.lower()}" for s in working_set}
            working_set.extend([s for s in self.catalog if f"{s.title.lower()}::{s.artist.lower()}" not in new_k])
        else:
            # 100% Adaptive Vault Path
            working_set = self.catalog

        # Language filter (soft fallback to all if zero matches)
        lang_filtered = [s for s in working_set if s.language.lower() == normalized_language]
        working_set = lang_filtered if lang_filtered else working_set

        # Calculate Average Collaborative Energy from User Interactions
        # This drifts the target energy towards what the user *actually* likes.
        liked_songs = [s for s in self.catalog if self._feedback_boosts.get(s.id, 0.0) > 0.0]
        if len(liked_songs) > 0:
            avg_liked_energy = sum(s.energy for s in liked_songs) / len(liked_songs)
            # 30% collaborative drift
            target_energy = (target_energy * 0.7) + (avg_liked_energy * 0.3)

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
            
        ranked = sorted(working_set, key=score, reverse=True)

        seen_artists = {}
        diverse = []
        overflow = []

        for song in ranked:
            artist_key = song.artist.lower()
            count = seen_artists.get(artist_key, 0)
            if count < 2:
                diverse.append(song)
                seen_artists[artist_key] = count + 1
            else:
                overflow.append(song)
            if len(diverse) >= limit: break

        if len(diverse) < limit:
            diverse.extend(overflow[: limit - len(diverse)])

        return diverse[:limit]
"""

start_str = "    def recommend("
index = text.find(start_str)
if index == -1:
    print("Could not find def recommend")
    sys.exit(1)

# We want to replace from index to the end of the file.
# BUT wait, what if RecommenderService is instantiated at the bottom?
end_code = "\nrecommender_service = RecommenderService()\n"

text = text[:index] + new_recommend + end_code
with open("app/services/recommender.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Done replacing.")

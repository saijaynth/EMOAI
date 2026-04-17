import sys

with open("app/api/routes.py", "r", encoding="utf-8") as f:
    text = f.read()

new_routes = """    if not recommender_service.catalog:
        recommender_service.load_catalog()

    # The Adaptive Vault Background Crawler
    background_tasks.add_task(
        recommender_service.enrich_catalog_bg,
        mood, language, tone_emotion, text_emotion
    )

    recommendations = recommender_service.recommend(
        mood=mood, language=language, context=context, limit=limit,
        use_live=False, # Use Adaptive Vault zero-latency local retrieval     
        tone_emotion=tone_emotion, text_emotion=text_emotion
    )"""

old_routes = """    if not recommender_service.catalog:
        # If catalog is somehow completely empty, we can't recommend without blocking.
        # But ordinarily we still shouldn't crash.
        recommender_service.load_catalog()

    recommendations = recommender_service.recommend(
        mood=mood, language=language, context=context, limit=limit,
        use_live=False, # Use Adaptive Vault zero-latency local retrieval     
        tone_emotion=tone_emotion, text_emotion=text_emotion
    )"""

text = text.replace(old_routes, new_routes)
with open("app/api/routes.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Done routes.")

import sys

with open("backend/app/services/recommender.py", "r", encoding="utf-8") as f:
    text = f.read()

old_ctx = """        context_hint = (
            "Context: This is a transcript from the user's voice recording. "
            "Consider spoken-language patterns, filler words (um, uh, like), "
            "sentence fragments, and the emotional energy implied by word choice. "
            "Spoken language often reveals mood more directly than written text."
        )"""
        
new_ctx = """        context_hint = (
            f"Context: This is a transcript from the user's voice recording in {language}. "
            "Consider spoken-language patterns, filler words (um, uh, like), "
            "sentence fragments, and the emotional energy implied by word choice. "
            "Spoken language often reveals mood more directly than written text."
        )"""

text = text.replace(old_ctx, new_ctx)
with open("backend/app/services/recommender.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Third patch done")

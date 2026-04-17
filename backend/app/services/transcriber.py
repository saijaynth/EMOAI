from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

LANGUAGE_HINTS: dict[str, str] = {
    "english": "English",
    "hindi": "Hindi",
    "tamil": "Tamil",
    "telugu": "Telugu",
    "spanish": "Spanish",
    "french": "French",
    "korean": "Korean",
    "arabic": "Arabic",
    "kannada": "Kannada",
    "malayalam": "Malayalam",
    "punjabi": "Punjabi",
}


class VoiceTranscriptionError(RuntimeError):
    pass


class VoiceTranscriberService:
    def _translate_text(self, text: str, language: str, api_key: str) -> tuple[str, float]:
        from google import genai
        from pydantic import BaseModel, Field as PField

        class TranscriptSchema(BaseModel):
            transcript: str
            confidence: float = PField(default=0.65, ge=0.0, le=1.0)

        lang_hint = LANGUAGE_HINTS.get(language.strip().lower(), language.strip() or "English")
        prompt = (
            "You are a translation engine for voice transcripts. "
            f"Translate the following user text into {lang_hint}. "
            f"Use natural {lang_hint} script and preserve meaning. "
            "Return only translated text."
        )

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, text],
            config={
                "response_mime_type": "application/json",
                "response_schema": TranscriptSchema,
                "temperature": 0.0,
            },
        )
        parsed: dict[str, Any] = json.loads(response.text)
        transcript = str(parsed.get("transcript", "")).strip()
        confidence = float(parsed.get("confidence", 0.65))
        if not transcript:
            return text, 0.5
        return transcript, max(0.0, min(1.0, confidence))

    def transcribe(self, audio_base64: str, language: str, mime_type: str, fallback_transcript: str | None = None) -> tuple[str, float]:
        deepgram_api_key = os.getenv("DEEPGRAM_API_KEY", "")
        gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        fallback_text = (fallback_transcript or "").strip()

        if ";base64," in audio_base64:
            _, encoded = audio_base64.split(";base64,", 1)
        else:
            encoded = audio_base64

        try:
            audio_bytes = base64.b64decode(encoded)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            logger.error("b64decode failed on %s... : %s", encoded[:50], exc)
            if fallback_text:
                return fallback_text, 0.45
            raise VoiceTranscriptionError(f"Invalid recorded audio payload: {str(exc)}") from exc

        lang_code = language.strip().lower()[:2]
        
        if deepgram_api_key:
            # Voice AI Agent Skill implementation (Deepgram Best-In-Class STT)
            import httpx
            
            try:
                response = httpx.post(
                    "https://api.deepgram.com/v1/listen",
                    headers={
                        "Authorization": f"Token {deepgram_api_key}",
                        "Content-Type": "audio/webm",
                    },
                    params={
                        "model": "nova-3",
                        "language": lang_code,
                        "smart_format": "true"
                    },
                    content=audio_bytes,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    transcript = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "").strip()
                    confidence = float(data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("confidence", 0.8))
                    
                    if transcript:
                        return transcript, confidence
                else:
                    logger.error(f"Deepgram failed with status {response.status_code}: {response.text}")
                    
            except Exception as e:
                logger.error(f"Deepgram request failed: {e}")

        # Fallback to Gemini if DEEPGRAM_API_KEY is not explicitly set, or if Deepgram request fails.
        if not gemini_api_key:
            if fallback_text:
                return fallback_text, 0.45
            raise VoiceTranscriptionError("DEEPGRAM_API_KEY or GEMINI_API_KEY missing to perform voice-to-text.")
            
        lang_hint = LANGUAGE_HINTS.get(language.strip().lower(), language.strip() or "English")
        prompt = (
            "You are a speech transcription and translation system. "
            "First detect the spoken language from audio. "
            f"Then output the final transcript translated into {lang_hint}. "
            f"Use natural {lang_hint} script. "
            "Return only user-spoken content as plain text."
        )

        try:
            from google import genai
            from pydantic import BaseModel, Field as PField

            class TranscriptSchema(BaseModel):
                transcript: str
                confidence: float = PField(default=0.7, ge=0.0, le=1.0)

            client = genai.Client(api_key=gemini_api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    prompt,
                    genai.types.Part.from_bytes(data=audio_bytes, mime_type=(mime_type or "audio/webm").split(";")[0].strip()),
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": TranscriptSchema,
                    "temperature": 0.0,
                },
            )
            parsed: dict[str, Any] = json.loads(response.text)
            transcript = str(parsed.get("transcript", "")).strip()
            confidence = float(parsed.get("confidence", 0.7))
            if not transcript:
                if fallback_text:
                    return fallback_text, 0.5
                raise VoiceTranscriptionError("No words detected in audio.")
            return transcript, max(0.0, min(1.0, confidence))
        except VoiceTranscriptionError:
            raise
        except Exception as exc:
            logger.warning("Generative AI transcription failed: %s", exc)
            if fallback_text:
                try:
                    return self._translate_text(fallback_text, language, gemini_api_key)
                except Exception:
                    return fallback_text, 0.5
            err_str = str(exc).lower()
            if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                raise VoiceTranscriptionError("Gemini AI transcription limit reached. Please set a DEEPGRAM_API_KEY for robust transcription.") from exc
            raise VoiceTranscriptionError("Generative AI transcription failed.") from exc


voice_transcriber_service = VoiceTranscriberService()

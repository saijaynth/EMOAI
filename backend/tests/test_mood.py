from fastapi.testclient import TestClient
from app.api import routes

def test_detect_text_mood_success(client: TestClient):
    payload = {"text": "I feel so happy today!", "language": "English"}
    response = client.post("/mood/detect/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mood"] == "happy"
    assert data["confidence"] > 0.5
    assert len(data["method_scores"]) == 1

def test_detect_text_mood_empty_text(client: TestClient):
    """TDD check for empty negative text ensuring validation fires"""
    payload = {"text": "", "language": "English"}
    response = client.post("/mood/detect/text", json=payload)
    assert response.status_code == 422

def test_detect_text_mood_missing_language(client: TestClient):
    """TDD check for missing required field"""
    payload = {"text": "I feel happy"}
    response = client.post("/mood/detect/text", json=payload)
    assert response.status_code == 422


def test_detect_face_mood_from_simulated_payload(client: TestClient):
    payload = {
        "image_data": '{"expression":"smile","intensity":0.8}',
        "language": "English",
    }
    response = client.post("/mood/detect/face", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mood"] == "happy"
    assert data["confidence"] >= 0.6


def test_detect_face_mood_requires_data_or_expression(client: TestClient):
    payload = {"language": "English"}
    response = client.post("/mood/detect/face", json=payload)
    assert response.status_code == 422


def test_transcribe_voice_success(client: TestClient, monkeypatch):
    def fake_transcribe(audio_base64: str, language: str, mime_type: str):
        assert language == "English"
        assert mime_type.startswith("audio/")
        return "I am feeling better now", 0.86

    monkeypatch.setattr(routes.voice_transcriber_service, "transcribe", fake_transcribe)
    payload = {
        "audio_base64": "dGVzdC1hdWRpby1ieXRlcw==",
        "language": "English",
        "mime_type": "audio/webm",
    }
    response = client.post("/voice/transcribe", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "I am feeling better now"
    assert data["confidence"] == 0.86


def test_transcribe_voice_failure(client: TestClient, monkeypatch):
    def fake_transcribe(audio_base64: str, language: str, mime_type: str):
        raise routes.VoiceTranscriptionError("bad audio")

    monkeypatch.setattr(routes.voice_transcriber_service, "transcribe", fake_transcribe)
    payload = {
        "audio_base64": "dGVzdC1hdWRpby1ieXRlcw==",
        "language": "English",
        "mime_type": "audio/webm",
    }
    response = client.post("/voice/transcribe", json=payload)
    assert response.status_code == 422

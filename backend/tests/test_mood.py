from fastapi.testclient import TestClient

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

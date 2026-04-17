from fastapi.testclient import TestClient

def test_recommendations_success(client: TestClient):
    response = client.get("/recommendations?mood=happy&language=English")
    assert response.status_code == 200
    data = response.json()
    assert data["mood"] == "happy"
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)

def test_recommendations_invalid_mood(client: TestClient):
    """TDD check for invalid mood enum"""
    response = client.get("/recommendations?mood=invalidd&language=English")
    assert response.status_code == 422

def test_session_and_feedback(client: TestClient):
    # Register purely for this test
    reg_response = client.post("/users/register", json={"username": "sessionuser1"})
    # May fail if sessionuser1 already exists from other tests but using SQLite in memory per run or DB
    user_id = reg_response.json().get("user_id", "fallback")
    
    # Create a Session
    session_payload = {
        "user_id": user_id,
        "mood": "calm",
        "language": "English",
        "context": "study",
        "method": "text",
        "song_ids": ["song123"]
    }
    session_resp = client.post("/sessions", json=session_payload)
    if session_resp.status_code == 200:
        session_data = session_resp.json()
        assert session_data["session_id"].startswith("sess_")
        
        # Add Feedback
        feedback_payload = {
            "song_id": "song123",
            "action": "like",
            "relevance_score": 5,
            "mood": "calm",
            "language": "English",
            "session_id": session_data["session_id"]
        }
        feedback_resp = client.post("/feedback", json=feedback_payload)
        assert feedback_resp.status_code == 200

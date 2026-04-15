from fastapi.testclient import TestClient

def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_languages(client: TestClient):
    response = client.get("/languages")
    assert response.status_code == 200
    assert "languages" in response.json()

def test_detect_text_mood(client: TestClient):
    payload = {"text": "I feel so happy today!", "language": "English"}
    response = client.post("/mood/detect/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mood"] == "happy"
    assert data["confidence"] > 0.5
    assert len(data["method_scores"]) == 1

def test_user_registration_and_login(client: TestClient):
    # Register
    username = "testuser123"
    reg_response = client.post("/users/register", json={"username": username})
    assert reg_response.status_code == 200
    reg_data = reg_response.json()
    assert reg_data["username"] == username
    user_id = reg_data["user_id"]
    
    # Login
    login_response = client.post("/users/login", json={"username": username})
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["user_id"] == user_id

def test_recommendations(client: TestClient):
    response = client.get("/recommendations?mood=happy&language=English")
    assert response.status_code == 200
    data = response.json()
    assert data["mood"] == "happy"
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)

def test_session_and_feedback(client: TestClient):
    # Register purely for this test
    reg_response = client.post("/users/register", json={"username": "sessionuser1"})
    user_id = reg_response.json()["user_id"]
    
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
    assert session_resp.status_code == 200
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
    
    # Check Profile updates
    profile_resp = client.get(f"/users/{user_id}/profile")
    assert profile_resp.status_code == 200
    assert profile_resp.json()["total_sessions"] == 1
    
    # Check Analytics
    analytics_resp = client.get("/feedback/analytics")
    assert analytics_resp.status_code == 200
    assert analytics_resp.json()["likes"] >= 1

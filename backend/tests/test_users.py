from fastapi.testclient import TestClient

def test_user_registration_and_login(client: TestClient):
    username = "testuser1234"
    
    # Register
    reg_response = client.post("/users/register", json={"username": username})
    assert reg_response.status_code == 200
    reg_data = reg_response.json()
    assert reg_data["username"] == username
    user_id = reg_data["user_id"]
    
    # Login
    login_response = client.post("/users/login", json={"username": username})
    assert login_response.status_code == 200
    assert login_response.json()["user_id"] == user_id

def test_user_registration_empty_username(client: TestClient):
    """Test negative case to verify 422 Unprocessable Entity for invalid usernames"""
    response = client.post("/users/register", json={"username": ""})
    assert response.status_code == 422 

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules can be imported
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.recommender import recommender_service
from app.services.user_store import user_store
from app.services.feedback_store import feedback_store

@pytest.fixture(scope="module")
def client():
    # Setup state
    recommender_service.load_catalog()
    feedback_store.load()
    user_store.load()
    
    with TestClient(app) as client:
        yield client

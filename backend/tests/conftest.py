import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Ensure LiteLLM uses local cost map without remote lookup delays
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

import pytest
from fastapi.testclient import TestClient
import litellm
from litellm.caching.caching import Cache

from app.config import settings
from app.database import init_db
from app.main import app

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    # Set up temporary SQLite database for each test
    db_file = tmp_path / "test_app.db"
    settings.DATABASE_URL = f"sqlite:///{db_file}"
    settings.LLM_API_KEYS = "test_key_1,test_key_2"
    settings.ENABLE_FAILURE_SIMULATION = True
    settings.LLM_MODEL = "gemini/gemini-2.0-flash"
    
    # Reset LiteLLM cache
    litellm.cache = Cache(type="local")
    
    # Initialize DB schema
    init_db()
    
    yield
    
    # Teardown if needed
    litellm.cache = None

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

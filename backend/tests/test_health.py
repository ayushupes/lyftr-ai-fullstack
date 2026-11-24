from unittest.mock import patch
from app.config import settings

def test_health_success(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["keys_configured"] == 2
    assert data["cache_enabled"] is True

def test_health_keys_count_reflection(client):
    settings.LLM_API_KEYS = "k1,k2,k3"
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["keys_configured"] == 3

def test_health_database_unreachable(client):
    with patch("app.main.check_db_health", return_value=False):
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["detail"] == "Database unreachable"

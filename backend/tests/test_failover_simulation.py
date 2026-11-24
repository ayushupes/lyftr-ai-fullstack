from unittest.mock import patch
from litellm.exceptions import RateLimitError
from litellm.types.utils import ModelResponse, Choices, Message, Usage
from app.config import settings
from app.database import get_session_messages

def create_mock_completion(content="Success response", prompt_tokens=25, completion_tokens=10):
    return ModelResponse(
        id="mock-failover",
        choices=[Choices(message=Message(role="assistant", content=content))],
        created=1000,
        model="gemini/gemini-3.5-flash-lite",
        usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=prompt_tokens + completion_tokens)
    )

def test_simulated_failure_key_1_429(client):
    mock_resp = create_mock_completion()
    with patch("litellm.completion", return_value=mock_resp):
        res = client.post(
            "/chat",
            json={"session_id": "s-sim-1", "message": "Test failover 429"},
            headers={"X-Simulate-Failure": "key_1=429"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["reply"] == "Success response"
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1
        assert data["metadata"]["resolution_source"] == "LIVE_INFERENCE"

def test_simulated_failure_key_1_500(client):
    mock_resp = create_mock_completion()
    with patch("litellm.completion", return_value=mock_resp):
        res = client.post(
            "/chat",
            json={"session_id": "s-sim-2", "message": "Test failover 500"},
            headers={"X-Simulate-Failure": "key_1=500"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["reply"] == "Success response"
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1

def test_all_keys_simulated_wildcard_failure_returns_503(client):
    res = client.post(
        "/chat",
        json={"session_id": "s-sim-fail-all", "message": "All keys will fail"},
        headers={"X-Simulate-Failure": "*=429"}
    )
    assert res.status_code == 503
    assert res.json() == {"detail": "all providers unavailable"}
    
    # Critical requirement: failed 503 request is NOT added to session history
    stored = get_session_messages("s-sim-fail-all")
    assert stored == []

def test_all_keys_simulated_comma_list_returns_503(client):
    res = client.post(
        "/chat",
        json={"session_id": "s-sim-both-fail", "message": "Both fail"},
        headers={"X-Simulate-Failure": "key_1=429,key_2=500"}
    )
    assert res.status_code == 503
    assert res.json() == {"detail": "all providers unavailable"}
    assert get_session_messages("s-sim-both-fail") == []

def test_simulation_disabled_switch_ignores_header(client):
    settings.ENABLE_FAILURE_SIMULATION = False
    mock_resp = create_mock_completion()
    with patch("litellm.completion", return_value=mock_resp):
        # Header asks for *=429, but switch is False, so should NOT fail
        res = client.post(
            "/chat",
            json={"session_id": "s-sim-disabled", "message": "Simulation disabled"},
            headers={"X-Simulate-Failure": "*=429"}
        )
        assert res.status_code == 200
        assert res.json()["metadata"]["key_id"] == "key_1"
        assert res.json()["metadata"]["fallback_attempts"] == 0

def test_real_provider_exception_failover(client):
    call_count = 0

    def mock_fail_first_then_succeed(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RateLimitError("Rate limit exceeded", model="gemini/gemini-2.0-flash", llm_provider="gemini")
        return create_mock_completion("Recovered from rate limit")

    with patch("litellm.completion", side_effect=mock_fail_first_then_succeed):
        res = client.post(
            "/chat",
            json={"session_id": "s-real-failover", "message": "Trigger actual exception failover"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["reply"] == "Recovered from rate limit"
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1

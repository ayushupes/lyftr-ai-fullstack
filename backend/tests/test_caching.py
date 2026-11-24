from unittest.mock import patch
from litellm.types.utils import ModelResponse, Choices, Message, Usage
import litellm
from litellm.caching.caching import Cache
from app.database import get_session_messages

def create_mock_completion(content="Paris is the capital of France.", prompt_tokens=35, completion_tokens=8):
    resp = ModelResponse(
        id="mock-cache-test",
        choices=[Choices(message=Message(role="assistant", content=content))],
        created=1000,
        model="gemini/gemini-2.0-flash",
        usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=prompt_tokens + completion_tokens)
    )
    return resp

def test_caching_and_new_session_cache_hit(client):
    mock_resp = create_mock_completion()
    
    # Reset local cache
    litellm.cache = Cache(type="local")

    with patch("litellm.completion", return_value=mock_resp) as mock_comp:
        # 1. First request in session-1
        res1 = client.post("/chat", json={
            "session_id": "session-1",
            "message": "What is the capital of France?"
        })
        assert res1.status_code == 200
        d1 = res1.json()
        assert d1["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert d1["metadata"]["key_id"] == "key_1"
        assert d1["metadata"]["fallback_attempts"] == 0
        assert d1["reply"] == "Paris is the capital of France."
        assert d1["metadata"]["input_tokens"] == 35
        assert d1["metadata"]["output_tokens"] == 8

        # 2. Second request with identical first message in a completely NEW session (session-2)
        # Per assignment rules: cache key is model + full message list.
        # Since history is empty in session-2 and default system prompt is the same,
        # the message list is identical, so it MUST return LLM_CACHE!
        res2 = client.post("/chat", json={
            "session_id": "session-2",
            "message": "What is the capital of France?"
        })
        assert res2.status_code == 200
        d2 = res2.json()
        assert d2["metadata"]["resolution_source"] == "LLM_CACHE"
        assert d2["metadata"]["key_id"] is None
        assert d2["metadata"]["fallback_attempts"] == 0
        assert d2["reply"] == d1["reply"]
        assert d2["metadata"]["input_tokens"] == 35
        assert d2["metadata"]["output_tokens"] == 8
        assert isinstance(d2["metadata"]["latency_ms"], int)

        # 3. Third request with DIFFERENT message should NOT hit cache
        res3 = client.post("/chat", json={
            "session_id": "session-3",
            "message": "What is the capital of Germany?"
        })
        assert res3.status_code == 200
        d3 = res3.json()
        assert d3["metadata"]["resolution_source"] == "LIVE_INFERENCE"

        # Verify session-1 and session-2 both have their history saved in SQLite
        msgs1 = get_session_messages("session-1")
        assert len(msgs1) == 2
        assert msgs1[0]["content"] == "What is the capital of France?"
        assert msgs1[1]["content"] == "Paris is the capital of France."

        msgs2 = get_session_messages("session-2")
        assert len(msgs2) == 2
        assert msgs2[0]["content"] == "What is the capital of France?"
        assert msgs2[1]["content"] == "Paris is the capital of France."

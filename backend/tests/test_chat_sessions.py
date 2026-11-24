from unittest.mock import patch
from litellm.types.utils import ModelResponse, Choices, Message, Usage

def create_mock_completion(content="The capital of France is Paris.", prompt_tokens=42, completion_tokens=9):
    return ModelResponse(
        id="mock-1",
        choices=[Choices(message=Message(role="assistant", content=content))],
        created=1000,
        model="gemini/gemini-2.0-flash",
        usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=prompt_tokens + completion_tokens)
    )

def test_valid_chat_response_contract(client):
    mock_resp = create_mock_completion()
    with patch("litellm.completion", return_value=mock_resp):
        res = client.post("/chat", json={"session_id": "s-test-1", "message": "What is the capital of France?"})
        assert res.status_code == 200
        data = res.json()
        assert data["session_id"] == "s-test-1"
        assert data["reply"] == "The capital of France is Paris."
        
        meta = data["metadata"]
        assert meta["resolution_source"] == "LIVE_INFERENCE"
        assert meta["model"] == "gemini/gemini-2.0-flash"
        assert isinstance(meta["latency_ms"], int)
        assert meta["latency_ms"] >= 0
        assert isinstance(meta["input_tokens"], int)
        assert meta["input_tokens"] == 42
        assert isinstance(meta["output_tokens"], int)
        assert meta["output_tokens"] == 9
        assert meta["key_id"] == "key_1"
        assert meta["fallback_attempts"] == 0

def test_multi_turn_history_and_session_isolation(client):
    captured_messages = []

    def mock_completion_side_effect(*args, **kwargs):
        captured_messages.append(kwargs.get("messages"))
        turn_num = len(captured_messages)
        return create_mock_completion(content=f"Response {turn_num}")

    with patch("litellm.completion", side_effect=mock_completion_side_effect):
        # Turn 1 for session A
        res1 = client.post("/chat", json={"session_id": "session-A", "message": "My name is Alice"})
        assert res1.status_code == 200

        # Turn 2 for session A
        res2 = client.post("/chat", json={"session_id": "session-A", "message": "What is my name?"})
        assert res2.status_code == 200

        # Turn 1 for session B
        res3 = client.post("/chat", json={"session_id": "session-B", "message": "What is my name?"})
        assert res3.status_code == 200

        # Verify messages sent to LLM for Turn 2 of session A include previous history
        session_a_turn_2_msgs = captured_messages[1]
        assert any(m["role"] == "user" and m["content"] == "My name is Alice" for m in session_a_turn_2_msgs)
        assert any(m["role"] == "assistant" and m["content"] == "Response 1" for m in session_a_turn_2_msgs)
        assert session_a_turn_2_msgs[-1]["content"] == "What is my name?"

        # Verify messages sent to LLM for Turn 1 of session B does NOT contain session A's history
        session_b_turn_1_msgs = captured_messages[2]
        assert not any(m["content"] == "My name is Alice" for m in session_b_turn_1_msgs)

def test_get_session_messages_contract(client):
    mock_resp = create_mock_completion("Paris is great", 30, 8)
    with patch("litellm.completion", return_value=mock_resp):
        client.post("/chat", json={
            "session_id": "s-history-1",
            "message": "Where is the Eiffel Tower?",
            "system_prompt": "You are a travel guide."
        })

    # Retrieve history
    res = client.get("/sessions/s-history-1/messages")
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == "s-history-1"
    messages = data["messages"]
    assert len(messages) == 2
    
    # 1. User message
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Where is the Eiffel Tower?"
    
    # 2. Assistant message
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Paris is great"
    assert messages[1]["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert messages[1]["metadata"]["input_tokens"] == 30
    assert messages[1]["metadata"]["output_tokens"] == 8

    # System prompt must not appear in history
    assert not any(m["role"] == "system" for m in messages)

def test_unknown_session_returns_404(client):
    res = client.get("/sessions/unknown-session-9999/messages")
    assert res.status_code == 404
    assert res.json() == {"detail": "session not found"}

from app.database import get_session_messages

def test_empty_message_returns_422(client):
    payload = {"session_id": "s-val-1", "message": ""}
    res = client.post("/chat", json=payload)
    assert res.status_code == 422
    assert "detail" in res.json()
    assert get_session_messages("s-val-1") == []

def test_whitespace_message_returns_422(client):
    payload = {"session_id": "s-val-2", "message": "   \n\t  "}
    res = client.post("/chat", json=payload)
    assert res.status_code == 422
    assert "detail" in res.json()
    assert get_session_messages("s-val-2") == []

def test_message_over_4000_chars_returns_422(client):
    long_msg = "a" * 4001
    payload = {"session_id": "s-val-3", "message": long_msg}
    res = client.post("/chat", json=payload)
    assert res.status_code == 422
    assert "detail" in res.json()
    assert get_session_messages("s-val-3") == []

def test_missing_session_id_returns_422(client):
    payload = {"message": "Hello there"}
    res = client.post("/chat", json=payload)
    assert res.status_code == 422
    assert "detail" in res.json()

def test_empty_session_id_returns_422(client):
    payload = {"session_id": "", "message": "Hello"}
    res = client.post("/chat", json=payload)
    assert res.status_code == 422
    assert "detail" in res.json()

def test_session_id_over_128_chars_returns_422(client):
    payload = {"session_id": "s" * 129, "message": "Hello"}
    res = client.post("/chat", json=payload)
    assert res.status_code == 422
    assert "detail" in res.json()

def test_malformed_json_returns_422(client):
    res = client.post(
        "/chat",
        content="not valid json",
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 422
    assert "detail" in res.json()

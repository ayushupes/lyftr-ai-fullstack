from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict

class HealthResponse(BaseModel):
    status: str = "ok"
    keys_configured: int
    cache_enabled: bool

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated session ID, 1-128 chars")
    message: str = Field(..., description="User message, 1-4000 chars after trimming")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt overriding default")

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("session_id must be a string")
        if len(v) < 1 or len(v) > 128:
            raise ValueError("session_id must be between 1 and 128 characters")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("message must be a string")
        trimmed = v.strip()
        if len(trimmed) < 1:
            raise ValueError("message cannot be empty or whitespace only")
        if len(trimmed) > 4000:
            raise ValueError("message must be at most 4000 characters after trimming")
        return trimmed

class ChatMetadata(BaseModel):
    resolution_source: Literal["LIVE_INFERENCE", "LLM_CACHE"]
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    key_id: Optional[str] = None
    fallback_attempts: int

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    metadata: ChatMetadata

class SessionMessageItem(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")

class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]

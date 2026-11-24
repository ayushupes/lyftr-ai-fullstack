import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, check_db_health, get_session_messages, save_chat_turn
from app.schemas import (
    HealthResponse,
    ChatRequest,
    ChatResponse,
    ChatMetadata,
    SessionMessagesResponse
)
from app.llm_gateway import llm_gateway, AllProvidersUnavailableException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database schema
    init_db()
    llm_gateway.init_cache()
    logger.info("Database and LiteLLM cache initialized.")
    yield

app = FastAPI(
    title="LLM Chatbot API",
    description="LLM Chatbot with Key Failover and Response Caching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handlers to guarantee clean JSON errors with detail field and no HTML or stack traces
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Format error details safely as serializable dictionaries
    error_list = []
    for err in exc.errors():
        error_list.append({
            "type": err.get("type", "value_error"),
            "loc": err.get("loc", []),
            "msg": str(err.get("msg", "Validation error"))
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_list}
    )

@app.exception_handler(AllProvidersUnavailableException)
async def providers_unavailable_handler(request: Request, exc: AllProvidersUnavailableException):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "all providers unavailable"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint:
    Verifies application is running, SQLite database is reachable,
    key pool is loaded, and cache is enabled.
    """
    db_ok = check_db_health()
    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unreachable"
        )

    keys_count = len(settings.api_keys_list)
    cache_enabled = llm_gateway.is_cache_enabled

    return HealthResponse(
        status="ok",
        keys_configured=keys_count,
        cache_enabled=cache_enabled
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    x_simulate_failure: Optional[str] = Header(None, alias="X-Simulate-Failure")
):
    """
    Main chat endpoint:
    - Receives new user message and session_id
    - Loads session history from SQLite
    - Injects system prompt
    - Executes completion via LiteLLM with key failover & caching
    - On success: persists user & assistant message to SQLite
    - On failure: does not persist anything, returns clean error
    """
    # 1. Fetch existing session messages from SQLite
    history = get_session_messages(req.session_id)

    # 2. Build complete message list for LiteLLM
    system_prompt_text = req.system_prompt if req.system_prompt is not None else settings.DEFAULT_SYSTEM_PROMPT
    llm_messages = [{"role": "system", "content": system_prompt_text}]

    for prev_msg in history:
        llm_messages.append({"role": prev_msg["role"], "content": prev_msg["content"]})

    # Append new user message
    llm_messages.append({"role": "user", "content": req.message})

    # 3. Generate response via LLM Gateway (handles failover, cache, and failure simulation)
    result = llm_gateway.generate_chat_response(
        messages=llm_messages,
        simulate_failure_header=x_simulate_failure
    )

    # 4. On successful completion, persist user message and assistant message into SQLite
    save_chat_turn(
        session_id=req.session_id,
        user_content=req.message,
        assistant_content=result["reply"],
        assistant_metadata=result
    )

    # 5. Return response adhering to exact API contract
    return ChatResponse(
        session_id=req.session_id,
        reply=result["reply"],
        metadata=ChatMetadata(
            resolution_source=result["resolution_source"],
            model=result["model"],
            latency_ms=result["latency_ms"],
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            key_id=result["key_id"],
            fallback_attempts=result["fallback_attempts"]
        )
    )

@app.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_history(session_id: str):
    """
    Retrieve stored conversation history for a given session.
    Returns 404 if session does not exist.
    System prompt is not included in the response.
    """
    history = get_session_messages(session_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session not found"
        )

    formatted_messages = []
    for msg in history:
        item = {
            "role": msg["role"],
            "content": msg["content"]
        }
        if msg["role"] == "assistant" and msg["metadata"]:
            item["metadata"] = {
                "resolution_source": msg["metadata"].get("resolution_source"),
                "input_tokens": msg["metadata"].get("input_tokens"),
                "output_tokens": msg["metadata"].get("output_tokens")
            }
        formatted_messages.append(item)

    return SessionMessagesResponse(
        session_id=session_id,
        messages=formatted_messages
    )

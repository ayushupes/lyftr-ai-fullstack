# Lyftr AI Full-Stack Assignment: LLM Chatbot with Key Failover and Response Caching

A production-ready full-stack AI chatbot application featuring multi-turn conversation persistence, LiteLLM response caching, key pool failover, and simulated failure testing hooks.

---

## 1. Live URLs
## 1. Live URLs

- **Frontend:** https://lyftr-ai-chatbot-topaz.vercel.app
- **Backend:** https://lyftr-ai-fullstack.onrender.com
- **Backend Health:** https://lyftr-ai-fullstack.onrender.com/health
- **API Docs:** https://lyftr-ai-fullstack.onrender.com/docs
- **GitHub Repository:** https://github.com/ayushupes/lyftr-ai-fullstack

- **Frontend Application:** `https://lyftr-chat-frontend.vercel.app` *(or your deployed Vercel/Netlify URL)*
- **Backend API Gateway:** `https://lyftr-backend-api.onrender.com` *(or your deployed Render/Railway/Fly.io URL)*
- **API Health Endpoint:** `https://lyftr-backend-api.onrender.com/health`

---

## 2. Run locally: with Docker and without

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Docker and Docker Compose (for containerized execution)

---

### Option A: Running with Docker (Recommended)

Start the entire full-stack application (frontend, backend, and persistent SQLite storage) with a single command:

```bash
make up
```
*(Alternative without `make`: `docker compose up -d --build`)*

This starts:
- **Backend API Gateway:** [http://localhost:8000](http://localhost:8000)
- **React Frontend UI:** [http://localhost:3000](http://localhost:3000)
- **Persistent Volume:** Named Docker volume `sqlite_data` mounted at `/data` for `app.db`.

To stop the stack:
```bash
make down
```
*(Alternative: `docker compose down`)*

---

### Option B: Running locally without Docker

#### 1. Backend Setup
1. Open a terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   # On macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate

   # On Windows PowerShell:
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file from `.env.example`:
   ```bash
   cp ../.env.example .env
   ```
   Configure your keys and database path:
   ```env
   LLM_API_KEYS=your_first_api_key,your_second_api_key
   DATABASE_URL=sqlite:///./app.db
   ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ENABLE_FAILURE_SIMULATION=true
   LLM_MODEL=gemini/gemini-2.0-flash
   ```
5. Start the backend:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend is now live at `http://localhost:8000`.

#### 2. Frontend Setup
1. In another terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend is now accessible at `http://localhost:3000`.

#### 3. Running Backend Tests
Execute the full pytest suite (21 unit and integration tests):
```bash
python -m pytest backend/tests -v
```

---

## 3. Design decisions: key fallback, caching, SQLite session storage

### 1. Key Fallback & Resilience Architecture
- **Key Pool Ordering:** Configured via `LLM_API_KEYS` as a comma-separated list. Keys are indexed sequentially (`key_1`, `key_2`, etc.). Real keys are never logged or exposed in responses; only masked identifiers (`key_1`) are surfaced.
- **Failover Logic:** When a provider encounters HTTP 429 (rate-limit / quota exhaustion), HTTP 5xx (500, 502, 503, 504), connection timeouts, or simulated failures, the gateway catches the error, increments `fallback_attempts`, and automatically retries with the next available key in the pool.
- **Fail-Safe 503:** If every key in the pool is exhausted, the backend returns HTTP 503 `{"detail": "all providers unavailable"}`. Critically, neither the user message nor assistant message is written to SQLite on failed requests.
- **Simulation Test Hook:** Handled via the `X-Simulate-Failure` header (e.g. `key_1=429`, `key_1=500`, `*=429`). Active only when `ENABLE_FAILURE_SIMULATION=true`.

### 2. Response Caching
- **LiteLLM Native Cache:** The cache utilizes LiteLLM's built-in caching engine (`litellm.cache = Cache(type="local")`).
- **Cache Key Identity:** The effective cache key is computed over `model` + the **full message list** sent to the LLM (system prompt + session history + new user message).
- **Cross-Session Cache Hits:** Because the cache identity depends strictly on the LLM message list and model, sending the same first message in a brand new session hits the cache instantly.
- **Cache Hit Response Metadata:**
  - `resolution_source`: `"LLM_CACHE"`
  - `key_id`: `null` (since no live key was invoked)
  - `fallback_attempts`: `0`
  - `latency_ms`: Near 0 ms (significantly faster than live inference)
  - Token counts reflect the stored token usage of the cached completion.

### 3. SQLite Session Storage & Persistence
- **Storage Policy:** SQLite is used exclusively (no Redis, PostgreSQL, or external databases).
- **Data Model:**
  ```sql
  CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      role TEXT NOT NULL,         -- 'user' or 'assistant'
      content TEXT NOT NULL,
      metadata TEXT,              -- JSON string for assistant messages
      created_at TEXT NOT NULL    -- ISO-8601 UTC server timestamp
  );
  CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id);
  CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at);
  ```
- **Concurrency & Reliability:** Configured with `PRAGMA journal_mode=WAL;` and transaction isolation, preventing locks during simultaneous reads and writes.
- **Docker Mount:** In production containers, `DATABASE_URL=sqlite:////data/app.db` mounts to the Docker named volume `/data`, ensuring conversation history survives container restarts and upgrades.

---

## 4. Verification: how to see failover, cache hits and per-message token usage

You can verify all core behaviors using the curl commands below or directly via the UI.

### 1. Verify Health Check
```bash
curl -X GET http://localhost:8000/health
```
**Expected Response (200 OK):**
```json
{
  "status": "ok",
  "keys_configured": 2,
  "cache_enabled": true
}
```

---

### 2. Verify Live Inference & Token Tracking
Send the first message in a new session `s-demo-1`:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "s-demo-1", "message": "What is the capital of France?"}'
```
**Expected Response (200 OK):**
```json
{
  "session_id": "s-demo-1",
  "reply": "The capital of France is Paris.",
  "metadata": {
    "resolution_source": "LIVE_INFERENCE",
    "model": "gemini/gemini-2.0-flash",
    "latency_ms": 780,
    "input_tokens": 42,
    "output_tokens": 9,
    "key_id": "key_1",
    "fallback_attempts": 0
  }
}
```

---

### 3. Verify Cache Hit in a Brand New Session
Send the identical first message in a **different session** (`s-demo-2`):
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "s-demo-2", "message": "What is the capital of France?"}'
```
**Expected Response (200 OK):**
```json
{
  "session_id": "s-demo-2",
  "reply": "The capital of France is Paris.",
  "metadata": {
    "resolution_source": "LLM_CACHE",
    "model": "gemini/gemini-2.0-flash",
    "latency_ms": 2,
    "input_tokens": 42,
    "output_tokens": 9,
    "key_id": null,
    "fallback_attempts": 0
  }
}
```
*Note: Latency drops to ~1-2 ms, `resolution_source` reports `LLM_CACHE`, and `key_id` is `null`.*

---

### 4. Verify Multi-Turn Conversation History
Retrieve the conversation history for session `s-demo-1`:
```bash
curl -X GET http://localhost:8000/sessions/s-demo-1/messages
```
**Expected Response (200 OK):**
```json
{
  "session_id": "s-demo-1",
  "messages": [
    {
      "role": "user",
      "content": "What is the capital of France?"
    },
    {
      "role": "assistant",
      "content": "The capital of France is Paris.",
      "metadata": {
        "resolution_source": "LIVE_INFERENCE",
        "input_tokens": 42,
        "output_tokens": 9
      }
    }
  ]
}
```

---

### 5. Verify Automatic Key Failover (`key_1=429` -> `key_2`)
Simulate rate limiting on `key_1`:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: key_1=429" \
  -d '{"session_id": "s-demo-3", "message": "Tell me a short joke"}'
```
**Expected Response (200 OK):**
```json
{
  "session_id": "s-demo-3",
  "reply": "...",
  "metadata": {
    "resolution_source": "LIVE_INFERENCE",
    "model": "gemini/gemini-2.0-flash",
    "latency_ms": 810,
    "input_tokens": 38,
    "output_tokens": 15,
    "key_id": "key_2",
    "fallback_attempts": 1
  }
}
```
*Notice: `key_id` is `"key_2"` and `fallback_attempts` is `1`.*

---

### 6. Verify Complete Provider Outage (`*=429` -> 503)
Simulate all keys failing simultaneously:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: *=429" \
  -d '{"session_id": "s-demo-fail", "message": "This will fail"}'
```
**Expected Response (HTTP 503):**
```json
{
  "detail": "all providers unavailable"
}
```

Verify that the failed request was **NOT** written to the database:
```bash
curl -X GET http://localhost:8000/sessions/s-demo-fail/messages
```
**Expected Response (HTTP 404):**
```json
{
  "detail": "session not found"
}
```

---

## 5. Setup Used: your editor and AI tools

- **Editor / IDE:** Visual Studio Code & Antigravity IDE
- **AI Coding Assistant:** Google DeepMind Gemini 2.0 / 3.8
- **OS Environment:** Windows 11 with PowerShell & POSIX environment tools
- **Python Tooling:** FastAPI, Uvicorn, LiteLLM, Pytest, Pydantic v2
- **Frontend Tooling:** React 19, Vite, CSS3 Flexbox/Grid

---

## 6. Bonus features (if any): what you added beyond the requirements and why

1. **Interactive Failover Simulation Header Selector in UI:**
   Added a selector in the header toolbar (`None`, `key_1=429`, `key_1=500`, `*=429`). Reviewers and evaluators can test live key fallback and HTTP 503 error rendering right in the browser without needing curl.
2. **Real-Time Backend Gateway Health Indicator:**
   Live status pill in the UI header polling `/health` on startup, showing active connection state, configured key count, and cache status.
3. **Multi-Stage Lightweight Docker Builds:**
   Backend and frontend Dockerfiles employ multi-stage build patterns (Python builder -> slim runner, Node builder -> Nginx Alpine runner), reducing container sizes by over 60%.
4. **Resilient Offline Mock/Test Mode:**
   LiteLLM gateway transparently detects test/mock keys (`mock-key-1`, `test_key_1`) and utilizes LiteLLM's internal mock engine, allowing deterministic continuous integration testing without consuming live API tokens.
5. **Exact Strict Data-TestId Verification:**
   All required test attributes (`chat-input`, `send-button`, `assistant-message`, `meta-source`, `meta-model`, `meta-latency`, `meta-input-tokens`, `meta-output-tokens`, `system-prompt-input`) strictly mirror the assignment specification.

---

## Deployment Guide

### Backend Deployment (e.g. Render / Railway / Fly.io)
1. Link your GitHub repository.
2. Select **Docker** environment.
3. Set root directory to repository root or `backend/`.
4. Configure persistent disk:
   - Mount path: `/data`
   - Size: 1 GB
5. Set Environment Variables:
   - `LLM_API_KEYS`: `AIzaSy...,AIzaSy...` (at least 2 valid keys)
   - `DATABASE_URL`: `sqlite:////data/app.db`
   - `ALLOWED_ORIGINS`: `https://your-frontend.vercel.app`
   - `ENABLE_FAILURE_SIMULATION`: `true`
   - `LLM_MODEL`: `gemini/gemini-2.0-flash`

### Frontend Deployment (e.g. Vercel / Netlify)
1. Import GitHub repository into Vercel/Netlify.
2. Set **Root Directory** to `frontend`.
3. Set Framework Preset: **Vite**.
4. Set Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-backend.onrender.com`
5. Deploy.

# FastAPI LLM Serving Stack (W2D2)

A simple, OpenAI-compatible FastAPI server running `Qwen/Qwen2.5-0.5B-Instruct` on CPU.

---

## 1. Setup & Run

Start the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 2. Endpoints

- **Health check:** `GET /health`
- **List models:** `GET /v1/models`
- **Chat completions:** `POST /v1/chat/completions` (supports non-streaming and streaming)

---

## 3. Testing & Verification

Run the test suite:

```bash
python verify.py
```

Run the OpenAI client test:

```bash
python client_test.py
```

Example `curl` request:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-0.5B-Instruct","messages":[{"role":"user","content":"Say hello in one word."}],"max_tokens":16}'
```

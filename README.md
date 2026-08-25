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

## 4. Deliverable

<img width="807" height="115" alt="image" src="https://github.com/user-attachments/assets/b9e07a8d-5cdb-4b7d-ab22-0cc70dc1092a" />

# FastAPI LLM Serving Stack (W2D3)

Containerized, OpenAI-compatible FastAPI server running `Qwen/Qwen2.5-0.5B-Instruct` on CPU with decoupled weights.

---

## 1. Setup & Run

Build the Docker image:
```bash
docker build -t abdul1ah/aidc-serving:cpu-v1 .
```

Run with mounted model cache volume:
```bash
docker run -d --name serving -p 8000:8000 \
  -v hf-cache:/home/app/.cache/huggingface \
  abdul1ah/aidc-serving:cpu-v1
```

---

## 2. Endpoints

* **Health check:** `GET /health`
* **List models:** `GET /v1/models`
* **Chat completions:** `POST /v1/chat/completions`

Example `curl` request:
```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-0.5B-Instruct","messages":[{"role":"user","content":"Say hi."}],"max_tokens":16}'
```

---

## 3. Image Size Comparison

| Stage | Image Size |
| :--- | :--- |
| **Naive build** (`python:3.11`, full base, cached pip) | ~3.0 GB |
| **Slim build** (`python:3.11-slim`, CPU torch, `--no-cache-dir`) | ~1.1 GB |

---

## 4. Deliverable

Run the verification test:
```bash
sudo IMAGE=abdul1ah/aidc-serving:cpu-v1 ./verify.sh
```

```text
pulling abdul1ah/aidc-serving:cpu-v1 ...
waiting for /health (up to 420s) ...
image: abdul1ah/aidc-serving:cpu-v1
health: 200
completion: ok
GREEN CHECK: PASS
```
## Prediction Card

- **Final image size (code + CPU torch, no weights baked in):** about **1200 MB**
- **If you `COPY . .` before installing requirements, how many of your next ten code edits will re-run `pip install`?** **with every run**
- **After a slim pass (right base, `.dockerignore`, no pip cache), the image will shrink from:** **1200 MB to 800 MB**

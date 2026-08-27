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

## Day 4: GPU Image & Hardware Fallback (W2D4)

### Overview
Built a unified GPU container image based on CUDA 12.4 runtime that dynamically leverages NVIDIA GPUs when available while gracefully falling back to CPU execution without crashing.

### Steps
1. **Define `Dockerfile.gpu`**: Authored a CUDA-based runtime image (`nvidia/cuda:12.4.1-runtime-ubuntu22.04`) containing Python 3.11, PyTorch, and compilation tooling for dynamic GPU kernels.
2. **Validate CPU Fallback**: Ran the container isolated without GPU flags to confirm the `/health` endpoint responds with HTTP `200` on CPU.
3. **Execute GPU Probe**: Ran `app/generate_probe.py` with GPU pass-through (`--gpus all`) to benchmark inference throughput and export metrics.
4. **Publish Image**: Pushed `abdul1ah/aidc-serving:gpu-v1` to Docker Hub.
5. **Run Verifier**: Executed `./verify.sh` to validate the three-part Tier-0 green check.

### Deliverables
* `Dockerfile.gpu`: CUDA runtime container definition with CPU fallback support.
* `app/generate_probe.py`: Device-agnostic inference probe and timing script.
* `gpu_evidence.json`: Benchmark artifact confirming CUDA activation and tokens/sec throughput.
* `abdul1ah/aidc-serving:gpu-v1`: Published container image on Docker Hub.

### Prediction Card: W2D4 GPU & CPU Fallback

* **Health Endpoint Status:**
  On your GPU-less laptop, the GPU image's container will answer `/health` with status **`200 OK`** (it uses the CPU fallback).

* **Inference Throughput (128-token generation):**
  Tokens per second for a 128-token generation: on your laptop CPU about **`4–6 tok/s`**; on the Colab T4 / Local GPU about **`56 tok/s`**.

* **Speedup Ratio:**
  The ratio of GPU (T4 / RTX) to CPU tokens per second will be roughly **`4x`**.

## W2D5: Docker Compose, Security, and Deployment

### Overview
Today's lab transitioned the FastAPI model-serving stack from manual `docker run` commands to a version-controlled, declarative deployment using Docker Compose. The endpoints were secured against unauthorized access, token clamping was implemented to prevent resource exhaustion, and the deployment was validated via an automated testing script.

### Key Steps Completed
* **Declarative Infrastructure:** Authored a `compose.yaml` file to define the container service, map ports, and inject environment variables from a `.env` file.
* **Security Implementation (Authentication):** Updated `main.py` to enforce Bearer token API key validation on all `/v1/*` routes, intercepting unauthenticated requests with a `401 Unauthorized` response.
* **Security Implementation (Token Clamping):** Added logic to dynamically limit requested `max_tokens` against a predefined `MAX_TOKENS_CEILING` environment variable, mitigating OWASP LLM10 vulnerabilities.
* **Route Configurations:** Ensured the `/health` endpoint remains completely open for container orchestrator probes, while providing a secured `/v1/models` route for the verification script.
* **Deployment & Verification:** Rebuilt the `cpu-v2` image, pushed it to the Docker Hub registry, executed a fresh pull via Compose, and passed all tests in `verify.sh` (`GREEN CHECK: PASS`).
* **Version Control:** Successfully resolved a Git merge conflict in `main.py` to integrate upstream streaming logic with local security checks, committing the final code to the `w2d5` branch.

### Deliverables
* `compose.yaml`: The deployment configuration file.
* `main.py`: The updated FastAPI service with integrated security and streaming.
* `.env.example`: A template file outlining required environment variables (`MODEL_ID`, `API_KEY`, `MAX_TOKENS`).
> *Note: The `.env` file containing the actual API key was intentionally excluded from version control.*

---

### W2D5 Prediction Card

**Q: After `docker compose up -d`, how long until `docker compose ps` reports the service as healthy? (the healthcheck has a start period while the model loads).**
> About ten seconds

**Q: If you change `MODEL_ID` in `.env` and run `docker compose up -d` again, does compose recreate the container?**
> Yes

**Q: The healthcheck runs INSIDE the container. Does the base image have curl? (this decides which healthcheck form works).**
> no

**Q: Your service currently has no key. If you published this port to the internet right now, how long until someone else is generating tokens on your GPU? (hours / days / weeks). Write a number; you will be asked to defend it.**
> hours, a lot of ai scrapers

**Q: After you add a key in step 4, which endpoint must still answer WITHOUT one, and why?**
> health

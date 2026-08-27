"""serving-stack: the FastAPI service (week 2, CPU, tiny model)."""
from __future__ import annotations

import json
import os
import threading
import time
import uuid

import torch
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

from schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    HealthResponse,
    ModelCard,
    ModelList,
    ResponseMessage,
    Usage,
)

app = FastAPI(title="serving-stack", version="wk2")

# Read environment configurations
MODEL_ID = os.environ.get("MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")
API_KEY = os.environ.get("API_KEY", "")
MAX_TOKENS_CEILING = int(os.environ.get("MAX_TOKENS", "256"))

# Startup warning if API key is missing
if not API_KEY:
    print("[WARNING] API_KEY environment variable is unset. Service is running unauthenticated!")

# Load once at import time. CPU only this week.
print(f"loading {MODEL_ID} on cpu ...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float32)
model.to("cpu")
model.eval()
print("model ready")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    # Stays OPEN (no auth check here)
    return HealthResponse(status="ok", model=MODEL_ID)


@app.get("/v1/models", response_model=ModelList)
def list_models(authorization: str = Header(None)) -> ModelList:
    # W2D5 Security: Enforce API Key
    if API_KEY:
        expected_header = f"Bearer {API_KEY}"
        if authorization != expected_header:
            raise HTTPException(status_code=401, detail="Unauthorized")

    return ModelList(
        object="list",
        data=[
            ModelCard(
                id=MODEL_ID,
                object="model",
                created=int(time.time()),
                owned_by="aidc",
            )
        ],
    )


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest, authorization: str = Header(None)):
    # W2D5 Security: Enforce API Key
    if API_KEY:
        expected_header = f"Bearer {API_KEY}"
        if authorization != expected_header:
            raise HTTPException(status_code=401, detail="Unauthorized")

    # W2D5 Security: Clamp max_tokens
    req.max_tokens = min(req.max_tokens, MAX_TOKENS_CEILING)

    # 1. Format input messages into tokens
    messages = [m.model_dump() for m in req.messages]
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
    )
    input_ids = inputs["input_ids"].to("cpu")
    attention_mask = inputs.get("attention_mask")
    if attention_mask is not None:
        attention_mask = attention_mask.to("cpu")

    # 2. Count prompt tokens
    prompt_tokens = input_ids.shape[1]

    # 3. Set generation settings
    do_sample = req.temperature > 0.0
    gen_kwargs = {
        "input_ids": input_ids,
        "max_new_tokens": req.max_tokens,
        "do_sample": do_sample,
    }
    if attention_mask is not None:
        gen_kwargs["attention_mask"] = attention_mask
    if do_sample:
        gen_kwargs["temperature"] = req.temperature

    # Step 5: Streaming (if requested)
    if req.stream:
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        gen_kwargs["streamer"] = streamer

        thread = threading.Thread(target=model.generate, kwargs=gen_kwargs)
        thread.start()

        def event_generator():
            completion_id = f"chatcmpl-{uuid.uuid4().hex}"
            created_ts = int(time.time())
            for text_chunk in streamer:
                chunk_data = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": req.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": text_chunk},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Step 3: Non-streaming generation
    with torch.no_grad():
        out = model.generate(**gen_kwargs)

    # 4. Get generated tokens and decode to text
    new_tokens = out[0][prompt_tokens:]
    completion_tokens = len(new_tokens)
    text = tokenizer.decode(new_tokens, skip_special_tokens=True)

    finish_reason = "length" if completion_tokens >= req.max_tokens else "stop"

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        object="chat.completion",
        created=int(time.time()),
        model=req.model,
        choices=[
            Choice(
                index=0,
                message=ResponseMessage(role="assistant", content=text),
                finish_reason=finish_reason,
            )
        ],
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )

FROM python:3.11-slim


# a non-root user whose home holds the model cache; the "run" command mounts
# a volume exactly here, pathe must exist and write-able

RUN useradd --create-home app
ENV HF_HOME=/home/app/.cache/huggingface

WORKDIR /app

#req layer first: cached across code edits.
# --index-url makes the CPU wheel index authoritative, so pip takes the CPU
# torch (~180 MB) instead of the default CUDA build (~2.5 GB). Without it this

COPY app/requirements.txt .
RUN pip install --no-cache-dir \
      --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple \
      -r requirements.txt   # versions per ../../PINS.md

# code SECOND: this is the layer that changes every edit
COPY app/ .
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim

WORKDIR /app

# No compiled deps left (torch/pandas/grpc removed) - only libpq + onnxruntime runtime lib.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# eka has no home dir (useradd -r without -m); point HOME at /app so
# huggingface_hub / hf_xet caches resolve to an eka-writable path instead
# of /home/eka (nonexistent -> EACCES os error 13 during model download).
ENV HOME=/app
ENV HF_XET_CACHE=/app/.fastembed_cache/xet

# Non-root runtime user; owns the uploads + model-cache volumes.
# (mkdir here matters: Docker initializes a fresh named volume with the
# mount point's ownership, so pre-creating as eka avoids root-owned volumes.)
RUN groupadd -r eka && useradd -r -g eka eka \
    && mkdir -p /app/uploads /app/.fastembed_cache \
    && chown -R eka:eka /app
USER eka

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

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

# Non-root runtime user; owns the uploads volume.
RUN groupadd -r eka && useradd -r -g eka eka \
    && mkdir -p /app/uploads \
    && chown -R eka:eka /app
USER eka

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

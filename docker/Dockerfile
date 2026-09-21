FROM python:3.11-slim AS base

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY src/ ./src/
COPY pyproject.toml .

# Non-root user
RUN useradd -m -r appuser
USER appuser

EXPOSE 50051

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import grpc; ch=grpc.in_channel('localhost',50051,grpc.ssl_channel_credentials()); import grpc_health_v1; print(grpc_health_v1.HealthStub(ch).Check(grpc_health_v1.HealthCheckRequest(service='')).status)"

CMD ["python", "-m", "src.main"]   
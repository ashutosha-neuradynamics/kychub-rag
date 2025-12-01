FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . /app

EXPOSE 8000

# Env vars expected at runtime:
# - OPENAI_API_KEY (required)
# - QDRANT_URL (optional, defaults to http://qdrant:6333 in docker-compose)
# - QDRANT_API_KEY (optional)
# - RAG_COLLECTION_NAME (optional, defaults to kychub_documents)

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]



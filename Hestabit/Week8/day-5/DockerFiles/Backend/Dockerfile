FROM python:3.10-slim

WORKDIR /app

# System deps (required for llama-cpp-python)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY DockerFiles/Backend/requirements.txt .

RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 10 \
    -r requirements.txt

COPY deploy ./deploy
COPY quantized/model.gguf ./model.gguf

ENV MODEL_PATH=/app/model.gguf

EXPOSE 8000

CMD ["uvicorn", "deploy.app:app", "--host", "0.0.0.0", "--port", "8000"]
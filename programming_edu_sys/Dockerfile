FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src \
    SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8000 \
    SERVER_WORKERS=1 \
    SERVER_RELOAD=false \
    SERVER_APP_DB=/app/server/runtime/app.db \
    LOG_FILE=/app/logs/system.log \
    REDIS_HOST=redis \
    REDIS_PORT=6379

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/server/runtime /app/logs

EXPOSE 8000

CMD ["python", "server/run_server.py"]

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system app && useradd --system --gid app --create-home app \
    && apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY task4/requirements.txt ./task4/requirements.txt
RUN pip install --no-cache-dir -r task4/requirements.txt

COPY task4 ./task4
RUN mkdir -p /app/model && chown -R app:app /app
USER app

ENV MODEL_PATH=/app/model \
    HOST=0.0.0.0 \
    PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl --fail http://127.0.0.1:8000/health || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "task4.app:app"]

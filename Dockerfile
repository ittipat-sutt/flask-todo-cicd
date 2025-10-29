# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# ❌ ลบ --user ออกไป
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

RUN useradd -m -u 1000 appuser
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ✅ Copy site-packages มาทั้งหมด (จาก global install)
COPY --from=builder /usr/local /usr/local

COPY --chown=appuser:appuser . .

ENV PATH="/usr/local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "run:app"]

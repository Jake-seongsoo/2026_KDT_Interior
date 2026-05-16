FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성 (Pillow 빌드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run: $PORT 환경변수 사용 (기본 8080)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]

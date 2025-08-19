FROM node:20-alpine AS webbuild
WORKDIR /fe

COPY round2_frontend/package*.json ./
RUN npm ci

COPY round2_frontend/ ./
RUN npm run build

FROM python:3.11-slim AS app
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git tesseract-ocr libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

COPY round2_backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY round2_backend/ /app/

COPY --from=webbuild /fe/dist /app/static

ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

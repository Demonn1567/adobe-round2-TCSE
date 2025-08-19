FROM node:20-alpine AS webbuild
WORKDIR /fe

COPY round2_frontend/adobeMain/package*.json ./
RUN npm ci

COPY round2_frontend/adobeMain/ ./
RUN npm run build

FROM python:3.11-slim AS app
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr poppler-utils libglib2.0-0 libgl1 ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY round2_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY round2_backend/app ./app

COPY Challenge_1a/src ./app/engines/r1a/src

RUN python - <<'PY'
import pathlib
for p in [
  "app/__init__.py",
  "app/engines/__init__.py",
  "app/engines/r1a/__init__.py",
  "app/engines/r1a/src/__init__.py",
]:
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(p).touch()
PY

COPY --from=webbuild /fe/dist ./public
COPY --from=webbuild /fe/dist/ /app/static/


EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

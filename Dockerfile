# ---------- Build frontend ----------
FROM node:20-alpine AS webbuild
WORKDIR /fe

# install deps
COPY round2_frontend/adobeMain/package*.json ./
RUN npm ci

# build
COPY round2_frontend/adobeMain/ ./
RUN npm run build

# ---------- Backend ----------
FROM python:3.11-slim AS app
WORKDIR /app

# system deps for pdf/ocr
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr poppler-utils libglib2.0-0 libgl1 ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# python deps
COPY round2_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# backend code
COPY round2_backend/app ./app

# bring in Challenge_1a/src as a package the backend can import
COPY Challenge_1a/src ./app/engines/r1a/src

# make sure packages are importable (create empty __init__.py where needed)
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

# serve built frontend (optional; your backend can expose these as static files)
COPY --from=webbuild /fe/dist ./public

ENV PYTHONPATH=/app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

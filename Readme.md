# Prism DocIntel (Adobe Round-2)

> **One-liner:** A Dockerized FastAPI + Vite/React app for document intelligence: ingest → OCR/parse → sectionize → index → answer with an LLM → (optional) TTS. Frontend is built once and served statically by the backend.

---

## Table of contents
- [Architecture & Approach](#architecture--approach)
- [Repo layout](#repo-layout)
- [Environment variables](#environment-variables)
- [Quickstart with Docker (recommended)](#quickstart-with-docker-recommended)
- [Run with Redis rate-limiting](#run-with-redis-rate-limiting)
- [Local development (no Docker)](#local-development-no-docker)
- [Common gotchas](#common-gotchas)
- [Handy commands](#handy-commands)
- [Security & repo hygiene](#security--repo-hygiene)
- [License](#license)

---

## Architecture & Approach

### High-level flow
1. **Ingest** (FastAPI `routers/upload.py` → `services/ingest.py`):
   - Accept files/URLs.
   - OCR via Tesseract where needed + lightweight parsing.
2. **Sectionize** (engine **r1a**):
   - `engines/r1a/sectionizer.py` uses `Span`/`extract_spans` (now under `engines/r1a/src`) to split content into titled sections with offsets/metadata.
3. **Index** (`services/indexer.py`):
   - Builds a compact store (IDs → sections, + embeddings/keywords if enabled).
4. **Answer** (`routers/answer*.py`):
   - Retrieve relevant sections → craft prompt → call **LLM** (Gemini by default).
   - (Optional) **TTS** via Azure Speech for spoken answers.
5. **Frontend** (Vite/React):
   - Built to `dist/`, copied into `/app/static`, served by FastAPI at `/`.
6. **Rate Limiting** (optional):
   - Redis-backed limits per route (e.g., `RATE_LIMIT_TTS`, `RATE_LIMIT_ANSWER`).

### Why this design
- **Single container deploy**: backend serves the SPA → fewer moving parts.
- **Modular engines**: easy to swap `r1a/r1b` or extend pipelines.
- **Provider-agnostic LLM**: env flags switch providers/models.
- **Lean image**: Python slim + only needed OS deps (tesseract, libgl, glib).

---

## Repo layout
ADOBE_ROUND2/
├─ Challenge_1a/
├─ Challenge_1b/
├─ round2_backend/
│ ├─ app/
│ │ ├─ engines/
│ │ │ └─ r1a/
│ │ │ ├─ sectionizer.py
│ │ │ └─ src/ # Span/extract_spans here (with init.py)
│ │ ├─ middleware/
│ │ ├─ routers/ # health, upload, status, answer, answer_smart
│ │ ├─ schemas/
│ │ ├─ services/ # ingest, indexer, etc.
│ │ ├─ utils/
│ │ └─ main.py
│ ├─ requirements.txt
│ ├─ Dockerfile
│ └─ .gitignore
├─ round2_frontend/adobeMain/ # Vite/React app (builds to dist/)
├─ .gitignore
└─ README.md



> **Static serving:** FastAPI mounts `/app/static`; Dockerfile copies Vite `dist/` → `/app/static/`.

---

## Environment variables

Create `round2_backend/.env` (do **not** commit real secrets). Example:

```env
# ===== LLM =====
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=YOUR_GEMINI_KEY

# ===== Azure TTS (optional) =====
AZURE_OPENAI_ENDPOINT=https://<your-endpoint>.openai.azure.com/
AZURE_OPENAI_API_KEY=YOUR_AZURE_OPENAI_KEY
AZURE_OPENAI_API_VERSION=2025-03-20
AZURE_TTS_DEPLOYMENT=tts

AZURE_SPEECH_KEY=YOUR_AZURE_SPEECH_KEY
AZURE_SPEECH_REGION=eastus
AZURE_SPEECH_VOICE=en-US-JennyNeural
AZURE_SPEECH_FORMAT=audio-24khz-48kbitrate-mono-mp3

# ===== Rate limiting (optional) =====
RATE_LIMIT_REDIS_URL=               # e.g., redis://redis:6379/0
RATE_LIMIT_TTS=60/hour
RATE_LIMIT_ANSWER=30/minute

# ===== Misc =====
TOKENIZERS_PARALLELISM=false
PORT=8080


Quickstart with Docker (recommended)

Build the image

# from repo root
docker build --no-cache --platform linux/amd64 \
  -f round2_backend/Dockerfile \
  -t prism-docintel .


Run the container (no Redis)

docker run --rm -p 8080:8080 \
  --env-file round2_backend/.env \
  prism-docintel


Smoke test

curl -s http://localhost:8080/health


Open http://localhost:8080
 to load the SPA.

 Local development (no Docker)

Backend

cd round2_backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload


Frontend

cd round2_frontend/adobeMain
npm ci
npm run dev


The SPA runs on http://localhost:5173; ensure CORS for calls to http://localhost:8080.

For prod: npm run build then serve via FastAPI (Dockerfile already copies dist/ → /app/static).

Common gotchas

RuntimeError: Directory '/app/static' does not exist
Ensure Vite built output exists and Dockerfile copies /fe/dist/ → /app/static/.
Quick check:

docker run --rm --entrypoint sh prism-docintel -c "ls -la /app/static | head"


Import path errors (src.extract)
We moved src under app/engines/r1a/src and use relative import:

from .src.extract import Span, extract_spans


Ensure __init__.py files are present.

Redis URL
In Docker networking, use service name (e.g., redis) not localhost.

Port already used
lsof -i :8080 on macOS, kill or switch ports.

Apple Silicon
Keep --platform linux/amd64 for parity with Linux servers.

Handy commands
# Rebuild clean
docker build --no-cache --platform linux/amd64 \
  -f round2_backend/Dockerfile -t prism-docintel .

# Run attached
docker run --rm -p 8080:8080 --env-file round2_backend/.env prism-docintel

# Shell inside image
docker run -it --rm --entrypoint sh prism-docintel

# List static assets
docker run --rm --entrypoint sh prism-docintel -c "ls -la /app/static | head -20"

# Health check
curl -s http://localhost:8080/health

Security & repo hygiene

Never commit real .env; keep a sanitized .env.example.

.gitignore ignores:

.env, .env.*, **/.env*

.venv/, venv/, env/

node_modules/, dist/, caches, editor files

For Docker builds, use .dockerignore to keep secrets/large folders out of context.

If secrets ever got staged:

git reset
git rm -r --cached **/.env .env .venv venv env
git commit -m "Remove tracked env/venv"
git push
# Rotate exposed keys immediately.

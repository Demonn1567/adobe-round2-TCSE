# Prism DocIntel (Adobe Round-2)

**A Dockerized FastAPI + Vite/React app for document intelligence: ingest → OCR/parse → sectionize → index → answer with an LLM → (optional) TTS. Frontend is built once and served statically by the backend.**

## 🚀 Special Deep + Narrate Mode: Smart + Deep + Narrate

**Smart**: Grounds answers in the exact passages from your PDFs for precise, cited responses you can trust.

**Deep**: Widens the context to fuse evidence across multiple documents when a question requires more complex reasoning.

**Narrate**: Converts these grounded insights into a concise, neural-voice audio clip for rapid consumption.

*This trio balances precision, breadth, and speed without sacrificing trust.*

---

## Table of Contents
- [Architecture & Approach](#architecture--approach)
- [Repo Layout](#repo-layout)
- [Environment Variables](#environment-variables)
- [Quickstart with Docker (Recommended)](#quickstart-with-docker-recommended)
- [Run with Redis Rate-Limiting](#run-with-redis-rate-limiting)
- [Local Development (No Docker)](#local-development-no-docker)
- [Common Gotchas](#common-gotchas)
- [Handy Commands](#handy-commands)
- [Security & Repo Hygiene](#security--repo-hygiene)
- [License](#license)

---

## Architecture & Approach

### High-Level Flow

1. **Ingest** (FastAPI `routers/upload.py` → `services/ingest.py`):
   - Accept files/URLs
   - OCR via Tesseract where needed + lightweight parsing

2. **Sectionize** (engine **r1a**):
   - `engines/r1a/sectionizer.py` uses `Span`/`extract_spans` (now under `engines/r1a/src`) to split content into titled sections with offsets/metadata

3. **Index** (`services/indexer.py`):
   - Builds a compact store (IDs → sections, + embeddings/keywords if enabled)

4. **Answer** (`routers/answer*.py`):
   - Retrieve relevant sections → craft prompt → call **LLM** (Gemini by default)
   - (Optional) **TTS** via Azure Speech for spoken answers

5. **Frontend** (Vite/React):
   - Built to `dist/`, copied into `/app/static`, served by FastAPI at `/`

6. **Rate Limiting** (optional):
   - Redis-backed limits per route (e.g., `RATE_LIMIT_TTS`, `RATE_LIMIT_ANSWER`)

### Why This Design

- **Single container deploy**: backend serves the SPA → fewer moving parts
- **Modular engines**: easy to swap `r1a/r1b` or extend pipelines
- **Provider-agnostic LLM**: env flags switch providers/models
- **Lean image**: Python slim + only needed OS deps (tesseract, libgl, glib)

---

## Repo Layout

```
ADOBE_ROUND2/
├─ Challenge_1a/
├─ Challenge_1b/
├─ round2_backend/
│  ├─ app/
│  │  ├─ engines/
│  │  │  └─ r1a/
│  │  │     ├─ sectionizer.py
│  │  │     └─ src/                    # Span/extract_spans here (with __init__.py)
│  │  ├─ middleware/
│  │  ├─ routers/                      # health, upload, status, answer, answer_smart
│  │  ├─ schemas/
│  │  ├─ services/                     # ingest, indexer, etc.
│  │  ├─ utils/
│  │  └─ main.py
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ .gitignore
├─ round2_frontend/adobeMain/          # Vite/React app (builds to dist/)
├─ .gitignore
└─ README.md
```

> **Static serving:** FastAPI mounts `/app/static`; Dockerfile copies Vite `dist/` → `/app/static/`.

---

## Environment Variables

Create `round2_backend/.env` (**do not commit real secrets**). Example:

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
RATE_LIMIT_REDIS_URL=                  # e.g., redis://redis:6379/0
RATE_LIMIT_TTS=60/hour
RATE_LIMIT_ANSWER=30/minute

# ===== Misc =====
TOKENIZERS_PARALLELISM=false
PORT=8080
```

---

## Quickstart with Docker (Recommended)

### Build the Image

```bash
# From repo root
docker build --no-cache --platform linux/amd64 \
  -f round2_backend/Dockerfile \
  -t prism-docintel .
```

### Run the Container (No Redis)

```bash
docker run --rm -p 8080:8080 \
  --env-file round2_backend/.env \
  prism-docintel
```

### Smoke Test

```bash
curl -s http://localhost:8080/health
```

Open **http://localhost:8080** to load the SPA.

### Quick Start (No .env File)

If you want to run directly without creating a `.env` file, use this command with inline environment variables:

```bash
docker run --rm -p 8080:8080 \
  -e LLM_PROVIDER=gemini \
  -e GEMINI_MODEL=gemini-2.5-flash \
  -e GEMINI_API_KEY=your_gemini_api_key_here \
  -e AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/ \
  -e AZURE_OPENAI_API_KEY=your_azure_openai_key_here \
  -e AZURE_OPENAI_API_VERSION=2025-03-20 \
  -e AZURE_TTS_DEPLOYMENT=tts \
  -e AZURE_SPEECH_KEY=your_azure_speech_key_here \
  -e AZURE_SPEECH_REGION=eastus \
  -e AZURE_SPEECH_VOICE=en-US-JennyNeural \
  -e AZURE_SPEECH_FORMAT=audio-24khz-48kbitrate-mono-mp3 \
  -e RATE_LIMIT_REDIS_URL=redis://localhost:6379/0 \
  -e RATE_LIMIT_TTS=60/hour \
  -e RATE_LIMIT_ANSWER=30/minute \
  -e TOKENIZERS_PARALLELISM=false \
  prism-docintel
```

> **Note**: Replace the placeholder API keys with your actual credentials.

---

## Run with Redis Rate-Limiting

### Docker Compose Example

```yaml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: round2_backend/Dockerfile
    ports:
      - "8080:8080"
    env_file:
      - round2_backend/.env
    depends_on:
      - redis
    environment:
      - RATE_LIMIT_REDIS_URL=redis://redis:6379/0

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## Local Development (No Docker)

### Backend

```bash
cd round2_backend
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Frontend

```bash
cd round2_frontend/adobeMain
npm ci
npm run dev
```

The SPA runs on **http://localhost:5173**; ensure CORS for calls to **http://localhost:8080**.

For production: `npm run build` then serve via FastAPI (Dockerfile already copies `dist/` → `/app/static`).

---

## Common Gotchas

### `RuntimeError: Directory '/app/static' does not exist`
Ensure Vite built output exists and Dockerfile copies `/fe/dist/` → `/app/static/`.

**Quick check:**
```bash
docker run --rm --entrypoint sh prism-docintel -c "ls -la /app/static | head"
```

### Import Path Errors (`src.extract`)
We moved `src` under `app/engines/r1a/src` and use relative import:

```python
from .src.extract import Span, extract_spans
```

Ensure `__init__.py` files are present.

### Redis URL
In Docker networking, use service name (e.g., `redis`) not `localhost`.

### Port Already Used
- macOS: `lsof -i :8080`
- Kill process or switch ports

### Apple Silicon
Keep `--platform linux/amd64` for parity with Linux servers.

---

## Handy Commands

```bash
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
```

---

## Security & Repo Hygiene

- **Never commit real `.env`**; keep a sanitized `.env.example`
- `.gitignore` ignores:
  - `.env`, `.env.*`, `**/.env*`
  - `.venv/`, `venv/`, `env/`
  - `node_modules/`, `dist/`, caches, editor files
- For Docker builds, use `.dockerignore` to keep secrets/large folders out of context

### If Secrets Ever Got Staged

```bash
git reset
git rm -r --cached **/.env .env .venv venv env
git commit -m "Remove tracked env/venv"
git push
# Rotate exposed keys immediately
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Support

If you encounter any issues or have questions, please:
1. Check the [Common Gotchas](#common-gotchas) section
2. Search existing issues
3. Create a new issue with detailed information about your problem

---

**Built with ❤️ for Adobe Round-2 Challenge**

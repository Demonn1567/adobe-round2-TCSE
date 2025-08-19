from __future__ import annotations
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import health, upload, status, answer_smart, answer
from app.routers import tts as tts_router
from app.routers import related as related_router
from app.routers import insights as insights_router
from app.routers import blocklist as blocklist_router 

from app.utils.ratelimit import limiter, ENABLED as RL_ENABLED
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.middleware.max_body import MaxBodyLimitMiddleware
from starlette.staticfiles import StaticFiles  

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="Document Intelligence Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if RL_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

_max_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
app.add_middleware(
    MaxBodyLimitMiddleware,
    max_body_size=_max_mb * 1024 * 1024,
    paths_prefixes=["/api/upload"],
)

app.include_router(health.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(answer_smart.router, prefix="/api")
app.include_router(tts_router.router, prefix="/api")
app.include_router(answer.router)
app.include_router(related_router.router, prefix="/api/answer")
app.include_router(insights_router.router, prefix="/api/answer")
app.include_router(blocklist_router.router, prefix="/api")  # /api/admin/blocklist/*

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    print(f"[BOOT] Static dir not found at {STATIC_DIR}; skipping static mount")

@app.get("/")
def root():
    return {"ok": True, "service": "doc-intel-backend"}

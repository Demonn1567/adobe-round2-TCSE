import os
import uuid
from pathlib import Path
import requests

from app.utils.config import DATA_DIR

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
DEPLOYMENT = os.getenv("AZURE_TTS_DEPLOYMENT", "tts")

DEFAULT_VOICE = os.getenv("AZURE_TTS_VOICE", "alloy")
DEFAULT_FORMAT = os.getenv("AZURE_TTS_FORMAT", "mp3")  

OUT_DIR = DATA_DIR / "tts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_TTS_VOICES = {"alloy"}

def _sanitize_voice(voice: str | None) -> str:
    v = (voice or DEFAULT_VOICE).strip()
    if "-" in v and v.lower() != "alloy":
        return DEFAULT_VOICE
    return v if v in OPENAI_TTS_VOICES else DEFAULT_VOICE

def _sanitize_format(fmt: str | None) -> str:
    f = (fmt or DEFAULT_FORMAT).lower()
    return f if f in {"mp3", "wav", "ogg", "webm"} else "mp3"

def synthesize_and_store(text: str, voice: str | None = None, output_format: str | None = None):
    if not ENDPOINT or not API_KEY:
        raise RuntimeError("Azure OpenAI credentials are missing.")

    v = _sanitize_voice(voice)
    fmt = _sanitize_format(output_format)

    url = f"{ENDPOINT}/openai/deployments/{DEPLOYMENT}/audio/speech?api-version={API_VERSION}"
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "input": text,
        "voice": v,
        "format": fmt, 
    }

    resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=90)
    try:
        resp.raise_for_status()
    except Exception:
        raise RuntimeError(f"OpenAI TTS failed: {resp.status_code} {resp.text[:300]}")

    audio_id = str(uuid.uuid4())
    out_path = OUT_DIR / f"{audio_id}.{fmt}"
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)

    return {
        "audioId": audio_id,
        "url": f"/api/tts/file/{out_path.name}",
        "voice": v,
        "format": fmt,
    }

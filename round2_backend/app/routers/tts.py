import os
import uuid
from typing import Optional, List, Dict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.utils.config import DATA_DIR
from app.utils.ratelimit import limiter

_AZURE_OAI_OK = False
_client_azure_oai = None
try:
    from openai import AzureOpenAI 
    _AZURE_OAI_ENDPOINT = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
    _AZURE_OAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    _AZURE_OAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-07-01-preview")
    _AZURE_TTS_DEPLOYMENT = os.getenv("AZURE_TTS_DEPLOYMENT") 

    if _AZURE_OAI_ENDPOINT and _AZURE_OAI_API_KEY and _AZURE_TTS_DEPLOYMENT:
        _client_azure_oai = AzureOpenAI(
            azure_endpoint=_AZURE_OAI_ENDPOINT,
            api_key=_AZURE_OAI_API_KEY,
            api_version=_AZURE_OAI_API_VERSION,
        )
        _AZURE_OAI_OK = True
except Exception:
    _AZURE_OAI_OK = False
    _client_azure_oai = None

_TTS_SDK = None
_TTS_HTTP = None
try:
    from app.services.tts_service import synthesize_and_store as _synthesize_sdk  
    _TTS_SDK = _synthesize_sdk
except Exception:
    _TTS_SDK = None

try:
    from app.services.tts import synthesize as _synthesize_http  
    _TTS_HTTP = _synthesize_http
except Exception:
    _TTS_HTTP = None

try:
    from app.services.voices import list_voices as _list_voices_speech
except Exception:
    def _list_voices_speech(*_, **__):
        return []

def _fetch_speech_voices_via_rest() -> List[Dict]:
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    if not key or not region:
        return []
    try:
        import httpx
        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
        r = httpx.get(url, headers={"Ocp-Apim-Subscription-Key": key}, timeout=15.0)
        r.raise_for_status()
        voices = []
        for v in r.json():
            short = v.get("ShortName") or v.get("DisplayName") or v.get("Name")
            name = v.get("DisplayName") or short
            loc = v.get("Locale") or v.get("LocaleName") or "en-US"
            if short:
                voices.append({"shortName": short, "name": name, "locale": loc})
        return voices
    except Exception:
        return []

router = APIRouter(tags=["tts"])

_AUDIO_DIR = DATA_DIR / "audio"
_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class SpeakReq(BaseModel):
    text: str
    voice: Optional[str] = None
    format: Optional[str] = None  


def _find_audio_file(filename: str) -> Path:
    p = _AUDIO_DIR / filename
    if p.exists():
        return p
    for ext in (".mp3", ".ogg", ".wav", ".webm"):
        q = _AUDIO_DIR / f"{filename}{ext}"
        if q.exists():
            return q
    raise FileNotFoundError(filename)

def _short_format(fmt: Optional[str]) -> str:
    if not fmt:
        fmt = os.getenv("AZURE_TTS_FORMAT", "audio/mp3")
    f = (fmt or "").lower().strip()
    if f.startswith("audio/"):
        f = f.split("/", 1)[1]
    return f if f in {"mp3", "ogg", "wav"} else "mp3"

def _ext_for(fmt_short: str) -> str:
    return ".mp3" if fmt_short == "mp3" else (".ogg" if fmt_short == "ogg" else ".wav")

def _default_openai_voice(override: Optional[str]) -> str:
    return (override or os.getenv("AZURE_TTS_VOICE") or "alloy").strip()

def _openai_voices_list() -> List[Dict]:
    names = ["alloy", "aria", "verse", "luna", "cove", "juniper"]
    return [{"shortName": n, "name": n, "locale": "en-US"} for n in names]


def _synthesize_openai_tts(text: str, voice: Optional[str], fmt: Optional[str]) -> Dict:
    if not _AZURE_OAI_OK or not _client_azure_oai:
        raise RuntimeError("Azure OpenAI TTS not configured.")

    dep = _AZURE_TTS_DEPLOYMENT
    if not dep:
        raise RuntimeError("AZURE_TTS_DEPLOYMENT is not set.")

    voice_to_use = _default_openai_voice(voice)
    fmt_short = _short_format(fmt)
    ext = _ext_for(fmt_short)

    audio_id = uuid.uuid4().hex
    out_path = _AUDIO_DIR / f"{audio_id}{ext}"

    try:
        result = _client_azure_oai.audio.speech.create(
            model=dep, voice=voice_to_use, input=text, format=fmt_short
        )
    except TypeError:
        result = _client_azure_oai.audio.speech.create(
            model=dep, voice=voice_to_use, input=text, response_format=fmt_short
        )

    data = result.read() if hasattr(result, "read") else (result or b"")
    if not data:
        raise RuntimeError("Azure OpenAI TTS returned empty audio.")

    with open(out_path, "wb") as f:
        f.write(data)

    return {"audioId": audio_id, "url": f"/api/tts/file/{out_path.name}", "voice": voice_to_use, "format": f"audio/{fmt_short}"}


@router.post("/tts/speak")
@limiter.limit(os.getenv("RATE_LIMIT_TTS", "60/hour"))
async def post_tts_speak(request: Request, req: SpeakReq):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    if _AZURE_OAI_OK:
        try:
            return _synthesize_openai_tts(text=text, voice=req.voice, fmt=req.format)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Azure OpenAI TTS failed: {e}")

    if _TTS_SDK:
        try:
            return _TTS_SDK(text=text, voice=req.voice, output_format=req.format)
        except Exception:
            pass

    if not _TTS_HTTP:
        raise HTTPException(status_code=503, detail="No TTS engine available (Azure OpenAI/SDK/HTTP).")

    used_voice = req.voice or os.getenv("AZURE_SPEECH_VOICE", "en-US-JennyNeural")
    used_fmt = req.format or os.getenv("AZURE_SPEECH_FORMAT", "audio-24khz-48kbitrate-mono-mp3")
    try:
        audio_id, out_path = _TTS_HTTP(text=text, voice=used_voice, fmt=used_fmt)
        return {"audioId": audio_id, "url": f"/api/tts/file/{out_path.name}", "voice": used_voice, "format": used_fmt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS fallback failed: {e}")

@router.get("/tts/file/{filename}")
def get_tts_file(filename: str):
    try:
        p = _find_audio_file(filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(path=p, filename=p.name)

@router.get("/tts/status")
def get_tts_status():
    return {
        "openaiConfigured": _AZURE_OAI_OK,
        "endpoint": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
        "deployment": bool(os.getenv("AZURE_TTS_DEPLOYMENT")),
        "speechConfigured": bool(os.getenv("AZURE_SPEECH_KEY") and os.getenv("AZURE_SPEECH_REGION")),
    }

@router.get("/tts/voices")
@limiter.limit(os.getenv("RATE_LIMIT_TTS_VOICES", "120/hour"))
async def get_tts_voices(
    request: Request,
    locale: Optional[str] = Query(None),
    contains: Optional[str] = Query(None),
    prefer: Optional[str] = Query("openai", description="'openai' | 'speech' | 'auto'"),
):

    prefer = (prefer or "openai").lower()

    def filt(vlist: List[Dict]) -> List[Dict]:
        out = vlist
        if locale:
            out = [v for v in out if (v.get("locale") or "").lower().startswith(locale.lower())]
        if contains:
            c = contains.lower()
            out = [v for v in out if c in (v.get("shortName","") + v.get("name","")).lower()]
        return out

    if prefer == "openai":
        if not _AZURE_OAI_OK:
            raise HTTPException(status_code=503, detail="Azure OpenAI TTS not configured.")
        voices = filt(_openai_voices_list())
        default_voice = os.getenv("AZURE_TTS_VOICE", "alloy")
        return {"voices": voices, "provider": "openai", "default": default_voice}

    if prefer == "speech":
        voices = filt(_list_voices_speech(locale=locale, contains=contains) or _fetch_speech_voices_via_rest())
        if not voices:
            raise HTTPException(status_code=503, detail="No Speech voices available.")
        default_voice = os.getenv("AZURE_SPEECH_VOICE", "en-US-JennyNeural")
        return {"voices": voices, "provider": "speech", "default": default_voice}

    if _AZURE_OAI_OK:
        voices = filt(_openai_voices_list())
        default_voice = os.getenv("AZURE_TTS_VOICE", "alloy")
        return {"voices": voices, "provider": "openai", "default": default_voice}
    voices = filt(_list_voices_speech(locale=locale, contains=contains) or _fetch_speech_voices_via_rest())
    if not voices:
        raise HTTPException(status_code=503, detail="No voices available.")
    default_voice = os.getenv("AZURE_SPEECH_VOICE", "en-US-JennyNeural")
    return {"voices": voices, "provider": "speech", "default": default_voice}

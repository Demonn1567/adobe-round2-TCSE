import os
import uuid
import html
import re
from pathlib import Path
from typing import Optional, Tuple

from app.utils.config import DATA_DIR

_AUDIO_DIR = DATA_DIR / "audio"
_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


_SPEECH_KEY = (
    os.getenv("AZURE_TTS_KEY")       
    or os.getenv("AZURE_SPEECH_KEY")    
)

_SPEECH_ENDPOINT = os.getenv("AZURE_TTS_ENDPOINT")  
_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")  



_OPENAI_READY = False
_OPENAI_CLIENT = None
_OPENAI_DEPLOYMENT = os.getenv("AZURE_TTS_DEPLOYMENT") 
_OPENAI_ENDPOINT = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-07-01-preview")

try:
    if _OPENAI_ENDPOINT and _OPENAI_KEY and _OPENAI_DEPLOYMENT:
        from openai import AzureOpenAI 
        _OPENAI_CLIENT = AzureOpenAI(
            azure_endpoint=_OPENAI_ENDPOINT,
            api_key=_OPENAI_KEY,
            api_version=_OPENAI_API_VERSION,
        )
        _OPENAI_READY = True
except Exception:
    _OPENAI_READY = False
    _OPENAI_CLIENT = None

_OPENAI_VOICES = {"alloy", "aria", "verse", "luna", "cove", "juniper"}

def _looks_like_openai_voice(v: Optional[str]) -> bool:
    if not v:
        return True  
    v = v.strip()
    return (v.lower() in _OPENAI_VOICES) and ("-" not in v)

def _is_speech_voice(v: Optional[str]) -> bool:
    if not v:
        return False
    return bool(re.match(r"^[a-z]{2}-[A-Z]{2}-", v)) or "Neural" in v

def _openai_format(fmt: Optional[str]) -> str:
    f = (fmt or os.getenv("AZURE_TTS_FORMAT") or "mp3").lower().strip()
    if f.startswith("audio/"):
        f = f.split("/", 1)[1]
    return f if f in {"mp3", "ogg", "wav"} else "mp3"

def _ext_for(fmt_short: str) -> str:
    return ".mp3" if fmt_short == "mp3" else (".ogg" if fmt_short == "ogg" else ".wav")

def _synthesize_openai(text: str, voice: Optional[str], fmt: Optional[str]) -> Tuple[str, Path, str]:
    if not _OPENAI_READY or not _OPENAI_CLIENT:
        raise RuntimeError("Azure OpenAI TTS not configured.")

    voice_to_use = (voice or os.getenv("AZURE_TTS_VOICE") or "alloy").strip()
    fmt_short = _openai_format(fmt)
    ext = _ext_for(fmt_short)

    audio_id = uuid.uuid4().hex
    out_path = _AUDIO_DIR / f"{audio_id}{ext}"

    try:
        result = _OPENAI_CLIENT.audio.speech.create(
            model=_OPENAI_DEPLOYMENT,
            voice=voice_to_use,
            input=text,
            format=fmt_short,
        )
    except TypeError:
        result = _OPENAI_CLIENT.audio.speech.create(
            model=_OPENAI_DEPLOYMENT,
            voice=voice_to_use,
            input=text,
            response_format=fmt_short,
        )

    blob = result.read() if hasattr(result, "read") else (result or b"")
    if not blob:
        raise RuntimeError("Azure OpenAI TTS returned empty audio.")

    with open(out_path, "wb") as f:
        f.write(blob)

    return audio_id, out_path, voice_to_use


_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
_SPEECH_DEFAULT_VOICE = os.getenv("AZURE_SPEECH_VOICE", "en-US-JennyNeural")

def _speech_format(fmt: Optional[str]) -> str:
    if not fmt:
        return os.getenv("AZURE_SPEECH_FORMAT", "audio-24khz-48kbitrate-mono-mp3")

    f = fmt.strip().lower()
    if f in {"mp3", "ogg", "wav"}:
        if f == "mp3":
            return "audio-24khz-48kbitrate-mono-mp3"
        if f == "ogg":
            return "ogg-48khz-16bit-mono-opus"
        return "riff-24khz-16bit-mono-pcm"  
    return fmt 

def _ssml_escape(text: str) -> str:
    s = " ".join(text.split())  
    s = html.escape(s, quote=True)  
    s = s.replace("'", "&apos;")
    return s

def _synthesize_speech(text: str, voice: Optional[str], fmt: Optional[str]) -> Tuple[str, Path, str]:
    if not _SPEECH_KEY or not _SPEECH_REGION:
        raise RuntimeError("Azure Speech credentials are not configured.")

    import httpx

    voice_name = voice if _is_speech_voice(voice) else _SPEECH_DEFAULT_VOICE
    output_format = _speech_format(fmt)

    ext = ".mp3" if "mp3" in output_format else (".wav" if ("pcm" in output_format or "wav" in output_format) else ".ogg")

    audio_id = uuid.uuid4().hex
    out_path = _AUDIO_DIR / f"{audio_id}{ext}"

    safe_text = _ssml_escape(text)
    ssml = f"""<speak version='1.0' xml:lang='en-US'>
  <voice name="{voice_name}">{safe_text}</voice>
</speak>""".encode("utf-8")

    url = f"https://{_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": _SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": output_format,
        "User-Agent": "prism-doc-intel",
    }

    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, headers=headers, content=ssml)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)

    return audio_id, out_path, voice_name


def synthesize(text: str, voice: Optional[str] = None, fmt: Optional[str] = None) -> Tuple[str, Path, str]:
 
    text = (text or "").strip()
    if not text:
        raise ValueError("Text must not be empty.")

    if _looks_like_openai_voice(voice) and _OPENAI_READY:
        try:
            return _synthesize_openai(text, voice, fmt)
        except Exception:
            pass

    return _synthesize_speech(text, voice, fmt)

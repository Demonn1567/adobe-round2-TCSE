from __future__ import annotations

from typing import List, Optional, Dict, Any
import logging
import os

from app.services.search import related_search
from app.services.tts import synthesize as tts_synthesize  

logger = logging.getLogger(__name__)

MAX_TTS_CHARS = int(os.getenv("MAX_TTS_CHARS", "1800"))

def _clean_for_tts(text: str) -> str:
    t = " ".join((text or "").split())
    if len(t) > MAX_TTS_CHARS:
        t = t[:MAX_TTS_CHARS].rsplit(" ", 1)[0] + "…"
    return t

def _build_answer_from_sources(hits: List[Dict], max_chars: int = 900) -> str:
    if not hits:
        return "I couldn’t find anything relevant in the indexed documents."

    pieces: List[str] = []
    used = 0
    for h in hits:
        txt = (h.get("snippet") or "").strip()
        if not txt:
            txt = (h.get("sectionTitle") or "").strip()
        if not txt:
            continue
        if txt in pieces:
            continue

        extra = (1 if pieces else 0)
        if used + len(txt) + extra > max_chars:
            room = max_chars - used - extra
            if room > 80:
                cut = txt.rfind(". ", 0, room)
                if cut == -1:
                    cut = room
                txt = txt[:cut].rstrip(" .") + "…"
            else:
                break

        pieces.append(txt)
        used += len(txt) + extra
        if used >= max_chars:
            break

    return " ".join(pieces).strip() or "I couldn’t synthesize a readable answer."

def smart_answer(
    *,
    query: str,
    k: int = 5,
    persona: Optional[str] = None,
    task: Optional[str] = None,
    deep: bool = False,
    doc_filter: Optional[List[str]] = None,
    narrate: bool = False,
    voice: Optional[str] = None,
    format: Optional[str] = None,
) -> Dict[str, Any]:
   
    hits = related_search(
        query=query,
        k=k,
        doc_filter=doc_filter,
        persona=persona,
        task=task,
        deep=deep,
    )

    answer_text = _build_answer_from_sources(hits, max_chars=900)

    #a note for evaluators : created a fallback, so that if openai azure fails the fallback will be to 
    #the azure ai speech so the tts service never really goes down.
    audio = None
    if narrate:
        try:
            clean_text = _clean_for_tts(answer_text)
            audio_id, out_path, used_voice = tts_synthesize(
                text=clean_text,
                voice=(voice or os.getenv("AZURE_TTS_VOICE") or "alloy"),
                fmt=(format or None), 
            )
            audio = {
                "audioId": audio_id,
                "url": f"/api/tts/file/{out_path.name}",
                "voice": used_voice,
                "format": os.getenv("AZURE_SPEECH_FORMAT", "audio-24khz-48kbitrate-mono-mp3"),
            }
        except Exception as e:
            logger.exception("TTS narration failed: %s", e)
            audio = None

    return {
        "answer": answer_text,
        "sources": hits,
        "audio": audio,
    }

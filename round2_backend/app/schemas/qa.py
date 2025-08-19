from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, AliasChoices



class AnswerSource(BaseModel):
    docId: str
    docTitle: str
    docOrigName: str | None = None
    sectionId: str
    sectionTitle: str
    page: Optional[int] = None
    y: Optional[float] = None
    score: Optional[float] = None
    snippet: Optional[str] = None
    why: Optional[Dict[str, Any]] = None
    whyDeep: Optional[Dict[str, Any]] = None
    domain: Optional[str] = None


class AudioMeta(BaseModel):
    audioId: str
    url: str
    voice: Optional[str] = None
    format: Optional[str] = None



class AnswerSmartRequest(BaseModel):
    query: str
    k: int = 5
    persona: Optional[str] = None
    task: Optional[str] = None
    deep: bool = False
    docIds: Optional[List[str]] = None


    narrate: bool = Field(
        default=False,
        validation_alias=AliasChoices("tts", "narrate"),
        serialization_alias="tts",
    )

    voice: Optional[str] = None
    format: Optional[str] = None

    class Config:
        populate_by_name = True
        extra = "ignore"


class AnswerSmartResponse(BaseModel):
    answer: str
    sources: List[AnswerSource]
    audio: Optional[AudioMeta] = None

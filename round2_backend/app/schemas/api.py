from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class UploadFreshResponse(BaseModel):
    jobIds: List[str]
    docId: str

class UploadedFileInfo(BaseModel):
    filename: str
    docId: Optional[str] = None
    pages: Optional[int] = None
    bytes: Optional[int] = None
    skippedReason: Optional[str] = None

class UploadResponse(BaseModel):
    jobIds: List[str]
    accepted: Optional[int] = None
    skipped: Optional[int] = None
    files: Optional[List[UploadedFileInfo]] = None
    message: Optional[str] = None


class JobStatus(BaseModel):
    jobId: str
    state: str                     
    docId: Optional[str] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    jobs: List[JobStatus]


class RelatedRequest(BaseModel):
    query: str
    k: int = 5
    docIds: Optional[List[str]] = None

    persona: Optional[str] = None
    task: Optional[str] = None
    deep: bool = False


class RelatedHit(BaseModel):
    docId: str
    docTitle: str = ""
    docOrigName: str = ""
    sectionId: str
    sectionTitle: str = ""
    page: int = 1
    y: float = 0.0
    score: float = 0.0
    snippet: str = ""

    why: Optional[Dict[str, Any]] = None
    whyDeep: Optional[Dict[str, Any]] = None
    domain: Optional[str] = None


class RelatedResponse(BaseModel):
    hits: List[RelatedHit]




class TtsAudio(BaseModel):
    audioId: str
    url: str        
    voice: str
    format: str       


class TtsSpeakRequest(BaseModel):
    text: str
    voice: Optional[str] = None      
    format: Optional[str] = None    


class TtsSpeakResponse(TtsAudio):
    pass




class AnswerSource(BaseModel):
    docId: str
    docTitle: str = ""
    docOrigName: str = ""
    sectionId: str
    sectionTitle: str = ""
    page: int = 1
    y: float = 0.0
    score: float = 0.0
    snippet: str = ""


class AnswerSmartRequest(BaseModel):
    query: str
    k: int = 5

    persona: Optional[str] = None
    task: Optional[str] = None
    deep: bool = False

    tts: bool = False
    voice: Optional[str] = None
    format: Optional[str] = None


class AnswerSmartResponse(BaseModel):
    answer: str
    sources: List[AnswerSource]
    audio: Optional[TtsAudio] = None

class AudioMeta(BaseModel):
    audioId: str
    url: str
    voice: str
    format: str

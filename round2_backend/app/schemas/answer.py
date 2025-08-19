from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    query: str = Field(..., description="User question")
    k: int = Field(5, ge=1, le=10, description="How many sections to retrieve")
    persona: Optional[str] = Field(None, description="Persona description")
    task: Optional[str] = Field(None, description="Job-to-be-done / task")
    deep: bool = Field(False, description="Use deep persona rerank (1B heuristics)")
    docIds: Optional[List[str]] = Field(None, description="Restrict search to these docIds")


class AnswerSource(BaseModel):
    docId: str
    docTitle: str
    docOrigName: str
    sectionId: str
    sectionTitle: str
    page: int
    y: float
    score: float


class AnswerResponse(BaseModel):
    answer: str
    sources: List[AnswerSource]

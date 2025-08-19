from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.schemas.api import (
    AnswerSmartRequest,
    AnswerSmartResponse,
)
from app.services.answer import smart_answer

router = APIRouter(prefix="/api/answer", tags=["answer"])


@router.post("/smart", response_model=AnswerSmartResponse)
def post_answer_smart(req: AnswerSmartRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    payload = smart_answer(
        query=req.query,
        k=req.k,
        persona=req.persona,
        task=req.task,
        deep=req.deep,
        do_tts=req.tts,
        voice=req.voice,
        fmt=req.format,
    )
    return AnswerSmartResponse(**payload)

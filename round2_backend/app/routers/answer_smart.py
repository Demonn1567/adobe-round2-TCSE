import os
from fastapi import APIRouter, HTTPException, Request
from app.schemas.qa import AnswerSmartRequest, AnswerSmartResponse
from app.services.answer import smart_answer
from app.utils.ratelimit import limiter

router = APIRouter(tags=["answer"])

@router.post("/answer/smart", response_model=AnswerSmartResponse)
@limiter.limit(os.getenv("RATE_LIMIT_ANSWER", "30/minute"))
async def post_answer_smart(request: Request, req: AnswerSmartRequest):  
    if not (req.query or "").strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    out = smart_answer(
        query=req.query,
        k=req.k,
        persona=req.persona,
        task=req.task,
        deep=req.deep,
        doc_filter=req.docIds,   
        narrate=req.narrate,     
        voice=req.voice,
        format=req.format,
    )
    return AnswerSmartResponse(**out)

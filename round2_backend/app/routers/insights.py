from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.answer import smart_answer

router = APIRouter(tags=["insights"])

class InsightSource(BaseModel):
    docId: Optional[str] = None
    docOrigName: Optional[str] = None
    docTitle: Optional[str] = None
    sectionId: Optional[str] = None
    sectionTitle: Optional[str] = None
    page: Optional[int] = None
    y: Optional[float] = None
    score: Optional[float] = None
    snippet: Optional[str] = None

class InsightsReq(BaseModel):
    query: str
    k: int = 5
    deep: bool = True
    docIds: Optional[List[str]] = None  

class InsightsResp(BaseModel):
    answer: str
    sources: List[InsightSource] = []

@router.post("/insights", response_model=InsightsResp)
async def insights(req: InsightsReq):
    q = (req.query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    out = smart_answer(
        query=q,
        k=max(1, req.k),
        deep=req.deep,
        doc_filter=req.docIds,
        task="insights",
        format="bullets", 
    )

    answer = (out.get("answer") or "").strip()
    sources = out.get("sources") or []
    if not answer:
        bullets = []
        for s in sources[: req.k]:
            snip = (s.get("snippet") or "").strip()
            if snip:
                bullets.append(f"• {snip}")
        answer = "💡 Insights\n" + ("\n".join(bullets) if bullets else "No insights found.")

    srcs = [InsightSource(**{
        "docId": s.get("docId"),
        "docOrigName": s.get("docOrigName"),
        "docTitle": s.get("docTitle"),
        "sectionId": s.get("sectionId"),
        "sectionTitle": s.get("sectionTitle"),
        "page": s.get("page"),
        "y": s.get("y"),
        "score": s.get("score"),
        "snippet": s.get("snippet"),
    }) for s in sources]

    return InsightsResp(answer=answer, sources=srcs)

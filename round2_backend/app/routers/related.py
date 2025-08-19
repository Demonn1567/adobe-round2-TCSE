from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.answer import smart_answer

router = APIRouter(tags=["related"])

class RelatedReq(BaseModel):
    query: str
    k: int = 5
    deep: bool = False
    docIds: Optional[List[str]] = None 

class RelatedHit(BaseModel):
    docId: Optional[str] = None
    docOrigName: Optional[str] = None
    docTitle: Optional[str] = None
    sectionId: Optional[str] = None
    sectionTitle: Optional[str] = None
    page: Optional[int] = None
    y: Optional[float] = None   
    score: Optional[float] = None
    snippet: Optional[str] = None

class RelatedResp(BaseModel):
    hits: List[RelatedHit] = []

@router.post("/related", response_model=RelatedResp)
async def related(req: RelatedReq):
    q = (req.query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    out = smart_answer(
        query=q,
        k=max(1, req.k),
        deep=req.deep,
        doc_filter=req.docIds,
        task="search-only",  
        format="none",
    )

    sources = out.get("sources") or []
    hits: List[RelatedHit] = []
    for s in sources[: req.k]:
        hits.append(RelatedHit(
            docId=s.get("docId"),
            docOrigName=s.get("docOrigName"),
            docTitle=s.get("docTitle"),
            sectionId=s.get("sectionId"),
            sectionTitle=s.get("sectionTitle"),
            page=s.get("page"),
            y=s.get("y"),
            score=s.get("score"),
            snippet=s.get("snippet"),
        ))
    return RelatedResp(hits=hits)

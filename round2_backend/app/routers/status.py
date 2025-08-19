from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from app.utils.config import DATA_DIR

router = APIRouter(tags=["status"])

@router.get("/status/{job_id}")
def get_status(job_id: str):
    p = DATA_DIR / "tmp" / f"{job_id}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="job not found")
    return json.loads(p.read_text())

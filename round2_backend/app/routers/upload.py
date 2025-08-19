from __future__ import annotations

from typing import List, Tuple, Any, Dict

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException

from app.schemas.api import UploadFreshResponse
from app.services.ingest import (
    handle_upload,
    handle_upload_many,
    handle_upload_zip,
)

router = APIRouter(tags=["upload"])


def _assert_pdf(filename: str):
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"Only PDF files are accepted: {filename}")


def _normalize_upload_result(res: Any) -> UploadFreshResponse:
    job_ids: List[str] = []
    doc_id: str | None = None

    if isinstance(res, dict):
        if "jobIds" in res and isinstance(res["jobIds"], list) and res["jobIds"]:
            job_ids = [str(j) for j in res["jobIds"]]
        elif "jobId" in res:
            job_ids = [str(res["jobId"])]
        doc_id = res.get("docId")
    elif isinstance(res, (list, tuple)):
        if len(res) >= 1:
            job_ids = [str(res[0])]
        if len(res) >= 2:
            doc_id = str(res[1])

    if not job_ids:
        raise HTTPException(status_code=500, detail="Upload handler returned no job id.")
    if not doc_id:
        raise HTTPException(status_code=500, detail="Upload handler returned no doc id.")

    return UploadFreshResponse(jobIds=job_ids, docId=str(doc_id))


@router.post("/upload/fresh", response_model=UploadFreshResponse)
async def upload_fresh(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    _assert_pdf(file.filename)
    raw = await handle_upload(file, background_tasks)
    return _normalize_upload_result(raw)


@router.post("/upload/bulk", response_model=List[UploadFreshResponse])
async def upload_bulk(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(status_code=400, detail="Provide at least one PDF.")
    for f in files:
        _assert_pdf(f.filename)

    raw_list = await handle_upload_many(files, background_tasks)
    return [_normalize_upload_result(r) for r in raw_list]


@router.post("/upload/zip", response_model=List[UploadFreshResponse])
async def upload_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a .zip file.")
    raw_list = await handle_upload_zip(file, background_tasks)
    return [_normalize_upload_result(r) for r in raw_list]

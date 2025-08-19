from __future__ import annotations
from fastapi import UploadFile, BackgroundTasks
from pathlib import Path
from uuid import uuid4
import json
import zipfile
import shutil
from typing import List, Set, Tuple
import fitz 

from app.utils.config import DATA_DIR, MAX_PDFS_PER_ZIP
from app.services.indexer import index_document  


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(data)

def _write_job(job_id: str, payload: dict) -> None:
    (DATA_DIR / "tmp" / f"{job_id}.json").write_text(json.dumps(payload))

def _is_probably_pdf(data: bytes) -> bool:
    if not data or len(data) < 5:
        return False
    if data[:4] == b"%PDF":
        return True
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        doc.close()
        return True
    except Exception:
        return False


def kickoff_indexing(doc_id: str, pdf_path: Path, job_id: str, orig_name: str | None = None) -> None:
    _write_job(job_id, {"jobId": job_id, "docId": doc_id, "status": "running", "progress": 5})
    try:
        index_document(doc_id, pdf_path, job_id, progress_cb=_write_job, orig_name=orig_name)
        _write_job(job_id, {"jobId": job_id, "docId": doc_id, "status": "done", "progress": 100})
    except Exception as e:
        _write_job(job_id, {"jobId": job_id, "docId": doc_id, "status": "error", "error": str(e), "progress": 0})


async def handle_upload(file: UploadFile, background_tasks: BackgroundTasks) -> dict:
    content = await file.read()
    doc_id = uuid4().hex[:12]
    job_id = uuid4().hex[:12]
    dest = DATA_DIR / "docs" / f"{doc_id}.pdf"
    _write_bytes(dest, content)

    _write_job(job_id, {"jobId": job_id, "docId": doc_id, "status": "queued", "progress": 0})
    background_tasks.add_task(kickoff_indexing, doc_id, dest, job_id, file.filename)
    return {"jobId": job_id, "docId": doc_id}

async def handle_upload_many(files: List[UploadFile], background_tasks: BackgroundTasks) -> List[dict]:
    results: List[dict] = []
    for f in files:
        res = await handle_upload(f, background_tasks)
        results.append(res)
    return results


async def handle_upload_zip(zip_file: UploadFile, background_tasks: BackgroundTasks) -> List[dict]:
    batch_id = uuid4().hex[:8]
    tmp_dir = DATA_DIR / "tmp" / f"zip_{batch_id}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = tmp_dir / "upload.zip"
    with zip_path.open("wb") as out:
        while True:
            chunk = await zip_file.read(2 * 1024 * 1024) 
            if not chunk:
                break
            out.write(chunk)
    await zip_file.close()

    results: List[dict] = []
    seen: Set[Tuple[int, int]] = set()  

    with zipfile.ZipFile(zip_path, "r") as z:
        members = []
        for m in z.infolist():
            name = m.filename
            base = Path(name).name
            if m.is_dir():
                continue
            if "__MACOSX/" in name:
                continue
            if base.startswith("._"):
                continue
            if not base.lower().endswith(".pdf"):
                continue
            members.append(m)

        if not members:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return results

        members = members[: MAX_PDFS_PER_ZIP]

        for m in members:
            sig = (m.CRC, m.file_size)
            if sig in seen:
                continue
            seen.add(sig)

            data = z.read(m)
            if not _is_probably_pdf(data):
                continue

            orig_name = Path(m.filename).name or "file.pdf"
            doc_id = uuid4().hex[:12]
            pdf_dest = DATA_DIR / "docs" / f"{doc_id}.pdf"
            _write_bytes(pdf_dest, data)

            job_id = uuid4().hex[:12]
            _write_job(job_id, {"jobId": job_id, "docId": doc_id, "status": "queued", "progress": 0})
            background_tasks.add_task(kickoff_indexing, doc_id, pdf_dest, job_id, orig_name)
            results.append({"jobId": job_id, "docId": doc_id})

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return results

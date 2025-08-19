from __future__ import annotations
from pathlib import Path
from typing import Callable, List, Dict, Any
import json
import numpy as np
import re
import fitz  

from app.utils.config import DATA_DIR
from app.services.vector_store import VectorStore
from app.services.embeddings import get_model

from app.engines.r1a.sectionizer import sectionize

def _split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", text)
    parts = [s.strip() for s in parts if 25 <= len(s.strip()) <= 600]
    return parts[:400]

def _fallback_page_sections(pdf_path: Path) -> Dict[str, Any]:
    doc = fitz.open(pdf_path)
    title = (doc.metadata or {}).get("title") or pdf_path.stem
    sections = []
    for i, page in enumerate(doc):
        page_num = i + 1
        text = page.get_text("text") or ""
        sec_id = f"{pdf_path.stem}-p{page_num}"
        sections.append({
            "sectionId": sec_id,
            "title": f"Page {page_num}",
            "level": "H2",
            "page": page_num,
            "y": 0.0,
            "text": text
        })
    doc.close()
    return {"title": title, "sections": sections}

def index_document(
    doc_id: str,
    pdf_path: Path,
    job_id: str,
    progress_cb: Callable[[str, dict], None] | None = None,
    orig_name: str | None = None
) -> None:

    try:
        sec_pack = sectionize(pdf_path)
    except Exception as _:
        sec_pack = {"title": "", "sections": []}

    if not sec_pack.get("sections"):
        sec_pack = _fallback_page_sections(pdf_path)

    title = sec_pack.get("title") or pdf_path.stem
    sections = sec_pack["sections"]

    (DATA_DIR / "meta" / f"{doc_id}_sections.json").write_text(json.dumps({
        "docId": doc_id,
        "title": title,
        "origName": orig_name or Path(pdf_path).name,
        "sections": sections
    }, ensure_ascii=False))

    if progress_cb:
        progress_cb(job_id, {"jobId": job_id, "docId": doc_id, "status": "running", "progress": 35})

    sent_records: List[tuple] = []  
    for s in sections:
        sents = _split_sentences(s.get("text", ""))
        for idx, sent in enumerate(sents):
            sent_records.append((s["sectionId"], int(s.get("page", 1)), float(s.get("y", 0.0)), sent))

    (DATA_DIR / "meta" / f"{doc_id}_sentences.json").write_text(json.dumps(
        {"docId": doc_id,
         "sentences": [
             {"sentId": f"s{i}", "sectionId": sid, "page": page, "y": y, "text": sent}
             for i, (sid, page, y, sent) in enumerate(sent_records)
         ]
        }, ensure_ascii=False))

    if progress_cb:
        progress_cb(job_id, {"jobId": job_id, "docId": doc_id, "status": "running", "progress": 60})

    if sent_records:
        model = get_model()
        texts = [x[3] for x in sent_records]
        vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        vecs = np.asarray(vecs, dtype="float32")
    else:
        vecs = np.zeros((0, 384), dtype="float32")
    np.save(DATA_DIR / "vecs" / f"{doc_id}.npy", vecs)

    if progress_cb:
        progress_cb(job_id, {"jobId": job_id, "docId": doc_id, "status": "running", "progress": 80})


    store = VectorStore(DATA_DIR / "index")
    title_by_section = {s["sectionId"]: s.get("title", "") for s in sections}

    mapping = []
    for i, (sid, page, y, _) in enumerate(sent_records):
        mapping.append({
            "docId": doc_id,
            "docTitle": title,
            "docOrigName": orig_name or Path(pdf_path).name,
            "sectionId": sid,
            "sectionTitle": title_by_section.get(sid, ""),
            "sentIdx": i,
            "page": page,
            "y": y,
        })
    store.add(vecs, mapping)

    if progress_cb:
        progress_cb(job_id, {"jobId": job_id, "docId": doc_id, "status": "running", "progress": 95})

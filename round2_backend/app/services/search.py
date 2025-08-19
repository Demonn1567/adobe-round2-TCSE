from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from functools import lru_cache
from collections import defaultdict
import json
import re
import os  

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from app.utils.config import DATA_DIR
from app.services.embeddings import get_model
from app.engines.r1b.rerank import apply_persona_reweight
from app.engines.r1b.deep import deep_persona_reweight 

INDEX_DIR = DATA_DIR / "index"
_BLOCKLIST_PATH = DATA_DIR / "blocklist.json"  

_RE_WORD = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")

STOP = {
    "the","a","an","and","or","of","to","in","on","for","with","by","from","at",
    "is","are","be","was","were","that","this","it","as","into","over","across",
    "about","we","you","your","our","their","not"
}

def _tok(s: str) -> List[str]:
    return [w for w in (w.lower() for w in _RE_WORD.findall(s or "")) if w not in STOP and len(w) > 1]

@lru_cache(maxsize=1)
def _load_faiss() -> Tuple[faiss.Index, List[Dict]]:
    idx_path = INDEX_DIR / "faiss.index"
    map_path = INDEX_DIR / "mapping.jsonl"
    if not idx_path.exists():
        raise RuntimeError("Vector index not found. Ingest PDFs first.")
    index = faiss.read_index(str(idx_path))
    mapping: List[Dict] = []
    if not map_path.exists():
        raise RuntimeError("mapping.jsonl not found in index directory.")
    with map_path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                mapping.append(json.loads(ln))
    return index, mapping

@lru_cache(maxsize=512)
def _load_sentences(doc_id: str) -> List[Dict]:
    p = DATA_DIR / "meta" / f"{doc_id}_sentences.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("sentences", [])

def _current_blocklist() -> set[str]:
    ids: set[str] = set()
    try:
        if _BLOCKLIST_PATH.exists():
            data = json.loads(_BLOCKLIST_PATH.read_text(encoding="utf-8"))
            raw = data.get("docIds") if isinstance(data, dict) else data
            if isinstance(raw, list):
                ids = {str(x).strip() for x in raw if str(x).strip()}
    except Exception:
        pass
    env = os.getenv("PRISM_BLOCK_DOCS", "")
    if env:
        ids |= {s.strip() for s in env.split(",") if s.strip()}
    return ids

def section_text_lookup(doc_id: str, section_id: str, max_chars: int = 1400) -> str:
    sents = [s for s in _load_sentences(doc_id) if s.get("sectionId") == section_id]
    out, n = [], 0
    for s in sents:
        t = (s.get("text") or "").strip()
        if not t:
            continue
        out.append(t); n += len(t)
        if n >= max_chars:
            break
    return " ".join(out)

def _make_snippet(doc_id: str, section_id: str, center_sent_idx: int) -> str:
    sents = _load_sentences(doc_id)
    picks = []
    for i in (center_sent_idx - 1, center_sent_idx, center_sent_idx + 1, center_sent_idx + 2):
        if 0 <= i < len(sents) and sents[i].get("sectionId") == section_id:
            txt = (sents[i].get("text") or "").strip()
            if txt:
                picks.append(txt)
        if len(picks) >= 4:
            break
    if not picks:
        picks = [s.get("text", "") for s in sents if s.get("sectionId") == section_id][:3]
    snippet = " ".join(" ".join(picks).split())
    if len(snippet) > 600:
        snippet = snippet[:597].rsplit(" ", 1)[0] + "…"
    return snippet

def _minmax(a: np.ndarray) -> np.ndarray:
    if a.size == 0:
        return a
    lo, hi = float(np.min(a)), float(np.max(a))
    if hi <= lo + 1e-12:
        return np.ones_like(a)
    return (a - lo) / (hi - lo + 1e-12)

def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0

def _mmr(cands: List[Dict], k: int, lam: float = 0.78) -> List[Dict]:
    selected: List[Dict] = []
    pool = cands[:]
    while pool and len(selected) < k:
        best = None
        best_val = -1e9
        for c in pool:
            base = float(c.get("finalScore", c.get("score", 0.0)))
            div_pen = 0.0
            if selected:
                sim = max((_jaccard(c.get("tokset", set()), s.get("tokset", set())) for s in selected), default=0.0)
                div_pen = (1 - lam) * 3.0 * sim
            val = lam * base - div_pen
            if val > best_val:
                best_val, best = val, c
        selected.append(best)
        pool.remove(best)
    return selected

def related_search(
    query: str,
    k: int = 5,
    doc_filter: Optional[List[str]] = None,
    persona: Optional[str] = None,
    task: Optional[str] = None,
    deep: bool = False,
) -> List[Dict]:
    index, mapping = _load_faiss()
    model = get_model()

    blocked = _current_blocklist()

    qv = model.encode([query], normalize_embeddings=True)
    qv = np.asarray(qv[0], dtype="float32").reshape(1, -1)
    topN = max(50, k * 10)
    D, I = index.search(qv, topN)
    scores = D[0]; ids = I[0]

    best_by_section: Dict[tuple, Dict] = {}
    qtok = _tok(query)
    filter_set = set(doc_filter) if doc_filter else None
    for score, ridx in zip(scores, ids):
        if ridx < 0:
            continue
        meta = mapping[ridx]
        if meta.get("docId") in blocked:
            continue
        if filter_set and meta.get("docId") not in filter_set:
            continue
        key = (meta["docId"], meta["sectionId"])
        cur = best_by_section.get(key)
        if (cur is None) or (score > cur["vecScore"]):
            best_by_section[key] = {
                "docId": meta["docId"],
                "docTitle": meta.get("docTitle", ""),
                "docOrigName": meta.get("docOrigName", ""),
                "sectionId": meta["sectionId"],
                "sectionTitle": meta.get("sectionTitle", "") or meta["sectionId"],
                "page": int(meta.get("page", 1)),
                "y": float(meta.get("y", 0.0)),
                "sentIdx": int(meta.get("sentIdx", 0)),
                "vecScore": float(score),
            }
    collapsed = list(best_by_section.values())
    if not collapsed:
        return []

    texts = [section_text_lookup(h["docId"], h["sectionId"]) for h in collapsed]
    corp_tokens = [_tok(t) for t in texts]
    bm25 = BM25Okapi(corp_tokens) if corp_tokens and any(corp_tokens) else None
    bm25_scores = np.array(bm25.get_scores(qtok), dtype="float32") if bm25 else np.zeros(len(collapsed), dtype="float32")
    vec_scores = np.array([c["vecScore"] for c in collapsed], dtype="float32")
    vec_n = _minmax(vec_scores); bm25_n = _minmax(bm25_scores)
    alpha = 0.65
    fused = alpha * vec_n + (1 - alpha) * bm25_n

    doc_counts: Dict[str, int] = defaultdict(int)
    for i, c in enumerate(collapsed):
        pen = -0.15 * doc_counts[c["docId"]]
        c["finalScore"] = float(fused[i] + pen)
        c["tokset"] = set(corp_tokens[i]) if i < len(corp_tokens) else set()
        doc_counts[c["docId"]] += 1

    pool = sorted(collapsed, key=lambda x: -x["finalScore"])[: max(40, k * 6)]

    if persona or task:
        for h in pool:
            if "score" not in h:
                h["score"] = float(h.get("finalScore", 0.0))
        pool = apply_persona_reweight(pool, section_text_lookup, persona or "", task or "")

    if deep and (persona or task):
        pool = deep_persona_reweight(pool, section_text_lookup, persona or "", task or "")

    for h in pool:
        h["finalScore"] = float(h.get("score", h.get("finalScore", 0.0)))

    diverse = _mmr(pool, k=k, lam=0.78)

    out: List[Dict] = []
    for h in diverse[:k]:
        snippet = _make_snippet(h["docId"], h["sectionId"], h.get("sentIdx", 0))
        out.append({
            "docId": h["docId"],
            "docTitle": h.get("docTitle", ""),
            "docOrigName": h.get("docOrigName", ""),
            "sectionId": h["sectionId"],
            "sectionTitle": h.get("sectionTitle", "") or h["sectionId"],
            "page": int(h.get("page", 1)),
            "y": float(h.get("y", 0.0)),
            "score": float(h.get("score", h.get("finalScore", 0.0))),
            "snippet": snippet,
            "why": h.get("why"),
            "whyDeep": h.get("whyDeep"),
        })
    return out

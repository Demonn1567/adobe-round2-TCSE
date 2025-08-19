from __future__ import annotations
from typing import Dict, List, Optional, Any, Callable
import re
import inspect

_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9’']+")

def _tok(s: str) -> List[str]:
    if not s:
        return []
    return [w.lower().strip("''") for w in _WORD.findall(str(s)) if len(w) > 1]

def _jaccard(a: List[str], b: List[str]) -> float:
    A, B = set(a), set(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)

def _safe_score(hit: Dict[str, Any]) -> float:
    s = hit.get("score", None)
    if s is None:
        s = hit.get("sim") or hit.get("similarity") or hit.get("baseScore") or 0.0
        try:
            s = float(s)
        except Exception:
            s = 0.0
        hit["score"] = s
    return float(hit["score"])

def _get_text_src(section_text_lookup: Any) -> Callable[[str, Optional[str]], str]:
    if callable(section_text_lookup):
        try:
            sig = inspect.signature(section_text_lookup)
            params = [
                p for p in sig.parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                and p.default is p.empty
            ]
            arity = len(params)
        except Exception:
            arity = 1

        if arity <= 1:
            return lambda sid, did=None: (section_text_lookup(sid) or "")  
        else:
            return lambda sid, did=None: (section_text_lookup(did, sid) or "")  
    if isinstance(section_text_lookup, dict):
        return lambda sid, did=None: str(section_text_lookup.get(sid, "") or "")
    return lambda sid, did=None: ""

def apply_persona_reweight(
    hits: List[Dict[str, Any]],
    section_text_lookup: Any,          
    persona: Optional[str],
    task: Optional[str],
) -> List[Dict[str, Any]]:

    if not persona and not task:
        return hits

    query = f"{persona or ''} {task or ''}".strip()
    if not query:
        return hits

    q_tokens = _tok(query)
    text_of = _get_text_src(section_text_lookup)

    reweighted: List[Dict[str, Any]] = []
    for h in hits:
        base = _safe_score(h)

        title   = h.get("sectionTitle") or ""
        snippet = h.get("snippet") or ""
        sid     = h.get("sectionId", "")
        did     = h.get("docId") or h.get("docid") or h.get("doc_id")
        body    = text_of(sid, did)

        t_tok = _tok(title)
        s_tok = _tok(snippet)
        b_tok = _tok(body)

        title_sim   = _jaccard(t_tok, q_tokens)
        snippet_sim = _jaccard(s_tok, q_tokens)
        body_sim    = _jaccard(b_tok, q_tokens)

        phrase_bonus = 0.0
        q_low   = " ".join(q_tokens)
        text_low = " ".join(t_tok + s_tok + b_tok)
        for kw in ("azure","tts","text to speech","environment","env","variable","variables","credentials","endpoint","key"):
            if kw in q_low and kw in text_low:
                phrase_bonus += 0.05

        new_score = (
            1.00 * base
            + 0.25 * title_sim
            + 0.20 * snippet_sim
            + 0.15 * body_sim
            + phrase_bonus
        )

        h["score"] = float(new_score)
        h["why"] = {
            "titleSim": round(title_sim, 3),
            "snippetSim": round(snippet_sim, 3),
            "bodySim": round(body_sim, 3),
            "phraseBonus": round(phrase_bonus, 3),
        }
        reweighted.append(h)

    reweighted.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return reweighted

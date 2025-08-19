from __future__ import annotations
from typing import List, Dict, Optional
import os
import textwrap

try:
    import google.generativeai as genai  
except Exception:  
    genai = None 


def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(key)
    return val if val else default


def _ensure_model() -> Optional["genai.GenerativeModel"]:  
    api_key = _env("GEMINI_API_KEY")
    if not api_key or not genai:
        return None
    genai.configure(api_key=api_key)
    model_name = _env("GEMINI_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(model_name) 


def _trim(s: str, max_chars: int) -> str:
    s = " ".join((s or "").split())
    if len(s) <= max_chars:
        return s
    cut = s[:max_chars]
    dot = cut.rfind(". ")
    if dot >= 200:
        return cut[: dot + 1]
    return cut + "…"


def build_prompt(query: str, persona: Optional[str], task: Optional[str], hits: List[Dict]) -> str:
    persona_block = f"\nPersona: {persona}" if persona else ""
    task_block = f"\nJob to be done: {task}" if task else ""
    header = textwrap.dedent(f"""\
        You are a concise technical assistant. Answer ONLY using the evidence below.
        If evidence is insufficient, say "I don't have enough evidence in the uploaded docs to answer."
        Cite sources in-line with bracketed numbers like [1], [2]. Be short and actionable.

        User query: {query}{persona_block}{task_block}
    """)

    lines = ["Evidence:"]
    for i, h in enumerate(hits, start=1):
        title = f"{h.get('docTitle','')} • {h.get('sectionTitle','')}".strip(" •")
        page = h.get("page")
        pref = f"[{i}] {title}" + (f" (p.{page})" if page else "")
        snippet = _trim(h.get("snippet",""), 900)
        lines.append(pref + f"\n{snippet}\n")

    guide = textwrap.dedent("""\
        Guidelines:
        - Use the user’s persona/job only to decide relevance and tone.
        - Prefer steps, bullet actions, or a short paragraph.
        - Keep answer <= 8 sentences.
        - Include the bracketed citations where facts come from.
    """)

    return header + "\n\n" + "\n".join(lines) + "\n" + guide


def generate_answer(query: str,
                    persona: Optional[str],
                    task: Optional[str],
                    hits: List[Dict],
                    max_chars_ctx: int = 8000) -> Optional[str]:

    model = _ensure_model()
    if not model:
        return None

    ctx_chars = 0
    packed: List[Dict] = []
    for h in hits:
        snip = " ".join((h.get("snippet", "") or "").split())
        budget = max(600, min(1400, max_chars_ctx // max(1, len(hits))))
        h2 = dict(h)
        h2["snippet"] = _trim(snip, budget)
        ctx_chars += len(h2["snippet"])
        packed.append(h2)

    prompt = build_prompt(query, persona, task, packed)
    out = model.generate_content(prompt) 
    txt = (out.text or "").strip() if out else ""
    return txt or None

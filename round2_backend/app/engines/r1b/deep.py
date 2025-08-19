from __future__ import annotations
from typing import List, Dict, Tuple
import re
import unicodedata

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9’']+")

_STOP = {
    "the","a","an","and","or","of","to","in","on","for","with","by","from","at",
    "is","are","be","was","were","that","this","it","as","into","over","across",
    "about","we","you","your","our","their","not","pdf"
}
def _norm(s: str) -> str:
    return unicodedata.normalize("NFKC", s or "")

def _tok_no_stop(s: str) -> List[str]:
    return [w.lower().strip("’'") for w in WORD_RE.findall(_norm(s)) if w.lower() not in _STOP and len(w) > 1]

def _pick_domain(persona: str, task: str) -> str:
    s = f"{persona} {task}".lower()
    if any(k in s for k in ["hr", "human resource", "onboard", "form", "e-sign", "signature", "compliance", "fillable"]):
        return "hr_forms"
    if any(k in s for k in ["travel", "trip", "itinerary", "tour", "friends", "college", "nightlife", "beach", "cuisine"]):
        return "travel"
    if any(k in s for k in ["food", "menu", "buffet", "dinner", "vegetarian", "gluten-free", "gluten free", "vegan"]):
        return "food_menu"
    return "generic"

LEXICONS = {
    "generic": {},
    "travel": {
        "city": 0.8, "guide": 1.2, "coast": 1.4, "beach": 1.6, "island": 1.2,
        "nightlife": 1.7, "entertainment": 1.3, "bar": 1.2, "club": 1.2,
        "cuisine": 1.2, "culinary": 1.4, "restaurant": 1.0, "wine": 1.0,
        "packing": 1.4, "tips": 1.2,
    },
    "hr_forms": {
        "form": 1.8, "fillable": 2.2, "fill": 1.6, "sign": 1.6, "signature": 1.8,
        "request": 1.4, "send": 1.2, "create": 1.2, "convert": 1.2, "export": 1.0,
        "field": 1.4, "checkbox": 1.0, "radio": 0.8, "interactive": 1.4,
        "onboarding": 1.6, "compliance": 1.6,
    },
    "food_menu": {
        "vegetarian": 2.4, "vegan": 1.8, "gluten-free": 2.6, "glutenfree": 2.6,
        "buffet": 1.8, "dinner": 1.6, "mains": 1.4, "sides": 1.4,
        "tofu": 1.2, "paneer": 1.2, "chickpea": 1.4, "lentil": 1.4, "quinoa": 1.6,
        "salad": 1.2, "lasagna": 1.6, "sushi": 1.8,
    },
}

PHRASE_BOOSTS = {
    "travel": [
        (re.compile(r"\bnightlife (and|&)? entertainment\b", re.I), 5.5),
        (re.compile(r"\bculinary experiences\b", re.I), 5.0),
        (re.compile(r"\bpacking tips?\b", re.I), 3.0),
    ],
    "hr_forms": [
        (re.compile(r"\bfill (and|&)? sign\b", re.I), 5.0),
        (re.compile(r"\brequest e-?signatures?\b", re.I), 4.5),
        (re.compile(r"\bconvert .* to pdf\b", re.I), 3.8),
    ],
    "food_menu": [
        (re.compile(r"\bvegetarian\b", re.I), 5.0),
        (re.compile(r"\bgluten[- ]?free\b", re.I), 6.0),
        (re.compile(r"\bbuffet(-style)?\b", re.I), 3.0),
    ],
    "generic": [],
}

def _build_query_weights(persona: str, task: str, domain: str) -> Dict[str, float]:
    w: Dict[str, float] = {}
    for t in _tok_no_stop(f"{persona} {task}"):
        w[t] = max(w.get(t, 0.0), 1.0)
    for t, wt in LEXICONS.get(domain, {}).items():
        w[t] = max(w.get(t, 0.0), wt)
    if "gluten-free" in w:
        w["glutenfree"] = max(w.get("glutenfree", 0.0), w["gluten-free"])
    return w

def _kw_score(tokens: List[str], weights: Dict[str, float]) -> float:
    s = 0.0
    for t in tokens:
        wt = weights.get(t)
        if wt:
            s += wt
    return s

def deep_persona_reweight(
    hits: List[Dict],
    section_text_lookup,  
    persona: str,
    task: str,
) -> List[Dict]:
   
    if not hits:
        return hits

    domain = _pick_domain(persona, task)
    weights = _build_query_weights(persona, task, domain)

    for h in hits:
        base = float(h.get("score", h.get("finalScore", 0.0)))
        title = h.get("sectionTitle", "")
        body = section_text_lookup(h["docId"], h["sectionId"], max_chars=1800)

        t_tokens = _tok_no_stop(title)
        b_tokens = _tok_no_stop(body[:1800])

        title_boost = 2.6 * _kw_score(t_tokens, weights)
        body_boost  = 0.9 * _kw_score(b_tokens, weights)
        phrase_bonus = 0.0
        for pat, wt in PHRASE_BOOSTS.get(domain, []):
            if pat.search(title) or pat.search(body):
                phrase_bonus += wt

        page_prior = 0.3 if int(h.get("page", 1)) in (1, 2, 3) else 0.1

        final_score = 0.70 * base + title_boost + body_boost + phrase_bonus + page_prior

        why = {
            "domain": domain,
            "titleTokensHit": [t for t in t_tokens if t in weights],
            "bodyTokensHitTop": sorted({t for t in b_tokens if t in weights})[:12],
            "titleBoost": round(title_boost, 4),
            "bodyBoost": round(body_boost, 4),
            "phraseBonus": round(phrase_bonus, 4),
            "pagePrior": round(page_prior, 4),
            "oldScore": round(base, 4),
            "newScore": round(final_score, 4),
        }

        h["score"] = float(final_score)
        h["whyDeep"] = why

    hits.sort(key=lambda x: -float(x.get("score", x.get("finalScore", 0.0))))
    return hits

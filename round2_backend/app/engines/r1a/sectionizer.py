from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple
import sys

def _add_r1a_to_syspath():
    here = Path(__file__).resolve()
    for up in range(2, 6):
        root = here.parents[up] if up < len(here.parents) else None
        if not root:
            continue
        cand = root / "Challenge_1a"
        if (cand / "src").exists():
            sys.path.insert(0, str(cand))
            return

_add_r1a_to_syspath()

from .src.extract import Span, extract_spans    
from .src.features import filter_spans          
from .src.classify import predict_headings      
from .src.runner import detect_title            



def _sort_key(span: Span) -> Tuple[int, float, float]:
    return (int(span.page), float(span.bbox[1] if span.bbox else 0.0), float(span.bbox[0] if span.bbox else 0.0))


def sectionize(pdf_path: Path) -> Dict:
    spans: List[Span] = extract_spans(pdf_path)
    if isinstance(spans, tuple):  
        spans = spans[0]
    if not spans:
        return {"title": pdf_path.stem, "sections": []}

    page_cnt = max(s.page for s in spans)
    title = detect_title(spans) or pdf_path.stem

    spans_flt = filter_spans(spans, title, page_cnt)
    heads = predict_headings(spans_flt)
    if isinstance(heads, tuple): 
        heads = heads[0]
    heads = sorted(heads, key=_sort_key)

    from collections import defaultdict
    lines_by_page: Dict[int, List[Span]] = defaultdict(list)
    for s in sorted(spans, key=_sort_key):
        lines_by_page[int(s.page)].append(s)

    bounds: List[Tuple[int, float, Span]] = []
    for h in heads:
        y_top = float(h.bbox[1] if h.bbox else 0.0)
        bounds.append((int(h.page), y_top, h))
    bounds.sort(key=lambda t: (t[0], t[1]))

    sections = []
    for i, (p, y_top, h) in enumerate(bounds):
        if i + 1 < len(bounds):
            p2, y2, _ = bounds[i + 1]
        else:
            p2, y2 = page_cnt + 1, 0.0  

        texts: List[str] = []

        for page in range(p, min(p2, page_cnt) + 1):
            lines = lines_by_page.get(page, [])
            if not lines:
                continue

            if page == p and page == p2:
                y_bottom = float(h.bbox[3] if h.bbox else y_top)
                texts.extend(s.text.strip() for s in lines if y_bottom <= s.bbox[1] < y2)
            elif page == p:
                y_bottom = float(h.bbox[3] if h.bbox else y_top)
                texts.extend(s.text.strip() for s in lines if s.bbox[1] >= y_bottom)
            elif page == p2:
                texts.extend(s.text.strip() for s in lines if s.bbox[1] < y2)
            else:
                texts.extend(s.text.strip() for s in lines)

        joined = " ".join(t for t in texts if t)
        joined = " ".join(joined.split())
        sec_id = f"sec{i:04d}-p{p}-{int(y_top)}"

        sections.append({
            "sectionId": sec_id,
            "title": h.text.strip(),
            "level": getattr(h, "level", "H3"),
            "page": p,
            "y": y_top,
            "text": joined
        })

    return {"title": title, "sections": sections}

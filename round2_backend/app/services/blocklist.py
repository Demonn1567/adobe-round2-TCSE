from __future__ import annotations
from typing import Iterable, Set, List
from pathlib import Path
import json

from app.utils.config import DATA_DIR

PATH: Path = DATA_DIR / "blocklist.json"

def _load() -> Set[str]:
    if PATH.exists():
        try:
            data = json.loads(PATH.read_text(encoding="utf-8"))
            raw = data.get("docIds") if isinstance(data, dict) else data
            if isinstance(raw, list):
                return {str(x).strip() for x in raw if str(x).strip()}
        except Exception:
            pass
    return set()

def _save(ids: Set[str]) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps({"docIds": sorted(ids)}, indent=2), encoding="utf-8")

def list_ids() -> List[str]:
    return sorted(_load())

def add(doc_ids: Iterable[str]) -> List[str]:
    s = _load()
    for d in doc_ids:
        d = str(d).strip()
        if d:
            s.add(d)
    _save(s)
    return sorted(s)

def remove(doc_ids: Iterable[str]) -> List[str]:
    s = _load()
    for d in doc_ids:
        s.discard(str(d).strip())
    _save(s)
    return sorted(s)

def clear() -> None:
    _save(set())

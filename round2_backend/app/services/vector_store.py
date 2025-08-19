from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple

class VectorStore:
    def __init__(self, index_dir: Path, dim: int = 384):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "faiss.index"
        self.map_path = self.index_dir / "mapping.jsonl"
        self.meta_path = self.index_dir / "faiss_meta.json"
        self.dim = dim
        self.index = None
        self._mapping_cache: List[Dict[str, Any]] | None = None
        self._load()

    def _load(self):
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.dim = self.index.d
        else:
            self.index = faiss.IndexFlatIP(self.dim) 
        if not self.meta_path.exists():
            self.meta_path.write_text(json.dumps({"ntotal": int(self.index.ntotal)}))

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(json.dumps({"ntotal": int(self.index.ntotal)}))

    def add(self, vectors: np.ndarray, mapping_rows: List[Dict[str, Any]]):
        if vectors.size == 0:
            return
        vectors = vectors.astype("float32")
        faiss.normalize_L2(vectors)
        start_id = int(self.index.ntotal)
        self.index.add(vectors)
        with self.map_path.open("a", encoding="utf-8") as f:
            for i, row in enumerate(mapping_rows):
                row_out = {"vecId": start_id + i}
                row_out.update(row)
                f.write(json.dumps(row_out, ensure_ascii=False) + "\n")
        self._mapping_cache = None  
        self._save()

    def _load_mapping(self) -> List[Dict[str, Any]]:
        if self._mapping_cache is not None:
            return self._mapping_cache
        rows: List[Dict[str, Any]] = []
        if self.map_path.exists():
            with self.map_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        rows.append(json.loads(line))
        if rows:
            max_id = max(r["vecId"] for r in rows)
            arr: List[Dict[str, Any] | None] = [None] * (max_id + 1)
            for r in rows:
                arr[r["vecId"]] = r
            rows = [r for r in arr if r is not None]
        self._mapping_cache = rows
        return rows

    def search(self, query_vec: np.ndarray, topk: int = 50) -> List[Tuple[int, float]]:
        
        if int(self.index.ntotal) == 0:
            return []
        q = query_vec.astype("float32")
        faiss.normalize_L2(q)
        D, I = self.index.search(q, topk)
        ids = I[0].tolist()
        scores = D[0].tolist()
        out = []
        for i, s in zip(ids, scores):
            if i == -1:
                continue
            out.append((int(i), float(s)))
        return out

    def resolve(self, vec_ids: List[int]) -> List[Dict[str, Any]]:
        mapping = self._load_mapping()
        out = []
        for vid in vec_ids:
            if 0 <= vid < len(mapping):
                out.append(mapping[vid])
        return out

import re
import textwrap
from typing import Dict
import numpy as np
import pandas as pd

from src.rag_models.embedding.embedding_factory import EmbeddingFactory
from src.utils.embedder_utils.embedder_warper import EmbeddingWrapper

# ───────────────────────────────────────────────────────────
# MC choice extractor
# ───────────────────────────────────────────────────────────
_RE_MC = re.compile(r"(?:^|[^A-D])\s*([ABCD])\s*(?:[)\.:,;!?\n]|$)")

def letter_only(txt: str) -> str:
    m = _RE_MC.search(txt)
    if m:
        return m.group(1).upper()
    for ch in txt:
        if ch in "ABCD":
            return ch
    return ""

def build_mc_question(row: pd.Series) -> str:
    base = row["question"].strip()
    opts = [c.strip() for c in row["choices"].split(",")]
    mc_lines = "\n".join(f"{l}) {o}" for l, o in zip("ABCD", opts))
    return textwrap.dedent(f"{base}\n\nSCELTE\n{mc_lines}")

# ───────────────────────────────────────────────────────────
# Cosine scorer
# ───────────────────────────────────────────────────────────
class SimilarityScorer:
    def __init__(self, model_name: str = "nomic-embed-text"):
        emb = EmbeddingFactory.get_embedding_model(model_name)
        self._embedder = EmbeddingWrapper(emb)
        self._cache: Dict[str, np.ndarray] = {}

    def _vec(self, txt: str) -> np.ndarray:
        if txt not in self._cache:
            self._cache[txt] = np.asarray(self._embedder.embed_query(txt), dtype=np.float32)
        return self._cache[txt]

    def cosine(self, a: str, b: str) -> float:
        va, vb = self._vec(a), self._vec(b)
        return float((va @ vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9))

# ───────────────────────────────────────────────────────────
# Latency stats
# ───────────────────────────────────────────────────────────
def lat_stats(series: pd.Series):
    if series.empty:
        return np.nan, np.nan, np.nan
    return float(series.mean()), float(series.quantile(0.95)), float(series.max())

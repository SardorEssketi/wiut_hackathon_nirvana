import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
import re
import time
from pathlib import Path
from .models import Passage
from .text import normalize

ROOT = Path(__file__).resolve().parents[1]


def lexical_scores(passages: list[Passage], queries: list[str]):
    """Simple multilingual term-prefix overlap baseline; no embeddings."""
    terms = {token[:6] for q in queries for token in re.findall(r"[\w']+", normalize(q)) if len(token)>2}
    scores = []
    for p in passages:
        tokens = {t[:6] for t in re.findall(r"[\w']+", p.normalized) if len(t)>2}
        scores.append(len(terms & tokens) / max(1, len(terms)))
    return scores


class Retriever:
    def __init__(self, mode="hybrid", model_path=None):
        if mode not in {"lexical", "semantic", "hybrid"}:
            raise ValueError("Unsupported retrieval mode")
        self.requested = mode
        self.used = mode
        self.warning = None
        self.model = None
        self.model_revision = None
        started = time.perf_counter()
        if mode != "lexical":
            path = Path(model_path or os.getenv("POLISDIFF_MODEL_PATH", str(ROOT / "models" / "multilingual-e5-small")))
            try:
                if not (path / "config.json").exists():
                    raise FileNotFoundError("Offline embedding model not provisioned")
                import torch
                torch.set_num_threads(max(1, min(4, int(os.getenv("POLISDIFF_TORCH_THREADS", "2")))))
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(str(path), device="cpu", local_files_only=True,
                                                trust_remote_code=False)
                self.model.max_seq_length = 512
                import json
                manifest = ROOT / "evaluation" / "model_manifest.json"
                if manifest.exists():
                    self.model_revision = json.loads(manifest.read_text(encoding="utf-8"))["revision"]
            except Exception as exc:
                self.used = "lexical"
                self.warning = f"Semantic retrieval unavailable ({type(exc).__name__}); lexical fallback used."
        self.initialization_seconds = time.perf_counter() - started
        self._passages = []
        self._embeddings = None

    def prepare(self, passages: list[Passage]):
        self._passages = passages
        if self.model is not None and passages:
            self._embeddings = self.model.encode(["passage: " + p.normalized for p in passages],
                batch_size=16, normalize_embeddings=True, show_progress_bar=False)

    def search(self, queries: list[str], k=5) -> list[tuple[Passage, float]]:
        if not self._passages:
            return []
        lexical = lexical_scores(self._passages, queries)
        if self.model is None:
            scores = lexical
        else:
            import numpy as np
            vectors = self.model.encode(["query: " + normalize(q) for q in queries],
                normalize_embeddings=True, show_progress_bar=False)
            semantic = np.max(self._embeddings @ vectors.T, axis=1).tolist()
            if self.used == "semantic":
                scores = semantic
            else:
                # Reciprocal rank fusion retains lexical fallback and bounds score effects.
                sr = sorted(range(len(semantic)), key=lambda i: semantic[i], reverse=True)
                lr = sorted(range(len(lexical)), key=lambda i: lexical[i], reverse=True)
                scores = [0.0] * len(lexical)
                for rank, idx in enumerate(sr):
                    scores[idx] += 1 / (60 + rank + 1)
                for rank, idx in enumerate(lr):
                    if lexical[idx] > 0:
                        scores[idx] += 1 / (60 + rank + 1)
        indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [(self._passages[i], float(scores[i])) for i in indices if scores[i] > 0]

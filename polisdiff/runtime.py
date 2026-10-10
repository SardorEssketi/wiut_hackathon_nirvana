"""One shared embedding model per web process; no uploaded evidence in this cache."""
from copy import copy
from functools import lru_cache
from threading import Lock
from .retrieval import Retriever

_MODEL_INIT_LOCK = Lock()


@lru_cache(maxsize=1)
def _ai_base():
    return Retriever("hybrid")


def web_retriever(mode):
    if mode == "lexical":
        return Retriever(mode)
    if mode not in {"semantic", "hybrid"}:
        raise ValueError("Unsupported retrieval mode")
    # lru_cache alone can execute the initial loader twice under contention.
    with _MODEL_INIT_LOCK:
        retriever = copy(_ai_base())
    retriever.requested = mode
    retriever.used = mode if retriever.model is not None else "lexical"
    retriever._passages = []
    retriever._embeddings = None
    retriever._query_vectors = dict(retriever._query_vectors)
    return retriever

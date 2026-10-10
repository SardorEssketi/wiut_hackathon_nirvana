"""One shared embedding model per web process; no uploaded evidence in this cache."""
from copy import copy
from functools import lru_cache
from .retrieval import Retriever


@lru_cache(maxsize=1)
def _ai_base():
    return Retriever("hybrid")


def web_retriever(mode):
    if mode == "lexical":
        return Retriever(mode)
    if mode not in {"semantic", "hybrid"}:
        raise ValueError("Unsupported retrieval mode")
    retriever = copy(_ai_base())
    retriever.requested = mode
    retriever.used = mode if retriever.model is not None else "lexical"
    retriever._passages = []
    retriever._embeddings = None
    return retriever

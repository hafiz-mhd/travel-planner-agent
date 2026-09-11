"""RAG retriever – FAISS-based vector search over destination knowledge base."""
from __future__ import annotations
import logging
import os
import pickle
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_model: Optional[SentenceTransformer] = None
_index = None          # faiss.IndexFlatIP
_docs: list[str] = []
_metas: list[dict] = []

INDEX_PATH = os.path.join(settings.chroma_persist_dir, "faiss.index")
STORE_PATH = os.path.join(settings.chroma_persist_dir, "docstore.pkl")


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def _load_index():
    """Load the FAISS index and doc store from disk (lazy, once per process)."""
    global _index, _docs, _metas
    if _index is not None:
        return

    if not os.path.exists(INDEX_PATH) or not os.path.exists(STORE_PATH):
        logger.warning("FAISS index not found at %s. Run seed_knowledge_base.py first.", INDEX_PATH)
        return

    import faiss  # local import so missing faiss gives a clear error
    _index = faiss.read_index(INDEX_PATH)
    with open(STORE_PATH, "rb") as f:
        data = pickle.load(f)
    _docs = data["docs"]
    _metas = data["metas"]
    logger.info("FAISS index loaded: %d vectors", _index.ntotal)


def retrieve_context(destination: str, interests: list[str]) -> tuple[str, list[str]]:
    """
    Return (context_string, list_of_source_titles) for the given destination.
    Falls back gracefully if the index hasn't been seeded yet.
    """
    _load_index()

    if _index is None or _index.ntotal == 0:
        return ("No destination context available. Use general travel knowledge.", [])

    query = destination
    if interests:
        query += " " + " ".join(interests)

    model = _get_model()
    embedding = model.encode([query], normalize_embeddings=True).astype("float32")

    k = min(settings.rag_top_k, _index.ntotal)
    distances, indices = _index.search(embedding, k)

    result_docs, result_metas = [], []
    for idx in indices[0]:
        if idx < len(_docs):
            result_docs.append(_docs[idx])
            result_metas.append(_metas[idx])

    sources = [m.get("title", "Unknown") for m in result_metas]
    context = "\n\n---\n\n".join(
        f"[{meta.get('title', 'Destination')}]\n{doc}"
        for doc, meta in zip(result_docs, result_metas)
    )
    return context, sources

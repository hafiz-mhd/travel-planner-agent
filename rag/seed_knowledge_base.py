"""Seed script: load destination JSON files into a FAISS vector store."""
from __future__ import annotations
import json
import logging
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()

INDEX_PATH = os.path.join(settings.chroma_persist_dir, "faiss.index")
STORE_PATH = os.path.join(settings.chroma_persist_dir, "docstore.pkl")


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        boundary = text.rfind(". ", start, end)
        if boundary > start:
            end = boundary + 1
        chunks.append(text[start:end].strip())
        start = end
    return chunks


def seed():
    data_dir = settings.rag_data_dir
    if not os.path.isdir(data_dir):
        logger.error("Data directory not found: %s", data_dir)
        sys.exit(1)

    os.makedirs(settings.chroma_persist_dir, exist_ok=True)

    model = SentenceTransformer(settings.embedding_model)
    dim = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatIP(dim)   # inner-product = cosine on normalised vecs

    all_docs: list[str] = []
    all_metas: list[dict] = []
    total_chunks = 0

    for fname in sorted(os.listdir(data_dir)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(data_dir, fname)
        with open(fpath, encoding="utf-8") as f:
            doc = json.load(f)

        title = doc.get("title", fname)
        body = _flatten_doc(doc)
        chunks = chunk_text(body)

        embeddings = model.encode(chunks, normalize_embeddings=True).astype("float32")
        index.add(embeddings)

        meta = {"title": title, "destination": doc.get("destination", title), "source_file": fname}
        all_docs.extend(chunks)
        all_metas.extend([meta] * len(chunks))
        total_chunks += len(chunks)
        logger.info("Seeded '%s' → %d chunk(s)", title, len(chunks))

    faiss.write_index(index, INDEX_PATH)
    with open(STORE_PATH, "wb") as f:
        pickle.dump({"docs": all_docs, "metas": all_metas}, f)

    logger.info("Done. Total vectors: %d  →  %s", total_chunks, INDEX_PATH)


def _flatten_doc(doc: dict) -> str:
    parts = []
    if "title" in doc:
        parts.append(f"Destination: {doc['title']}")
    if "overview" in doc:
        parts.append(doc["overview"])
    if "best_time_to_visit" in doc:
        parts.append(f"Best time to visit: {doc['best_time_to_visit']}")
    if "climate" in doc:
        parts.append(f"Climate: {doc['climate']}")
    if "attractions" in doc:
        parts.append("Top attractions: " + "; ".join(
            a if isinstance(a, str)
            else a.get("name", "") + " – " + a.get("description", "")
            for a in doc["attractions"]
        ))
    if "food" in doc:
        parts.append("Food & dining: " + "; ".join(
            f if isinstance(f, str)
            else f.get("name", "") + " – " + f.get("description", "")
            for f in doc["food"]
        ))
    if "accommodation" in doc:
        parts.append("Accommodation: " + "; ".join(
            a if isinstance(a, str)
            else a.get("name", "") + " (" + a.get("type", "") + ") ~$" + str(a.get("avg_price_usd", "?"))
            for a in doc["accommodation"]
        ))
    if "transport" in doc:
        parts.append("Getting around: " + doc["transport"])
    if "budget_guide" in doc:
        bg = doc["budget_guide"]
        bd = bg.get("budget_per_day_usd", {})
        parts.append(
            f"Budget: ${bd.get('low','?')}/day budget, ${bd.get('mid','?')}/day mid, ${bd.get('high','?')}/day luxury"
        )
    if "tips" in doc:
        parts.append("Tips: " + "; ".join(doc["tips"]))
    if "interests" in doc:
        parts.append("Good for: " + ", ".join(doc["interests"]))
    return "\n".join(parts)


if __name__ == "__main__":
    seed()

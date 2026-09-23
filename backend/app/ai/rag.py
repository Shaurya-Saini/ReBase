"""Manual Q&A retrieval (B10): ChromaDB vector store + sentence-transformers.

- Source: data/manuals/<machine_type>_manual.md. Each `###` section is one
  chunk; its id is the section heading, e.g. "4.2 Operating modes", which is
  what E23 returns as `sources[].section`.
- Embeddings: settings.EMBEDDING_MODEL (English, all-MiniLM-L6-v2). Questions in
  Hindi/Tamil are translated to English before `retrieve` (B11, DECISIONS #17).
- Store: persistent Chroma collection at settings.CHROMA_DIR, cosine distance.
  Rebuilt automatically when the manuals (or the embedding model) change —
  a content hash is kept in the collection metadata.
- Checklists are NOT here: they're structured content served directly (E12).
"""

import hashlib
import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path

from app.config import BACKEND_DIR, settings

log = logging.getLogger(__name__)

MANUAL_DIR = BACKEND_DIR / "data" / "manuals"
COLLECTION = "manuals"
# Below this cosine similarity a section is treated as "not about the question".
# Measured on the demo manuals: real questions >= 0.35, off-topic <= 0.25.
RELEVANCE_MIN = 0.30

_lock = threading.RLock()
_model = None
_collection = None


@dataclass
class Chunk:
    id: str
    doc: str  # e.g. "excavator_manual.md"
    machine_type: str
    section: str  # e.g. "4.2 Operating modes"
    text: str  # chapter + section title + body (what gets embedded)
    body: str  # section body only


@dataclass
class Hit:
    doc: str
    machine_type: str
    section: str
    text: str
    score: float  # cosine similarity, higher = more relevant


def chunk_manual(path: Path) -> list[Chunk]:
    doc = path.name
    machine_type = doc.removesuffix("_manual.md")
    chunks, chapter = [], ""
    for block in re.split(r"(?m)^(?=#{2,3} )", path.read_text()):
        m = re.match(r"(#{2,3}) (.+)\n?", block)
        if not m:
            continue
        title = m.group(2).strip()
        if m.group(1) == "##":
            chapter = title
            continue
        body = block[m.end():].strip()
        chunks.append(Chunk(id=f"{machine_type}:{title}", doc=doc, machine_type=machine_type,
                            section=title, text=f"{chapter}\n{title}\n{body}", body=body))
    return chunks


def all_chunks(manual_dir: Path = MANUAL_DIR) -> list[Chunk]:
    return [c for p in sorted(manual_dir.glob("*_manual.md")) for c in chunk_manual(p)]


def _content_hash(chunks: list[Chunk]) -> str:
    h = hashlib.sha256(settings.EMBEDDING_MODEL.encode())
    for c in chunks:
        h.update(c.id.encode())
        h.update(c.text.encode())
    return h.hexdigest()[:16]


def _embedder():
    global _model
    with _lock:
        if _model is None:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return _model


def _embed(texts: list[str]) -> list[list[float]]:
    return _embedder().encode(texts, normalize_embeddings=True).tolist()


def _client():
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    Path(settings.CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=settings.CHROMA_DIR,
                                     settings=ChromaSettings(anonymized_telemetry=False))


def build(force: bool = False):
    """(Re)build the vector store if the manuals changed. Returns the collection."""
    global _collection
    with _lock:
        chunks = all_chunks()
        digest = _content_hash(chunks)
        client = _client()
        existing = next((c for c in client.list_collections() if c.name == COLLECTION), None)
        if existing is not None and not force:
            col = client.get_collection(COLLECTION, embedding_function=None)
            # Reuse only a complete store: an interrupted build (e.g. `uvicorn --reload`
            # restarting mid-embedding) must never be trusted, whatever its metadata says.
            if (col.metadata or {}).get("content_hash") == digest and col.count() == len(chunks):
                _collection = col
                return col
        if existing is not None:
            client.delete_collection(COLLECTION)
        col = client.create_collection(
            COLLECTION, embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
            metadata={"content_hash": "building", "embedding_model": settings.EMBEDDING_MODEL},
        )
        if chunks:
            col.add(
                ids=[c.id for c in chunks],
                embeddings=_embed([c.text for c in chunks]),
                documents=[c.body for c in chunks],
                metadatas=[{"doc": c.doc, "machine_type": c.machine_type, "section": c.section}
                           for c in chunks],
            )
        # Mark complete only after every section is in.
        col.modify(metadata={"content_hash": digest, "embedding_model": settings.EMBEDDING_MODEL})
        log.info("rag: indexed %d manual sections (%s)", len(chunks), digest)
        _collection = col
        return col


def _get_collection():
    with _lock:
        return _collection if _collection is not None else build()


def retrieve(question: str, machine_type: str | None = None, k: int = 3) -> list[Hit]:
    """Top-k manual sections for an **English** question, best first.
    `machine_type` restricts to that machine's manual."""
    col = _get_collection()
    res = col.query(
        query_embeddings=_embed([question]),
        n_results=k,
        where={"machine_type": machine_type} if machine_type else None,
        include=["documents", "metadatas", "distances"],
    )
    return [
        Hit(doc=m["doc"], machine_type=m["machine_type"], section=m["section"], text=d,
            score=round(1.0 - dist, 4))
        for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def relevant(hits: list[Hit]) -> list[Hit]:
    return [h for h in hits if h.score >= RELEVANCE_MIN]


def warm_in_background() -> threading.Thread:
    """Load the model + build the store without blocking server start-up."""
    def run():
        try:
            build()
        except Exception as e:  # noqa: BLE001 — assistant falls back; never kill the server
            log.warning("rag: warm-up failed: %s", e)

    t = threading.Thread(target=run, name="rag-warmup", daemon=True)
    t.start()
    return t

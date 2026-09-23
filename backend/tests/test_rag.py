"""B10: manual chunking + ChromaDB retrieval (real embedding model, English questions).

Builds the store once for the module (~20 s the first time: model load + 75 sections).
"""

import pytest

from app.ai import rag

MTYPES = ["excavator", "wheel_loader", "drill_rig", "dump_truck"]


@pytest.fixture(scope="module")
def store():
    rag._collection = None
    return rag.build(force=True)


# ---------- chunking (no model) ----------

@pytest.mark.parametrize("mtype", MTYPES)
def test_every_machine_has_a_manual(mtype):
    chunks = rag.chunk_manual(rag.MANUAL_DIR / f"{mtype}_manual.md")
    assert len(chunks) >= 12
    assert all(c.machine_type == mtype and c.doc == f"{mtype}_manual.md" for c in chunks)
    assert all(c.body and c.section[0].isdigit() for c in chunks)
    assert len({c.id for c in chunks}) == len(chunks)


def test_contract_example_source_exists():
    sections = {c.section for c in rag.chunk_manual(rag.MANUAL_DIR / "excavator_manual.md")}
    assert "4.2 Operating modes" in sections  # CONTRACT §4 AssistantAnswer.sources example


def test_chunk_text_carries_chapter_context():
    c = next(c for c in rag.all_chunks() if c.id == "excavator:4.2 Operating modes")
    assert c.text.startswith("4 Operating\n4.2 Operating modes\n")
    assert "mode button" in c.body and not c.body.startswith("#")


def test_manuals_match_telemetry_thresholds():
    """The manuals should say the same numbers the tablet rules use (95/105 °C, 5/2 m)."""
    body = next(c for c in rag.all_chunks() if c.id == "excavator:5.1 Hydraulic oil temperature warning").body
    assert "95 °C" in body and "105 °C" in body
    prox = next(c for c in rag.all_chunks() if c.id == "excavator:5.5 Proximity warning").body
    assert "5 m" in prox and "2 m" in prox


# ---------- retrieval (real model) ----------

@pytest.mark.parametrize("mtype,question,section", [
    ("excavator", "How do I switch to power mode?", "4.2 Operating modes"),
    ("excavator", "What should I do if the hydraulic oil gets too hot?", "5.1 Hydraulic oil temperature warning"),
    ("excavator", "How far should I stay from power lines?", "1.2 Working near power lines"),
    ("excavator", "The engine won't start", "7.2 Engine does not start"),
    ("excavator", "How do I lower the boom if the engine stopped?", "8.2 Lowering the boom with the engine stopped"),
    ("wheel_loader", "How high should I carry the bucket when driving?", "4.3 Travelling with a load"),
    ("drill_rig", "The drill string is stuck, what do I do?", "6.1 Stuck drill string"),
    ("dump_truck", "How do I tip the load?", "4.3 Tipping the load"),
])
def test_finds_the_right_section(store, mtype, question, section):
    hits = rag.retrieve(question, mtype, k=3)
    assert hits[0].section == section
    assert hits[0].doc == f"{mtype}_manual.md" and hits[0].score >= rag.RELEVANCE_MIN
    assert hits[0].score >= hits[-1].score


def test_machine_filter(store):
    hits = rag.retrieve("How do I switch to power mode?", "dump_truck", k=3)
    assert {h.machine_type for h in hits} == {"dump_truck"}


def test_off_topic_is_not_relevant(store):
    for q in ["What is the cricket score today?", "Tell me a joke", "What's the weather tomorrow?"]:
        assert rag.relevant(rag.retrieve(q, "excavator", k=3)) == [], q


def test_reopen_without_rebuild_and_rebuild_on_change(store, monkeypatch):
    rag._collection = None
    assert rag.build().metadata["content_hash"] == store.metadata["content_hash"]
    # a changed embedding model / manual changes the hash → rebuilt
    monkeypatch.setattr(rag.settings, "EMBEDDING_MODEL", rag.settings.EMBEDDING_MODEL)
    real_chunks = rag.all_chunks
    monkeypatch.setattr(rag, "all_chunks", lambda: real_chunks()[:5])
    rebuilt = rag.build()
    assert rebuilt.count() == 5 and rebuilt.metadata["content_hash"] != store.metadata["content_hash"]
    monkeypatch.undo()
    rag._collection = None
    assert rag.build().count() == len(rag.all_chunks())

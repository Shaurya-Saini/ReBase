"""B13: Training Hub content + E26 next module + E27 complete."""

import pytest
from sqlmodel import Session, select

from app.db import engine
from app.models import TrainingCompletion
from app.services import training

MTYPES = ["excavator", "wheel_loader", "drill_rig", "dump_truck"]


# ---------- content ----------

@pytest.mark.parametrize("mtype", MTYPES)
@pytest.mark.parametrize("level", training.LEVELS)
def test_every_machine_and_level_has_a_module(mtype, level):
    m = training.module_for(mtype, level)
    assert m is not None
    assert m["id"].startswith("trn_") and m["id"].endswith("_01")
    assert 30 <= m["duration_min"] <= 45  # 30–45 min pre-shift recap
    assert len(m["steps"]) >= 4 and len(m["quiz"]) >= 3
    assert all(s["kind"] in ("text", "video", "tip") and s["content"] for s in m["steps"])
    assert all(len(q["options"]) >= 2 and 0 <= q["answer_index"] < len(q["options"]) for q in m["quiz"])


def test_contract_example_id():
    m = training.all_modules()["trn_ex_novice_01"]
    assert m["title"] == "Excavator basics before your shift"
    assert m["quiz"][0] == {"q": "What must you do if a hydraulic hose leaks?",
                            "options": ["Ignore it", "Report and do not start", "Start slowly"], "answer_index": 1}


def test_quiz_agrees_with_the_manual():
    """Training and the manual Q&A must not contradict each other."""
    manual = (training.BACKEND_DIR / "data" / "manuals" / "excavator_manual.md").read_text()
    assert "at least 6 m from overhead power lines" in manual
    q = next(q for q in training.all_modules()["trn_ex_novice_01"]["quiz"] if "power lines" in q["q"])
    assert q["options"][q["answer_index"]] == "6 m"


# ---------- E26 ----------

def test_next_matches_operator_experience(client):
    get = lambda op, mt: client.get(f"/operators/{op}/training/next", params={"machine_type": mt}).json()  # noqa: E731
    assert get("op_001", "excavator")["id"] == "trn_ex_expert_01"      # Ravi: expert excavator
    assert get("op_001", "wheel_loader")["id"] == "trn_wl_novice_01"   # Ravi: novice loader
    assert get("op_003", "excavator")["id"] == "trn_ex_novice_01"      # Arjun: novice
    assert get("op_005", "drill_rig")["id"] == "trn_dr_intermediate_01"
    assert get("op_002", "drill_rig")["level"] == "novice"             # never run one → novice


def test_next_shape(client):
    m = client.get("/operators/op_003/training/next", params={"machine_type": "excavator"}).json()
    assert set(m) == {"id", "machine_type", "level", "title", "duration_min", "steps", "quiz"}
    assert all(set(s) == {"kind", "content", "url"} for s in m["steps"])


def test_next_errors(client):
    r = client.get("/operators/op_999/training/next")
    assert r.status_code == 404 and r.json()["error"]["code"] == "OPERATOR_NOT_FOUND"
    r = client.get("/operators/op_001/training/next", params={"machine_type": "crane"})
    assert r.status_code == 422


# ---------- E27 ----------

def test_complete_records_result(client):
    r = client.post("/training/trn_ex_novice_01/complete", json={"operator_id": "op_003", "score": 3})
    assert r.status_code == 200 and r.json() == {"ok": True}
    with Session(engine) as db:
        rows = db.exec(select(TrainingCompletion)).all()
    assert [(c.operator_id, c.module_id, c.score) for c in rows] == [("op_003", "trn_ex_novice_01", 3)]


def test_complete_errors(client):
    r = client.post("/training/trn_nope/complete", json={"operator_id": "op_003", "score": 1})
    assert r.status_code == 404 and r.json()["error"]["code"] == "TRAINING_NOT_FOUND"
    r = client.post("/training/trn_ex_novice_01/complete", json={"operator_id": "op_999", "score": 1})
    assert r.status_code == 404 and r.json()["error"]["code"] == "OPERATOR_NOT_FOUND"
    for bad in (-1, 5):  # trn_ex_novice_01 has 4 questions
        r = client.post("/training/trn_ex_novice_01/complete", json={"operator_id": "op_003", "score": bad})
        assert r.status_code == 422 and r.json()["error"]["code"] == "SCORE_OUT_OF_RANGE"

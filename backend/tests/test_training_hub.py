"""Training Hub v2.3: personalized plan (E28), localized modules (E29 / E26 ?lang), quiz grading (E30)."""

import json

import pytest

from app.services import training
from app.services.training_i18n import guard, source_payload


def plan(client, op="op_001", lang=None):
    r = client.get(f"/operators/{op}/training/plan", params={"lang": lang} if lang else {})
    assert r.status_code == 200, r.json()
    return r.json()


def reasons(item):
    return {r["code"] for r in item["reasons"]}


# ---------- content ----------

def test_every_quiz_source_exists_in_the_manual():
    from app.ai import rag

    sections = {(c.machine_type, c.section) for c in rag.all_chunks()}
    for m in training.all_modules().values():
        assert m["topics"], m["id"]
        for q in m["quiz"]:
            assert q["explanation"] and (m["machine_type"], q["source"]) in sections, (m["id"], q["source"])


@pytest.mark.parametrize("lang", ["hi-IN", "ta-IN"])
def test_every_module_has_a_guarded_translation(lang):
    for mid, m in training.all_modules().items():
        path = training.TRAINING_I18N_DIR / lang / f"{mid}.json"
        assert path.exists(), (lang, mid)
        guard(source_payload(m), json.loads(path.read_text(encoding="utf-8")), lang)  # raises if bad


def test_guard_rejects_romanized_or_changed_numbers():
    m = training.all_modules()["trn_ex_novice_01"]
    src = source_payload(m)
    with pytest.raises(ValueError, match="script"):
        guard(src, src, "ta-IN")  # English "translation"
    t = json.loads((training.TRAINING_I18N_DIR / "ta-IN" / "trn_ex_novice_01.json").read_text(encoding="utf-8"))
    t["steps"][6] = t["steps"][6].replace("6", "4")  # a translation that changed 6 m → 4 m
    out, kept = guard(src, t, "ta-IN")
    assert kept == 1 and out["steps"][6] == src["steps"][6]  # falls back to the English sentence


# ---------- E28 plan ----------

def test_ravi_plan_is_driven_by_live_data(client):
    p = plan(client)
    assert p["operator_id"] == "op_001" and p["lang"] == "en-IN"
    items = {it["module_id"]: it for it in p["items"]}
    assert p["items"][0]["module_id"] == "trn_ex_novice_01"  # seatbelt + proximity alerts + power line
    assert {"recent_alert", "job_hazard"} <= reasons(items["trn_ex_novice_01"])
    texts = " | ".join(r["text"] for r in items["trn_ex_novice_01"]["reasons"])
    assert "2 seatbelt alert(s)" in texts and "1 proximity alert(s)" in texts and "power line" in texts
    assert {"retake", "job_hazard"} <= reasons(items["trn_ex_intermediate_01"])  # 2/4 last time, soft ground
    assert items["trn_ex_intermediate_01"]["last_result"]["score"] == 2
    assert "assigned" in reasons(items["trn_ex_expert_01"])
    assert [it["priority"] for it in p["items"]] == list(range(1, len(p["items"]) + 1))
    assert p["total_minutes"] == sum(it["duration_min"] for it in p["items"] if it["status"] == "todo")
    assert p["progress"] == {"attempts": 3, "modules_passed": 2, "avg_score_pct": 83, "streak_days": 3}


def test_plan_in_tamil(client):
    p = plan(client, lang="ta-IN")
    novice = next(it for it in p["items"] if it["module_id"] == "trn_ex_novice_01")
    assert novice["title"] != training.all_modules()["trn_ex_novice_01"]["title"]  # translated title
    assert any("சீட் பெல்ட்" in r["text"] for r in novice["reasons"])
    assert any("மின் கம்பி" in r["text"] for r in novice["reasons"])


def test_new_machine(client):
    """Arjun has never run a loader; a loader job in 3 days → 'You're new to the wheel loader'."""
    from datetime import timedelta

    from app.clock import today_ist

    day = (today_ist() + timedelta(days=3)).isoformat()
    r = client.post("/assignments", json={"operator_id": "op_003", "job_id": "job_006", "machine_id": "mc_002",
                                          "date": day, "shift": "night"})
    assert r.status_code == 201
    items = {it["module_id"]: it for it in plan(client, "op_003")["items"]}
    loader = items["trn_wl_novice_01"]
    assert {"new_machine", "assigned"} <= reasons(loader)
    assert any("new to the wheel loader" in r["text"] for r in loader["reasons"])


def test_level_up_after_a_strong_pass(client):
    """Priya is an expert loader operator; Sam (intermediate drill) aces his module → offer expert."""
    client.post("/training/trn_dr_intermediate_01/submit", json={"operator_id": "op_005", "answers": [0, 0, 0]})
    items = {it["module_id"]: it for it in plan(client, "op_005")["items"]}
    assert "level_up" in reasons(items["trn_dr_expert_01"])


def test_no_upcoming_work_falls_back_to_own_machines(client):
    p = plan(client, "op_003")
    assert p["items"] and all(reasons(it) == {"keep_fresh"} for it in p["items"])
    assert p["progress"]["attempts"] == 0 and p["progress"]["streak_days"] == 0


def test_plan_unknown_operator(client):
    r = client.get("/operators/op_999/training/plan")
    assert r.status_code == 404 and r.json()["error"]["code"] == "OPERATOR_NOT_FOUND"


# ---------- E29 module / E26 ?lang ----------

def test_module_endpoint_localized_and_hides_explanations(client):
    en = client.get("/training/modules/trn_ex_novice_01").json()
    ta = client.get("/training/modules/trn_ex_novice_01", headers={"Accept-Language": "ta-IN"}).json()
    assert en["title"] == "Excavator basics before your shift" and ta["title"] != en["title"]
    assert [q["answer_index"] for q in ta["quiz"]] == [q["answer_index"] for q in en["quiz"]]
    assert set(ta["quiz"][0]) == {"q", "options", "answer_index"}  # no explanation/source before submitting
    assert client.get("/training/modules/trn_nope").status_code == 404
    nxt = client.get("/operators/op_003/training/next", params={"machine_type": "excavator", "lang": "hi-IN"}).json()
    assert nxt["id"] == "trn_ex_novice_01" and any("ऀ" <= ch <= "ॿ" for ch in nxt["title"])


# ---------- E30 submit ----------

def test_submit_grades_and_explains(client):
    r = client.post("/training/trn_ex_novice_01/submit", json={"operator_id": "op_003", "answers": [1, 0, 0, None]})
    assert r.status_code == 200
    res = r.json()
    assert (res["score"], res["total"], res["passed"]) == (2, 4, False)
    first, second = res["results"][0], res["results"][1]
    assert first["correct"] and first["source"] == {"doc": "excavator_manual.md", "section": "6.1 Walk-around inspection"}
    assert not second["correct"] and second["correct_index"] == 2 and "10 m" in second["explanation"]
    assert res["results"][3]["chosen"] is None and not res["results"][3]["correct"]


def test_submit_feeds_the_plan(client):
    client.post("/training/trn_ex_intermediate_01/submit", json={"operator_id": "op_001", "answers": [1, 1, 0, 1]})
    items = {it["module_id"]: it for it in plan(client)["items"]}
    inter = items["trn_ex_intermediate_01"]
    assert inter["status"] == "done" and "retake" not in reasons(inter)
    assert p_last(inter) == (4, 4)
    assert plan(client)["items"][-1]["module_id"] == "trn_ex_intermediate_01"  # done items sink to the bottom


def p_last(item):
    return item["last_result"]["score"], item["last_result"]["total"]


def test_submit_in_tamil_explains_in_tamil(client):
    res = client.post("/training/trn_ex_novice_01/submit", params={"lang": "ta-IN"},
                      json={"operator_id": "op_003", "answers": [1, 2, 0, 1]}).json()
    assert res["passed"] and res["score"] == 4
    assert any("஀" <= ch <= "௿" for ch in res["results"][0]["explanation"])


def test_submit_errors(client):
    r = client.post("/training/trn_ex_novice_01/submit", json={"operator_id": "op_003", "answers": [1, 2]})
    assert r.status_code == 422 and r.json()["error"]["code"] == "ANSWER_COUNT_MISMATCH"
    r = client.post("/training/trn_ex_novice_01/submit", json={"operator_id": "op_003", "answers": [9, 0, 0, 0]})
    assert r.status_code == 422 and r.json()["error"]["code"] == "ANSWER_OUT_OF_RANGE"
    r = client.post("/training/trn_nope/submit", json={"operator_id": "op_003", "answers": []})
    assert r.status_code == 404
    r = client.post("/training/trn_ex_novice_01/submit", json={"operator_id": "op_999", "answers": [0, 0, 0, 0]})
    assert r.status_code == 404

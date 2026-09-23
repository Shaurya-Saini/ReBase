"""B7: session state machine, checklist + critical-defect gate, briefing (E10–E17)."""

import pytest

from app.ai import briefing as briefing_mod
from app.ai.checklists import checklist_items, load_checklist

RAVI = {"operator_id": "op_001", "machine_id": "mc_001", "job_id": "job_001"}
MTYPES = ["excavator", "wheel_loader", "drill_rig", "dump_truck"]


def err(r):
    return r.json()["error"]


def new_session(client, body=RAVI):
    r = client.post("/sessions", json=body)
    assert r.status_code == 201, r.json()
    return r.json()["id"]


def mark_all(client, sid, status="ok", **override):
    chk = client.get(f"/sessions/{sid}/checklist").json()
    for sec in chk["sections"]:
        for item in sec["items"]:
            st = override.get(item["id"], status)
            r = client.put(f"/sessions/{sid}/checklist/items/{item['id']}", json={"status": st})
            assert r.status_code == 200


def to_active(client, body=RAVI):
    sid = new_session(client, body)
    mark_all(client, sid)
    assert client.post(f"/sessions/{sid}/checklist/complete").status_code == 200
    assert client.post(f"/sessions/{sid}/start").status_code == 200
    return sid


# ---------- checklist content ----------

@pytest.mark.parametrize("mtype", MTYPES)
def test_checklist_content(mtype):
    c = load_checklist(mtype)
    assert c["machine_type"] == mtype and "MSHA 30 CFR 56.14100" in c["standard_refs"]
    items = checklist_items(mtype)
    assert len(items) >= 15
    texts = " ".join(i["text"].lower() for i in items.values())
    for must in ("seatbelt", "brake", "horn", "leak"):  # MSHA 56.14100 essentials
        assert must in texts, (mtype, must)
    assert any(i["critical"] for i in items.values()) and not all(i["critical"] for i in items.values())


def test_excavator_matches_contract_example():
    items = checklist_items("excavator")
    assert items["chk_01"] == {"id": "chk_01", "text": "Check tracks and undercarriage for damage", "critical": False}
    assert items["chk_02"]["text"] == "Check hydraulic hoses for leaks" and items["chk_02"]["critical"]


# ---------- E10 create ----------

def test_create_session(client):
    r = client.post("/sessions", json=RAVI)
    assert r.status_code == 201
    s = r.json()
    assert s["id"] == "ses_001" and s["state"] == "pre_start"
    assert s["started_at"] is None and s["ended_at"] is None
    assert client.get(f"/sessions/{s['id']}").json() == s


def test_create_errors(client):
    r = client.post("/sessions", json={**RAVI, "machine_id": "mc_002"})
    assert r.status_code == 422 and err(r)["code"] == "MACHINE_TYPE_MISMATCH"
    for field, code in [("operator_id", "OPERATOR_NOT_FOUND"), ("machine_id", "MACHINE_NOT_FOUND"),
                        ("job_id", "JOB_NOT_FOUND")]:
        r = client.post("/sessions", json={**RAVI, field: "x_999"})
        assert r.status_code == 404 and err(r)["code"] == code
    r = client.post("/sessions", json={"operator_id": "op_004", "machine_id": "mc_004", "job_id": "job_004"})
    assert r.status_code == 409 and err(r)["code"] == "REST_REQUIRED"
    assert client.get("/sessions/ses_999").json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_restart_abandons_unstarted_session(client):
    first = new_session(client)
    second = new_session(client)
    assert first != second
    old = client.get(f"/sessions/{first}").json()
    assert old["state"] == "ended" and old["started_at"] is None


def test_active_session_blocks_new_ones(client):
    sid = to_active(client)
    r = client.post("/sessions", json=RAVI)
    assert r.status_code == 409 and err(r)["code"] == "SESSION_ALREADY_ACTIVE" and err(r)["session_id"] == sid
    # Arjun (novice excavator) can't take Ravi's machine while it's in use
    r = client.post("/sessions", json={"operator_id": "op_003", "machine_id": "mc_001", "job_id": "job_005"})
    assert r.status_code == 409 and err(r)["code"] == "MACHINE_IN_USE"


# ---------- E12–E14 checklist ----------

def test_checklist_starts_pending(client):
    sid = new_session(client)
    c = client.get(f"/sessions/{sid}/checklist").json()
    assert c["session_id"] == sid and c["machine_type"] == "excavator"
    items = [i for s in c["sections"] for i in s["items"]]
    assert all(i["status"] == "pending" and i["note"] is None for i in items)


def test_update_item(client):
    sid = new_session(client)
    r = client.put(f"/sessions/{sid}/checklist/items/chk_02", json={"status": "defect", "note": "Weeping at fitting"})
    assert r.json() == {"id": "chk_02", "text": "Check hydraulic hoses for leaks", "critical": True,
                        "status": "defect", "note": "Weeping at fitting"}
    c = client.get(f"/sessions/{sid}/checklist").json()
    assert c["sections"][0]["items"][1]["status"] == "defect"
    r = client.put(f"/sessions/{sid}/checklist/items/chk_99", json={"status": "ok"})
    assert r.status_code == 404 and err(r)["code"] == "CHECKLIST_ITEM_NOT_FOUND"
    r = client.put(f"/sessions/{sid}/checklist/items/chk_01", json={"status": "broken"})
    assert r.status_code == 422


def test_complete_incomplete(client):
    sid = new_session(client)
    client.put(f"/sessions/{sid}/checklist/items/chk_01", json={"status": "ok"})
    r = client.post(f"/sessions/{sid}/checklist/complete")
    assert r.status_code == 422 and err(r)["code"] == "CHECKLIST_INCOMPLETE"
    assert "chk_02" in err(r)["items"] and "chk_01" not in err(r)["items"]


def test_critical_defect_blocks_then_fix_allows(client):
    """Demo beat 4–5: hose leak blocks start; fix it, re-check, complete."""
    sid = new_session(client)
    mark_all(client, sid, chk_02="defect")
    r = client.post(f"/sessions/{sid}/checklist/complete")
    assert r.status_code == 422
    assert err(r) == {"code": "CRITICAL_DEFECT", "message": "Critical items have defects", "items": ["chk_02"]}
    assert client.get(f"/sessions/{sid}").json()["state"] == "pre_start"

    client.put(f"/sessions/{sid}/checklist/items/chk_02", json={"status": "ok", "note": "Fitting tightened"})
    r = client.post(f"/sessions/{sid}/checklist/complete")
    assert r.status_code == 200 and r.json()["state"] == "briefing"


def test_non_critical_defect_and_na_allowed(client):
    sid = new_session(client)
    mark_all(client, sid, chk_04="defect", chk_17="na")  # worn teeth, extinguisher n/a
    assert client.post(f"/sessions/{sid}/checklist/complete").json()["state"] == "briefing"


def test_checklist_locked_after_complete(client):
    sid = new_session(client)
    mark_all(client, sid)
    client.post(f"/sessions/{sid}/checklist/complete")
    r = client.put(f"/sessions/{sid}/checklist/items/chk_01", json={"status": "defect"})
    assert r.status_code == 409 and err(r)["code"] == "INVALID_STATE"


# ---------- E15 briefing ----------

def test_briefing_requires_checklist(client):
    sid = new_session(client)
    r = client.get(f"/sessions/{sid}/briefing")
    assert r.status_code == 409 and err(r)["code"] == "INVALID_STATE"


def test_briefing_template(client):
    sid = new_session(client)
    mark_all(client, sid, chk_04="defect")
    client.put(f"/sessions/{sid}/checklist/items/chk_04", json={"status": "defect", "note": "2 teeth worn"})
    client.post(f"/sessions/{sid}/checklist/complete")
    b = client.get(f"/sessions/{sid}/briefing").json()
    assert b["session_id"] == sid and b["lang"] == "en-IN"
    assert b["machine_summary"] == "Generic 20t Excavator, 4521 hours on the meter, last inspection today."
    assert b["job_summary"].startswith("Trench excavation – Block C at Site 2, North Pit. Planned 6 h, starting 09:00")
    assert "Overhead power line near east edge" in b["hazards"]
    assert any("Wet ground" in h for h in b["hazards"])  # job_001 weather = rain
    assert "Reported defect: Check bucket teeth and cutting edge (2 teeth worn)" in b["hazards"]
    assert "Never swing the bucket over people or vehicles" in b["reminders"]
    assert b["estimated_hours"] == client.get("/jobs/job_001/estimate").json()["estimated_hours"]


@pytest.mark.parametrize("lang,word", [("hi-IN", "सीटबेल्ट"), ("ta-IN", "சீட் பெல்ட்")])
def test_briefing_localized_template(client, lang, word):
    sid = new_session(client)
    mark_all(client, sid)
    client.post(f"/sessions/{sid}/checklist/complete")
    b = client.get(f"/sessions/{sid}/briefing", params={"lang": lang}).json()
    assert b["lang"] == lang and any(word in r for r in b["reminders"])


def test_briefing_fatigue_reminder_for_warning_operator(client):
    sid = new_session(client, {"operator_id": "op_002", "machine_id": "mc_002", "job_id": "job_002"})
    mark_all(client, sid)
    client.post(f"/sessions/{sid}/checklist/complete")
    b = client.get(f"/sessions/{sid}/briefing").json()
    assert any("working-hour limit" in r for r in b["reminders"])


def test_briefing_uses_llm_when_available(client, monkeypatch):
    seen = {}

    def fake_llm(system, prompt, schema, max_tokens=2000):
        seen["prompt"] = prompt
        return {"machine_summary": "M", "job_summary": "J", "hazards": ["H"], "reminders": ["R"]}

    monkeypatch.setattr(briefing_mod, "complete_json", fake_llm)
    sid = new_session(client)
    mark_all(client, sid)
    client.post(f"/sessions/{sid}/checklist/complete")
    b = client.get(f"/sessions/{sid}/briefing", params={"lang": "ta-IN"}).json()
    assert (b["machine_summary"], b["hazards"], b["lang"]) == ("M", ["H"], "ta-IN")
    assert "Tamil" in seen["prompt"] and "Overhead power line" in seen["prompt"]
    assert isinstance(b["estimated_hours"], float)  # always from our estimator, never the LLM


def test_briefing_falls_back_when_anthropic_has_no_credentials(client, monkeypatch):
    """Real code path with provider=anthropic and no key: must be a 200 template, never a 500."""
    from app.ai import llm

    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(llm.settings, "LLM_API_KEY", "")
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ANTHROPIC_CONFIG_DIR", "/nonexistent")  # ignore any local `ant` login
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://127.0.0.1:9")  # and never reach the network
    sid = new_session(client)
    mark_all(client, sid)
    client.post(f"/sessions/{sid}/checklist/complete")
    r = client.get(f"/sessions/{sid}/briefing", params={"lang": "ta-IN"})
    assert r.status_code == 200 and any("சீட் பெல்ட்" in x for x in r.json()["reminders"])


def test_llm_errors_become_unavailable(monkeypatch):
    from app.ai import llm

    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(llm.settings, "LLM_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://127.0.0.1:9")  # connection refused
    with pytest.raises(llm.LLMUnavailable):
        llm.complete_json("s", "p", {"type": "object", "properties": {}, "additionalProperties": False})
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "sarvam")
    with pytest.raises(llm.LLMUnavailable, match="not implemented"):
        llm.complete_json("s", "p", {})


# ---------- E16 / E17 start + end ----------

def test_start_and_end(client):
    sid = new_session(client)
    r = client.post(f"/sessions/{sid}/start")
    assert r.status_code == 409 and err(r)["code"] == "INVALID_STATE"  # checklist first

    mark_all(client, sid)
    client.post(f"/sessions/{sid}/checklist/complete")
    s = client.post(f"/sessions/{sid}/start").json()
    assert s["state"] == "active" and s["started_at"].endswith("Z")
    assert client.get("/machines/mc_001").json()["status"] == "in_use"
    assert client.get("/jobs/job_001").json()["status"] == "in_progress"
    assert client.get(f"/sessions/{sid}/briefing").status_code == 200  # still readable while active

    summary = client.post(f"/sessions/{sid}/end").json()
    assert summary["session_id"] == sid and summary["duration_hours"] >= 0
    assert summary["alerts_total"] == 0 and summary["alerts_critical"] == 0
    assert client.get(f"/sessions/{sid}").json()["state"] == "ended"
    assert client.get("/machines/mc_001").json()["status"] == "available"
    r = client.post(f"/sessions/{sid}/end")
    assert r.status_code == 409 and err(r)["code"] == "INVALID_STATE"


def test_active_session_counts_toward_fatigue(client):
    before = client.get("/operators/op_001").json()["hours_today"]
    to_active(client)
    assert client.get("/operators/op_001").json()["hours_today"] >= before


@pytest.fixture(autouse=True)
def _clear_briefing_cache():
    briefing_mod._cache.clear()
    yield
    briefing_mod._cache.clear()

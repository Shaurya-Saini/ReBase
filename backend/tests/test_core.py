"""B2: E2–E7 + E9 on seeded data (see app/seed.py for the demo cast)."""

from datetime import timedelta

from app.clock import today_ist


def err(r):
    return r.json()["error"]["code"]


# ---------- E2 login ----------

def test_login_ok(client):
    r = client.post("/auth/login", json={"operator_id": "op_001", "pin": "1234"})
    assert r.status_code == 200
    op = r.json()
    assert op["name"] == "Ravi Kumar" and op["lang"] == "ta-IN"
    assert op["experience"] == {"excavator": "expert", "wheel_loader": "novice"}
    assert set(op) == {"id", "name", "lang", "experience", "hours_today", "hours_7d", "rest"}
    assert "pin" not in op


def test_login_bad_pin(client):
    r = client.post("/auth/login", json={"operator_id": "op_001", "pin": "0000"})
    assert r.status_code == 401 and err(r) == "BAD_PIN"


def test_login_unknown_operator(client):
    r = client.post("/auth/login", json={"operator_id": "op_999", "pin": "1234"})
    assert r.status_code == 404 and err(r) == "OPERATOR_NOT_FOUND"


# ---------- E3 / E4 operators ----------

def test_list_operators(client):
    ops = client.get("/operators").json()
    assert [o["id"] for o in ops] == ["op_001", "op_002", "op_003", "op_004", "op_005"]
    assert {o["lang"] for o in ops} == {"en-IN", "hi-IN", "ta-IN"}
    assert all(o["rest"]["status"] in {"ok", "warning", "must_rest"} for o in ops)


def test_get_operator(client):
    assert client.get("/operators/op_002").json()["name"] == "Priya Sharma"
    r = client.get("/operators/op_999")
    assert r.status_code == 404 and err(r) == "OPERATOR_NOT_FOUND"


# ---------- E6 machines ----------

def test_machines(client):
    ms = client.get("/machines").json()
    assert {m["type"] for m in ms} == {"excavator", "wheel_loader", "drill_rig", "dump_truck"}
    m = client.get("/machines/mc_001").json()
    assert m["serial"] == "EX20-0001" and m["status"] == "available"
    assert m["last_inspection"].endswith("Z")  # CONTRACT §1: ISO 8601 UTC
    r = client.get("/machines/mc_999")
    assert r.status_code == 404 and err(r) == "MACHINE_NOT_FOUND"


# ---------- E7 job ----------

def test_job(client):
    j = client.get("/jobs/job_001").json()
    assert j["title"] == "Trench excavation – Block C" and j["planned_hours"] == 6.0
    assert j["scheduled_start"].endswith("T03:30:00Z")  # 09:00 IST
    assert set(j) == {"id", "project_id", "title", "site", "machine_type",
                      "scheduled_start", "planned_hours", "status"}  # no internal fields
    r = client.get("/jobs/job_999")
    assert r.status_code == 404 and err(r) == "JOB_NOT_FOUND"


# ---------- E5 assignments ----------

def _ids(client, op, rng):
    return [a["id"] for a in client.get(f"/operators/{op}/assignments", params={"range": rng}).json()]


def test_assignments_ranges(client):
    assert _ids(client, "op_001", "day") == ["asg_001"]
    assert _ids(client, "op_001", "week") == ["asg_001", "asg_005"]
    assert _ids(client, "op_005", "day") == []
    assert _ids(client, "op_005", "week") == ["asg_004"]
    assert _ids(client, "op_005", "month") == ["asg_004", "asg_007"]
    assert _ids(client, "op_003", "month") == ["asg_008"]


def test_assignment_shape(client):
    a = client.get("/operators/op_001/assignments").json()[0]
    assert a["date"] == today_ist().isoformat() and a["shift"] == "day"
    assert a["job"]["id"] == "job_001" and a["machine"]["id"] == "mc_001"


def test_assignments_default_range_and_errors(client):
    assert _ids(client, "op_001", "day") == [
        a["id"] for a in client.get("/operators/op_001/assignments").json()]
    r = client.get("/operators/op_001/assignments", params={"range": "year"})
    assert r.status_code == 422 and err(r) == "VALIDATION_ERROR"
    r = client.get("/operators/op_999/assignments")
    assert r.status_code == 404 and err(r) == "OPERATOR_NOT_FOUND"


# ---------- E9 create assignment ----------

def _new(date, **over):
    return {"operator_id": "op_003", "job_id": "job_005", "machine_id": "mc_001",
            "date": date.isoformat(), "shift": "day", **over}


def test_create_assignment(client):
    day = today_ist() + timedelta(days=3)
    r = client.post("/assignments", json=_new(day))
    assert r.status_code == 201
    a = r.json()
    assert a["id"] == "asg_009" and a["job"]["id"] == "job_005" and a["machine"]["type"] == "excavator"
    assert "asg_009" in _ids(client, "op_003", "week")


def test_create_assignment_errors(client):
    day = today_ist() + timedelta(days=3)
    r = client.post("/assignments", json=_new(day, machine_id="mc_002"))
    assert r.status_code == 422 and err(r) == "MACHINE_TYPE_MISMATCH"
    r = client.post("/assignments", json=_new(day, operator_id="op_999"))
    assert r.status_code == 404 and err(r) == "OPERATOR_NOT_FOUND"
    r = client.post("/assignments", json=_new(day, job_id="job_999"))
    assert r.status_code == 404 and err(r) == "JOB_NOT_FOUND"
    # mc_001 is Ravi's today (asg_001), day shift → conflict
    r = client.post("/assignments", json=_new(today_ist()))
    assert r.status_code == 409 and err(r) == "ASSIGNMENT_CONFLICT"
    # same machine on the night shift is fine
    assert client.post("/assignments", json=_new(today_ist(), shift="night")).status_code == 201

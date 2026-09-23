"""B0: endpoints still on stubs return the §4 shape. (real ones: test_core / test_estimator / test_fatigue / test_sessions / test_simulator)

As each task replaces a stub with the real thing, move its checks into that
router's own test file with real seeded data.
"""

from sqlmodel import SQLModel


def test_e1_health(client):
    assert client.get("/health").json() == {"status": "ok", "version": "2.0"}


def test_tables_created(client):
    tables = set(SQLModel.metadata.tables)
    assert {"operator", "machine", "project", "job", "assignment", "session",
            "checklistitemstate", "alert", "joblog",
            "trainingcompletion"} <= tables




def test_e18_e19_e20_alerts(client):
    body = {"type": "seatbelt_off", "source": "telemetry", "severity": "warning",
            "message": "Seatbelt not fastened"}
    r = client.post("/sessions/ses_001/alerts", json=body)
    assert r.status_code == 201
    a = r.json()
    assert a["type"] == "seatbelt_off" and a["ts"] and a["acknowledged"] is False
    assert client.get("/sessions/ses_001/alerts").json()[0]["id"].startswith("alr_")
    assert client.post("/alerts/alr_001/ack").json()["acknowledged"] is True


def test_e18_rejects_unknown_alert_type(client):
    r = client.post("/sessions/ses_001/alerts", json={
        "type": "alien", "source": "telemetry", "severity": "warning", "message": "x"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"



def test_e23_assistant(client):
    r = client.post("/assistant/ask", json={"machine_id": "mc_001", "session_id": "ses_001",
                                            "question": "How do I switch to power mode?",
                                            "lang": "hi-IN"})
    assert r.json()["lang"] == "hi-IN" and r.json()["sources"]


def test_e24_e25_voice(client):
    r = client.post("/voice/tts", json={"text": "नमस्ते", "lang": "hi-IN"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"
    r = client.post("/translate", json={"text": "hello", "target": "ta-IN"})
    assert r.json() == {"text": "hello", "lang": "ta-IN"}


def test_e26_e27_training(client):
    m = client.get("/operators/op_001/training/next",
                   params={"machine_type": "excavator"}).json()
    assert m["quiz"][0]["answer_index"] == 1
    r = client.post(f"/training/{m['id']}/complete", json={"operator_id": "op_001", "score": 1})
    assert r.json() == {"ok": True}


def test_404_uses_error_format(client):
    r = client.get("/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"

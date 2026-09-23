"""B0 leftovers: health, tables, E24/E25 (still stubs until B12), error format. (real ones: test_core / test_estimator / test_fatigue / test_sessions / test_simulator / test_alerts / test_assistant / test_training)

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







def test_e24_e25_voice(client):
    r = client.post("/voice/tts", json={"text": "नमस्ते", "lang": "hi-IN"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"
    r = client.post("/translate", json={"text": "hello", "target": "ta-IN"})
    assert r.json() == {"text": "hello", "lang": "ta-IN"}



def test_404_uses_error_format(client):
    r = client.get("/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"

"""B9: incident log — E18 post, E19 list, E20 ack, and the session summary counts."""

import pytest

RAVI = {"operator_id": "op_001", "machine_id": "mc_001", "job_id": "job_001"}

DROWSY = {"type": "drowsiness", "source": "edge_cv", "severity": "critical",
          "message": "Operator eyes closed for more than 2 seconds", "ts": "2026-09-24T05:12:44Z"}
BELT = {"type": "seatbelt_off", "source": "telemetry", "severity": "warning",
        "message": "Seatbelt not fastened", "ts": "2026-09-24T05:10:00.123456Z"}  # Dart toIso8601String


def err(r):
    return r.json()["error"]["code"]


def new_session(client):
    return client.post("/sessions", json=RAVI).json()["id"]


def active_session(client):
    sid = new_session(client)
    for sec in client.get(f"/sessions/{sid}/checklist").json()["sections"]:
        for i in sec["items"]:
            client.put(f"/sessions/{sid}/checklist/items/{i['id']}", json={"status": "ok"})
    client.post(f"/sessions/{sid}/checklist/complete")
    client.post(f"/sessions/{sid}/start")
    return sid


def test_post_alert_matches_contract(client):
    sid = active_session(client)
    r = client.post(f"/sessions/{sid}/alerts", json=DROWSY)
    assert r.status_code == 201
    assert r.json() == {"id": "alr_001", "session_id": sid, "type": "drowsiness", "source": "edge_cv",
                        "severity": "critical", "message": DROWSY["message"],
                        "ts": "2026-09-24T05:12:44Z", "acknowledged": False}


def test_ts_optional_and_dart_format(client):
    sid = active_session(client)
    a = client.post(f"/sessions/{sid}/alerts", json={k: v for k, v in DROWSY.items() if k != "ts"}).json()
    assert a["ts"].endswith("Z")
    b = client.post(f"/sessions/{sid}/alerts", json=BELT).json()
    assert b["ts"].startswith("2026-09-24T05:10:00.123456")


def test_retry_does_not_duplicate(client):
    sid = active_session(client)
    first = client.post(f"/sessions/{sid}/alerts", json=DROWSY)
    again = client.post(f"/sessions/{sid}/alerts", json=DROWSY)
    assert first.status_code == 201 and again.status_code == 200
    assert again.json()["id"] == first.json()["id"]
    # escalation = new severity → a separate incident
    esc = client.post(f"/sessions/{sid}/alerts", json={**BELT, "severity": "critical"})
    assert esc.status_code == 201
    assert len(client.get(f"/sessions/{sid}/alerts").json()) == 2
    # the tablet's microsecond timestamps dedupe too
    b1 = client.post(f"/sessions/{sid}/alerts", json=BELT)
    b2 = client.post(f"/sessions/{sid}/alerts", json=BELT)
    assert b1.status_code == 201 and b2.status_code == 200 and b1.json()["id"] == b2.json()["id"]


def test_list_newest_first(client):
    sid = active_session(client)
    client.post(f"/sessions/{sid}/alerts", json=BELT)      # 05:10
    client.post(f"/sessions/{sid}/alerts", json=DROWSY)    # 05:12
    log = client.get(f"/sessions/{sid}/alerts").json()
    assert [a["type"] for a in log] == ["drowsiness", "seatbelt_off"]
    assert client.get("/sessions/ses_999/alerts").json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_ack(client):
    sid = active_session(client)
    aid = client.post(f"/sessions/{sid}/alerts", json=DROWSY).json()["id"]
    r = client.post(f"/alerts/{aid}/ack")
    assert r.status_code == 200 and r.json()["acknowledged"] is True
    assert client.post(f"/alerts/{aid}/ack").json()["acknowledged"] is True  # idempotent
    assert client.get(f"/sessions/{sid}/alerts").json()[0]["acknowledged"] is True
    r = client.post("/alerts/alr_999/ack")
    assert r.status_code == 404 and err(r) == "ALERT_NOT_FOUND"


@pytest.mark.parametrize("bad", [{"type": "alien"}, {"source": "radar"}, {"severity": "meh"}])
def test_rejects_bad_enums(client, bad):
    sid = active_session(client)
    r = client.post(f"/sessions/{sid}/alerts", json={**DROWSY, **bad})
    assert r.status_code == 422 and err(r) == "VALIDATION_ERROR"


def test_state_rules(client):
    sid = new_session(client)  # pre_start
    r = client.post(f"/sessions/{sid}/alerts", json=DROWSY)
    assert r.status_code == 409 and err(r) == "SESSION_NOT_ACTIVE"
    assert client.post("/sessions/ses_999/alerts", json=DROWSY).status_code == 404

    sid = active_session(client)
    client.post(f"/sessions/{sid}/end")
    late = client.post(f"/sessions/{sid}/alerts", json=BELT)  # in flight at end → still logged
    assert late.status_code == 201


def test_summary_counts_real_alerts(client):
    sid = active_session(client)
    client.post(f"/sessions/{sid}/alerts", json=BELT)
    client.post(f"/sessions/{sid}/alerts", json=DROWSY)
    client.post(f"/sessions/{sid}/alerts", json={**BELT, "severity": "critical"})
    s = client.post(f"/sessions/{sid}/end").json()
    assert s["alerts_total"] == 3 and s["alerts_critical"] == 2


def test_alert_ids_are_global(client):
    a = active_session(client)
    first = client.post(f"/sessions/{a}/alerts", json=DROWSY).json()["id"]
    client.post(f"/sessions/{a}/end")
    b = active_session(client)
    second = client.post(f"/sessions/{b}/alerts", json=DROWSY).json()["id"]
    assert (first, second) == ("alr_001", "alr_002")

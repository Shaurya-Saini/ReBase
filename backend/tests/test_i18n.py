"""Display text in Hindi/Tamil without an LLM (data/i18n/*.yaml)."""

import pytest

from app import i18n, seed
from app.ai.checklists import load_checklist

LANGS = ["hi-IN", "ta-IN"]
MTYPES = ["excavator", "wheel_loader", "drill_rig", "dump_truck"]
RAVI = {"operator_id": "op_001", "machine_id": "mc_001", "job_id": "job_001"}


# ---------- coverage: nothing seeded or in a checklist may be missing ----------

@pytest.mark.parametrize("lang", LANGS)
def test_every_checklist_text_is_translated(lang):
    t = i18n._table(lang)
    for mtype in MTYPES:
        c = load_checklist(mtype)
        for sec in c["sections"]:
            assert sec["title"] in t["checklist_sections"], (lang, mtype, sec["title"])
            for item in sec["items"]:
                assert item["text"] in t["checklist_items"], (lang, mtype, item["text"])


@pytest.mark.parametrize("lang", LANGS)
def test_every_seeded_entity_is_translated(lang):
    t = i18n._table(lang)
    assert {o[0] for o in seed.OPERATORS} <= set(t["operators"])
    assert {m[0] for m in seed.MACHINES} <= set(t["machines"])
    for job_id, *_rest, hazards in seed.JOBS:
        j = t["jobs"][job_id]
        assert j["title"] and j["site"] and len(j["hazards"]) == len(hazards), (lang, job_id)
    terms = t["terms"]
    assert set(terms["machine_types"]) == set(MTYPES) and set(terms["levels"]) == {"novice", "intermediate", "expert"}
    assert set(terms["weather_notes"]) == {"clear", "rain", "heat", "wind"}


@pytest.mark.parametrize("lang,script", [("hi-IN", (0x0900, 0x097F)), ("ta-IN", (0x0B80, 0x0BFF))])
def test_translations_are_in_the_right_script(lang, script):
    lo, hi = script
    for name in (v["name"] for v in i18n._table(lang)["operators"].values()):
        assert any(lo <= ord(ch) <= hi for ch in name), (lang, name)


# ---------- language selection ----------

@pytest.mark.parametrize("header,expected", [("ta-IN", "ta-IN"), ("ta", "ta-IN"), ("hi-IN,hi;q=0.9,en;q=0.8", "hi-IN"),
                                             ("fr-FR", None), ("", None), (None, None)])
def test_accept_language_parsing(header, expected):
    assert i18n._from_accept_language(header) == expected


def test_default_is_english_and_query_beats_header(client):
    assert client.get("/operators/op_001").json()["name"] == "Ravi Kumar"
    assert client.get("/operators/op_001", headers={"Accept-Language": "ta-IN"}).json()["name"] == "ரவி குமார்"
    r = client.get("/operators/op_001", params={"lang": "hi-IN"}, headers={"Accept-Language": "ta-IN"})
    assert r.json()["name"] == "रवि कुमार"


# ---------- every display endpoint ----------

def test_operators_login_machines_jobs(client):
    h = {"Accept-Language": "ta-IN"}
    assert client.post("/auth/login", json={"operator_id": "op_001", "pin": "1234"}, headers=h).json()["name"] == "ரவி குமார்"
    assert [o["name"] for o in client.get("/operators", headers=h).json()][1] == "பிரியா சர்மா"
    m = client.get("/machines/mc_001", headers=h).json()
    assert m["model"] == "பொது 20 டன் எக்ஸ்கவேட்டர்" and m["type"] == "excavator"  # enum untouched
    j = client.get("/jobs/job_001", headers=h).json()
    assert j["title"] == "அகழி தோண்டுதல் – பிளாக் C" and j["site"] == "தளம் 2, நார்த் பிட்" and j["id"] == "job_001"


def test_assignments(client):
    a = client.get("/operators/op_001/assignments", params={"range": "day", "lang": "hi-IN"}).json()[0]
    assert a["job"]["title"] == "खाई की खुदाई – ब्लॉक C" and a["machine"]["model"].startswith("जेनेरिक")


def test_estimate_notes(client):
    f = {x["name"]: x["note"] for x in client.get("/jobs/job_001/estimate", params={"lang": "hi-IN"}).json()["factors"]}
    assert f == {"weather": "बारिश का पूर्वानुमान", "operator_experience": "एक्सकेवेटर पर विशेषज्ञ"}
    f = {x["name"]: x["note"] for x in client.get("/jobs/job_001/estimate").json()["factors"]}
    assert f["operator_experience"] == "Expert on excavator"


def test_checklist_and_item_update(client):
    sid = client.post("/sessions", json=RAVI).json()["id"]
    c = client.get(f"/sessions/{sid}/checklist", headers={"Accept-Language": "ta-IN"}).json()
    assert c["sections"][0]["title"] == "சுற்றிப் பார்த்தல்"
    item = c["sections"][0]["items"][1]
    assert item["id"] == "chk_02" and item["text"] == "ஹைட்ராலிக் குழாய்களில் கசிவு உள்ளதா சரிபார்க்கவும்"
    r = client.put(f"/sessions/{sid}/checklist/items/chk_02", json={"status": "defect"},
                   headers={"Accept-Language": "hi-IN"}).json()
    assert r["text"] == "हाइड्रोलिक होज़ में रिसाव जाँचें" and r["critical"] is True


def test_briefing_template_is_fully_localized(client):
    sid = client.post("/sessions", json=RAVI).json()["id"]
    for sec in client.get(f"/sessions/{sid}/checklist").json()["sections"]:
        for i in sec["items"]:
            client.put(f"/sessions/{sid}/checklist/items/{i['id']}",
                       json={"status": "defect" if i["id"] == "chk_04" else "ok"})
    client.post(f"/sessions/{sid}/checklist/complete")
    b = client.get(f"/sessions/{sid}/briefing", params={"lang": "ta-IN"}).json()  # no LLM in tests
    text = " ".join([b["machine_summary"], b["job_summary"], *b["hazards"], *b["reminders"]])
    assert "அகழி தோண்டுதல்" in b["job_summary"] and "பொது 20 டன்" in b["machine_summary"]
    assert "கிழக்கு ஓரத்தின் அருகே மேல்நிலை மின் கம்பி" in b["hazards"]
    assert any("பக்கெட் பற்கள்" in h for h in b["hazards"])  # defect text translated too
    for english in ("Trench", "Overhead", "Generic", "bucket teeth", "Site 2"):
        assert english not in text, english

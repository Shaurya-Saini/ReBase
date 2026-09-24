"""Training Hub (E26/E27 + v2.3 plan / modules / quiz grading).

Content: data/training/<machine_type>_<level>.yaml — one pre-shift recap per
machine type × experience level, with `topics` (for matching) and, per quiz
question, an `explanation` + manual `source` (revealed only after submitting).
Translations: data/i18n/training/<lang>/<module_id>.json (generated once by
`python -m app.services.training_i18n`); English fallback.

The **plan** ranks modules for one operator from live data:
  next 7 days of assignments (machine + job hazards matched to module topics),
  safety alerts from the last 7 days (alert type → topic → module),
  being new to an assigned machine, and past quiz results (retake / level up).
Each item carries localized "why" reasons.
"""

import json
from collections import Counter
from datetime import date, datetime, timedelta
from functools import lru_cache

import yaml
from sqlmodel import Session, select

from app import models
from app.clock import IST, now_utc, today_ist
from app.config import BACKEND_DIR
from app.i18n import DEFAULT, term, tr_entity

TRAINING_DIR = BACKEND_DIR / "data" / "training"
TRAINING_I18N_DIR = BACKEND_DIR / "data" / "i18n" / "training"
LEVELS = ("novice", "intermediate", "expert")
PASS_PCT = 0.7        # passed = at least 70 % correct
LEVEL_UP_PCT = 0.8    # suggest the next level at 80 %+
PLAN_DAYS = 7
MAX_ITEMS = 5

ALERT_TOPICS = {
    "seatbelt_off": {"seatbelt", "startup"},
    "proximity": {"proximity"},
    "overheat": {"overheat"},
    "overload": {"overload"},
    "excessive_idle": {"idle"},
    "unsafe_operation": {"unsafe_operation"},
    "drowsiness": set(), "distraction": set(), "operator_absent": set(),  # → machine basics
}
HAZARD_TOPICS = [  # keyword in the (English) job hazard → module topics
    ("power line", {"power_lines"}), ("soft ground", {"slopes"}), ("slope", {"slopes"}), ("rain", {"slopes"}),
    ("crew", {"proximity"}), ("traffic", {"proximity"}), ("bench edge", {"bench_edge"}),
    ("dust", {"dust"}), ("visibility", {"haul"}), ("slippery", {"haul"}), ("haul road", {"haul"}),
    ("loose rock", {"stuck_string", "drilling"}),
]
WEIGHTS = {"recent_alert": 6, "job_hazard": 4, "retake": 4, "assigned": 3, "new_machine": 3,
           "level_up": 2, "keep_fresh": 1}

REASONS = {
    "en-IN": {
        "assigned": "Your {machine} job {when}: {job}",
        "job_hazard": "Hazard on your job: {hazard}",
        "recent_alert": "{count} {alert} alert(s) in the last 7 days",
        "new_machine": "You're new to the {machine}",
        "retake": "Last score {score}/{total}: retake to pass",
        "level_up": "You scored {score}/{total} at {level} level: ready for the next level",
        "keep_fresh": "Keep your {machine} skills fresh",
        "today": "today", "tomorrow": "tomorrow", "on": "on {date}",
    },
    "hi-IN": {
        "assigned": "{when} आपका {machine} काम: {job}",
        "job_hazard": "आपके काम का खतरा: {hazard}",
        "recent_alert": "पिछले 7 दिनों में {count} {alert} अलर्ट",
        "new_machine": "आप {machine} पर नए हैं",
        "retake": "पिछला स्कोर {score}/{total}: पास होने के लिए दोबारा करें",
        "level_up": "{level} स्तर पर आपका स्कोर {score}/{total}: अगले स्तर के लिए तैयार",
        "keep_fresh": "अपने {machine} कौशल को ताज़ा रखें",
        "today": "आज", "tomorrow": "कल", "on": "{date} को",
    },
    "ta-IN": {
        "assigned": "{when} உங்கள் {machine} பணி: {job}",
        "job_hazard": "உங்கள் பணியின் ஆபத்து: {hazard}",
        "recent_alert": "கடந்த 7 நாட்களில் {count} {alert} எச்சரிக்கைகள்",
        "new_machine": "நீங்கள் {machine}-க்கு புதியவர்",
        "retake": "கடைசி மதிப்பெண் {score}/{total}: தேர்ச்சி பெற மீண்டும் செய்யுங்கள்",
        "level_up": "{level} நிலையில் {score}/{total}: அடுத்த நிலைக்குத் தயார்",
        "keep_fresh": "உங்கள் {machine} திறன்களைப் புதுப்பித்துக் கொள்ளுங்கள்",
        "today": "இன்று", "tomorrow": "நாளை", "on": "{date} அன்று",
    },
}
ALERT_NAMES = {
    "en-IN": {"seatbelt_off": "seatbelt", "proximity": "proximity", "overheat": "overheat", "overload": "overload",
              "excessive_idle": "idling", "unsafe_operation": "unsafe operation", "drowsiness": "drowsiness",
              "distraction": "distraction", "operator_absent": "out-of-seat"},
    "hi-IN": {"seatbelt_off": "सीटबेल्ट", "proximity": "नज़दीकी खतरे", "overheat": "ओवरहीट", "overload": "ओवरलोड",
              "excessive_idle": "आइडलिंग", "unsafe_operation": "असुरक्षित संचालन", "drowsiness": "उनींदापन",
              "distraction": "ध्यान भटकने", "operator_absent": "सीट से अनुपस्थित"},
    "ta-IN": {"seatbelt_off": "சீட் பெல்ட்", "proximity": "அருகாமை", "overheat": "அதிக வெப்ப", "overload": "அதிக சுமை",
              "excessive_idle": "செயலற்ற இயக்க", "unsafe_operation": "பாதுகாப்பற்ற இயக்க", "drowsiness": "தூக்கக் கலக்க",
              "distraction": "கவனச் சிதறல்", "operator_absent": "இருக்கையில் இல்லை"},
}


# ---------------------------------------------------------------- content

@lru_cache
def all_modules() -> dict[str, dict]:
    """module id → module dict (English, incl. topics + quiz explanations)."""
    modules = {}
    for path in sorted(TRAINING_DIR.glob("*.yaml")):
        m = yaml.safe_load(path.read_text())
        if m["id"] in modules:
            raise ValueError(f"Duplicate training module id {m['id']} in {path}")
        for q in m["quiz"]:
            if not 0 <= q["answer_index"] < len(q["options"]):
                raise ValueError(f"{m['id']}: answer_index out of range in {q['q']!r}")
        m["steps"] = [{"url": None, **s} for s in m["steps"]]
        m.setdefault("topics", [])
        modules[m["id"]] = m
    return modules


def module_for(machine_type: str, level: str) -> dict | None:
    for m in all_modules().values():
        if m["machine_type"] == machine_type and m["level"] == level:
            return m
    return None


def next_module(experience: dict[str, str], machine_type: str) -> dict | None:
    level = experience.get(machine_type, "novice")
    return module_for(machine_type, level) or module_for(machine_type, "novice")


@lru_cache
def _translation(lang: str, module_id: str) -> dict | None:
    path = TRAINING_I18N_DIR / lang / f"{module_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def localized(module: dict, lang: str) -> dict:
    """Module with display text in `lang` where a complete translation exists."""
    t = _translation(lang, module["id"]) if lang != DEFAULT else None
    if not t or len(t.get("steps", [])) != len(module["steps"]) or len(t.get("quiz", [])) != len(module["quiz"]):
        return module
    quiz = []
    for q, tq in zip(module["quiz"], t["quiz"]):
        ok = len(tq.get("options", [])) == len(q["options"])
        quiz.append({**q, "q": tq.get("q") or q["q"], "options": tq["options"] if ok else q["options"],
                     "explanation": tq.get("explanation") or q["explanation"]})
    return {**module, "title": t.get("title") or module["title"],
            "steps": [{**s, "content": c or s["content"]} for s, c in zip(module["steps"], t["steps"])],
            "quiz": quiz}


# ---------------------------------------------------------------- grading

def grade(module: dict, answers: list[int | None]) -> dict:
    results, score = [], 0
    for i, (q, chosen) in enumerate(zip(module["quiz"], answers)):
        correct = chosen == q["answer_index"]
        score += correct
        results.append({"index": i, "chosen": chosen, "correct_index": q["answer_index"], "correct": correct,
                        "explanation": q["explanation"],
                        "source": {"doc": f"{module['machine_type']}_manual.md", "section": q["source"]}})
    total = len(module["quiz"])
    return {"module_id": module["id"], "score": score, "total": total,
            "passed": score >= PASS_PCT * total, "results": results}


# ---------------------------------------------------------------- plan

def _pct(c: models.TrainingCompletion) -> float:
    total = len(all_modules()[c.module_id]["quiz"]) if c.module_id in all_modules() else 0
    return c.score / total if total else 0.0


def _ist_day(ts: datetime) -> date:
    return ts.astimezone(IST).date()


def progress(completions: list[models.TrainingCompletion], today: date) -> dict:
    pcts = [_pct(c) for c in completions]
    passed = {c.module_id for c in completions if _pct(c) >= PASS_PCT}
    days = {_ist_day(c.completed_at) for c in completions}
    streak, d = 0, today if today in days else today - timedelta(days=1)
    while d in days:
        streak, d = streak + 1, d - timedelta(days=1)
    return {"attempts": len(completions), "modules_passed": len(passed),
            "avg_score_pct": round(100 * sum(pcts) / len(pcts)) if pcts else None, "streak_days": streak}


def build_plan(db: Session, operator: models.Operator, lang: str = DEFAULT, now: datetime | None = None) -> dict:
    now = now or now_utc()
    today = today_ist(now)
    phr = REASONS.get(lang, REASONS[DEFAULT])
    machine_name = lambda t: term(lang, "machine_types", t, t.replace("_", " "))  # noqa: E731
    mods = all_modules()
    cand: dict[str, dict] = {}

    def add(module: dict | None, code: str, text: str, boost: int = 0):
        if module is None:
            return
        c = cand.setdefault(module["id"], {"score": 0, "reasons": []})
        if all((r["code"], r["text"]) != (code, text) for r in c["reasons"]):
            c["reasons"].append({"code": code, "text": text})
            c["score"] += WEIGHTS[code] + boost

    exp = operator.experience
    # 1. upcoming assignments: machine + job hazards
    upcoming = db.exec(select(models.Assignment).where(
        models.Assignment.operator_id == operator.id, models.Assignment.date >= today,
        models.Assignment.date < today + timedelta(days=PLAN_DAYS)).order_by(models.Assignment.date)).all()
    for a in upcoming:
        job = db.get(models.Job, a.job_id)
        mt = job.machine_type
        soon = 1 if a.date == today else 0
        when = phr["today"] if a.date == today else phr["tomorrow"] if a.date == today + timedelta(days=1) \
            else phr["on"].format(date=a.date.isoformat())
        level = exp.get(mt, "novice")
        job_title = tr_entity(lang, "jobs", job.id, "title", job.title)
        add(module_for(mt, level), "assigned", phr["assigned"].format(machine=machine_name(mt), when=when, job=job_title), soon)
        if mt not in exp:
            add(module_for(mt, "novice"), "new_machine", phr["new_machine"].format(machine=machine_name(mt)), soon)
        hazards_local = tr_entity(lang, "jobs", job.id, "hazards", list(job.hazards))
        for hz_en, hz_local in zip(job.hazards, hazards_local):
            topics = set().union(*(t for kw, t in HAZARD_TOPICS if kw in hz_en.lower())) if hz_en else set()
            for m in mods.values():
                if m["machine_type"] == mt and topics & set(m["topics"]):
                    add(m, "job_hazard", phr["job_hazard"].format(hazard=hz_local), soon)

    # 2. safety alerts from the operator's sessions in the last 7 days
    rows = db.exec(select(models.Alert, models.WorkSession).where(
        models.Alert.session_id == models.WorkSession.id, models.WorkSession.operator_id == operator.id,
        models.Alert.ts >= now - timedelta(days=PLAN_DAYS))).all()
    counts = Counter((db.get(models.Machine, s.machine_id).type, a.type) for a, s in rows)
    for (mt, atype), n in counts.items():
        topics = ALERT_TOPICS.get(atype, set())
        matches = [m for m in mods.values() if m["machine_type"] == mt and topics & set(m["topics"])] \
            or [module_for(mt, "novice")]
        text = phr["recent_alert"].format(count=n, alert=ALERT_NAMES.get(lang, ALERT_NAMES[DEFAULT]).get(atype, atype))
        for m in matches:
            add(m, "recent_alert", text, min(n, 3))

    # 3. past results: retake / level up
    completions = db.exec(select(models.TrainingCompletion).where(
        models.TrainingCompletion.operator_id == operator.id).order_by(models.TrainingCompletion.completed_at)).all()
    last: dict[str, models.TrainingCompletion] = {}
    for c in completions:
        last[c.module_id] = c
    upcoming_types = {db.get(models.Job, a.job_id).machine_type for a in upcoming}
    for mid, c in last.items():
        m = mods.get(mid)
        if m is None:
            continue
        total = len(m["quiz"])
        if _pct(c) < PASS_PCT:
            add(m, "retake", phr["retake"].format(score=int(c.score), total=total))
        elif _pct(c) >= LEVEL_UP_PCT and m["level"] != "expert" and m["machine_type"] in upcoming_types \
                and exp.get(m["machine_type"], "novice") == m["level"]:
            nxt = module_for(m["machine_type"], LEVELS[LEVELS.index(m["level"]) + 1])
            add(nxt, "level_up", phr["level_up"].format(score=int(c.score), total=total,
                                                         level=term(lang, "levels", m["level"], m["level"])))

    # 4. nothing coming up → keep their own machines fresh
    if not cand:
        for mt, level in exp.items():
            add(module_for(mt, level), "keep_fresh", phr["keep_fresh"].format(machine=machine_name(mt)))

    def status(mid: str) -> str:
        c = last.get(mid)
        return "done" if c and _ist_day(c.completed_at) == today and _pct(c) >= PASS_PCT else "todo"

    ranked = sorted(cand.items(), key=lambda kv: (status(kv[0]) == "done", -kv[1]["score"], kv[0]))[:MAX_ITEMS]
    items = []
    for i, (mid, c) in enumerate(ranked, 1):
        m = localized(mods[mid], lang)
        lc = last.get(mid)
        items.append({
            "module_id": mid, "title": m["title"], "machine_type": m["machine_type"], "level": m["level"],
            "duration_min": m["duration_min"], "priority": i, "status": status(mid),
            "reasons": sorted(c["reasons"], key=lambda r: -WEIGHTS[r["code"]]),
            "last_result": {"score": int(lc.score), "total": len(m["quiz"]), "at": lc.completed_at} if lc else None,
        })
    return {"operator_id": operator.id, "date": today, "lang": lang,
            "total_minutes": sum(it["duration_min"] for it in items if it["status"] == "todo"),
            "items": items, "progress": progress(completions, today)}

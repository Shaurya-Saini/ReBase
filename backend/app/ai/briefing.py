"""Operational briefing (E15): LLM in the operator's language, template fallback.

The facts (machine, job, estimate, hazards, defects, fatigue) are gathered
here; the LLM only rewrites them as a short briefing in `lang`. Without an LLM
(no key, timeout, refusal) the template below produces the same shape, with
fixed phrases in en/hi/ta; free-text data (job titles, site hazards) stays in
English in that case. Hindi/Tamil phrases want a native-speaker review.
"""

import logging
from datetime import datetime

from sqlmodel import Session

from app import models
from app.ai.llm import LLMUnavailable, complete_json
from app.clock import IST, today_ist
from app.services import sessions as svc
from app.services.estimates import predict_job
from app.services.fatigue import operator_fatigue
from app.views import get_or_404

log = logging.getLogger(__name__)

PHRASES = {
    "en-IN": {
        "machine": "{model}, {hours} hours on the meter, last inspection {when}.",
        "today": "today", "yesterday": "yesterday", "on": "on {date}", "never": "not recorded",
        "job": "{title} at {site}. Planned {planned} h, starting {time}.",
        "rain": "Wet ground: reduce speed and watch for soft edges",
        "heat": "High heat: watch hydraulic and engine temperature, drink water",
        "wind": "Strong wind: watch for dust and flying debris",
        "defect": "Reported defect: {text}",
        "seatbelt": "Wear your seatbelt at all times",
        "crew": "Keep 10 m from the ground crew unless signalled",
        "excavator": "Never swing the bucket over people or vehicles",
        "wheel_loader": "Carry the bucket low when travelling",
        "drill_rig": "Keep clear of the rotating drill string",
        "dump_truck": "Never raise the body on a slope or near power lines",
        "fatigue": "You are close to your working-hour limit: take regular breaks",
    },
    "hi-IN": {
        "machine": "{model}, मीटर पर {hours} घंटे, अंतिम निरीक्षण {when}।",
        "today": "आज", "yesterday": "कल", "on": "{date} को", "never": "दर्ज नहीं",
        "job": "{title}, {site}। नियोजित {planned} घंटे, शुरुआत {time} बजे।",
        "rain": "गीली ज़मीन: गति कम रखें और नरम किनारों से सावधान रहें",
        "heat": "अधिक गर्मी: हाइड्रोलिक और इंजन तापमान पर नज़र रखें, पानी पीते रहें",
        "wind": "तेज़ हवा: धूल और उड़ते मलबे से सावधान रहें",
        "defect": "दर्ज की गई खराबी: {text}",
        "seatbelt": "हर समय सीटबेल्ट पहनें",
        "crew": "संकेत के बिना ज़मीनी कर्मचारियों से 10 मीटर दूर रहें",
        "excavator": "बाल्टी को कभी भी लोगों या वाहनों के ऊपर से न घुमाएँ",
        "wheel_loader": "चलते समय बाल्टी नीचे रखें",
        "drill_rig": "घूमते ड्रिल स्ट्रिंग से दूर रहें",
        "dump_truck": "ढलान पर या बिजली की लाइनों के पास बॉडी कभी न उठाएँ",
        "fatigue": "आप कार्य-घंटों की सीमा के करीब हैं: बीच-बीच में आराम करें",
    },
    "ta-IN": {
        "machine": "{model}, மீட்டரில் {hours} மணி நேரம், கடைசி ஆய்வு {when}.",
        "today": "இன்று", "yesterday": "நேற்று", "on": "{date} அன்று", "never": "பதிவு இல்லை",
        "job": "{title}, {site}. திட்டமிட்ட நேரம் {planned} மணி, தொடக்கம் {time}.",
        "rain": "ஈரமான தரை: வேகத்தைக் குறைத்து, மென்மையான ஓரங்களில் கவனமாக இருங்கள்",
        "heat": "அதிக வெப்பம்: ஹைட்ராலிக் மற்றும் இன்ஜின் வெப்பநிலையைக் கவனியுங்கள், தண்ணீர் குடியுங்கள்",
        "wind": "பலத்த காற்று: தூசி மற்றும் பறக்கும் குப்பைகளில் கவனமாக இருங்கள்",
        "defect": "பதிவான குறைபாடு: {text}",
        "seatbelt": "எப்போதும் சீட் பெல்ட் அணியுங்கள்",
        "crew": "சைகை இல்லாமல் தரைப் பணியாளர்களிடமிருந்து 10 மீ தூரம் இருங்கள்",
        "excavator": "வாளியை ஒருபோதும் மனிதர்கள் அல்லது வாகனங்கள் மேல் சுழற்றாதீர்கள்",
        "wheel_loader": "பயணிக்கும்போது வாளியைத் தாழ்வாக வைத்திருங்கள்",
        "drill_rig": "சுழலும் டிரில் கம்பியிலிருந்து விலகி இருங்கள்",
        "dump_truck": "சரிவிலோ மின் கம்பிகளுக்கு அருகிலோ பெட்டியை ஒருபோதும் உயர்த்தாதீர்கள்",
        "fatigue": "நீங்கள் வேலை நேர வரம்பை நெருங்குகிறீர்கள்: இடையிடையே ஓய்வு எடுங்கள்",
    },
}

LANG_NAMES = {"en-IN": "English (India)", "hi-IN": "Hindi", "ta-IN": "Tamil", "te-IN": "Telugu"}

BRIEFING_SCHEMA = {
    "type": "object",
    "properties": {
        "machine_summary": {"type": "string"},
        "job_summary": {"type": "string"},
        "hazards": {"type": "array", "items": {"type": "string"}},
        "reminders": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["machine_summary", "job_summary", "hazards", "reminders"],
    "additionalProperties": False,
}

SYSTEM = (
    "You write pre-shift safety briefings for heavy-equipment operators, shown on a tablet in "
    "the cab and read aloud. Use short, plain sentences an operator can take in at a glance. "
    "Use only the facts provided; do not invent hazards, numbers or instructions. Keep every "
    "hazard and reminder from the facts, one per list item, and keep all numbers unchanged."
)

_cache: dict[tuple[str, str], dict] = {}


def _when(ts: datetime | None, p: dict) -> str:
    if ts is None:
        return p["never"]
    d = ts.astimezone(IST).date()
    days = (today_ist() - d).days
    return p["today"] if days <= 0 else p["yesterday"] if days == 1 else p["on"].format(date=d.isoformat())


def _facts(db: Session, s: models.WorkSession) -> dict:
    machine = get_or_404(db, models.Machine, s.machine_id)
    job = get_or_404(db, models.Job, s.job_id)
    op = get_or_404(db, models.Operator, s.operator_id)
    return {
        "machine": machine, "job": job, "operator": op,
        "estimate": predict_job(db, job, experience=op.experience.get(job.machine_type)),
        "defects": svc.defects(db, s),
        "rest": operator_fatigue(db, op).rest,
    }


def template_briefing(f: dict, lang: str) -> dict:
    p = PHRASES.get(lang, PHRASES["en-IN"])
    m, j = f["machine"], f["job"]
    hazards = list(j.hazards)
    if j.weather in ("rain", "heat", "wind"):
        hazards.append(p[j.weather])
    for d in f["defects"]:
        hazards.append(p["defect"].format(text=d["text"]) + (f" ({d['note']})" if d["note"] else ""))
    reminders = [p["seatbelt"], p["crew"], p[m.type]]
    if f["rest"]["status"] == "warning":
        reminders.append(p["fatigue"])
    return {
        "machine_summary": p["machine"].format(model=m.model, hours=f"{m.hour_meter:.0f}",
                                               when=_when(m.last_inspection, p)),
        "job_summary": p["job"].format(title=j.title, site=j.site, planned=f"{j.planned_hours:g}",
                                       time=j.scheduled_start.astimezone(IST).strftime("%H:%M")),
        "hazards": hazards,
        "reminders": reminders,
    }


def _llm_briefing(f: dict, draft: dict, lang: str) -> dict:
    j, est = f["job"], f["estimate"]
    prompt = (
        f"Write the briefing in {LANG_NAMES.get(lang, 'English')}.\n\n"
        f"Operator: {f['operator'].name}\n"
        f"Machine: {draft['machine_summary']}\n"
        f"Job: {draft['job_summary']}\n"
        f"Estimated duration: {est.estimated_hours} h (range {est.range_hours[0]}–{est.range_hours[1]} h); "
        f"weather: {j.weather}\n"
        "Hazards:\n" + "\n".join(f"- {h}" for h in draft["hazards"]) + "\n"
        "Reminders:\n" + "\n".join(f"- {r}" for r in draft["reminders"])
    )
    out = complete_json(SYSTEM, prompt, BRIEFING_SCHEMA)
    if not out.get("hazards") and draft["hazards"]:
        raise LLMUnavailable("LLM dropped the hazards")
    return out


def build(db: Session, s: models.WorkSession, lang: str) -> dict:
    """Briefing for a session in `lang` (cached per session + language)."""
    if (s.id, lang) in _cache:
        return _cache[(s.id, lang)]
    f = _facts(db, s)
    draft = template_briefing(f, "en-IN")
    try:
        body = _llm_briefing(f, draft, lang)
    except LLMUnavailable as e:
        log.info("briefing: template fallback (%s)", e)
        body = template_briefing(f, lang)
    result = {"session_id": s.id, "lang": lang, "estimated_hours": f["estimate"].estimated_hours, **body}
    _cache[(s.id, lang)] = result
    return result

"""AI-produced narrated video lessons (prototype).

Run:  python -m app.ai.video_lesson --operator op_001 --lang ta-IN
      → data/media/videos/<video_id>.mp4 (+ .srt subtitles, .json storyboard)

Pipeline (everything grounded in our own content — nothing is invented):
1. Context   today's assignment for the operator → job hazards + weather →
             matching manual sections (vector search) + core safety sections.
2. Script    the LLM writes a 5–7 scene storyboard in the operator's language
             (heading, 2–3 points, narration, highlight, icon, source section).
             Grounding guard: any number the LLM uses must appear in the facts
             it was given, otherwise that scene falls back to template text.
             No LLM → template storyboard in English.
3. Voice     neural TTS per language (edge-tts), gTTS as fallback.
4. Slides    Pillow draws the layout, icon, highlight and progress bar; all
             Tamil/Hindi text is drawn by ffmpeg's libass (HarfBuzz shaping) —
             Pillow here can't shape Indic scripts.
5. Video     per scene: slow zoom over the slide + narration; concatenated,
             text burned in; SRT + storyboard JSON saved alongside.
"""

import argparse
import asyncio
import hashlib
import json
import logging
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sqlmodel import Session, select

from app import models
from app.ai import rag
from app.ai.briefing import LANG_NAMES
from app.ai.llm import LLMUnavailable, complete_json
from app.clock import today_ist
from app.config import BACKEND_DIR
from app.db import engine

log = logging.getLogger(__name__)

W, H, FPS = 1280, 720, 25
FONT_DIR = BACKEND_DIR / "data" / "fonts"
OUT_DIR = BACKEND_DIR / "data" / "media" / "videos"
SCRIPT_FONTS = {"ta-IN": "Noto Sans Tamil", "hi-IN": "Noto Sans Devanagari", "en-IN": "Noto Sans"}
EDGE_VOICES = {"ta-IN": "ta-IN-PallaviNeural", "hi-IN": "hi-IN-SwaraNeural", "en-IN": "en-IN-NeerjaNeural"}
GTTS_LANG = {"ta-IN": "ta", "hi-IN": "hi", "en-IN": "en"}
ICONS = ("warning", "power_line", "ground", "crew", "machine", "check")
CORE_SECTIONS = ("1.2 Working near power lines", "1.3 Ground crew and swing area", "4.6 Working on slopes")
PAD_S = 0.7  # silence after each scene's narration
M = 64  # safe margin: nothing is drawn closer than this to an edge
ZOOM_MAX = 1.025  # gentle push-in; crops ≤ 1.25 % per side, well inside M

# Palette (RGB)
BG, PANEL, INK, MUTED = (22, 30, 40), (32, 43, 56), (235, 240, 245), (140, 155, 170)
AMBER, RED, GREEN, BLUE = (255, 183, 3), (230, 57, 70), (46, 196, 132), (72, 149, 239)
ICON_COLOUR = {"warning": AMBER, "power_line": RED, "ground": AMBER, "crew": BLUE,
               "machine": BLUE, "check": GREEN}


@dataclass
class Scene:
    heading: str
    points: list[str]
    narration: str
    highlight: str = ""
    icon: str = "warning"
    source: str = ""  # manual section title
    duration: float = 0.0


@dataclass
class Storyboard:
    title: str
    lang: str
    machine_type: str
    operator_id: str
    job_id: str
    generated_by: str  # "llm" | "template"
    scenes: list[Scene] = field(default_factory=list)


# ---------------------------------------------------------------- 1. context

def gather_context(db: Session, operator_id: str) -> dict:
    op = db.get(models.Operator, operator_id)
    if op is None:
        raise ValueError(f"Unknown operator {operator_id}")
    asg = db.exec(select(models.Assignment).where(models.Assignment.operator_id == operator_id,
                                                  models.Assignment.date >= today_ist())
                  .order_by(models.Assignment.date)).first()
    if asg is None:
        raise ValueError(f"No upcoming assignment for {operator_id}")
    job = db.get(models.Job, asg.job_id)
    machine = db.get(models.Machine, asg.machine_id)

    rag.build()
    by_title = {c.section: c for c in rag.all_chunks() if c.machine_type == machine.type}
    sections: dict[str, str] = {}
    queries = list(job.hazards) + ([f"working in {job.weather}"] if job.weather != "clear" else [])
    for q in queries:
        for hit in rag.relevant(rag.retrieve(q, machine.type, k=1)):
            sections.setdefault(hit.section, hit.text)
    for title in CORE_SECTIONS:
        if title in by_title:
            sections.setdefault(title, by_title[title].body)
    return {"operator": op, "job": job, "machine": machine, "assignment": asg,
            "sections": dict(list(sections.items())[:5])}


# ---------------------------------------------------------------- 2. script

STORYBOARD_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "scenes": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "heading": {"type": "string"},
                "points": {"type": "array", "items": {"type": "string"}},
                "narration": {"type": "string"},
                "highlight": {"type": "string"},
                "icon": {"type": "string", "enum": list(ICONS)},
                "source": {"type": "string"},
            },
            "required": ["heading", "points", "narration", "highlight", "icon", "source"],
            "additionalProperties": False,
        }},
    },
    "required": ["title", "scenes"],
    "additionalProperties": False,
}

SYSTEM = (
    "You write short pre-shift safety video lessons for heavy-equipment operators. "
    "Use ONLY the facts provided (job hazards and manual sections); never add rules, numbers or "
    "steps that are not in them, and keep every number and unit exactly as given. "
    "Write 5 to 7 scenes: an opening scene about today's job, one scene per hazard or manual "
    "section, and a closing recap. Each scene: a heading of at most 6 words, 2 or 3 points of at "
    "most 8 words each, a narration of 2 or 3 short spoken sentences, a highlight that is a key "
    "number with its unit from the facts (e.g. '6 m') or an empty string, one icon, and the exact "
    "manual section title it is based on (or an empty string for the opening/recap). "
    "Address the operator directly, calm and clear."
)

_NUM = re.compile(r"\d+(?:[.,]\d+)?")


def _numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in _NUM.findall(text)}


def _facts_text(ctx: dict) -> str:
    j, m = ctx["job"], ctx["machine"]
    lines = [f"Job: {j.title} at {j.site}. Planned {j.planned_hours:g} h. Weather: {j.weather}.",
             f"Machine: {m.model} ({m.type.replace('_', ' ')}).",
             "Job hazards: " + "; ".join(j.hazards)]
    for title, text in ctx["sections"].items():
        lines.append(f"\n[{title}]\n{text}")
    return "\n".join(lines)


def template_storyboard(ctx: dict) -> Storyboard:
    """No LLM: English storyboard straight from the manual sections."""
    j, m, op = ctx["job"], ctx["machine"], ctx["operator"]
    scenes = [Scene(heading="Today's job", points=[j.title, j.site, f"Weather: {j.weather}"],
                    narration=f"Hello {op.name.split()[0]}. Today's job is {j.title} at {j.site}. "
                              f"Here are the hazards to watch.", icon="machine")]
    for title, text in ctx["sections"].items():
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        nums = _NUM.findall(text)
        scenes.append(Scene(heading=re.sub(r"^\d+(\.\d+)*\s+", "", title),
                            points=[s[:60] for s in sentences[:3]],
                            narration=" ".join(sentences[:2]),
                            highlight=(nums[0] + (" m" if " m" in text else "")) if nums else "",
                            icon="power_line" if "power" in title.lower() else
                                 "crew" if "crew" in title.lower() else
                                 "ground" if "slope" in title.lower() else "warning",
                            source=title))
    scenes.append(Scene(heading="Before you start", points=["Seatbelt on", "Area clear", "Report defects"],
                        narration="Fasten your seatbelt, check the area is clear and report any defect. Work safely.",
                        icon="check"))
    return Storyboard(title=f"Pre-shift safety: {j.title}", lang="en-IN", machine_type=m.type,
                      operator_id=op.id, job_id=j.id, generated_by="template", scenes=scenes)


def llm_storyboard(ctx: dict, lang: str) -> Storyboard:
    op, j, m = ctx["operator"], ctx["job"], ctx["machine"]
    level = op.experience.get(m.type, "novice")
    facts = _facts_text(ctx)
    prompt = (f"Language: {LANG_NAMES.get(lang, 'English')} (write everything in this language; "
              f"keep technical words like power line/boom in the language's usual form).\n"
              f"Operator: {op.name}, {level} on this machine.\n\nFACTS:\n{facts}")
    out = complete_json(SYSTEM, prompt, STORYBOARD_SCHEMA, max_tokens=4000)
    allowed_numbers = _numbers(facts) | {str(i) for i in range(1, 11)}  # counting words are fine
    valid_sources = set(ctx["sections"])
    template = {s.source: s for s in template_storyboard(ctx).scenes if s.source}
    scenes = []
    for raw in out.get("scenes", [])[:8]:
        s = Scene(heading=raw["heading"].strip(), points=[p.strip() for p in raw["points"][:3] if p.strip()],
                  narration=raw["narration"].strip(), highlight=raw["highlight"].strip(),
                  icon=raw["icon"] if raw["icon"] in ICONS else "warning",
                  source=raw["source"] if raw["source"] in valid_sources else "")
        invented = _numbers(" ".join([s.narration, s.highlight, *s.points])) - allowed_numbers
        if invented:
            log.warning("video: scene %r used numbers not in the facts %s → template scene",
                        s.heading, sorted(invented))
            fallback = template.get(s.source)
            if fallback is None:
                continue
            s = fallback
        if s.narration:
            scenes.append(s)
    if len(scenes) < 3:
        raise LLMUnavailable("storyboard too short after grounding checks")
    return Storyboard(title=out.get("title") or j.title, lang=lang, machine_type=m.type, operator_id=op.id,
                      job_id=j.id, generated_by="llm", scenes=scenes)


def make_storyboard(ctx: dict, lang: str) -> Storyboard:
    try:
        return llm_storyboard(ctx, lang)
    except LLMUnavailable as e:
        log.info("video: LLM storyboard unavailable (%s) → English template", e)
        return template_storyboard(ctx)


# ---------------------------------------------------------------- 3. voice

def _ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def media_duration(path: Path) -> float:
    err = subprocess.run([_ffmpeg(), "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if not m:
        raise RuntimeError(f"can't read duration of {path}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def tts(text: str, lang: str, out: Path) -> None:
    """Narration audio (mp3). edge-tts neural voice, gTTS fallback."""
    try:
        import edge_tts

        asyncio.run(edge_tts.Communicate(text, EDGE_VOICES.get(lang, EDGE_VOICES["en-IN"])).save(str(out)))
        if out.stat().st_size > 0:
            return
    except Exception as e:  # noqa: BLE001
        log.info("video: edge-tts failed (%s) → gTTS", e)
    from gtts import gTTS

    gTTS(text, lang=GTTS_LANG.get(lang, "en")).save(str(out))


# ---------------------------------------------------------------- 4. slides

def _font(size: int):
    from PIL import ImageFont

    return ImageFont.truetype(str(FONT_DIR / "NotoSans.ttf"), size)


def _draw_icon(d, kind: str, cx: int, cy: int, r: int) -> None:
    c = ICON_COLOUR.get(kind, AMBER)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=8)
    if kind == "power_line":  # lightning bolt
        pts = [(cx + 8, cy - r * .62), (cx - r * .3, cy + 6), (cx + 2, cy + 6),
               (cx - 10, cy + r * .62), (cx + r * .32, cy - 10), (cx - 2, cy - 10)]
        d.polygon(pts, fill=c)
    elif kind == "ground":  # slope with a crack
        d.polygon([(cx - r * .6, cy + r * .45), (cx + r * .6, cy + r * .45), (cx + r * .6, cy - r * .35)], fill=c)
        d.line([(cx + r * .1, cy + r * .45), (cx + r * .2, cy + r * .1), (cx + r * .05, cy - r * .02)], fill=BG, width=7)
    elif kind == "crew":  # worker in a hard hat: helmet dome + brim, face, shoulders
        hy = cy - r * .30
        d.pieslice([cx - 34, hy - 34, cx + 34, hy + 34], 180, 360, fill=c)          # helmet dome
        d.rounded_rectangle([cx - 44, hy - 4, cx + 44, hy + 6], radius=4, fill=c)    # brim
        d.ellipse([cx - 22, hy + 10, cx + 22, hy + 52], fill=c)                      # face
        d.pieslice([cx - 58, cy + r * .20, cx + 58, cy + r * .20 + 116], 180, 360, fill=c)  # shoulders
    elif kind == "machine":  # excavator-ish silhouette
        d.rounded_rectangle([cx - r * .55, cy + r * .2, cx + r * .35, cy + r * .45], radius=10, fill=c)
        d.rectangle([cx - r * .4, cy - r * .1, cx + r * .1, cy + r * .2], fill=c)
        d.line([(cx + r * .05, cy - r * .05), (cx + r * .4, cy - r * .45), (cx + r * .58, cy - r * .05)], fill=c, width=12)
    elif kind == "check":
        d.line([(cx - r * .45, cy), (cx - r * .1, cy + r * .35), (cx + r * .5, cy - r * .35)], fill=c, width=16)
    else:  # warning triangle with "!"
        d.polygon([(cx, cy - r * .6), (cx - r * .62, cy + r * .45), (cx + r * .62, cy + r * .45)], fill=c)
        d.rectangle([cx - 6, cy - r * .25, cx + 6, cy + r * .12], fill=BG)
        d.ellipse([cx - 7, cy + r * .2, cx + 7, cy + r * .34], fill=BG)


def _short_highlight(text: str) -> str:
    """'15 degrees' → '15°', '6 metres' → '6 m': shorter, language-neutral."""
    t = text.strip()
    t = re.sub(r"\s*degrees?\b", "°", t, flags=re.I)
    t = re.sub(r"\s*(metres?|meters?)\b", " m", t, flags=re.I)
    t = re.sub(r"\s*(hours?|hrs?)\b", " h", t, flags=re.I)
    t = re.sub(r"\s*(minutes?|mins?)\b", " min", t, flags=re.I)
    return t


def render_slide(scene: Scene, index: int, total: int, sb: Storyboard, out: Path) -> None:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    accent = ICON_COLOUR.get(scene.icon, AMBER)
    d.rounded_rectangle([M, 30, W - M, 38], radius=4, fill=accent)
    d.rounded_rectangle([M, 150, 830, 540], radius=24, fill=PANEL)       # text panel (text via libass)
    _draw_icon(d, scene.icon, 1025, 280, 120)
    hl = _short_highlight(scene.highlight)
    # Pillow can't shape Indic scripts; Latin, digits and symbols like ° are fine.
    if hl and all(ord(ch) < 0x0900 for ch in hl):
        size, max_w = 96, (W - M) - 860  # right column: x 860 … W-M
        while size > 40 and d.textlength(hl, font=_font(size)) > max_w:
            size -= 4
        f = _font(size)
        tw = d.textlength(hl, font=f)
        d.text((1025 - tw / 2, 430 + (96 - size) // 2), hl, font=f, fill=accent)
    d.text((M, 58), "REBASE  ·  PRE-SHIFT TRAINING", font=_font(22), fill=MUTED)
    label = f"{sb.machine_type.replace('_', ' ').upper()}  ·  {sb.job_id}"
    d.text((W - M - d.textlength(label, font=_font(22)), 58), label, font=_font(22), fill=MUTED)
    if scene.source:
        d.text((M, 552), f"Manual § {scene.source}", font=_font(20), fill=MUTED)
    seg = (W - 2 * M) / total
    for i in range(total):
        d.rounded_rectangle([M + i * seg + 3, H - 44, M + (i + 1) * seg - 3, H - 36], radius=4,
                            fill=accent if i <= index else PANEL)
    img.save(out)


# ---------------------------------------------------------------- 5. text + video

def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


def _ts(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _srt_ts(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"


def build_ass(sb: Storyboard) -> str:
    # Layout budget inside the text panel (y 150–540): heading at y 175 has room for
    # two wrapped lines (40 px font); points start at y 300, 72 px apart.
    font = SCRIPT_FONTS.get(sb.lang, "Noto Sans")
    style = ("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
             "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
             "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding")
    head = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "",
        "[V4+ Styles]", style,
        f"Style: Heading,{font},40,&H00F5F0EB,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,7,94,470,0,1",
        f"Style: Point,{font},30,&H00F5F0EB,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,70,480,0,1",
        f"Style: Sub,{font},28,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,3,10,0,2,94,94,68,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    ev, t = [], 0.0
    for s in sb.scenes:
        a, b = _ts(t), _ts(t + s.duration)
        ev.append(f"Dialogue: 0,{a},{b},Heading,,0,0,0,,{{\\pos(94,175)\\fad(250,0)}}{_ass_escape(s.heading)}")
        for i, p in enumerate(s.points):
            ev.append(f"Dialogue: 0,{_ts(t + 0.4 + 0.5 * i)},{b},Point,,0,0,0,,"
                      f"{{\\pos(94,{300 + i * 72})\\fad(300,0)}}•  {_ass_escape(p)}")
        ev.append(f"Dialogue: 0,{a},{_ts(t + s.duration - PAD_S)},Sub,,0,0,0,,{_ass_escape(s.narration)}")
        t += s.duration
    return "\n".join(head + ev) + "\n"


def build_srt(sb: Storyboard) -> str:
    out, t = [], 0.0
    for i, s in enumerate(sb.scenes, 1):
        out += [str(i), f"{_srt_ts(t)} --> {_srt_ts(t + s.duration - PAD_S)}", s.narration, ""]
        t += s.duration
    return "\n".join(out)


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {r.stderr[-800:]}")


def render_video(sb: Storyboard, out_path: Path, tts_fn=tts) -> Path:
    ff = _ffmpeg()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rebase-video-") as tmpd:
        tmp = Path(tmpd)
        parts = []
        for i, s in enumerate(sb.scenes):
            audio, slide, part = tmp / f"a{i}.mp3", tmp / f"s{i}.png", tmp / f"p{i}.mp4"
            tts_fn(s.narration, sb.lang, audio)
            s.duration = round(media_duration(audio) + PAD_S, 2)
            render_slide(s, i, len(sb.scenes), sb, slide)
            frames = int(s.duration * FPS)
            _run([ff, "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-i", str(slide), "-i", str(audio),
                  "-filter_complex",
                  f"[0:v]scale={W * 2}:-1,zoompan=z='min(zoom+0.0003,{ZOOM_MAX})':d={frames}"
                  f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}[v];[1:a]apad[a]",
                  "-map", "[v]", "-map", "[a]", "-t", f"{s.duration}", "-c:v", "libx264", "-preset", "veryfast",
                  "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100", "-ac", "1", str(part)])
            parts.append(part)
        concat = tmp / "list.txt"
        concat.write_text("".join(f"file '{p}'\n" for p in parts))
        joined = tmp / "joined.mp4"
        _run([ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
              "-c", "copy", str(joined)])
        ass = tmp / "text.ass"
        ass.write_text(build_ass(sb), encoding="utf-8")
        _run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(joined),
              "-vf", f"ass={ass}:fontsdir={FONT_DIR}", "-c:v", "libx264", "-preset", "veryfast",
              "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(out_path)])
    return out_path


# ---------------------------------------------------------------- entry point

def load_storyboard(path: Path) -> Storyboard:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    data["scenes"] = [Scene(**{**s, "duration": 0.0}) for s in data["scenes"]]
    return Storyboard(**data)


def generate(operator_id: str, lang: str, out_dir: Path = OUT_DIR, tts_fn=tts,
             storyboard: Storyboard | None = None) -> dict:
    """Build (or reuse) a storyboard and render it. Pass `storyboard` to re-render
    an existing one without a new LLM call."""
    if storyboard is None:
        with Session(engine) as db:
            ctx = gather_context(db, operator_id)
        storyboard = make_storyboard(ctx, lang)
    sb = storyboard
    key = hashlib.sha256(json.dumps(asdict(sb), ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:8]
    video_id = f"vid_{sb.operator_id}_{sb.job_id}_{sb.lang}_{key}"
    mp4 = render_video(sb, out_dir / f"{video_id}.mp4", tts_fn=tts_fn)
    (out_dir / f"{video_id}.srt").write_text(build_srt(sb), encoding="utf-8")
    (out_dir / f"{video_id}.json").write_text(json.dumps(asdict(sb), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"video_id": video_id, "path": str(mp4), "lang": sb.lang, "generated_by": sb.generated_by,
            "scenes": len(sb.scenes), "duration_s": round(sum(s.duration for s in sb.scenes), 1)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for noisy in ("httpx", "sentence_transformers", "chromadb", "google_genai", "groq", "urllib3",
                  "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    p = argparse.ArgumentParser(description="Generate a narrated pre-shift video lesson")
    p.add_argument("--operator", default="op_001")
    p.add_argument("--lang", default="ta-IN", choices=list(SCRIPT_FONTS))
    p.add_argument("--storyboard", type=Path, help="re-render a saved storyboard .json (no LLM call)")
    args = p.parse_args()
    sb = load_storyboard(args.storyboard) if args.storyboard else None
    print(json.dumps(generate(args.operator, args.lang, storyboard=sb), ensure_ascii=False, indent=2))

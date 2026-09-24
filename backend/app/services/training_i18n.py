"""Translate Training Hub modules once and commit the result (no LLM needed at demo time).

Run:  python -m app.services.training_i18n            # missing hi-IN + ta-IN files
      python -m app.services.training_i18n --force    # redo all

Writes data/i18n/training/<lang>/<module_id>.json:
  {"title", "steps": [content…], "quiz": [{"q", "options": […], "explanation"}…]}
Guard: every translated string must keep exactly the numbers of its English
source (so "6 m" can't become "4 m"); a string that fails keeps its English
text. Structure mismatches keep the whole module in English.
"""

import argparse
import json
import logging
import re

from app.ai.briefing import LANG_NAMES
from app.ai.llm import LLMUnavailable, complete_json
from app.services.training import TRAINING_I18N_DIR, all_modules

log = logging.getLogger(__name__)
LANGS = ("hi-IN", "ta-IN")
SCRIPTS = {"hi-IN": ("Devanagari script (देवनागरी)", 0x0900, 0x097F),
           "ta-IN": ("Tamil script (தமிழ்)", 0x0B80, 0x0BFF)}
MIN_IN_SCRIPT = 0.8  # share of text strings that must be in the target script
_NUM = re.compile(r"\d+(?:[.,]\d+)?")

SYSTEM = (
    "You translate pre-shift safety training for heavy-equipment operators. Translate every string "
    "naturally and simply, as an experienced operator would say it. Keep all numbers, units and "
    "letters like P, E, L, B, M exactly as written, with Western digits (0-9). Keep common machine "
    "words (boom, bucket, joystick, hydraulic, …) in the form operators use in that language. "
    "Keep the same number of steps, questions and options, in the same order."
)


def _schema(module: dict) -> dict:
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "steps": {"type": "array", "items": {"type": "string"}},
            "quiz": {"type": "array", "items": {
                "type": "object",
                "properties": {"q": {"type": "string"}, "options": {"type": "array", "items": {"type": "string"}},
                               "explanation": {"type": "string"}},
                "required": ["q", "options", "explanation"], "additionalProperties": False}},
        },
        "required": ["title", "steps", "quiz"],
        "additionalProperties": False,
    }


def source_payload(m: dict) -> dict:
    return {"title": m["title"], "steps": [s["content"] for s in m["steps"]],
            "quiz": [{"q": q["q"], "options": q["options"], "explanation": q["explanation"]} for q in m["quiz"]]}


def _nums(text: str) -> list[str]:
    return sorted(n.replace(",", ".") for n in _NUM.findall(text))


def _in_script(text: str, lang: str) -> bool:
    _, lo, hi = SCRIPTS[lang]
    return any(lo <= ord(ch) <= hi for ch in text)


def guard(src: dict, out: dict, lang: str) -> tuple[dict, int]:
    """Keep translated strings only where numbers match the source. Reject the module if it isn't
    really in the target script (models sometimes answer in English or romanized text).
    Returns (result, #strings kept English)."""
    kept = 0

    def pick(en: str, tr) -> str:
        nonlocal kept
        if isinstance(tr, str) and tr.strip() and _nums(tr) == _nums(en):
            return tr.strip()
        kept += 1
        return en

    if len(out.get("steps", [])) != len(src["steps"]) or len(out.get("quiz", [])) != len(src["quiz"]):
        raise ValueError("structure mismatch")
    quiz = []
    for q_en, q_tr in zip(src["quiz"], out["quiz"]):
        if len(q_tr.get("options", [])) != len(q_en["options"]):
            raise ValueError("option count mismatch")
        quiz.append({"q": pick(q_en["q"], q_tr.get("q")),
                     "options": [pick(a, b) for a, b in zip(q_en["options"], q_tr["options"])],
                     "explanation": pick(q_en["explanation"], q_tr.get("explanation"))})
    result = {"title": pick(src["title"], out.get("title")),
              "steps": [pick(a, b) for a, b in zip(src["steps"], out["steps"])], "quiz": quiz}
    texts = [result["title"], *result["steps"],
             *[x for q in quiz for x in (q["q"], *q["options"], q["explanation"])]]
    wordy = [t for t in texts if re.search(r"[^\W\d_]{3,}", t)]  # has real words, not just "6 m"
    share = sum(_in_script(t, lang) for t in wordy) / max(1, len(wordy))
    if share < MIN_IN_SCRIPT:
        raise ValueError(f"only {share:.0%} of strings in {SCRIPTS[lang][0]}")
    return result, kept


def translate_module(m: dict, lang: str) -> tuple[dict, int]:
    src = source_payload(m)
    prompt = (f"Target language: {LANG_NAMES[lang]}, written in {SCRIPTS[lang][0]} — not in Latin letters.\n\n"
              f"{json.dumps(src, ensure_ascii=False)}")
    out = complete_json(SYSTEM, prompt, _schema(m), max_tokens=6000)
    return guard(src, out, lang)


def main(force: bool = False) -> None:
    for lang in LANGS:
        (TRAINING_I18N_DIR / lang).mkdir(parents=True, exist_ok=True)
        for mid, m in all_modules().items():
            path = TRAINING_I18N_DIR / lang / f"{mid}.json"
            if path.exists() and not force:
                continue
            try:
                data, kept = translate_module(m, lang)
            except (LLMUnavailable, ValueError) as e:
                print(f"  ✗ {lang} {mid}: {e} — stays English")
                continue
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  ✓ {lang} {mid}" + (f" ({kept} string(s) kept English by the number guard)" if kept else ""))


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    main(p.parse_args().force)

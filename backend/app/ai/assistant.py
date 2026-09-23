"""Manual Q&A assistant (E23): translate → retrieve → answer in the operator's language.

1. Hindi/Tamil question → English with the LLM (the embeddings are English,
   DECISIONS #17). English questions skip this step.
2. Retrieve the top-k sections of this machine's manual; keep those above
   rag.RELEVANCE_MIN.
3. Nothing relevant → say so in `lang` (never guess).
4. LLM answers in `lang` from those sections only, short enough to be read
   aloud in the cab, and names the sections it used → `sources`.

Without an LLM (no key, quota, timeout…) the best section is returned as-is,
in English, with `lang: "en-IN"` so the tablet speaks it with an English voice.
"""

import logging
import re

from app.ai import rag
from app.ai.briefing import LANG_NAMES
from app.ai.llm import LLMUnavailable, complete_json

log = logging.getLogger(__name__)

TOP_K = 3

NOT_FOUND = {
    "en-IN": "I couldn't find that in the {machine} manual. Please check with your supervisor.",
    "hi-IN": "मुझे यह {machine} मैनुअल में नहीं मिला। कृपया अपने सुपरवाइज़र से पूछें।",
    "ta-IN": "இதை {machine} கையேட்டில் கண்டுபிடிக்க முடியவில்லை. உங்கள் மேற்பார்வையாளரிடம் கேளுங்கள்.",
}

TRANSLATE_SCHEMA = {
    "type": "object",
    "properties": {"english": {"type": "string"}},
    "required": ["english"],
    "additionalProperties": False,
}

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answerable": {"type": "boolean"},
        "answer": {"type": "string"},
        "used_sections": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answerable", "answer", "used_sections"],
    "additionalProperties": False,
}

TRANSLATE_SYSTEM = (
    "Translate a heavy-equipment operator's spoken question into plain English. "
    "Keep machine terms (boom, bucket, joystick, power mode, hydraulic, ...) as English words. "
    "Return only the translation."
)

ANSWER_SYSTEM = (
    "You answer questions from heavy-equipment operators using ONLY the manual sections provided. "
    "The answer is shown on a tablet in the cab and read aloud, so use 1 to 4 short, plain "
    "sentences with concrete steps, and keep every number and unit from the manual unchanged. "
    "If the sections do not answer the question, set answerable to false and say briefly that the "
    "manual does not cover it. Never add instructions that are not in the sections. "
    "In used_sections, list the exact section titles you relied on."
)


def _english(question: str, lang: str) -> str:
    if lang == "en-IN" or question.isascii():
        return question
    out = complete_json(TRANSLATE_SYSTEM, f"Question ({LANG_NAMES.get(lang, lang)}): {question}",
                        TRANSLATE_SCHEMA, max_tokens=300, fast=True)
    return out.get("english") or question


def _machine_label(machine_type: str) -> str:
    return machine_type.replace("_", " ")


def _source(h: rag.Hit) -> dict:
    return {"doc": h.doc, "section": h.section}


def _first_sentences(text: str, n: int = 3) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:n])


def ask(question: str, machine_type: str, lang: str) -> dict:
    """Returns an AssistantAnswer dict (CONTRACT §4)."""
    machine = _machine_label(machine_type)
    llm_ok = True
    try:
        english = _english(question, lang)
    except LLMUnavailable as e:
        log.info("assistant: translation unavailable (%s)", e)
        english, llm_ok = question, False

    hits = rag.relevant(rag.retrieve(english, machine_type, k=TOP_K))
    if not hits:
        return {"answer": NOT_FOUND.get(lang, NOT_FOUND["en-IN"]).format(machine=machine),
                "lang": lang if lang in NOT_FOUND else "en-IN", "sources": []}

    if llm_ok:
        sections = "\n\n".join(f"[{h.section}]\n{h.text}" for h in hits)
        prompt = (
            f"Machine: {machine}\n"
            f"Answer in: {LANG_NAMES.get(lang, 'English')}\n"
            f"Operator's question: {question}\n"
            + (f"(English: {english})\n" if english != question else "")
            + f"\nManual sections ({hits[0].doc}):\n\n{sections}"
        )
        try:
            out = complete_json(ANSWER_SYSTEM, prompt, ANSWER_SCHEMA, max_tokens=800)
            by_title = {h.section: h for h in hits}
            used = [by_title[s] for s in out.get("used_sections", []) if s in by_title]
            if not out.get("answerable"):
                return {"answer": out.get("answer") or NOT_FOUND.get(lang, NOT_FOUND["en-IN"]).format(
                    machine=machine), "lang": lang, "sources": []}
            if out.get("answer"):
                return {"answer": out["answer"], "lang": lang,
                        "sources": [_source(h) for h in (used or hits[:1])]}
        except LLMUnavailable as e:
            log.info("assistant: answer LLM unavailable (%s)", e)

    # No LLM: read out the best manual section (English).
    top = hits[0]
    return {
        "answer": f"From the {machine} manual, {top.section}: {_first_sentences(top.text)}",
        "lang": "en-IN",
        "sources": [_source(top)],
    }

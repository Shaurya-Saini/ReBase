"""Display text in the operator's language, without an LLM.

Seed data and checklist content are authored in English. `data/i18n/<lang>.yaml`
holds hand-written Hindi/Tamil versions of every display string (operator
names, machine models, job titles/sites/hazards, checklist items, estimate
notes). IDs and enum values are never translated.

The API picks the language from `?lang=` or, if absent, the `Accept-Language`
header (so the app can set it once for every request). Missing translations
fall back to English, so nothing ever breaks.
"""

from functools import lru_cache

import yaml
from fastapi import Header, Query

from app.config import BACKEND_DIR
from app.schemas import Lang

I18N_DIR = BACKEND_DIR / "data" / "i18n"
DEFAULT = "en-IN"


@lru_cache
def _table(lang: str) -> dict:
    path = I18N_DIR / f"{lang}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def tr(lang: str, section: str, key: str, default: str) -> str:
    """Translation of `default` (English) for `section`/`key`, or `default` itself."""
    if lang == DEFAULT:
        return default
    value = (_table(lang).get(section) or {}).get(key)
    return value if isinstance(value, str) and value else default


def tr_list(lang: str, section: str, key: str, default: list[str]) -> list[str]:
    if lang == DEFAULT:
        return list(default)
    value = (_table(lang).get(section) or {}).get(key)
    return list(value) if isinstance(value, list) and len(value) == len(default) else list(default)


def tr_entity(lang: str, section: str, entity_id: str, field: str, default: str):
    """Field of a seeded entity, e.g. tr_entity('ta-IN', 'jobs', 'job_001', 'title', 'Trench…')."""
    if lang == DEFAULT:
        return default
    entity = (_table(lang).get(section) or {}).get(entity_id) or {}
    value = entity.get(field)
    if isinstance(default, list):
        return list(value) if isinstance(value, list) and len(value) == len(default) else list(default)
    return value if isinstance(value, str) and value else default


def term(lang: str, group: str, key: str, default: str) -> str:
    """Nested term, e.g. term('hi-IN', 'machine_types', 'excavator', 'excavator')."""
    if lang == DEFAULT:
        return default
    value = ((_table(lang).get("terms") or {}).get(group) or {}).get(key)
    return value if isinstance(value, str) and value else default


def experience_note(lang: str, level: str, machine_type: str, default: str) -> str:
    fmt = (_table(lang).get("terms") or {}).get("experience_note") if lang != DEFAULT else None
    if not fmt:
        return default
    return fmt.format(machine=term(lang, "machine_types", machine_type, machine_type.replace("_", " ")),
                      level=term(lang, "levels", level, level))


def _from_accept_language(header: str | None) -> str | None:
    """'ta-IN,ta;q=0.9,en;q=0.8' → 'ta-IN'. Matches our languages by full tag or prefix."""
    if not header:
        return None
    ours = [l.value for l in Lang]
    for part in header.split(","):
        tag = part.split(";")[0].strip()
        if not tag:
            continue
        for code in ours:
            if tag.lower() == code.lower() or tag.split("-")[0].lower() == code.split("-")[0]:
                return code
    return None


def display_lang(
    lang: Lang | None = Query(None, description="Language for display text; default: Accept-Language, else en-IN"),
    accept_language: str | None = Header(None),
) -> str:
    """FastAPI dependency: the language to render display strings in."""
    if lang is not None:
        return lang.value
    return _from_accept_language(accept_language) or DEFAULT

"""Training Hub content (E26/E27): data/training/<machine_type>_<level>.yaml.

One pre-shift recap module per machine type × experience level. The "next"
module for an operator is the one matching their experience on that machine
type (novice if they have none). Content is English; module steps are text/tip
only — no video links yet (video synthesis deferred, DECISIONS #13).
"""

from functools import lru_cache

import yaml

from app.config import BACKEND_DIR

TRAINING_DIR = BACKEND_DIR / "data" / "training"
LEVELS = ("novice", "intermediate", "expert")


@lru_cache
def all_modules() -> dict[str, dict]:
    """module id → module dict (CONTRACT §4 TrainingModule shape)."""
    modules = {}
    for path in sorted(TRAINING_DIR.glob("*.yaml")):
        m = yaml.safe_load(path.read_text())
        if m["id"] in modules:
            raise ValueError(f"Duplicate training module id {m['id']} in {path}")
        for q in m["quiz"]:
            if not 0 <= q["answer_index"] < len(q["options"]):
                raise ValueError(f"{m['id']}: answer_index out of range in {q['q']!r}")
        m["steps"] = [{"url": None, **s} for s in m["steps"]]
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

"""Checklist content: data/checklists/<machine_type>.yaml (served by E12).

Checklists are structured content, not vector retrieval (see ai/CLAUDE.md).
Per-session item status lives in the DB (ChecklistItemState).
"""

from functools import lru_cache
from pathlib import Path

import yaml

from app.config import BACKEND_DIR

CHECKLIST_DIR = BACKEND_DIR / "data" / "checklists"


@lru_cache
def load_checklist(machine_type: str) -> dict:
    path = CHECKLIST_DIR / f"{machine_type}.yaml"
    data = yaml.safe_load(Path(path).read_text())
    ids = [i["id"] for s in data["sections"] for i in s["items"]]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate checklist item ids in {path}")
    return data


def checklist_items(machine_type: str) -> dict[str, dict]:
    """item_id → {id, text, critical}"""
    return {i["id"]: i for s in load_checklist(machine_type)["sections"] for i in s["items"]}

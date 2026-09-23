"""Prefixed string IDs (CONTRACT §1): op_, mc_, job_, asg_, ses_, alr_, ..."""

import re

from sqlmodel import Session, SQLModel, select


def next_id(db: Session, model: type[SQLModel], prefix: str) -> str:
    """Next `<prefix>_NNN` after the highest numeric id of that prefix.

    Non-numeric ids with the same prefix (e.g. seeded history `ses_h001`) are
    ignored. Fine for a single-process demo server.
    """
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
    ids = db.exec(select(model.id).where(model.id.startswith(f"{prefix}_"))).all()
    highest = max((int(m.group(1)) for i in ids if (m := pattern.match(i))), default=0)
    return f"{prefix}_{highest + 1:03d}"

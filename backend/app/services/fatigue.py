"""Hours worked + rest status (E4) and the session-start gate (E10).

B2 placeholder: always `ok` with zero hours. B3 replaces the body of
`operator_fatigue` with the real rules (settings.MAX_SHIFT_HOURS,
MIN_REST_HOURS, MAX_HOURS_7D over ended/active WorkSessions).
"""

from dataclasses import dataclass, field
from datetime import datetime

from sqlmodel import Session

from app.models import Operator


@dataclass
class Fatigue:
    hours_today: float = 0.0
    hours_7d: float = 0.0
    rest: dict = field(
        default_factory=lambda: {"status": "ok", "next_allowed_start": None, "reason": None}
    )


def operator_fatigue(db: Session, operator: Operator, now: datetime | None = None) -> Fatigue:
    # TODO B3: real hours + rest rules.
    return Fatigue()

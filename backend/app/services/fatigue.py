"""Hours worked + rest status (E4) and the session-start gate (E10).

Rules (placeholders inspired by aviation duty-time rules, not legal limits;
limits live in settings):

- Work = sessions that were started; an active session counts up to now.
- A **shift** is a run of work where each break is shorter than
  MIN_REST_HOURS. A break of MIN_REST_HOURS or more starts a new shift.
- `hours_today` = hours in the current shift (0 once the operator has had a
  full rest). Shift-based rather than calendar-based, so night shifts that
  cross midnight count correctly.
- `hours_7d` = hours worked in the rolling last 7 days.
- `must_rest`: current shift reached MAX_SHIFT_HOURS (allowed again after
  MIN_REST_HOURS off), or the 7-day total reached MAX_HOURS_7D (allowed again
  once old work rolls out of the window).
- `warning`: current shift ≥ WARN_FRACTION_SHIFT of the cap, or 7-day total ≥
  WARN_FRACTION_7D of the cap.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.clock import now_utc
from app.config import settings
from app.models import Operator, WorkSession

WARN_FRACTION_SHIFT = 0.8  # 9.6 h of a 12 h shift
WARN_FRACTION_7D = 0.85  # 51 h of 60 h
WEEK = timedelta(days=7)

Interval = tuple[datetime, datetime]


@dataclass
class Fatigue:
    hours_today: float = 0.0
    hours_7d: float = 0.0
    rest: dict = field(
        default_factory=lambda: {"status": "ok", "next_allowed_start": None, "reason": None}
    )


def _hours(td: timedelta) -> float:
    return td.total_seconds() / 3600


def work_intervals(db: Session, operator_id: str, now: datetime) -> list[Interval]:
    rows = db.exec(
        select(WorkSession).where(
            WorkSession.operator_id == operator_id, WorkSession.started_at.is_not(None)
        )
    ).all()
    spans = [(s.started_at, min(s.ended_at or now, now)) for s in rows]
    return sorted((a, b) for a, b in spans if a < b)


def current_shift(intervals: list[Interval], now: datetime) -> list[Interval]:
    """Intervals of the latest shift, or [] if the operator has fully rested."""
    if not intervals:
        return []
    min_rest = timedelta(hours=settings.MIN_REST_HOURS)
    if now - intervals[-1][1] >= min_rest:
        return []
    shift = [intervals[-1]]
    for prev in reversed(intervals[:-1]):
        if shift[0][0] - prev[1] >= min_rest:
            break
        shift.insert(0, prev)
    return shift


def hours_in_window(intervals: list[Interval], start: datetime, end: datetime) -> float:
    return sum(
        _hours(min(b, end) - max(a, start)) for a, b in intervals if b > start and a < end
    )


def _week_cap_clears_at(intervals: list[Interval], now: datetime) -> datetime:
    """Earliest time (15-min steps) the rolling 7-day total drops below the cap,
    assuming no new work."""
    t = now
    while t < now + WEEK:
        t += timedelta(minutes=15)
        if hours_in_window(intervals, t - WEEK, t) < settings.MAX_HOURS_7D:
            return t
    return now + WEEK


def operator_fatigue(db: Session, operator: Operator, now: datetime | None = None) -> Fatigue:
    now = now or now_utc()
    intervals = work_intervals(db, operator.id, now)
    shift = current_shift(intervals, now)
    shift_h = sum(_hours(b - a) for a, b in shift)
    week_h = hours_in_window(intervals, now - WEEK, now)

    status, reason, next_start = "ok", None, None
    if shift_h >= settings.MAX_SHIFT_HOURS:
        status = "must_rest"
        next_start = shift[-1][1] + timedelta(hours=settings.MIN_REST_HOURS)
        reason = (f"Shift limit reached ({shift_h:.1f} h of {settings.MAX_SHIFT_HOURS:g} h); "
                  f"{settings.MIN_REST_HOURS:g} h rest required")
    elif week_h >= settings.MAX_HOURS_7D:
        status = "must_rest"
        next_start = _week_cap_clears_at(intervals, now)
        reason = f"7-day limit reached ({week_h:.1f} h of {settings.MAX_HOURS_7D:g} h)"
    elif shift_h >= WARN_FRACTION_SHIFT * settings.MAX_SHIFT_HOURS:
        status = "warning"
        reason = f"Long shift: {shift_h:.1f} h of {settings.MAX_SHIFT_HOURS:g} h"
    elif week_h >= WARN_FRACTION_7D * settings.MAX_HOURS_7D:
        status = "warning"
        reason = f"High weekly hours: {week_h:.1f} h of {settings.MAX_HOURS_7D:g} h"

    if next_start is not None:
        next_start = next_start.replace(microsecond=0)
    return Fatigue(
        hours_today=shift_h,
        hours_7d=week_h,
        rest={"status": status, "next_allowed_start": next_start, "reason": reason},
    )

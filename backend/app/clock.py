"""One place for "now". Stored times are UTC; "today" is the IST calendar day
(the operators work in India), matching how the seed lays out shifts."""

from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def today_ist(now: datetime | None = None) -> date:
    return (now or now_utc()).astimezone(IST).date()

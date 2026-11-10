"""Reporting periods: whole calendar days in the business's reporting timezone.

Why this matters: at 01:00 on 1 October in Karachi it is still 30 September in
UTC. A server that uses its own (UTC) date would put that day's invoices in the
wrong month and mark tasks overdue a day late. Every "today" and every period
boundary in the app goes through this module instead.

Accepted inputs (one style per request):
    period=2026-09                   a calendar month
    start=2026-09-01&end=2026-09-15  a custom range, both days inclusive
    (nothing)                        the current month
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


class InvalidPeriod(ValueError):
    pass


@dataclass(frozen=True)
class Period:
    start: date  # inclusive
    end: date  # inclusive
    timezone: str

    def contains(self, day: date | None) -> bool:
        return day is not None and self.start <= day <= self.end


def local_today(timezone_name: str) -> date:
    """Today's date where the business is, not where the server is."""
    try:
        return datetime.now(ZoneInfo(timezone_name)).date()
    except (ZoneInfoNotFoundError, ValueError):
        raise InvalidPeriod(f"Unknown timezone {timezone_name!r}.") from None


def resolve_period(
    period: str | None, start: date | None, end: date | None, today: date, timezone_name: str, max_days: int = 366
) -> Period:
    if period and (start or end):
        raise InvalidPeriod("Use either 'period' or 'start' and 'end', not both.")
    if period:
        m = _MONTH.match(period.strip())
        if not m:
            raise InvalidPeriod("'period' must look like YYYY-MM, for example 2026-09.")
        year, month = int(m.group(1)), int(m.group(2))
        if not 2000 <= year <= 2100:
            raise InvalidPeriod("'period' year is out of range.")
        return Period(date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1]), timezone_name)
    if start or end:
        if not (start and end):
            raise InvalidPeriod("Both 'start' and 'end' are required for a custom range.")
        if start > end:
            raise InvalidPeriod("'start' must be on or before 'end'.")
        if (end - start).days + 1 > max_days:
            raise InvalidPeriod(f"A custom range can be at most {max_days} days.")
        return Period(start, end, timezone_name)
    last = calendar.monthrange(today.year, today.month)[1]
    return Period(today.replace(day=1), today.replace(day=last), timezone_name)

"""Calendar-grid dates independent of GTK."""
from datetime import date


def month_days(year, month, first_weekday=0):
    """Six weeks, with blank cells only at Python's supported date boundaries."""
    first = date(year, month, 1)
    start = first.toordinal() - (first.weekday() - first_weekday) % 7
    return [date.fromordinal(day) if 1 <= day <= date.max.toordinal() else None
            for day in range(start, start + 42)]

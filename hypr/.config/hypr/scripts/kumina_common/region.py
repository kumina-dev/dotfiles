"""Shared, user-scoped regional preferences (no system locale changes)."""
import calendar
from datetime import datetime
import html
import json
import os
from pathlib import Path
import tempfile
import time

from .i18n import MONTHS, WEEKDAYS, translate

DEFAULTS = {
    "clock": "24", "date": "day-first", "week_start": "monday",
    "number_format": "fi", "currency": "EUR",
}
CHOICES = {
    "clock": ("24", "12"),
    "date": ("day-first", "iso", "month-first"),
    "week_start": ("monday", "sunday"),
    "number_format": ("fi", "en"),
    "currency": ("EUR", "USD", "GBP"),
}


def preferences_path():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "kumios/region.json"


def read_preferences(*, strict=False):
    try:
        data = json.loads(preferences_path().read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Expected a preferences object.")
        if any(data.get(key, value) not in CHOICES[key] for key, value in DEFAULTS.items()):
            raise ValueError("Unknown regional preference.")
        return {key: data.get(key, value) for key, value in DEFAULTS.items()}
    except FileNotFoundError:
        return dict(DEFAULTS)
    except (OSError, ValueError) as error:
        if strict:
            raise RuntimeError(f"Could not read regional preferences: {error}") from error
        return dict(DEFAULTS)


def save_preferences(values):
    if set(values) != set(DEFAULTS) or any(values[key] not in CHOICES[key] for key in DEFAULTS):
        raise ValueError("Invalid regional preferences.")
    path = preferences_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(values, stream, indent=2)
            stream.write("\n")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def local_now():
    # Long-lived calendar/clock processes must observe timedatectl changes.
    time.tzset()
    return datetime.now().astimezone()


def format_time(moment, preferences):
    if preferences["clock"] == "12":
        return f"{moment.hour % 12 or 12}:{moment.minute:02d} {'AM' if moment.hour < 12 else 'PM'}"
    return f"{moment.hour:02d}:{moment.minute:02d}"


def format_date(moment, preferences):
    if preferences["date"] == "iso":
        return moment.strftime("%Y-%m-%d")
    if preferences["date"] == "month-first":
        return moment.strftime("%m/%d/%Y")
    return f"{moment.day}.{moment.month}.{moment.year}"


def first_weekday(preferences):
    return 6 if preferences["week_start"] == "sunday" else 0


def clock_payload(moment, preferences, language="en"):
    first = first_weekday(preferences)
    days = WEEKDAYS[first:] + WEEKDAYS[:first]
    title = f"{translate(MONTHS[moment.month - 1], language=language)} {moment.year}"
    heading = " ".join(translate(day, language=language)[:2] for day in days)
    weeks = calendar.Calendar(first).monthdayscalendar(moment.year, moment.month)
    rows = [" ".join(f"{day:2d}" if day else "  " for day in week).rstrip() for week in weeks]
    month = "\n".join([title.center(20).rstrip(), heading, *rows])
    return {
        "text": format_time(moment, preferences),
        "tooltip": html.escape(format_date(moment, preferences)) + "\n<tt>" + html.escape(month) + "</tt>",
    }

"""Local all-day events, stored separately from dotfiles."""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
import os
from pathlib import Path
import sqlite3

from kumina_common.i18n import translate as tr


class CalendarError(RuntimeError):
    pass


@dataclass(frozen=True)
class Event:
    id: int
    day: str
    title: str
    notes: str


def database_path():
    return Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share') / 'kumios/calendar.sqlite3'


def validate_day(day):
    try:
        parsed = date.fromisoformat(day)
        if parsed.isoformat() != day:
            raise ValueError
    except (TypeError, ValueError):
        raise CalendarError(tr('Enter a valid date as YYYY-MM-DD.')) from None
    return day


def validate_event(day, title, notes):
    validate_day(day)
    if not isinstance(title, str) or not isinstance(notes, str):
        raise CalendarError(tr('An event title and notes must be text.'))
    title = title.strip()
    notes = notes.strip()
    if not title or len(title) > 160 or '\n' in title or '\r' in title:
        raise CalendarError(tr('Use a title of 1–160 characters on one line.'))
    if len(notes) > 2000:
        raise CalendarError(tr('Notes can contain up to 2000 characters.'))
    return day, title, notes


@contextmanager
def database():
    connection = None
    try:
        path = database_path()
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        connection = sqlite3.connect(path, timeout=3)
        connection.row_factory = sqlite3.Row
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, 1):
            raise CalendarError(tr('This calendar database needs a newer KumiOS version.'))
        if version == 0:
            with connection:
                connection.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day TEXT NOT NULL,
                    title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 160),
                    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 2000)
                )''')
                connection.execute('CREATE INDEX IF NOT EXISTS events_day ON events(day)')
                connection.execute('PRAGMA user_version = 1')
        with connection:
            yield connection
    except (sqlite3.Error, OSError) as error:
        raise CalendarError(tr('Could not access calendar events: {error}', error=str(error))) from error
    finally:
        if connection is not None:
            connection.close()


def list_range(start, end):
    validate_day(start)
    validate_day(end)
    if start > end:
        raise CalendarError(tr('The end date must not precede the start date.'))
    with database() as connection:
        rows = connection.execute(
            'SELECT id, day, title, notes FROM events WHERE day BETWEEN ? AND ? ORDER BY day, title COLLATE NOCASE, id',
            (start, end),
        ).fetchall()
    return [Event(**dict(row)) for row in rows]


def save(day, title, notes='', *, event_id=None):
    day, title, notes = validate_event(day, title, notes)
    with database() as connection:
        if event_id is None:
            cursor = connection.execute('INSERT INTO events(day, title, notes) VALUES (?, ?, ?)', (day, title, notes))
            event_id = cursor.lastrowid
        else:
            cursor = connection.execute('UPDATE events SET day=?, title=?, notes=? WHERE id=?', (day, title, notes, event_id))
            if cursor.rowcount != 1:
                raise CalendarError(tr('This event no longer exists. Refresh the calendar.'))
    return Event(event_id, day, title, notes)


def delete(event_id):
    with database() as connection:
        cursor = connection.execute('DELETE FROM events WHERE id=?', (event_id,))
        if cursor.rowcount != 1:
            raise CalendarError(tr('This event no longer exists. Refresh the calendar.'))

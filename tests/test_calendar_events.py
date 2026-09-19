from concurrent.futures import ThreadPoolExecutor
from datetime import date
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hypr/.config/hypr/scripts'))
from calendar_app import events
from calendar_app.model import month_days
from kumina_common import i18n


class EventTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        env = patch.dict(os.environ, {'XDG_DATA_HOME': directory.name})
        env.start()
        self.addCleanup(env.stop)
        language = patch.object(i18n, 'LANGUAGE', 'en')
        language.start()
        self.addCleanup(language.stop)

    def test_create_persists_across_connections_and_honors_data_directory(self):
        event = events.save('2026-09-19', '  Appointment  ', 'Some notes')
        self.assertEqual(events.list_range('2026-09-19', '2026-09-19'), [event])
        self.assertEqual(event.title, 'Appointment')
        self.assertEqual(events.database_path(), Path(os.environ['XDG_DATA_HOME']) / 'kumios/calendar.sqlite3')
        with sqlite3.connect(events.database_path()) as connection:
            self.assertEqual(connection.execute('SELECT title FROM events').fetchone()[0], 'Appointment')

    def test_edit_can_move_an_event_without_creating_a_duplicate(self):
        event = events.save('2026-09-19', 'Before')
        edited = events.save('2026-10-01', 'After', 'Changed', event_id=event.id)
        self.assertEqual(edited.id, event.id)
        self.assertEqual(events.list_range('2026-09-19', '2026-09-19'), [])
        self.assertEqual(events.list_range('2026-10-01', '2026-10-01'), [edited])

    def test_delete_removes_only_the_requested_event(self):
        first = events.save('2026-09-19', 'First')
        second = events.save('2026-09-19', 'Second')
        events.delete(first.id)
        self.assertEqual(events.list_range('2026-09-19', '2026-09-19'), [second])
        with self.assertRaisesRegex(events.CalendarError, 'no longer exists'):
            events.delete(first.id)

    def test_stale_edit_is_not_inserted_as_a_new_event(self):
        event = events.save('2026-09-19', 'Old')
        events.delete(event.id)
        replacement = events.save(event.day, 'Replacement')
        self.assertNotEqual(replacement.id, event.id)
        with self.assertRaisesRegex(events.CalendarError, 'no longer exists'):
            events.save(event.day, 'Changed', event_id=event.id)
        self.assertEqual(events.list_range(event.day, event.day), [replacement])

    def test_invalid_dates_are_rejected_before_creating_database(self):
        for value in ('2026-02-29', '20260919', '2026-9-19', '19.9.2026', '', None):
            with self.subTest(value=value), self.assertRaises(events.CalendarError):
                events.save(value, 'Title')
        self.assertFalse(events.database_path().exists())
        self.assertEqual(events.save('2024-02-29', 'Leap day').day, '2024-02-29')

    def test_invalid_edit_leaves_previous_values_intact(self):
        event = events.save('2026-09-19', 'Keep me')
        for title, notes in (('', ''), ('   ', ''), ('a' * 161, ''), ('two\nlines', ''), ('Title', 'a' * 2001), (None, '')):
            with self.assertRaises(events.CalendarError):
                events.save(event.day, title, notes, event_id=event.id)
            self.assertEqual(events.list_range(event.day, event.day), [event])

    def test_unicode_quotes_and_sql_are_stored_as_text(self):
        title = "Äiti's <event>; DROP TABLE events; --"
        event = events.save('2026-09-19', title, 'Line 1\nLine 2 & {notes}')
        self.assertEqual(events.list_range(event.day, event.day), [event])
        events.save(event.day, 'Still works')
        self.assertEqual(len(events.list_range(event.day, event.day)), 2)

    def test_range_is_inclusive_and_stably_sorted(self):
        events.save('2026-09-18', 'Outside')
        z = events.save('2026-09-19', 'zebra')
        a = events.save('2026-09-19', 'Alpha')
        end = events.save('2026-09-20', 'End')
        events.save('2026-09-21', 'Outside')
        self.assertEqual(events.list_range('2026-09-19', '2026-09-20'), [a, z, end])
        with self.assertRaises(events.CalendarError):
            events.list_range('2026-09-20', '2026-09-19')

    def test_newer_schema_is_not_downgraded(self):
        events.save('2026-09-19', 'Preserved')
        with sqlite3.connect(events.database_path()) as connection:
            connection.execute('PRAGMA user_version=2')
        with self.assertRaisesRegex(events.CalendarError, 'newer KumiOS'):
            events.save('2026-09-20', 'Rejected')
        with sqlite3.connect(events.database_path()) as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 2)
            self.assertEqual(connection.execute('SELECT title FROM events').fetchall(), [('Preserved',)])

    def test_corrupt_file_is_reported_without_replacing_it(self):
        path = events.database_path()
        path.parent.mkdir(parents=True)
        original = b'not a SQLite database'
        path.write_bytes(original)
        with self.assertRaisesRegex(events.CalendarError, 'Could not access'):
            events.list_range('2026-09-19', '2026-09-19')
        self.assertEqual(path.read_bytes(), original)

    def test_simultaneous_initialization_and_writes_do_not_lose_events(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            created = list(pool.map(lambda n: events.save('2026-09-19', f'Event {n}'), range(8)))
        loaded = events.list_range('2026-09-19', '2026-09-19')
        self.assertEqual({event.id for event in created}, {event.id for event in loaded})
        self.assertEqual(len(loaded), 8)

    def test_failed_transaction_rolls_back(self):
        event = events.save('2026-09-19', 'Preserved')
        with self.assertRaises(events.CalendarError):
            with events.database() as connection:
                connection.execute('DELETE FROM events')
                connection.execute('INSERT INTO missing_table VALUES (1)')
        self.assertEqual(events.list_range(event.day, event.day), [event])


class MonthGridTests(unittest.TestCase):
    def test_every_month_has_six_weeks_in_both_week_orders(self):
        for month in range(1, 13):
            for first in (0, 6):
                days = month_days(2024, month, first)
                self.assertEqual(len(days), 42)
                self.assertEqual(days[0].weekday(), first)
                self.assertEqual([day.toordinal() for day in days], list(range(days[0].toordinal(), days[0].toordinal() + 42)))
                self.assertIn(date(2024, month, 1), days)
        self.assertIn(date(2024, 2, 29), month_days(2024, 2))

    def test_date_boundaries_have_blank_cells_instead_of_overflow(self):
        first = month_days(1, 1, 6)
        last = month_days(9999, 12, 0)
        self.assertEqual(len(first), 42)
        self.assertEqual(len(last), 42)
        self.assertIsNone(first[0])
        self.assertIsNone(last[-1])
        self.assertIn(date.min, first)
        self.assertIn(date.max, last)


if __name__ == '__main__':
    unittest.main()

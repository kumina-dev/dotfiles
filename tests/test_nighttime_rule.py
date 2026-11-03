"""Day/night rule for Automatic appearance (KNightTime schedule).

plasma/appearance.py and the Control Center's NightTime.js must agree. The JS
rule runs under Node on the same cases. Nothing here talks to D-Bus.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kumios_appearance_rule', ROOT / 'plasma/appearance.py')
appearance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(appearance)
NIGHT_TIME_JS = ROOT / 'plasma/plasmoids/org.kumios.controlcenter/contents/ui/NightTime.js'

HOUR = 3600 * 1000
DAY = 24 * HOUR


def day(index, noon=12 * HOUR):
    """One schedule entry: morning 06:00-07:00, evening 18:00-19:00 (relative ms)."""
    base = index * DAY
    return (base + noon, base + 6 * HOUR, base + 7 * HOUR, base + 18 * HOUR, base + 19 * HOUR)


def reply(entries):
    """gdbus text form: the first tuple carries int64 type prefixes, the rest do not."""
    parts = []
    for i, entry in enumerate(entries):
        prefix = 'int64 ' if i == 0 else ''
        parts.append('(' + ', '.join(prefix + str(v) for v in entry) + ')')
    return "({'Cookie': <uint32 8>, 'Schedule': <('dynamic', <[" + ', '.join(parts) + "]>)>},)"


WEEK = reply([day(i) for i in range(3)])
CASES = [
    ('mid-day', WEEK, DAY + 12 * HOUR, True),
    ('night between days', WEEK, DAY + 23 * HOUR, False),
    ('early morning transition is night', WEEK, DAY + 6 * HOUR + 10 * 60000, False),
    ('late morning transition is day', WEEK, DAY + 6 * HOUR + 40 * 60000, True),
    ('early evening transition is day', WEEK, DAY + 18 * HOUR + 10 * 60000, True),
    ('late evening transition is night', WEEK, DAY + 18 * HOUR + 40 * 60000, False),
    ('first entry has int64 prefixes', WEEK, 12 * HOUR, True),
    ('before the schedule is unknown', WEEK, 2 * HOUR, None),
    ('after the schedule is unknown', WEEK, 3 * DAY + 2 * HOUR, None),
    ('empty schedule is unknown', "({'Cookie': <uint32 1>, 'Schedule': <('dynamic', <@a(xxxxx) []>)>},)", 0, None),
    ('unreadable reply is unknown', 'Error: org.freedesktop.DBus.Error.ServiceUnknown', 0, None),
]


class RuleTests(unittest.TestCase):
    def test_python_rule(self):
        for label, text, now, expected in CASES:
            with self.subTest(label):
                self.assertIs(appearance.is_daytime(text, now), expected)

    @unittest.skipUnless(shutil.which('node'), 'node is not installed')
    def test_control_center_rule_matches(self):
        source = NIGHT_TIME_JS.read_text().replace('.pragma library', '', 1)
        script = (source + '\nconst cases = ' + json.dumps([[t, n] for _, t, n, _ in CASES]) + ';\n'
                  + 'console.log(JSON.stringify(cases.map(c => { const r = isDaytime(c[0], c[1]);'
                  + ' return r === undefined ? null : r })));\n')
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=30, check=True)
        self.assertEqual(json.loads(result.stdout), [expected for *_, expected in CASES])

    def test_daytime_subscribes_once_and_releases(self):
        calls = []

        def fake_run(*args):
            calls.append(args)
            return WEEK if args[-2].endswith('Subscribe') else '()'

        original = appearance.run
        appearance.run = fake_run
        try:
            appearance.daytime()
        finally:
            appearance.run = original
        self.assertTrue(calls[0][-2].endswith('Subscribe'))
        self.assertEqual(calls[1][-2:], ('org.kde.NightTime.Manager.Unsubscribe', '8'))
        self.assertEqual(len(calls), 2)

    def test_unavailable_service_is_unknown(self):
        def failing_run(*args):
            raise subprocess.CalledProcessError(1, args)

        original = appearance.run
        appearance.run = failing_run
        try:
            self.assertIsNone(appearance.daytime())
        finally:
            appearance.run = original


if __name__ == '__main__':
    unittest.main()

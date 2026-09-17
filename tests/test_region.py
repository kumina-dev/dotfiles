import json
import os
from datetime import datetime
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hypr/.config/hypr/scripts"))
from kumina_common import region
from settings_app import region as backend


class RegionTests(unittest.TestCase):
    def test_twelve_hour_midnight_noon_and_evening(self):
        prefs = dict(region.DEFAULTS, clock="12")
        for hour, expected in ((0, "12:05 AM"), (12, "12:05 PM"), (23, "11:05 PM")):
            self.assertEqual(region.format_time(datetime(2026, 9, 17, hour, 5), prefs), expected)
        self.assertEqual(region.format_time(datetime(2026, 9, 17, 0, 5), region.DEFAULTS), "00:05")

    def test_date_formats_and_calendar_week_start(self):
        now = datetime(2026, 9, 17)
        for style, expected in (("day-first", "17.9.2026"), ("iso", "2026-09-17"), ("month-first", "09/17/2026")):
            self.assertEqual(region.format_date(now, dict(region.DEFAULTS, date=style)), expected)
        monday = region.clock_payload(now, region.DEFAULTS)
        sunday = region.clock_payload(now, dict(region.DEFAULTS, week_start="sunday"))
        self.assertIn("Mo Tu We Th Fr Sa Su", monday["tooltip"])
        self.assertIn("Su Mo Tu We Th Fr Sa", sunday["tooltip"])
        self.assertEqual(json.loads(json.dumps(sunday)), sunday)

    def test_preferences_roundtrip_and_invalid_file_fallback(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"XDG_CONFIG_HOME": temp}):
            self.assertEqual(region.read_preferences(), region.DEFAULTS)
            prefs = dict(region.DEFAULTS, clock="12", week_start="sunday")
            region.save_preferences(prefs)
            self.assertEqual(region.read_preferences(strict=True), prefs)
            path = region.preferences_path()
            for content in ('{', '[]', '{"clock": "13"}', '{"clock": null}'):
                path.write_text(content)
                self.assertEqual(region.read_preferences(), region.DEFAULTS)
                with self.assertRaises(RuntimeError):
                    region.read_preferences(strict=True)

    def test_invalid_save_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"XDG_CONFIG_HOME": temp}):
            region.save_preferences(region.DEFAULTS)
            original = region.preferences_path().read_bytes()
            with self.assertRaises(ValueError):
                region.save_preferences(dict(region.DEFAULTS, clock="13"))
            self.assertEqual(region.preferences_path().read_bytes(), original)

    def test_failed_replace_preserves_preferences_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"XDG_CONFIG_HOME": temp}):
            region.save_preferences(region.DEFAULTS)
            with patch.object(Path, "replace", side_effect=OSError("disk error")):
                with self.assertRaises(OSError):
                    region.save_preferences(dict(region.DEFAULTS, clock="12"))
            self.assertEqual(region.read_preferences(strict=True), region.DEFAULTS)
            self.assertEqual(list(region.preferences_path().parent.iterdir()), [region.preferences_path()])

    def test_timezone_change_is_validated_and_verified(self):
        with patch.object(backend, "_command", side_effect=["UTC\nEurope/Helsinki", "UTC", "", "Europe/Helsinki"]) as command:
            self.assertEqual(backend.set_timezone("Europe/Helsinki"), "Europe/Helsinki")
            self.assertEqual(command.call_args_list[2].args, ("set-timezone", "Europe/Helsinki"))

    def test_invalid_timezone_never_changes_system(self):
        with patch.object(backend, "_command", return_value="UTC") as command:
            with self.assertRaises(ValueError):
                backend.set_timezone("Europe/Helsinki; touch /tmp/no")
            self.assertEqual(command.call_count, 1)

    def test_same_timezone_never_requests_authentication(self):
        with patch.object(backend, "_command", side_effect=["UTC", "UTC", "UTC"]) as command:
            self.assertEqual(backend.set_timezone("UTC"), "UTC")
            self.assertFalse(any(call.args[0] == "set-timezone" for call in command.call_args_list))

    def test_denied_timezone_change_is_reported(self):
        with patch.object(backend, "_command", side_effect=["UTC\nEurope/Helsinki", "UTC", RuntimeError("Access denied")]):
            with self.assertRaisesRegex(RuntimeError, "Access denied"):
                backend.set_timezone("Europe/Helsinki")

    def test_unapplied_timezone_is_not_reported_as_success(self):
        with patch.object(backend, "_command", side_effect=["UTC\nEurope/Helsinki", "UTC", "", "UTC"]):
            with self.assertRaisesRegex(RuntimeError, "not applied"):
                backend.set_timezone("Europe/Helsinki")


if __name__ == "__main__":
    unittest.main()

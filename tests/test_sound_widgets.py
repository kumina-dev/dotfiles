import sys
import time
import unittest
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hypr/.config/hypr/scripts"))

from control_center.audio import Device

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import GLib, Gtk
    HAS_GTK = Gtk.init_check()[0]
except (ImportError, ValueError):
    HAS_GTK = False

if HAS_GTK:
    from control_center.widgets import sound


SPEAKERS = Device(41, "141", "speakers", "Speakers", "output")
HEADPHONES = Device(42, "142", "headphones", "USB Headphones", "output")


def endpoint_state(volume=55, device=SPEAKERS, muted=False):
    return {"devices": [SPEAKERS, HEADPHONES], "device": device,
            "volume": volume, "muted": muted, "error": None}


def pump_until(condition, timeout=1):
    end = time.monotonic() + timeout
    while not condition() and time.monotonic() < end:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.005)
    if not condition():
        raise AssertionError("GTK operation did not finish")


@unittest.skipUnless(HAS_GTK, "GTK 3 and a display are required")
class WidgetTests(unittest.TestCase):
    def setUp(self):
        self.jobs = []
        self.refreshes = []
        self.patcher = patch.object(sound, "run_async", side_effect=self.defer)
        self.patcher.start()
        self.endpoint = sound.AudioEndpoint("output", lambda: self.refreshes.append(True))
        self.endpoint.apply_state(endpoint_state(), self.endpoint.revision)

    def tearDown(self):
        self.endpoint.destroy()
        # Allow any accepted final volume to finish before removing the mock.
        for job in self.jobs:
            if not job["future"].done():
                job["future"].set_result(None)
        self.patcher.stop()

    def defer(self, action, callback=None, error_callback=None):
        future = Future()
        self.jobs.append({"action": action, "callback": callback,
                          "error_callback": error_callback, "future": future})
        return future

    def finish(self, index, error=None):
        job = self.jobs[index]
        if error is not None:
            job["future"].set_exception(error)
            if job["error_callback"]:
                job["error_callback"](error)
        else:
            job["future"].set_result(None)
            if job["callback"]:
                job["callback"](None)

    def test_refresh_is_read_only_even_above_slider_limit(self):
        for value in (12, 65, 135):
            self.endpoint.apply_state(endpoint_state(volume=value), self.endpoint.revision)
            self.assertEqual(self.endpoint.volume_label.get_text(), f"{value}%")
        self.assertEqual(self.endpoint.volume_scale.get_value(), 100)
        self.assertEqual(self.jobs, [])
        self.assertIsNone(self.endpoint._volume_timeout)

    def test_dragging_blocks_refresh_from_overwriting_user_value(self):
        self.endpoint.volume_press(None, None)
        self.endpoint.volume_scale.set_value(28)
        self.endpoint.apply_state(endpoint_state(volume=90), self.endpoint.revision)
        self.assertEqual(self.endpoint.volume_scale.get_value(), 28)
        self.assertEqual(self.endpoint.volume_label.get_text(), "28%")
        self.endpoint.volume_release(None, None)

    def test_volume_writes_are_ordered_and_keep_the_latest_value(self):
        self.endpoint.volume_scale.set_value(25)
        pump_until(lambda: len(self.jobs) == 1)
        self.endpoint.volume_scale.set_value(35)
        self.endpoint.volume_scale.set_value(45)
        pump_until(lambda: self.endpoint._volume_timeout is None)
        self.assertEqual(len(self.jobs), 1)
        self.finish(0)
        self.assertEqual(len(self.jobs), 2)
        with patch.object(sound.audio, "set_volume") as write:
            self.jobs[0]["action"]()
            self.jobs[1]["action"]()
            self.assertEqual(write.call_args_list, [
                unittest.mock.call(SPEAKERS, 25), unittest.mock.call(SPEAKERS, 45),
            ])
        self.finish(1)
        self.assertFalse(self.endpoint.pending())

    def test_late_snapshot_cannot_undo_completed_user_change(self):
        old_revision = self.endpoint.revision
        self.endpoint.volume_scale.set_value(20)
        pump_until(lambda: bool(self.jobs))
        self.finish(0)
        self.endpoint.apply_state(endpoint_state(volume=55), old_revision)
        self.assertEqual(self.endpoint.volume_scale.get_value(), 20)
        self.endpoint.apply_state(endpoint_state(volume=20), self.endpoint.revision)
        self.assertEqual(len(self.jobs), 1)

    def test_device_selection_waits_for_confirmed_state_before_volume_writes(self):
        self.endpoint.device_combo.set_active_id(str(HEADPHONES.id))
        self.assertFalse(self.endpoint.volume_scale.get_sensitive())
        self.finish(0)
        self.assertFalse(self.endpoint.volume_scale.get_sensitive())
        self.assertFalse(self.endpoint.mute_button.get_sensitive())
        self.endpoint.apply_state(endpoint_state(device=HEADPHONES), self.endpoint.revision)
        self.assertTrue(self.endpoint.volume_scale.get_sensitive())
        self.assertEqual(self.endpoint._device, HEADPHONES)
        self.assertEqual(len(self.jobs), 1)

    def test_failed_selection_restores_actual_device_and_keeps_error_visible(self):
        self.endpoint.device_combo.set_active_id(str(HEADPHONES.id))
        self.finish(0, RuntimeError("Device disconnected"))
        self.endpoint.apply_state(endpoint_state(), self.endpoint.revision)
        self.assertEqual(self.endpoint.device_combo.get_active_id(), str(SPEAKERS.id))
        self.assertEqual(self.endpoint.error_label.get_text(), "Device disconnected")
        self.assertTrue(self.endpoint.error_label.get_visible())
        self.assertTrue(self.endpoint.volume_scale.get_sensitive())

    def test_mute_cannot_be_submitted_twice_before_confirmation(self):
        self.endpoint.toggle_mute(None)
        self.endpoint.toggle_mute(None)
        self.assertEqual(len(self.jobs), 1)
        self.finish(0)
        self.endpoint.toggle_mute(None)
        self.assertEqual(len(self.jobs), 1)
        self.endpoint.apply_state(endpoint_state(muted=True), self.endpoint.revision)
        self.assertEqual(self.endpoint.mute_button.get_label(), "Unmute")
        self.endpoint.toggle_mute(None)
        self.assertEqual(len(self.jobs), 2)
        with patch.object(sound.audio, "set_mute") as write:
            self.jobs[0]["action"]()
            self.jobs[1]["action"]()
            self.assertEqual(write.call_args_list, [
                unittest.mock.call(SPEAKERS, True), unittest.mock.call(SPEAKERS, False),
            ])
        self.finish(1)

    def test_disconnected_device_disables_controls_and_hotplug_restores_them(self):
        self.endpoint.apply_state({"devices": [], "device": None, "volume": None,
                                   "muted": False, "error": None}, self.endpoint.revision)
        self.assertFalse(self.endpoint.device_combo.get_sensitive())
        self.assertFalse(self.endpoint.volume_scale.get_sensitive())
        self.assertFalse(self.endpoint.mute_button.get_sensitive())
        self.assertEqual(self.endpoint.volume_label.get_text(), "—")
        self.endpoint.apply_state(endpoint_state(), self.endpoint.revision)
        self.assertTrue(self.endpoint.device_combo.get_sensitive())
        self.assertTrue(self.endpoint.volume_scale.get_sensitive())
        self.assertEqual(self.jobs, [])

    def test_destroy_finishes_last_queued_volume_after_running_write(self):
        self.endpoint.volume_scale.set_value(25)
        pump_until(lambda: len(self.jobs) == 1)
        self.endpoint.volume_scale.set_value(40)
        self.endpoint.destroy()
        self.assertIsNone(self.endpoint._volume_timeout)
        self.assertEqual(len(self.jobs), 2)
        self.finish(0)
        with patch.object(sound.audio, "set_volume") as write:
            self.jobs[1]["action"]()
            write.assert_called_once_with(SPEAKERS, 40)
        self.finish(1)

    def test_polling_stops_when_card_is_hidden_and_resumes_when_shown(self):
        window = Gtk.Window()
        card = sound.SoundCard()
        window.add(card)
        window.show_all()
        self.assertIsNotNone(card._timer)
        window.hide()
        self.assertIsNone(card._timer)
        window.show_all()
        self.assertIsNotNone(card._timer)
        window.destroy()
        self.assertIsNone(card._timer)
        self.assertTrue(card._destroyed)


if __name__ == "__main__":
    unittest.main()
